from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"


def config_with_harnesses(entries: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "home": "crewing",
        "repo": "/tmp/skipi-crewing-fixture",
        "harness_commands": {
            "plugin-host": entries,
        },
    }


class SkipiGuardConfigSupersetTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        (repo / "configs" / "homes").mkdir(parents=True)

    def commit_config(self, repo: Path, message: str, config: dict[str, Any]) -> str:
        (repo / "configs" / "homes" / "crewing.json").write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )
        self.run_git(repo, "add", "configs/homes/crewing.json")
        self.run_git(repo, "commit", "-q", "-m", message)
        return self.run_git(repo, "rev-parse", "HEAD").stdout.strip()

    def run_superset(self, repo: Path, old_ref: str, new_ref: str, result_json: Path) -> tuple[int, dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "assert-config-superset",
                "--home",
                "crewing",
                "--repo",
                str(repo),
                "--old-ref",
                old_ref,
                "--new-ref",
                new_ref,
                "--json",
                str(result_json),
            ],
            text=True,
            capture_output=True,
        )
        with result_json.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return proc.returncode, payload

    def test_equal_config_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-superset-equal-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.init_repo(repo)
            base = self.commit_config(
                repo,
                "base",
                config_with_harnesses([
                    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
                ]),
            )

            code, payload = self.run_superset(repo, base, base, Path(tmp) / "result.json")

        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["missing_harnesses"], [])

    def test_superset_config_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-superset-add-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.init_repo(repo)
            base = self.commit_config(
                repo,
                "base",
                config_with_harnesses([
                    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
                ]),
            )
            next_ref = self.commit_config(
                repo,
                "add harness",
                config_with_harnesses([
                    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
                    {"name": "crewing_crew_flow_demo", "command": "node tests/crewing_crew_flow_demo_harness.mjs"},
                ]),
            )

            code, payload = self.run_superset(repo, base, next_ref, Path(tmp) / "result.json")

        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["missing_harnesses"], [])

    def test_removed_harness_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-superset-remove-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.init_repo(repo)
            base = self.commit_config(
                repo,
                "base",
                config_with_harnesses([
                    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
                    {"name": "crewing_crew_flow_demo", "command": "node tests/crewing_crew_flow_demo_harness.mjs"},
                ]),
            )
            next_ref = self.commit_config(
                repo,
                "remove harness",
                config_with_harnesses([
                    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
                ]),
            )

            code, payload = self.run_superset(repo, base, next_ref, Path(tmp) / "result.json")

        self.assertEqual(code, 1, payload)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(
            payload["missing_harnesses"],
            [
                {
                    "task": "plugin-host",
                    "name": "crewing_crew_flow_demo",
                    "command": "node tests/crewing_crew_flow_demo_harness.mjs",
                }
            ],
        )
        self.assertIn("new guard config removes harness_commands from the current config", payload["errors"])


if __name__ == "__main__":
    unittest.main()
