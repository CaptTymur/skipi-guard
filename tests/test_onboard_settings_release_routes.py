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
CONFIG_PATH = ROOT / "configs" / "homes" / "onboard.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

# Literal file set of the onboard settings-adopt candidate
# (worktree skipi-onboard-unified-settings @ 9102071a, diff vs bdc1267a)
# plus the home settings harness (tests/settings_standard_harness.mjs,
# already on onboard origin/main).
SETTINGS_ADOPT_SET = [
    "UNIFIED_SETTINGS_DEFECTS.md",
    "dist/SETTINGS_VERSION",
    "dist/index.html",
    "dist/skipi-onboard-settings-host.js",
    "dist/skipi-settings.css",
    "dist/skipi-settings.js",
    "tests/settings_standard_harness.mjs",
]

SETTINGS_HARNESS = ("onboard_settings_standard", "node tests/settings_standard_harness.mjs")


class OnboardSettingsReleaseRoutesTests(unittest.TestCase):
    """Settings-wave 5x2: settings-adopt + canonical version-bump routing
    for the onboard home."""

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
            "seed onboard home",
            {
                "dist/index.html": "APP_VERSION = '0.1.1';\n",
                "src-tauri/Cargo.toml": 'version = "0.1.1"\n',
                "src-tauri/Cargo.lock": 'version = "0.1.1"\n',
                "src-tauri/tauri.conf.json": '{"version":"0.1.1"}\n',
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
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "onboard",
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
            env=self.child_env(),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def settings_adopt_change(self) -> dict[str, str]:
        return {
            "UNIFIED_SETTINGS_DEFECTS.md": "# defects log\n",
            "dist/SETTINGS_VERSION": "9caeff6\n",
            "dist/index.html": "APP_VERSION = '0.1.1'; /* unified settings menu */\n",
            "dist/skipi-onboard-settings-host.js": "export const host = 'onboard';\n",
            "dist/skipi-settings.css": ":root { color-scheme: light; }\n",
            "dist/skipi-settings.js": "export const settings = 'unified';\n",
            "tests/settings_standard_harness.mjs": "// settings standard harness\n",
        }

    def canonical_bump(self) -> dict[str, str]:
        return {
            "dist/index.html": "APP_VERSION = '0.1.2';\n",
            "src-tauri/Cargo.toml": 'version = "0.1.2"\n',
            "src-tauri/Cargo.lock": 'version = "0.1.2"\n',
            "src-tauri/tauri.conf.json": '{"version":"0.1.2"}\n',
        }

    # --- settings-adopt route ---------------------------------------------

    def test_auto_routes_exact_settings_adopt_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-settings-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "adopt unified settings", self.settings_adopt_change())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "settings-adopt")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "settings-adopt routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertFalse(payload["release_changes"])

    def test_settings_set_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-settings-scope-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            updates = self.settings_adopt_change()
            updates["src-tauri/src/lib.rs"] = "// must stay blocked\n"
            self.commit_files(repo, "settings plus unrelated source", updates)

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIn("src-tauri/src/lib.rs", payload["scope_violations"])
        self.assertIn("changes outside allowed patterns for task 'plugin-host'", payload["errors"])

    def test_settings_adopt_task_cannot_touch_presence_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-settings-presence-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "change protected presence contract",
                {"presence-manifest.json": '{"contracts":["changed"]}\n'},
            )

            proc, payload = self.run_guard(repo, root / "result.json", task="settings-adopt")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("protected path touch requires --override-protected", payload["errors"])

    # --- canonical version-bump route -------------------------------------

    def test_auto_routes_exact_canonical_version_bump_to_release(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-release-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump onboard version", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "release")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "canonical version-bump routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertTrue(payload["release_changes"])

    def test_canonical_bump_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-release-scope-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-non-release-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump under non-release task", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", task="plugin-host")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("release-sensitive path touch is blocked for this task", payload["errors"])

    # --- config contracts ---------------------------------------------------

    def test_settings_adopt_allowlist_is_exactly_the_candidate_file_set(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        allowed = config["allowed_file_patterns"]["settings-adopt"]
        self.assertEqual(sorted(allowed), sorted(SETTINGS_ADOPT_SET))

    def test_settings_adopt_runs_plugin_host_harnesses_plus_settings_standard(self) -> None:
        """Fail-closed precedent (broker/seafarer): settings-adopt keeps the
        full plugin-host harness set and adds the home settings harness."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        plugin_host = {
            (entry["name"], entry["command"])
            for entry in config["harness_commands"]["plugin-host"]
        }
        settings_adopt = {
            (entry["name"], entry["command"])
            for entry in config["harness_commands"]["settings-adopt"]
        }
        self.assertEqual(settings_adopt, plugin_host | {SETTINGS_HARNESS})

    def test_no_task_references_absent_theme_harness(self) -> None:
        """Defect Д1: tests/onboard_theme_default_harness.mjs is absent from
        onboard main and is not part of any onboard route's file set (the
        settings-adopt allowlist does not include it), so no diff can carry it
        into the pushed tree. Any task referencing it would fail every push
        with MODULE_NOT_FOUND. Re-add together with the file (theme-default
        route, precedent crewing/management)."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        for task, entries in config["harness_commands"].items():
            names = {entry["name"] for entry in entries}
            self.assertNotIn("onboard_theme_default", names, task)

    def test_release_allowlist_is_exactly_the_version_banner(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(config["allowed_file_patterns"]["release"], ["dist/index.html"])


if __name__ == "__main__":
    unittest.main()
