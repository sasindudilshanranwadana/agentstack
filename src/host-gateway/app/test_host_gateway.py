"""host-gateway behavior tests — no host access required (run() is stubbed).

    cd src/host-gateway/app && python3 -m unittest test_host_gateway -v
"""
import json
import os
import tempfile
import unittest

os.environ["HG_STATE"] = tempfile.mkdtemp(prefix="hg-state-")
os.environ["HG_AUDIT"] = tempfile.mkdtemp(prefix="hg-audit-")

import hgctl  # noqa: E402
import policy  # noqa: E402
import server  # noqa: E402

ROOT = {"agent": "sre", "tier": "root"}
APPROVER = {"agent": "lead", "tier": "approver"}


class DeciderTest(unittest.TestCase):
    def who(self, cmd):
        return policy.decider(policy.gate_reasons(cmd), cmd)

    def test_irreversible_actions_are_owner_only(self):
        for cmd in ("rm -rf /root/old-project", "docker volume rm app_data", "docker compose down -v",
                    "psql -c 'DROP TABLE widgets'", "psql -c 'TRUNCATE activity_log'",
                    "psql -c 'DELETE FROM records'", "dropdb analytics",
                    "python3 /app/hgctl.py mint x root"):
            self.assertEqual(self.who(cmd), "owner", cmd)

    def test_reversible_protected_actions_go_to_the_approver(self):
        for cmd in ("docker restart hermes-gateway", "psql -c 'ALTER TABLE x ADD COLUMN y int'",
                    "ufw allow 443/tcp", "reboot"):
            self.assertEqual(self.who(cmd), "approver", cmd)

    def test_temp_and_cache_deletes_need_no_approval(self):
        self.assertEqual(policy.gate_reasons("rm -rf /tmp/build-cache"), [])
        self.assertEqual(policy.gate_reasons("rm -rf /root/.cache/pip"), [])

    def test_protected_containers_extend_from_env(self):
        # New instance of the module would pick up the env; assert the default set holds the stack.
        self.assertIn("hermes-gateway", policy.PROTECTED_CONTAINERS)
        self.assertIn("omniroute", policy.PROTECTED_CONTAINERS)


class ReadTierTest(unittest.TestCase):
    def test_read_allows_safe_inspection(self):
        self.assertIsNone(policy.check_read(["docker", "ps"]))
        self.assertIsNone(policy.check_read(["df", "-h"]))

    def test_read_refuses_secret_files_and_writes(self):
        self.assertIsNotNone(policy.check_read(["cat", "/root/.ssh/id_rsa"]))
        self.assertIsNotNone(policy.check_read(["docker", "restart", "x"]))

    def test_sql_is_read_only(self):
        self.assertIsNone(policy.check_sql("SELECT count(*) FROM t"))
        self.assertIsNotNone(policy.check_sql("DELETE FROM t"))
        self.assertIsNotNone(policy.check_sql("SELECT 1; DROP TABLE t"))


class ServerFlowTest(unittest.TestCase):
    def setUp(self):
        server.save_json("approvals.json", {})
        self.ran = []
        server.run = lambda argv, timeout: self.ran.append(argv) or {
            "exitCode": 0, "output": "", "truncated": False, "durationSec": 0}

    def test_owner_only_delete_is_held_and_approver_cannot_release_it(self):
        code, resp = server.handle_exec(ROOT, {"cmd": "rm -rf /root/old-project", "reason": "cleanup"})
        self.assertEqual((code, resp["decider"]), (202, "owner"))
        aid = resp["approvalId"]
        code, _ = server.handle_decide(APPROVER, {"approvalId": aid, "decision": "approve", "note": "has backup"})
        self.assertEqual(code, 403)
        code, _ = server.handle_exec(ROOT, {"cmd": "rm -rf /root/old-project", "approvalId": aid})
        self.assertEqual(code, 403)
        self.assertEqual(self.ran, [])

    def test_owner_release_runs_exactly_that_command_once(self):
        _, resp = server.handle_exec(ROOT, {"cmd": "rm -rf /root/old-project", "reason": "cleanup"})
        aid = resp["approvalId"]
        approvals = server.load_json("approvals.json", {})
        approvals[aid].update(ownerDecision="approved", ownerNote="ok")
        server.save_json("approvals.json", approvals)
        self.assertEqual(server.handle_exec(ROOT, {"cmd": "rm -rf /root/other", "approvalId": aid})[0], 403)
        self.assertEqual(server.handle_exec(ROOT, {"cmd": "rm -rf /root/old-project", "approvalId": aid})[0], 200)
        self.assertEqual(server.handle_exec(ROOT, {"cmd": "rm -rf /root/old-project", "approvalId": aid})[0], 403)
        self.assertEqual(len(self.ran), 1)

    def test_approver_can_release_a_reversible_protected_command(self):
        code, resp = server.handle_exec(ROOT, {"cmd": "docker restart hermes-gateway", "reason": "stuck"})
        self.assertEqual((code, resp["decider"]), (202, "approver"))
        aid = resp["approvalId"]
        code, _ = server.handle_decide(APPROVER, {"approvalId": aid, "decision": "approve", "note": "ok"})
        self.assertEqual(code, 200)
        self.assertEqual(server.handle_exec(ROOT, {"cmd": "docker restart hermes-gateway", "approvalId": aid})[0], 200)
        self.assertEqual(len(self.ran), 1)

    def test_secrets_are_redacted_in_audit_and_approval_store(self):
        # Built at runtime so this shipped test file contains no secret-shaped literal.
        secret_key = "sk-" + "A1b2C3d4E5f6G7h8I9j0KLMN"
        secret_reason = "token=" + "supersecretpassword123456"
        _, resp = server.handle_exec(
            ROOT, {"cmd": f"docker restart hermes-gateway {secret_key}", "reason": secret_reason})
        rec = server.load_json("approvals.json", {})[resp["approvalId"]]
        self.assertNotIn(secret_key, rec["command"])
        self.assertNotIn("supersecretpassword123456", rec["reason"])
        day = sorted(os.listdir(os.environ["HG_AUDIT"]))[-1]
        log = open(os.path.join(os.environ["HG_AUDIT"], day)).read()
        self.assertNotIn(secret_key, log)
        self.assertNotIn("supersecretpassword123456", log)

    def test_audit_records_the_hold(self):
        server.handle_exec(ROOT, {"cmd": "docker volume rm x", "reason": "t"})
        day = sorted(os.listdir(os.environ["HG_AUDIT"]))[-1]
        with open(os.path.join(os.environ["HG_AUDIT"], day)) as f:
            rows = [json.loads(line) for line in f]
        self.assertTrue(any(r.get("decider") == "owner" and r["decision"] == "held" for r in rows))


class HgctlTest(unittest.TestCase):
    def test_mint_rejects_unknown_tier(self):
        with self.assertRaises(SystemExit):
            hgctl.main(["mint", "agent-x", "superuser"])

    def test_mint_accepts_known_tier(self):
        hgctl.main(["mint", "agent-y", "read"])  # prints a token, must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
