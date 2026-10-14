"""host-gateway: the only privileged path from agents to the host.

POST /exec    {cmd, reason, approvalId?, timeoutSec?}
POST /sql     {container, db, query}        read-only SQL in a *postgres* container
POST /decide  {approvalId, decision: approve|reject, note}   (approver tier only)
GET  /whoami, /health

Auth: Authorization: Bearer <per-agent token>. The token's standing tier (from
tokens.json, minted with hgctl.py) decides what the agent may do. Protected and
destructive commands are held for approval: reversible ones an approver-tier
token can release over the network; irreversible/trust-widening ones only the
host operator releases, on the host, with `hgctl.py owner-decide`.

Every action is written to a redacted, append-only audit log.

TRUST MODEL — READ THIS. The tiers reduce *accidental* damage by *well-behaved*
agents; they are NOT a sandbox for a hostile or compromised one. A `root`-tier
token runs `bash -lc` in the host namespaces, which is full host root by design.
The `read`/`operate` allowlists are convenience guardrails, not an airtight
boundary — a determined agent can find escapes. Approval state lives in a bind
mount the executed commands can reach, so a root agent can forge approvals.
Only enable host-gateway, and only hand out a token, for an agent and a host you
trust as much as yourself. See the module README's "Security limitations".
"""
import hashlib
import json
import os
import re
import shlex
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import policy

STATE = os.environ.get("HG_STATE", "/state")
AUDIT_DIR = os.environ.get("HG_AUDIT", "/audit")
MAX_OUTPUT = 60_000
RATE_PER_MIN = {"read": 60, "operate": 40, "root": 30, "approver": 20}
TIMEOUT_MAX = {"read": 120, "operate": 300, "root": 900}
NSENTER = ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "-p", "--"]
HOST_ENV = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", "LANG": "C.UTF-8"}

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}

REDACT = [
    (re.compile(r"(?i)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PWD|CREDENTIAL|AUTH)[A-Z0-9_]*\"?\s*[=:]\s*\"?)[^\s\"',}]+"), r"\1***"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer ***"),
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16})"), "***"),
    (re.compile(r"(\w+://[^:/\s]+:)[^@\s]+@"), r"\1***@"),
]


def redact(text: str) -> str:
    for rx, repl in REDACT:
        text = rx.sub(repl, text)
    return text


def load_json(name, default):
    try:
        with open(os.path.join(STATE, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(name, data):
    path = os.path.join(STATE, name)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def audit(entry: dict):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    day = entry["ts"][:10]
    with _lock, open(os.path.join(AUDIT_DIR, f"{day}.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def rate_ok(token_hash: str, tier: str) -> bool:
    now = time.time()
    with _lock:
        hits = [t for t in _hits.get(token_hash, []) if now - t < 60]
        if len(hits) >= RATE_PER_MIN[tier]:
            _hits[token_hash] = hits
            return False
        _hits[token_hash] = hits + [now]
        return True


def run(argv: list[str], timeout: int) -> dict:
    started = time.time()
    try:
        p = subprocess.run(NSENTER + argv, capture_output=True, timeout=timeout, env=HOST_ENV)
        out = (p.stdout + (b"\n[stderr]\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"") + b"\n[timed out]").decode("utf-8", "replace")
        code = 124
    truncated = len(out) > MAX_OUTPUT
    out = redact(out[-MAX_OUTPUT:] if truncated else out)
    return {"exitCode": code, "output": out, "truncated": truncated, "durationSec": round(time.time() - started, 2)}


def request_approval(ident: dict, cmd: str, reasons: list[str], body: dict) -> tuple[str, str]:
    """File a pending approval in the local store and return (approvalId, decider)."""
    sha = hashlib.sha256(cmd.encode()).hexdigest()
    who = policy.decider(reasons, cmd)
    approval_id = str(uuid.uuid4())
    with _lock:
        pending = load_json("approvals.json", {})
        # Store redacted display copies; the sha above binds the raw command.
        pending[approval_id] = {"sha": sha, "agent": ident["agent"], "used": False, "decider": who,
                                "command": redact(cmd), "gatedBecause": reasons,
                                "reason": redact(body.get("reason") or ""),
                                "requestedAt": datetime.now(timezone.utc).isoformat()}
        save_json("approvals.json", pending)
    return approval_id, who


def approval_valid(approval_id: str, ident: dict, cmd: str) -> str | None:
    rec = load_json("approvals.json", {}).get(approval_id)
    if not rec or rec["agent"] != ident["agent"]:
        return "unknown approval for this agent"
    if rec["used"]:
        return "approval already used"
    if rec["sha"] != hashlib.sha256(cmd.encode()).hexdigest():
        return "command differs from the approved one"
    key = "ownerDecision" if rec.get("decider") == "owner" else "approverDecision"
    if rec.get(key) != "approved":
        who = "owner (on the host)" if rec.get("decider") == "owner" else "an approver"
        return f"approval is not approved by {who}"
    return None


def mark_used(approval_id: str):
    with _lock:
        pending = load_json("approvals.json", {})
        pending[approval_id]["used"] = True
        save_json("approvals.json", pending)


def handle_exec(ident: dict, body: dict) -> tuple[int, dict]:
    cmd = (body.get("cmd") or "").strip()
    tier = ident["tier"]
    if not cmd:
        return 400, {"error": "cmd required"}
    timeout = max(1, min(int(body.get("timeoutSec") or 60), TIMEOUT_MAX[tier]))
    base = {"agent": ident["agent"], "tier": tier, "cmd": redact(cmd), "reason": redact(body.get("reason") or "")}

    if tier in ("read", "operate"):
        try:
            argv = shlex.split(cmd)
        except ValueError as e:
            return 400, {"error": f"parse: {e}"}
        refusal = policy.check_read(argv) if tier == "read" else policy.check_operate(argv, cmd)
        if tier == "operate" and refusal is None and policy.check_read(argv) is not None and policy.gate_reasons(cmd):
            refusal = "operate tier may not touch protected stacks: " + ", ".join(policy.gate_reasons(cmd))
        if refusal:
            audit({**base, "decision": "refused", "why": refusal})
            return 403, {"status": "refused", "error": refusal}
        result = run(argv, timeout)
        audit({**base, "decision": "ran", "exitCode": result["exitCode"]})
        return 200, {"status": "ran", **result}

    plain_read = read_only_argv(cmd)
    if plain_read:
        result = run(plain_read, timeout)
        audit({**base, "decision": "ran", "readOnly": True, "exitCode": result["exitCode"]})
        return 200, {"status": "ran", **result}

    reasons = policy.gate_reasons(cmd)
    approval_id = body.get("approvalId")
    if reasons and not approval_id:
        approval_id, who = request_approval(ident, cmd, reasons, body)
        audit({**base, "decision": "held", "gatedBecause": reasons, "approvalId": approval_id, "decider": who})
        nxt = ("An approver releases it with POST /decide (or `hgctl.py owner-decide`); "
               "then resend the identical cmd with approvalId."
               if who != "owner" else
               "Owner-only: an irreversible or trust-widening command. Write the case "
               "(what, why, backup, rollback) for the operator, who releases it on the host "
               "with `hgctl.py owner-decide`. Then resend the identical cmd with approvalId.")
        return 202, {"status": "approval_required", "approvalId": approval_id, "gatedBecause": reasons,
                     "decider": who, "next": nxt}
    if reasons:
        problem = approval_valid(approval_id, ident, cmd)
        if problem:
            audit({**base, "decision": "refused", "why": problem, "approvalId": approval_id})
            return 403, {"status": "refused", "error": problem}
        mark_used(approval_id)
    result = run(["/bin/bash", "-lc", cmd], timeout)
    audit({**base, "decision": "ran", "exitCode": result["exitCode"], "approvalId": approval_id if reasons else None})
    return 200, {"status": "ran", **result}


SHELL_SYNTAX = re.compile(r"[|&;<>()$`\\*?{}\[\]~\n]")


def read_only_argv(cmd: str) -> list[str] | None:
    """A root agent's plain read (what the read tier may run) skips the gate and runs without a shell."""
    if SHELL_SYNTAX.search(cmd):
        return None
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return None
    return argv if argv and policy.check_read(argv) is None else None


def handle_decide(ident: dict, body: dict) -> tuple[int, dict]:
    approval_id, decision = body.get("approvalId") or "", body.get("decision") or ""
    note = (body.get("note") or "").strip()
    base = {"agent": ident["agent"], "tier": ident["tier"], "cmd": f"DECIDE {approval_id} {decision}", "reason": redact(note)}
    if decision not in ("approve", "reject") or not note:
        return 400, {"error": "decision must be approve or reject, and note (why) is required"}
    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", approval_id):
        return 400, {"error": "approvalId must be an approval UUID"}
    # Decide under the lock, then audit outside it — audit() also takes _lock,
    # and threading.Lock is not reentrant.
    with _lock:
        pending = load_json("approvals.json", {})
        rec = pending.get(approval_id)
        if rec is None:
            outcome, final = "missing", None
        elif rec.get("decider") == "owner":
            outcome, final = "owner_only", None
        elif "approverDecision" in rec:
            outcome, final = "already", rec["approverDecision"]
        else:
            final = "approved" if decision == "approve" else "rejected"
            rec["approverDecision"], rec["approverNote"] = final, note
            save_json("approvals.json", pending)
            outcome, requester = "decided", rec["agent"]

    if outcome == "missing":
        return 404, {"error": "no such approval"}
    if outcome == "owner_only":
        audit({**base, "decision": "refused", "why": "owner-only", "approvalId": approval_id})
        return 403, {"error": "owner-only approval (destroys persistent data or widens gateway trust); "
                              "the operator releases it on the host with hgctl.py owner-decide"}
    if outcome == "already":
        return 409, {"error": f"approval is already {final}"}
    audit({**base, "decision": final, "approvalId": approval_id, "requester": requester})
    return 200, {"status": final, "approvalId": approval_id,
                 "next": f"Tell {requester} to resend the identical cmd with this approvalId."}


def handle_sql(ident: dict, body: dict) -> tuple[int, dict]:
    container, db, query = body.get("container", ""), body.get("db", ""), body.get("query", "")
    base = {"agent": ident["agent"], "tier": ident["tier"], "cmd": redact(f"SQL[{container}/{db}] {query}")}
    if not re.fullmatch(r"[\w.-]*postgres[\w.-]*", container) or not re.fullmatch(r"[\w-]+", db):
        return 400, {"error": "container must be a *postgres* container and db a plain name"}
    refusal = policy.check_sql(query)
    if refusal:
        audit({**base, "decision": "refused", "why": refusal})
        return 403, {"status": "refused", "error": refusal}
    try:
        user = subprocess.run(NSENTER + ["docker", "exec", container, "printenv", "POSTGRES_USER"],
                              capture_output=True, env=HOST_ENV, timeout=15).stdout.decode().strip() or "postgres"
    except (subprocess.TimeoutExpired, OSError):
        user = "postgres"
    argv = ["docker", "exec", "-e", "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=30000",
            container, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1", "-P", "pager=off", "-c", query]
    result = run(argv, 60)
    audit({**base, "decision": "ran", "exitCode": result["exitCode"]})
    return 200, {"status": "ran", **result}


class Handler(BaseHTTPRequestHandler):
    server_version = "host-gateway/1"

    def _send(self, code: int, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _ident(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None, None
        h = hashlib.sha256(auth[7:].strip().encode()).hexdigest()
        return load_json("tokens.json", {}).get(h), h

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        ident, _ = self._ident()
        if not ident:
            return self._send(401, {"error": "bad token"})
        if self.path == "/whoami":
            return self._send(200, {k: ident[k] for k in ("agent", "tier") if k in ident})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        ident, h = self._ident()
        if not ident:
            return self._send(401, {"error": "bad token"})
        if ident["tier"] == "approver":
            routes = {"/decide": handle_decide}
        elif ident["tier"] in policy.TIERS:
            routes = {"/exec": handle_exec, "/sql": handle_sql}
        else:
            return self._send(403, {"error": "this agent has no host access; delegate to an ops agent"})
        if self.path not in routes:
            return self._send(403 if self.path in ("/exec", "/sql", "/decide") else 404,
                              {"error": f"{ident['tier']} tier may not use {self.path}"})
        if not rate_ok(h, ident["tier"]):
            audit({"agent": ident["agent"], "tier": ident["tier"], "decision": "rate_limited", "path": self.path})
            return self._send(429, {"error": "rate limit"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid json"})
        self._send(*routes[self.path](ident, body))

    def log_message(self, fmt, *args):
        pass  # the audit log is the record


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
