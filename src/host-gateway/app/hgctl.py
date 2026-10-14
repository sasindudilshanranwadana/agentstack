"""Mint/revoke host-gateway tokens and release approvals from the host. Usage:

  hgctl.py mint <agent> <read|operate|root|approver|none>   -> prints token once
  hgctl.py revoke <agent>
  hgctl.py list
  hgctl.py pending                                   -> list approvals awaiting a decision
  hgctl.py owner-decide <approvalId> <approve|reject> "<why>"

Run on the host inside the container, e.g.
  docker exec host-gateway python hgctl.py mint sre root
"""
import hashlib
import json
import os
import secrets
import sys

STATE = os.environ.get("HG_STATE", "/state")
TOKENS = os.path.join(STATE, "tokens.json")
APPROVALS = os.path.join(STATE, "approvals.json")


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save(path, data, mode=0o600):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def main(argv):
    cmd, *rest = argv or ["list"]
    if cmd == "mint":
        agent, tier = rest
        if tier not in ("read", "operate", "root", "approver", "none"):
            sys.exit("tier must be one of: read operate root approver none")
        tokens = {h: v for h, v in _load(TOKENS).items() if v["agent"] != agent}
        tok = "hg_" + secrets.token_urlsafe(32)
        tokens[hashlib.sha256(tok.encode()).hexdigest()] = {"agent": agent, "tier": tier}
        _save(TOKENS, tokens)
        print(tok)
    elif cmd == "revoke":
        _save(TOKENS, {h: v for h, v in _load(TOKENS).items() if v["agent"] != rest[0]})
    elif cmd == "pending":
        for aid, rec in _load(APPROVALS).items():
            decided = rec.get("ownerDecision") or rec.get("approverDecision")
            if not decided and not rec.get("used"):
                print(f"{aid}  [{rec.get('decider', '?')}]  {rec['agent']}: "
                      f"{rec.get('command', '')[:100]}  ({', '.join(rec.get('gatedBecause', []))})")
    elif cmd == "owner-decide":
        approval_id, decision, note = rest
        if decision not in ("approve", "reject") or not note.strip():
            sys.exit("decision must be approve|reject and note must be non-empty")
        approvals = _load(APPROVALS)
        rec = approvals[approval_id]
        key = "ownerDecision" if rec.get("decider") == "owner" else "approverDecision"
        rec[key] = "approved" if decision == "approve" else "rejected"
        rec[key.replace("Decision", "Note")] = note
        _save(APPROVALS, approvals, mode=0o600)
        print(rec[key])
    else:
        for v in sorted(_load(TOKENS).values(), key=lambda v: v["agent"]):
            print(f"{v['agent']:20} {v['tier']}")


if __name__ == "__main__":
    main(sys.argv[1:])
