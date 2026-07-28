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
CONFIG_PATH = ROOT / "configs" / "homes" / "management.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

# Literal file set of the management settings-adopt candidate
# (worktree skipi-shipmgmt-unified-settings @ 7f5113aa, diff vs 1fece729)
# plus the literal wave-fix paths: presence contract harness, theme fix
# (theme-shipmgmt-20260721 @ 5b6f6fdf) and presence-manifest.json.
# presence-manifest.json stays a protected path: routing/scope inclusion
# does NOT lift the protected stop-line (override token still required).
SETTINGS_ADOPT_SET = [
    "dist/SETTINGS_VERSION",
    "dist/index.html",
    "dist/settings-adapter.js",
    "dist/skipi-settings.css",
    "dist/skipi-settings.js",
    "docs/settings-adoption-2026-07-19/CONFLICT-presence-contract.md",
    "docs/settings-adoption-2026-07-19/README.md",
    "docs/settings-adoption-2026-07-19/desktop-launched.png",
    "docs/settings-adoption-2026-07-19/mobile-launched.png",
    "docs/settings-adoption-2026-07-19/settings-connection-saved.png",
    "docs/settings-adoption-2026-07-19/settings-general-company.png",
    "presence-manifest.json",
    "tests/management_presence_contract_harness.mjs",
    "tests/management_theme_default_harness.mjs",
]


class ManagementSettingsReleaseRoutesTests(unittest.TestCase):
    """Settings-wave 5x2: settings-adopt + canonical version-bump routing
    for the management home. Management has no tracked src-tauri/Cargo.lock,
    so its canonical version set is three files."""

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
            "seed management home",
            {
                "dist/index.html": 'version:"0.1.0"; managementCurrentTheme\n',
                "src-tauri/Cargo.toml": 'version = "0.1.0"\n',
                "src-tauri/tauri.conf.json": '{"version":"0.1.0"}\n',
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
            "management",
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
        """Candidate-shaped diff: everything from the exact set except the
        protected presence-manifest.json (protected negative is separate)."""
        return {
            "dist/SETTINGS_VERSION": "9caeff6\n",
            "dist/index.html": 'version:"0.1.0"; managementCurrentTheme /* light default */\n',
            "dist/settings-adapter.js": "export const adapter = 'management';\n",
            "dist/skipi-settings.css": ":root { color-scheme: light; }\n",
            "dist/skipi-settings.js": "export const settings = 'unified';\n",
            "docs/settings-adoption-2026-07-19/CONFLICT-presence-contract.md": "# conflict note\n",
            "docs/settings-adoption-2026-07-19/README.md": "# adoption evidence\n",
            "docs/settings-adoption-2026-07-19/desktop-launched.png": "png-bytes\n",
            "docs/settings-adoption-2026-07-19/mobile-launched.png": "png-bytes\n",
            "docs/settings-adoption-2026-07-19/settings-connection-saved.png": "png-bytes\n",
            "docs/settings-adoption-2026-07-19/settings-general-company.png": "png-bytes\n",
            "tests/management_presence_contract_harness.mjs": "// semantic presence harness\n",
            "tests/management_theme_default_harness.mjs": "// light theme default harness\n",
        }

    def canonical_bump(self) -> dict[str, str]:
        return {
            "dist/index.html": 'version:"0.1.1"; managementCurrentTheme\n',
            "src-tauri/Cargo.toml": 'version = "0.1.1"\n',
            "src-tauri/tauri.conf.json": '{"version":"0.1.1"}\n',
        }

    # --- settings-adopt route ---------------------------------------------

    def test_auto_routes_exact_settings_adopt_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-settings-route-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-settings-scope-") as tmp:
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

    def test_settings_route_does_not_lift_presence_protection(self) -> None:
        """The exact set includes presence-manifest.json for routing/scope,
        but touching it still hits the protected stop-line without an
        explicit override token."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-settings-presence-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            updates = self.settings_adopt_change()
            updates["presence-manifest.json"] = '{"contracts":["settings"]}\n'
            self.commit_files(repo, "settings plus presence contract", updates)

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "settings-adopt")
        self.assertEqual(payload["scope_violations"], [])
        self.assertIn("protected path touch requires --override-protected", payload["errors"])

    # --- canonical version-bump route -------------------------------------

    def test_auto_routes_exact_canonical_version_bump_to_release(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-release-route-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "bump management version", self.canonical_bump())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "release")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "canonical version-bump routing")
        self.assertEqual(payload["scope_violations"], [])
        self.assertTrue(payload["release_changes"])

    def test_canonical_bump_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-release-scope-") as tmp:
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
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-non-release-") as tmp:
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
        """settings-adopt is fail-closed with the plugin-host harness set plus
        the theme-default harness: the settings-adopt candidate diff carries
        tests/management_theme_default_harness.mjs, while plugin-host (default
        task, reached by any main-based diff) must not reference a file absent
        from management main (defect Д1)."""
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
        theme_harness = (
            "management_theme_default",
            "node tests/management_theme_default_harness.mjs",
        )
        self.assertNotIn(theme_harness, plugin_host)
        self.assertEqual(settings_adopt, plugin_host | {theme_harness})

    def test_plugin_host_and_release_do_not_reference_absent_theme_harness(self) -> None:
        """Defect Д1: tests/management_theme_default_harness.mjs exists only in
        the theme branch (theme-shipmgmt-20260721 @ 5b6f6fdf), not on
        management main. Tasks reachable by a main-based diff (plugin-host as
        default; release, which also inherits plugin-host harnesses) must not
        execute it, otherwise every main-based push fails MODULE_NOT_FOUND."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        for task in ("plugin-host", "release", "provenance"):
            names = {entry["name"] for entry in config["harness_commands"][task]}
            self.assertNotIn("management_theme_default", names, task)

    # --- theme-default route ------------------------------------------------

    def theme_default_change(self) -> dict[str, str]:
        # Literal file set of the management light-theme candidate
        # (theme-shipmgmt-20260721 @ 5b6f6fdf, diff vs management main af0f0c8e).
        return {
            "dist/index.html": 'version:"0.1.0"; managementCurrentTheme /* light default */\n',
            "tests/management_theme_default_harness.mjs": "// light theme default harness\n",
        }

    def test_auto_routes_exact_theme_default_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-theme-route-") as tmp:
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
            harnesses["management_theme_default"],
            "node tests/management_theme_default_harness.mjs",
        )
        self.assertIn("management_plugin_isolation", harnesses)
        self.assertIn("management_presence_contract", harnesses)

    def test_theme_default_set_plus_unrelated_source_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-management-theme-scope-") as tmp:
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

    def test_theme_default_allowlist_is_exactly_the_candidate_file_set(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(
            config["allowed_file_patterns"]["theme-default"],
            ["dist/index.html", "tests/management_theme_default_harness.mjs"],
        )

    def test_release_allowlist_is_exactly_the_version_banner(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(config["allowed_file_patterns"]["release"], ["dist/index.html"])

    def test_presence_manifest_stays_protected(self) -> None:
        """Trust policy invariant: adding wave routes must not remove the
        presence-contracts protected path."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        presence_rules = [
            rule
            for rule in config["protected_paths"]
            if "presence-manifest.json" in rule.get("patterns", [])
        ]
        self.assertTrue(presence_rules)


if __name__ == "__main__":
    unittest.main()
