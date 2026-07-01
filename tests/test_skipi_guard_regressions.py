from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"


class SkipiGuardRegressionTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")

    def run_guard(
        self, repo: Path, result_json: Path
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "broker",
                "--task",
                "plugin-host",
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

    def test_deleted_protected_and_release_sensitive_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-delete-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "backend").mkdir()
            (repo / "backend" / "prod-data.json").write_text('{"prod": true}\n', encoding="utf-8")
            (repo / "latest.json").write_text('{"latest": "1.0.0"}\n', encoding="utf-8")
            self.run_git(repo, "add", "backend/prod-data.json", "latest.json")
            self.run_git(repo, "commit", "-q", "-m", "seed protected files")

            (repo / "backend" / "prod-data.json").unlink()
            (repo / "latest.json").unlink()
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "delete protected files")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["changed_files"], ["backend/prod-data.json", "latest.json"])
        self.assertTrue(payload["release_changes"])
        touched = payload["protected_paths_touched"]
        self.assertTrue(
            any(entry["path"] == "backend/prod-data.json" and entry["kind"] == "protected" for entry in touched)
        )
        self.assertTrue(
            any(entry["path"] == "latest.json" and entry["kind"] == "release-sensitive" for entry in touched)
        )

    def test_added_protected_and_release_sensitive_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-add-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
            self.run_git(repo, "add", "README.md")
            self.run_git(repo, "commit", "-q", "-m", "seed repo")

            (repo / "backend").mkdir()
            (repo / "backend" / "prod-data.json").write_text('{"prod": true}\n', encoding="utf-8")
            (repo / "latest.json").write_text('{"latest": "1.0.0"}\n', encoding="utf-8")
            self.run_git(repo, "add", "backend/prod-data.json", "latest.json")
            self.run_git(repo, "commit", "-q", "-m", "add protected files")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["changed_files"], ["backend/prod-data.json", "latest.json"])
        self.assertTrue(payload["protected_paths_touched"])
        self.assertTrue(payload["release_changes"])


if __name__ == "__main__":
    unittest.main()
