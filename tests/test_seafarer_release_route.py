from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"


class SeafarerReleaseRouteTests(unittest.TestCase):
    def child_env(self, *, override_env: str | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
        if override_env is not None:
            env[OVERRIDE_ENV] = override_env
        return env

    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
            env=self.child_env(),
        )

    def commit_files(self, repo: Path, message: str, updates: dict[str, str]) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        self.commit_files(
            repo,
            "seed seafarer version",
            {
                "dist/index.html": '<meta name="app-version" content="0.4.178">\n',
                "src-tauri/Cargo.toml": 'version = "0.4.178"\n',
                "src-tauri/Cargo.lock": 'version = "0.4.178"\n',
                "src-tauri/tauri.conf.json": '{"version":"0.4.178"}\n',
                "presence-manifest.json": '{"contracts":[]}\n',
            },
        )

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        task: str | None = None,
        auto_task: bool = False,
        override: str | None = None,
        override_env: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "seafarer",
            "--repo",
            str(repo),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
            "--json",
            str(result_json),
        ]
        if auto_task:
            command.append("--auto-task")
        elif task:
            command.extend(["--task", task])
        else:
            raise ValueError("task or auto_task is required")
        if override:
            command.extend(["--override-protected", override])
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            env=self.child_env(override_env=override_env),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def canonical_bump(self) -> dict[str, str]:
        return {
            "dist/index.html": '<meta name="app-version" content="0.4.179">\n',
            "src-tauri/Cargo.toml": 'version = "0.4.179"\n',
            "src-tauri/Cargo.lock": 'version = "0.4.179"\n',
            "src-tauri/tauri.conf.json": '{"version":"0.4.179"}\n',
        }

    def test_auto_routes_exact_canonical_version_bump_to_release(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-release-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump seafarer version", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "release")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "canonical version-bump routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertTrue(payload["release_changes"])

    def test_canonical_bump_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-release-scope-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            updates = self.canonical_bump()
            updates["src/unreviewed.js"] = "console.log('must stay blocked');\n"
            self.commit_files(repo, "bump plus unrelated source", updates)

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIn("src/unreviewed.js", payload["scope_violations"])
        self.assertIn("changes outside allowed patterns for task 'plugin-host'", payload["errors"])

    def test_non_release_task_cannot_touch_release_sensitive_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-non-release-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump under non-release task", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", task="plugin-host")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("release-sensitive path touch is blocked for this task", payload["errors"])

    def test_protected_path_requires_valid_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-protected-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "change protected presence contract",
                {"presence-manifest.json": '{"contracts":["changed"]}\n'},
            )

            proc, payload = self.run_guard(repo, root / "result.json", task="release")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("protected path touch requires --override-protected", payload["errors"])

    def test_unknown_override_does_not_authorize_protected_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-unknown-override-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "change protected presence contract",
                {"presence-manifest.json": '{"contracts":["changed"]}\n'},
            )

            proc, payload = self.run_guard(
                repo,
                root / "result.json",
                task="release",
                override="totally-made-up-xyz",
            )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("unknown override token", payload["errors"])

    def test_ambient_override_does_not_authorize_protected_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-ambient-override-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "change protected presence contract",
                {"presence-manifest.json": '{"contracts":["changed"]}\n'},
            )

            proc, payload = self.run_guard(
                repo,
                root / "result.json",
                task="release",
                override_env="seafarer-presence-contracts-bootstrap",
            )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["override_present"])
        self.assertIn("protected path touch requires --override-protected", payload["errors"])


if __name__ == "__main__":
    unittest.main()
