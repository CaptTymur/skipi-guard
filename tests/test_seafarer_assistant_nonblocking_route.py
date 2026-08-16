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
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

ROUTE_TASK = "assistant-nonblocking"
ROUTE_RULE = "assistant non-blocking fix routing (140)"
ROUTE_FILES = [
    "src-tauri/src/commands/assistant.rs",
    "tests/no_dead_tauri_invoke_harness.mjs",
]
ROUTE_HARNESSES = [
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
    {"name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs"},
]


class SeafarerAssistantNonblockingRouteTests(unittest.TestCase):
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
                "seafarer",
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

    def test_exact_candidate_routes_to_assistant_nonblocking(self) -> None:
        proc, payload = self.verify_updates(
            self.route_candidate(),
            prefix="skipi-guard-seafarer-assistant-nonblocking-route-",
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
        self.assertEqual(routes[0]["require_all_of"], ROUTE_FILES)
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        self.assertNotIn(ROUTE_TASK, config["release_tasks"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        self.assertIn("seafarer_no_dead_tauri_invoke", harness_names)
        for pattern in routes[0]["when_all_files_in"] + routes[0]["require_all_of"] + config["allowed_file_patterns"][ROUTE_TASK]:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)

    def test_partial_diff_does_not_route_and_stays_red(self) -> None:
        # Only assistant.rs, without the harness contract file: require_all_of
        # must keep the route closed -> default plugin-host -> scope violation.
        proc, payload = self.verify_updates(
            {"src-tauri/src/commands/assistant.rs": "fixture partial\n"},
            prefix="skipi-guard-seafarer-assistant-nonblocking-partial-",
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
            prefix="skipi-guard-seafarer-assistant-nonblocking-mixed-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_existing_seafarer_routes_keep_their_classification(self) -> None:
        existing_routes = {
            "repo-meta": (
                "repo-meta routing",
                {"AGENTS.md": "fixture agents\n", "CLAUDE.md": "fixture claude\n"},
            ),
            "publication-infra": (
                "publication-infra routing",
                {
                    ".github/workflows/skipi-guard.yml": "fixture workflow\n",
                    "scripts/publish-rf-mirror.sh": "fixture publish\n",
                    "scripts/prepare-rf-mirror.sh": "fixture prepare\n",
                    "scripts/RF_MIRROR_PUBLISH.md": "fixture doc\n",
                    "tests/rf_mirror_publish_contract_harness.mjs": "console.log('ok');\n",
                },
            ),
        }
        for expected_task, (expected_rule, updates) in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    updates,
                    prefix=f"skipi-guard-seafarer-existing-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
