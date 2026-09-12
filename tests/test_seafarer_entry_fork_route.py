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

ROUTE_TASK = "entry-fork-187"
ROUTE_RULE = "seafarer mobile entry fork + 0.4.187 bump routing (187)"
# Push set of feature/seafarer-entry-fork-20260906 against the live home main
# c94802f6 as owner-authorized on 2026-09-06 (DECISIONS (297); task card
# TASKCARD-2026-09-06-seafarer-mobile-entry-fork, OWNER (a)): the native
# entry fork (Sign in / Demo) in dist/index.html, the 0.4.187 bump and the
# three harness files the slice extends. No Rust file is opened by this route.
ROUTE_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "tests/bundled_plugin_isolation_harness.mjs",
    "tests/login_gate_first_screen_harness.mjs",
    "tests/stack_build_metadata_harness.mjs",
]
ROUTE_CORE_FILES = [
    "dist/index.html",
    "tests/login_gate_first_screen_harness.mjs",
]
ROUTE_HARNESSES = [
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
    {"name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs"},
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
    {"name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs"},
    {"name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs"},
]

# Seafarer config surface on main 58a7d86 (before this route). The route must
# be purely additive: every entry below stays, nothing else is added.
PRE_ROUTE_RELEASE_TASKS = [
    "release",
    "release-infra",
    "build-release",
    "stack-metadata",
    "mobile-external-url",
    "login-gate-first-162b",
]
PRE_ROUTE_ROUTING_TASKS = [
    "mobile-external-url",
    "assistant-nonblocking",
    "login-gate-first-162b",
    "repo-meta",
    "stack-metadata",
    "release",
    "settings-adopt",
    "publication-infra",
    "assistant-module",
]
PRE_ROUTE_HARNESS_TASKS = {
    "mobile-external-url",
    "assistant-nonblocking",
    "login-gate-first-162b",
    "plugin-host",
    "assistant-module",
    "demo-vault",
    "contract-sync",
    "release",
    "provenance",
    "publication-infra",
    "settings-adopt",
    "stack-metadata",
}
PRE_ROUTE_ALLOWED_TASKS = {
    "mobile-external-url",
    "assistant-nonblocking",
    "login-gate-first-162b",
    "repo-meta",
    "plugin-host",
    "demo-vault",
    "contract-sync",
    "publication-infra",
    "settings-adopt",
    "stack-metadata",
    "assistant-module",
    "release",
}

# Owner-authorized exact routes added AFTER this one (each with its own test
# module); the snapshot stays strict for anything else.
LATER_OWNER_ROUTES = [
    "mobile-ime-inset",  # DECISIONS (309), 2026-09-06
    "version-bump",  # DECISIONS (309), 2026-09-06
    "native-share",  # DECISIONS (332), 2026-09-06
    "ios-apple-project-265b",  # task card A0 wave 0.4.191 (OWNER (430)/(431)), 2026-09-09: release + exact set (34 files)
    "brand-icons",  # wave 0.4.192 brand icons (owner-accepted app icon), 2026-09-12: release + exact set (52 files), oracle in tests/test_seafarer_brand_icons_route.py
]
# Later owner routes that are deliberately NOT release tasks: they open no
# release-sensitive path, so adding them to release_tasks would only glue every
# release_sensitive_path onto their allowed patterns (finding Н-1, RISKS
# №224b). They register in routing/harness/allowed, never in release_tasks.
LATER_OWNER_ROUTES_NON_RELEASE = [
    "mobile-189-native",  # owner word 2026-09-06, 0.4.189 native fixes
    "ai-recognize-257",  # task card A0 wave 0.4.191 (OWNER (430)/(431)), 2026-09-09: ai.rs only
    "guard-pin-bump",  # wave 0.4.192, 2026-09-12: the lone .github/workflows/skipi-guard.yml pin bump, oracle in tests/test_seafarer_brand_icons_route.py
]

LOGIN_GATE_162B_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/src/commands/app_login.rs",
    "src-tauri/src/lib.rs",
    "src-tauri/tauri.conf.json",
    "tests/login_gate_first_screen_harness.mjs",
    "tests/no_dead_tauri_invoke_harness.mjs",
    "tests/stack_build_metadata_harness.mjs",
]


class SeafarerEntryForkRouteTests(unittest.TestCase):
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

    def candidate(self, files: list[str]) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in files}

    def load_config(self) -> dict[str, Any]:
        with CONFIG.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_routed_pass(
        self,
        payload: dict[str, Any],
        proc: subprocess.CompletedProcess[str],
        files: list[str],
        *,
        release_changes: bool,
    ) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(files))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        # Cargo.toml/Cargo.lock/tauri.conf.json are release-sensitive: the
        # 0.4.187 bump is authorized because the task is a release task, not
        # silenced.
        self.assertEqual(payload["release_changes"], release_changes)
        # Effective harness list is exactly the declared one: the inherited
        # plugin-host/provenance commands are identical (name, command) pairs
        # and dedupe away, so nothing extra and nothing missing runs.
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_push_set_of_7_routes_to_entry_fork(self) -> None:
        # Base c94802f6 (live home main): 7 files, no Rust.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-entry-fork-union7-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES, release_changes=True)

    def test_core_only_diff_routes_without_release_changes(self) -> None:
        # The fork slice without the bump commit (dist + its harness): still
        # bounded by when_all_files_in, still this route, nothing
        # release-sensitive touched.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_CORE_FILES),
            prefix="skipi-guard-seafarer-entry-fork-core-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_CORE_FILES, release_changes=False)
        self.assertEqual(payload["release_paths_touched"], [])

    def test_route_is_literal_release_task_bounded_by_routing(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(routes[0]["require_all_of"], ROUTE_CORE_FILES)
        self.assertNotIn("require_any_of", routes[0])
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        # The bump commit touches version files -> the task must be a release
        # task. It deliberately has NO exact_task_file_sets entry (exact sets
        # are strict on `missing`, so the fork slice without the bump could not
        # ride the route); the diff is bounded by the routing rule
        # (when_all_files_in) plus allowed_file_patterns instead (mirrors the
        # login-gate-first-162b route).
        self.assertIn(ROUTE_TASK, config["release_tasks"])
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        for required in (
            "seafarer_no_dead_tauri_invoke",
            "seafarer_stack_build_metadata",
            "seafarer_stack_verification_negative_control",
            "seafarer_build_provenance",
            "seafarer_login_gate_first_screen",
            "seafarer_demo_vault_contract",
        ):
            self.assertIn(required, harness_names)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        # Every harness this route runs is the same (name, command) pair as the
        # existing task that already owns it: nothing is redefined here.
        owned_elsewhere = {
            (entry["name"], entry["command"])
            for task, entries in config["harness_commands"].items()
            if task != ROUTE_TASK
            for entry in entries
        }
        for entry in config["harness_commands"][ROUTE_TASK]:
            self.assertIn((entry["name"], entry["command"]), owned_elsewhere)
        for pattern in (
            routes[0]["when_all_files_in"]
            + routes[0]["require_all_of"]
            + config["allowed_file_patterns"][ROUTE_TASK]
        ):
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
        for core in ROUTE_CORE_FILES:
            self.assertIn(core, ROUTE_FILES)
        # No Rust source is opened by this route (STOP line of the task card:
        # profile.rs/vault.rs edits are out of this slice).
        for pattern in ROUTE_FILES:
            self.assertFalse(pattern.endswith(".rs"), pattern)

    def test_route_is_additive_to_pre_route_config(self) -> None:
        config = self.load_config()

        later_routes = LATER_OWNER_ROUTES + LATER_OWNER_ROUTES_NON_RELEASE
        self.assertEqual(config["release_tasks"], PRE_ROUTE_RELEASE_TASKS + [ROUTE_TASK] + LATER_OWNER_ROUTES)
        for non_release in LATER_OWNER_ROUTES_NON_RELEASE:
            self.assertNotIn(non_release, config["release_tasks"])
        self.assertEqual(config["default_task"], "plugin-host")
        # ios-apple-project-265b is the second (and only other) exact-set task:
        # task card A0 of wave 0.4.191 (skipi-ops/handoffs/seafarer-0-4-191/TASKCARD-A0-guard-routes.md),
        # oracle in tests/test_seafarer_ios_apple_route.py.
        # brand-icons joined as the third exact-set task in wave 0.4.192
        # (2026-09-12), oracle in tests/test_seafarer_brand_icons_route.py.
        self.assertEqual(
            set(config["exact_task_file_sets"]),
            {"stack-metadata", "ios-apple-project-265b", "brand-icons"},
        )
        routing_tasks = [rule["task"] for rule in config["task_routing"]]
        self.assertEqual(
            [task for task in routing_tasks if task != ROUTE_TASK and task not in later_routes],
            PRE_ROUTE_ROUTING_TASKS,
        )
        self.assertEqual(routing_tasks.count(ROUTE_TASK), 1)
        self.assertEqual(set(config["harness_commands"]), PRE_ROUTE_HARNESS_TASKS | {ROUTE_TASK} | set(later_routes))
        self.assertEqual(set(config["allowed_file_patterns"]), PRE_ROUTE_ALLOWED_TASKS | {ROUTE_TASK} | set(later_routes))
        # The route is the only task named after the entry fork: no alias, no
        # draft name left behind.
        for task in set(config["release_tasks"]) | set(config["harness_commands"]) | set(config["allowed_file_patterns"]) | set(routing_tasks):
            if "entry" in task or "fork" in task or "187" in task:
                self.assertEqual(task, ROUTE_TASK)

    def test_union_without_core_file_does_not_route_and_stays_red(self) -> None:
        # require_all_of core: without dist/index.html or without the login
        # gate harness the route stays closed -> default plugin-host ->
        # release-sensitive + scope violation.
        for core in ROUTE_CORE_FILES:
            with self.subTest(missing=core):
                files = [path for path in ROUTE_FILES if path != core]
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-entry-fork-no-core-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_bump_only_does_not_route_to_this_route(self) -> None:
        # Only the bump commit (version files + stack harness) without the
        # entry fork: this route may not silently authorize it. Since
        # DECISIONS (309) the bump has its own permanent owner-authorized
        # route (version-bump, tests/test_seafarer_version_bump_route.py) — it
        # is authorized there, by name, never as a side effect of this one.
        proc, payload = self.verify_updates(
            self.candidate(
                [
                    "dist/index.html",
                    "src-tauri/Cargo.lock",
                    "src-tauri/Cargo.toml",
                    "src-tauri/tauri.conf.json",
                    "tests/stack_build_metadata_harness.mjs",
                ]
            ),
            prefix="skipi-guard-seafarer-entry-fork-bumponly-",
        )

        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task"], "version-bump")
        self.assertNotEqual(payload["task_rule"], ROUTE_RULE)

    def test_harnesses_only_diff_does_not_route_and_stays_red(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(
                [
                    "tests/bundled_plugin_isolation_harness.mjs",
                    "tests/login_gate_first_screen_harness.mjs",
                    "tests/stack_build_metadata_harness.mjs",
                ]
            ),
            prefix="skipi-guard-seafarer-entry-fork-harnesses-only-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)

    def test_candidate_plus_extra_file_does_not_route_and_stays_red(self) -> None:
        # when_all_files_in is the upper bound: any 8th file falls through to
        # default plugin-host and stays RED. The Rust files are the ones the
        # task card forbids in this slice; the workflow file is the gate pin.
        for extra in (
            "src-tauri/src/commands/app_login.rs",
            "src-tauri/src/commands/profile.rs",
            "src-tauri/src/commands/vault.rs",
            "src-tauri/src/lib.rs",
            ".github/workflows/skipi-guard.yml",
            "src/unrelated.txt",
        ):
            with self.subTest(extra=extra):
                updates = self.candidate(ROUTE_FILES)
                updates[extra] = "forbidden extra file\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-entry-fork-mixed-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_candidate_plus_release_sensitive_file_cannot_reach_route(self) -> None:
        # Without an exact set, a release task's allowed patterns are widened
        # by release_sensitive_paths for EXPLICIT --task use only. Under
        # auto-task (hook + CI default) the routing rule bounds the diff to the
        # 7 files, so a generated/mobile file never reaches this task.
        updates = self.candidate(ROUTE_FILES)
        updates["src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"] = "fixture activity\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-seafarer-entry-fork-release-sensitive-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_existing_seafarer_routes_keep_their_classification(self) -> None:
        existing_routes = {
            "mobile-external-url": (
                "mobile external-url fix routing",
                {
                    "src-tauri/src/commands/vault.rs": "fixture vault\n",
                    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt": "fixture activity\n",
                },
            ),
            "assistant-nonblocking": (
                "assistant non-blocking fix routing (140)",
                {
                    "src-tauri/src/commands/assistant.rs": "fixture assistant\n",
                    "tests/no_dead_tauri_invoke_harness.mjs": "fixture harness\n",
                },
            ),
            "login-gate-first-162b": (
                "login gate first screen + 0.4.186 bump routing (162b)",
                self.candidate(LOGIN_GATE_162B_FILES),
            ),
            "stack-metadata": (
                "seafarer Stage 4 stack-metadata routing",
                {
                    "dist/index.html": "fixture dist\n",
                    "src-tauri/Cargo.lock": "fixture lock\n",
                    "src-tauri/Cargo.toml": "fixture toml\n",
                    "src-tauri/src/commands/vault.rs": "fixture vault\n",
                    "src-tauri/tauri.conf.json": "fixture conf\n",
                    "tests/stack_build_metadata_harness.mjs": "console.log('ok');\n",
                    "tests/stack_verification_negative_control_harness.mjs": "console.log('ok');\n",
                },
            ),
            "release": (
                "canonical version-bump routing",
                {
                    "dist/index.html": "fixture dist\n",
                    "src-tauri/Cargo.lock": "fixture lock\n",
                    "src-tauri/Cargo.toml": "fixture toml\n",
                    "src-tauri/tauri.conf.json": "fixture conf\n",
                },
            ),
            "repo-meta": (
                "repo-meta routing",
                {"AGENTS.md": "fixture agents\n", "CLAUDE.md": "fixture claude\n"},
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
