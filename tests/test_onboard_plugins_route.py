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
CONFIG = ROOT / "configs" / "homes" / "onboard.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

ROUTE_TASK = "onboard-plugins"
ROUTE_RULE = "onboard-plugins routing (BACKLOG №1, owner-authorized 2026-08-20)"
ROUTE_FILES = [
    "dist/index.html",
    "dist/plugins/bnwas-time-anchor/CHANGELOG.md",
    "dist/plugins/bnwas-time-anchor/REPORT.md",
    "dist/plugins/bnwas-time-anchor/assets/.gitkeep",
    "dist/plugins/bnwas-time-anchor/checksums.json",
    "dist/plugins/bnwas-time-anchor/index.css",
    "dist/plugins/bnwas-time-anchor/index.js",
    "dist/plugins/bnwas-time-anchor/plugin.json",
    "dist/plugins/ecdis-position-reminder/checksums.json",
    "dist/plugins/ecdis-position-reminder/index.css",
    "dist/plugins/ecdis-position-reminder/index.js",
    "dist/plugins/ecdis-position-reminder/plugin.json",
    "dist/plugins/navigation-calculators/CHANGELOG.md",
    "dist/plugins/navigation-calculators/REPORT.md",
    "dist/plugins/navigation-calculators/assets/.gitkeep",
    "dist/plugins/navigation-calculators/checksums.json",
    "dist/plugins/navigation-calculators/index.css",
    "dist/plugins/navigation-calculators/index.js",
    "dist/plugins/navigation-calculators/plugin.json",
]
ROUTE_MARKERS = [
    "dist/plugins/bnwas-time-anchor/plugin.json",
    "dist/plugins/ecdis-position-reminder/plugin.json",
    "dist/plugins/navigation-calculators/plugin.json",
]
ROUTE_HARNESSES = [
    {"name": "onboard_plugin_isolation", "command": "node tests/plugin_isolation_harness.mjs"},
    {"name": "onboard_apps_launcher", "command": "node tests/apps_launcher_harness.mjs"},
    {"name": "onboard_presence_contract", "command": "node tests/onboard_presence_contract_harness.mjs"},
]


class OnboardPluginsRouteTests(unittest.TestCase):
    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
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
        self.commit_files(repo, "seed fixture", {"fixture.txt": "seed\n"})

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "onboard",
                "--auto-task",
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
            env=self.child_env(),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def verify_updates(
        self,
        updates: dict[str, str],
        *,
        prefix: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json")

    def route_candidate(self) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in ROUTE_FILES}

    def test_exact_candidate_routes_to_onboard_plugins(self) -> None:
        proc, payload = self.verify_updates(
            self.route_candidate(),
            prefix="skipi-guard-onboard-plugins-route-",
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(ROUTE_FILES))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["scope_violations"], [])
        self.assertFalse(payload["release_changes"])
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_route_is_literal_exact_and_non_release(self) -> None:
        with CONFIG.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(routes[0]["require_any_of"], ROUTE_MARKERS)
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        # The route reuses the existing plugin-host harness set: no weakening.
        self.assertEqual(config["harness_commands"][ROUTE_TASK], config["harness_commands"]["plugin-host"])
        self.assertNotIn(ROUTE_TASK, config["release_tasks"])
        for pattern in routes[0]["when_all_files_in"] + routes[0]["require_any_of"] + config["allowed_file_patterns"][ROUTE_TASK]:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)

    def test_diff_without_plugin_manifest_marker_does_not_route_and_stays_red(self) -> None:
        # All 19 paths minus the plugin.json markers: require_any_of must keep
        # the route closed -> default plugin-host -> dist/plugins/** files are
        # outside the plugin-host allowlist -> scope violation.
        updates = {
            path: f"fixture for {path}\n"
            for path in ROUTE_FILES
            if path not in ROUTE_MARKERS
        }
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-onboard-plugins-nomarker-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_candidate_plus_unrelated_file_does_not_route_and_stays_red(self) -> None:
        updates = self.route_candidate()
        updates["src/unrelated.txt"] = "forbidden extra file\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-onboard-plugins-mixed-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_existing_onboard_routes_keep_their_classification(self) -> None:
        existing_routes = {
            "repo-meta": (
                "repo-meta routing",
                {"AGENTS.md": "fixture agents\n", "CLAUDE.md": "fixture claude\n"},
            ),
            "settings-adopt": (
                "settings-adopt routing",
                {
                    "UNIFIED_SETTINGS_DEFECTS.md": "fixture defects\n",
                    "dist/SETTINGS_VERSION": "fixture version\n",
                    "dist/index.html": "fixture html\n",
                    "dist/skipi-onboard-settings-host.js": "console.log('host');\n",
                    "dist/skipi-settings.css": "body {}\n",
                    "dist/skipi-settings.js": "console.log('settings');\n",
                    "tests/settings_standard_harness.mjs": "console.log('ok');\n",
                },
            ),
        }
        for expected_task, (expected_rule, updates) in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    updates,
                    prefix=f"skipi-guard-onboard-existing-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
