"""Tier policy for host-gateway: what each tier may run, and what needs approval.

Nothing here is specific to any one deployment. The protected container and
project-directory lists default to the agentstack stack's own services and can
be extended for your own environment with the env vars named below — the agent
must never be able to stop, delete, or reconfigure the pieces it depends on
without a human approving it first.
"""
import os
import re
import shlex

TIERS = ("read", "operate", "root")


def _env_list(name: str, defaults: tuple[str, ...]) -> tuple[str, ...]:
    """Defaults plus any comma-separated additions from the environment."""
    extra = [s.strip() for s in os.environ.get(name, "").split(",") if s.strip()]
    return tuple(dict.fromkeys((*defaults, *extra)))


SECRET_PATH = re.compile(
    r"(\.env\b|/secrets?/|/\.ssh\b|/etc/ssh\b|rclone|\.credentials\.json|auth\.json"
    r"|/etc/shadow|id_rsa|id_ed25519|\.pem\b|\.key\b|tokens\.json)",
    re.I,
)

# Services the agent must not disrupt without approval. Extend for your stack
# with HG_PROTECTED_CONTAINERS / HG_PROTECTED_PROJECTS (comma-separated).
PROTECTED_CONTAINERS = _env_list("HG_PROTECTED_CONTAINERS", (
    "hermes-gateway", "omniroute", "mem0", "mem0-postgres", "host-gateway",
))
PROTECTED_PROJECT_DIRS = _env_list("HG_PROTECTED_PROJECTS", (
    "agentstack", "hermes", "omniroute", "mem0", "host-gateway",
))

# (reason, pattern) — any match on a root/operate command holds it for approval.
GATED = [
    ("protected path", re.compile(
        r"(\.env\b|/secrets?/|/root/\.ssh|/etc/ssh|rclone|\.credentials\.json"
        r"|/var/lib/docker|/boot\b|/app/(state|audit)\b|tokens\.json)", re.I)),
    ("protected container", re.compile(
        r"\bdocker\b.*\b(stop|rm|kill|restart|pause|update|rename|exec|down|up|recreate)\b.*("
        + "|".join(map(re.escape, PROTECTED_CONTAINERS)) + r")", re.I)),
    ("protected compose project", re.compile(
        r"\bcompose\b.*(/opt|/root|/srv)/(" + "|".join(map(re.escape, PROTECTED_PROJECT_DIRS)) + r")\b", re.I)),
    ("volume destruction", re.compile(
        r"\bvolume\s+(rm|prune)\b|\bprune\b.*--volumes|\bdown\b.*\s-v\b|\bdown\b.*--volumes", re.I)),
    ("firewall/ssh/vpn", re.compile(
        r"\b(ufw\s+(?!status)\w+|iptables|ip6tables|nft\b|sshd|tailscale\s+(up|down|set|logout)"
        r"|fail2ban-client\s+(set|unban|stop|reload))", re.I)),
    ("power", re.compile(r"\b(reboot|shutdown|poweroff|halt)\b|\binit\s+[06]\b", re.I)),
    ("package removal/os upgrade", re.compile(
        r"\bapt(-get)?\s+(dist-upgrade|full-upgrade|remove|purge|autoremove)\b|do-release-upgrade", re.I)),
    ("database destruction", re.compile(
        r"\bdrop\s+(table|database|schema|role|user|index|view|materialized)\b|\btruncate\b(?!\s+-s)|\bdelete\s+from\b"
        r"|\bdropdb\b|\bdropuser\b|\bpg_restore\b.*--clean", re.I)),
    ("database schema change", re.compile(r"\balter\s+(table|database|schema|role|user)\b", re.I)),
    ("gateway trust", re.compile(r"/app/(state|audit)\b|tokens\.json|hgctl", re.I)),
    ("disk/account tools", re.compile(
        r"\b(mkfs\S*|wipefs|fdisk|parted|dd\s+if=|userdel|usermod|passwd|chpasswd|crontab\s+-r)\b", re.I)),
    ("recursive perms on system path", re.compile(r"\b(chmod|chown)\s+-R\s+\S*\s*/(etc|usr|bin|root|opt|var)?(\s|$)", re.I)),
]

# Reversible, protected operations are decided by an approver-tier token over the
# network (POST /decide). These few are irreversible or trust-widening: only the
# host operator decides them, on the host, with `hgctl.py owner-decide`. A backup
# plus a waiting period is not permission to delete.
OWNER_ONLY = ("volume destruction", "delete outside allowlist", "database destruction", "gateway trust")


def decider(reasons: list[str], cmd: str) -> str:
    return "owner" if any(r in OWNER_ONLY for r in reasons) else "approver"


DELETE_ALLOW = re.compile(
    r"^(/tmp/|/var/tmp/|/root/\.cache/|/home/[^/]+/\.cache/|/root/\.npm/_cacache"
    r"|/var/log/.+\.(gz|\d+)$|/var/cache/apt/)"
)
DELETE_CMD = re.compile(r"\b(rm|shred|unlink|rmdir)\b|-delete\b|\btruncate\s+-s")


def gate_reasons(cmd: str) -> list[str]:
    reasons = [name for name, rx in GATED if rx.search(cmd)]
    if DELETE_CMD.search(cmd) and not _deletes_within_allowlist(cmd):
        reasons.append("delete outside allowlist")
    return reasons


def _deletes_within_allowlist(cmd: str) -> bool:
    if re.search(r"[`$]|\beval\b", cmd):
        return False
    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError:
        return False
    paths = [t for t in tokens if t.startswith("/")]
    if not paths:
        return False
    return all(DELETE_ALLOW.match(p.rstrip("*") if p.endswith("/*") else p) and ".." not in p for p in paths)


# ---- read tier: argv allowlist, executed without a shell ----
READ_SIMPLE = {
    "df", "du", "free", "uptime", "uname", "hostname", "cat", "head", "tail", "ls", "stat", "wc",
    "grep", "zgrep", "zcat", "ps", "lsblk", "findmnt", "date", "id", "sha256sum", "file", "vmstat",
    "iostat", "dig", "nslookup", "whoami", "nproc", "lscpu", "dpkg", "last", "who", "w", "sensors",
}
DOCKER_READ = {"ps", "inspect", "logs", "stats", "images", "top", "port", "version", "info", "events"}
DOCKER_READ_PAIRS = {("system", "df"), ("volume", "ls"), ("volume", "inspect"), ("network", "ls"),
                     ("network", "inspect"), ("image", "ls"), ("image", "inspect"), ("container", "ls"),
                     ("compose", "ls"), ("scout", "cves"), ("scout", "quickview")}
SYSTEMCTL_READ = {"status", "is-active", "is-enabled", "is-failed", "list-units", "list-timers",
                  "list-unit-files", "show", "--failed"}
CURL_DENY = re.compile(r"^(-X|--request|-d|--data.*|-F|--form|-T|--upload-file|-o|--output|-O|--remote-name|-K|--config)$")


def check_read(argv: list[str]) -> str | None:
    """Return None if allowed for the read tier, else a refusal reason."""
    if not argv:
        return "empty command"
    prog, args = argv[0].rsplit("/", 1)[-1], argv[1:]
    if any(SECRET_PATH.search(a) for a in args):
        return "read tier may not touch secret files"
    if prog in READ_SIMPLE:
        if prog == "dpkg" and args[:1] not in (["-l"], ["-s"], ["--list"]):
            return "dpkg: only -l/-s"
        return None
    if prog == "find":
        bad = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls"}
        return "find action not allowed" if bad & set(args) else None
    if prog == "docker":
        sub = [a for a in args if not a.startswith("-")]
        if not sub:
            return "docker: subcommand required"
        if sub[0] in DOCKER_READ or tuple(sub[:2]) in DOCKER_READ_PAIRS:
            if sub[0] == "events" and "--until" not in args:
                return "docker events needs --until"
            if sub[0] == "logs" and ("-f" in args or "--follow" in args):
                return "no follow"
            if sub[0] == "stats" and "--no-stream" not in args:
                return "docker stats needs --no-stream"
            return None
        if sub[0] == "compose" and ({"ps", "logs"} & set(sub[1:])) and "--follow" not in args:
            after_logs = args[args.index("logs") + 1:] if "logs" in args else []
            return "no follow" if "-f" in after_logs else None
        return f"docker {sub[0]} not allowed for read tier"
    if prog == "journalctl":
        bad = ("--vacuum", "--rotate", "--flush", "--sync", "--relinquish", "-f", "--follow")
        return "journalctl write/follow flags not allowed" if any(a.startswith(bad) for a in args) else None
    if prog == "systemctl":
        return None if args and args[0] in SYSTEMCTL_READ else "systemctl: read verbs only"
    if prog in ("ss", "netstat"):
        return None if "-K" not in args and "--kill" not in args else "no kill"
    if prog == "ip":
        return None if args and args[-1] in ("show", "list", "addr", "route", "link") or "show" in args else "ip: show only"
    if prog == "top":
        return None if "-b" in args else "top needs -b -n1"
    if prog == "curl":
        return "curl write flags not allowed" if any(CURL_DENY.match(a) for a in args) else None
    if prog == "ping":
        return None if "-c" in args else "ping needs -c"
    if prog == "openssl":
        return None if args[:1] in (["s_client"], ["x509"]) else "openssl: s_client/x509 only"
    if prog in ("ufw", "fail2ban-client", "tailscale"):
        return None if args[:1] == ["status"] else f"{prog}: status only"
    if prog == "apt":
        return None if args[:2] == ["list", "--upgradable"] else "apt: list --upgradable only"
    return f"{prog} not in read-tier allowlist"


def check_operate(argv: list[str], cmd: str) -> str | None:
    """Operate tier: read tier plus restarts/compose for non-protected stacks."""
    if check_read(argv) is None:
        return None
    if argv[:1] != ["docker"]:
        return "operate tier: docker restart/compose only beyond read"
    sub = [a for a in argv[1:] if not a.startswith("-")]
    if sub[:1] in (["restart"], ["start"]):
        return None
    if sub[:1] == ["compose"] and any(v in sub for v in ("up", "restart", "pull", "build", "ps", "logs")):
        return None if re.search(r"(/opt|/root|/srv)/[\w.-]+", cmd) else "compose needs an explicit -f/--project-directory path"
    return f"docker {sub[:1]} not allowed for operate tier"


SQL_OK = re.compile(r"^\s*(select|with|explain|show|table|values)\b", re.I)
SQL_BAD = re.compile(r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|set|reset"
                     r"|begin|commit|rollback|vacuum|reindex|cluster|lock|listen|notify|prepare|execute"
                     r"|pg_terminate_backend|pg_cancel_backend|pg_reload_conf|lo_\w+|dblink\w*)\b", re.I)


def check_sql(query: str) -> str | None:
    q = query.strip().rstrip(";")
    if ";" in q:
        return "one statement only"
    if not SQL_OK.match(q):
        return "read-only statements only (SELECT/WITH/EXPLAIN/SHOW)"
    if SQL_BAD.search(re.sub(r"'[^']*'", "''", q)):
        return "statement contains a write/admin keyword"
    return None
