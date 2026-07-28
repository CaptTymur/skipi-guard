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
CONFIG_PATH = ROOT / "configs" / "homes" / "crewing.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

# Literal file set of the crewing settings-adopt candidate
# (worktree skipi-crewing-unified-settings @ 62bda59e, diff vs merge-base
# a207120a) plus the light-theme fix paths (theme-crewing-20260721 @ 59f06243).
SETTINGS_ADOPT_SET = [
    "dist/SETTINGS_VERSION",
    "dist/index.html",
    "dist/skipi-settings.css",
    "dist/skipi-settings.js",
    "tests/crewing_theme_default_harness.mjs",
]


class CrewingSettingsReleaseRoutesTests(unittest.TestCase):
    """Settings-wave 5x2: settings-adopt + canonical version-bump routing
    for the crewing home (precedents: broker/seafarer settings-adopt,
    seafarer release route skipi-guard#33)."""

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
            "seed crewing home",
            {
                "dist/index.html": "appVersion: '0.4.133'\n",
                "src-tauri/Cargo.toml": 'version = "0.4.133"\n',
                "src-tauri/Cargo.lock": 'version = "0.4.133"\n',
                "src-tauri/tauri.conf.json": '{"version":"0.4.133"}\n',
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
        auto_bootstrap_override: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "crewing",
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
        if auto_bootstrap_override:
            command.append("--auto-bootstrap-override")
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
            "dist/SETTINGS_VERSION": "9caeff6\n",
            "dist/index.html": "appVersion: '0.4.133' /* unified settings menu */\n",
            "dist/skipi-settings.css": ":root { color-scheme: light; }\n",
            "dist/skipi-settings.js": "export const settings = 'unified';\n",
            "tests/crewing_theme_default_harness.mjs": "// light theme default harness\n",
        }

    def canonical_bump(self) -> dict[str, str]:
        return {
            "dist/index.html": "appVersion: '0.4.134'\n",
            "src-tauri/Cargo.toml": 'version = "0.4.134"\n',
            "src-tauri/Cargo.lock": 'version = "0.4.134"\n',
            "src-tauri/tauri.conf.json": '{"version":"0.4.134"}\n',
        }

    # --- settings-adopt route ---------------------------------------------

    def test_auto_routes_exact_settings_adopt_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-settings-route-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-settings-scope-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-settings-presence-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-release-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump crewing version", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "release")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "canonical version-bump routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertTrue(payload["release_changes"])

    def test_canonical_bump_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-release-scope-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-non-release-") as tmp:
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

    def test_settings_adopt_runs_plugin_host_harnesses_plus_theme_default(self) -> None:
        """BACKLOG п.47 precedent (broker): settings-adopt is fail-closed with
        the plugin-host harness set, plus the theme-default harness — the
        settings-adopt candidate diff carries the harness file, while
        plugin-host (default task, reached by any main-based diff) must not
        reference a file absent from crewing main (defect Д1)."""
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
        theme_harness = ("crewing_theme_default", "node tests/crewing_theme_default_harness.mjs")
        self.assertNotIn(theme_harness, plugin_host)
        self.assertEqual(settings_adopt, plugin_host | {theme_harness})

    def test_plugin_host_and_release_do_not_reference_absent_theme_harness(self) -> None:
        """Defect Д1: tests/crewing_theme_default_harness.mjs exists only in
        the theme branch, not on crewing main. Any task reachable by a
        main-based diff (plugin-host as default; release, which also inherits
        plugin-host harnesses) must not execute it, otherwise every main-based
        push fails with MODULE_NOT_FOUND (live repro: crewing pin-bump push
        rejected by the pre-push hook)."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        for task in ("plugin-host", "release", "provenance"):
            names = {entry["name"] for entry in config["harness_commands"][task]}
            self.assertNotIn("crewing_theme_default", names, task)

    def test_workflow_pin_bump_routes_to_plugin_host_without_theme_harness(self) -> None:
        """Live repro of Д1: a one-file guard-pin bump of
        .github/workflows/skipi-guard.yml (bootstrap override set) lands in the
        default plugin-host task; its configured harnesses must all exist on
        crewing main (the theme harness does not, so it must not be there)."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-pin-bump-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "bump skipi-guard pin",
                {".github/workflows/skipi-guard.yml": "name: skipi-guard # pin e04dfab3\n"},
            )

            proc, payload = self.run_guard(
                repo, root / "result.json", auto_task=True, auto_bootstrap_override=True
            )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "plugin-host")
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertNotIn("crewing_theme_default", harnesses)
        self.assertIn("crewing_plugin_isolation", harnesses)
        self.assertIn("crewing_presence_contract", harnesses)
        self.assertIn("crewing_crew_flow_demo", harnesses)

    # --- theme-default route ------------------------------------------------

    def theme_default_change(self) -> dict[str, str]:
        # Literal file set of the crewing light-theme candidate
        # (theme-crewing-20260721 @ 59f06243, diff vs crewing main 79070627).
        return {
            "dist/index.html": "appVersion: '0.4.133' /* light theme default */\n",
            "tests/crewing_theme_default_harness.mjs": "// light theme default harness\n",
        }

    def test_auto_routes_exact_theme_default_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-theme-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "light theme by default", self.theme_default_change())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "theme-default")
        self.assertEqual(payload["task_rule"], "theme-default routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertFalse(payload["release_changes"])
        harnesses = {entry["name"]: entry["command"] for entry in payload["tests"]}
        self.assertEqual(
            harnesses["crewing_theme_default"], "node tests/crewing_theme_default_harness.mjs"
        )
        self.assertIn("crewing_plugin_isolation", harnesses)
        self.assertIn("crewing_presence_contract", harnesses)
        self.assertIn("crewing_crew_flow_demo", harnesses)

    def test_theme_default_set_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-theme-scope-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            updates = self.theme_default_change()
            updates["src/unreviewed.js"] = "console.log('must stay blocked');\n"
            self.commit_files(repo, "theme plus unrelated source", updates)

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIn("src/unreviewed.js", payload["scope_violations"])
        self.assertIn("changes outside allowed patterns for task 'plugin-host'", payload["errors"])

    def test_index_only_diff_stays_plugin_host_without_theme_harness(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-index-only-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo, "host change", {"dist/index.html": "appVersion: '0.4.133' /* host */\n"}
            )

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "plugin-host")
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertNotIn("crewing_theme_default", harnesses)

    def test_theme_default_allowlist_is_exactly_the_candidate_file_set(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(
            config["allowed_file_patterns"]["theme-default"],
            ["dist/index.html", "tests/crewing_theme_default_harness.mjs"],
        )

    def test_release_allowlist_is_exactly_the_version_banner(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(config["allowed_file_patterns"]["release"], ["dist/index.html"])


if __name__ == "__main__":
    unittest.main()
