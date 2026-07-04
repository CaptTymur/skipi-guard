from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"


class PluginDeliveryConfigTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-plugin-delivery-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Plugin Delivery Guard Fixture")

    def run_guard(self, repo: Path, result_json: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "plugin-delivery",
                "--task",
                "plugin-delivery",
                "--repo",
                str(repo),
                "--base",
                "HEAD~1",
                "--head",
                "HEAD",
                "--json",
                str(result_json),
            ],
            text=True,
            capture_output=True,
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def seed_repo(self, repo: Path) -> None:
        (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
        self.run_git(repo, "add", "README.md")
        self.run_git(repo, "commit", "-q", "-m", "seed")

    def test_catalog_and_pack_changes_are_release_sensitive_but_allowed_for_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-plugin-delivery-guard-pass-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_repo(repo)

            (repo / "server" / "packs").mkdir(parents=True)
            (repo / "server" / "catalog.json").write_text('{"schema":"skipi-catalog/1"}\n', encoding="utf-8")
            (repo / "server" / "packs" / "demo-0.1.0.skpack.json").write_text('{"schema":"skipi-pack/1"}\n', encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "candidate")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["release_changes"])
        self.assertEqual(payload["errors"], [])
        touched_paths = {entry["path"] for entry in payload["release_paths_touched"]}
        self.assertIn("server/catalog.json", touched_paths)
        self.assertIn("server/packs/demo-0.1.0.skpack.json", touched_paths)

    def test_key_changes_remain_protected_and_fail_without_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-plugin-delivery-guard-key-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_repo(repo)

            (repo / "keys").mkdir()
            (repo / "keys" / "signing-private.jwk").write_text('{"placeholder":"redacted"}\n', encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "bad key")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertTrue(payload["protected_paths_touched"])
        self.assertTrue(any(entry["path"] == "keys/signing-private.jwk" for entry in payload["protected_paths_touched"]))

    def test_harness_command_is_required_for_plugin_delivery_task(self) -> None:
        config = json.loads((ROOT / "configs" / "homes" / "plugin-delivery.json").read_text(encoding="utf-8"))
        commands = {entry["name"]: entry["command"] for entry in config["harness_commands"]["plugin-delivery"]}
        self.assertEqual(commands["plugin_delivery_required_verify_prod_candidate"], "node tests/ci-required-verify-prod-candidate.js")


if __name__ == "__main__":
    unittest.main()
