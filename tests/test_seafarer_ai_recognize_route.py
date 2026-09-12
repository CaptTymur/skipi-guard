"""Seafarer route `ai-recognize-257` — one literal file, no release, no exact set.

Task card: skipi-ops/handoffs/seafarer-0-4-191/TASKCARD-A0-guard-routes.md
(wave Seafarer 0.4.191, OWNER (430)/(431); route-PR merge = owner click only).

Defect №257 / slice A6 (AI field recognition) lives in
`src-tauri/src/commands/ai.rs`, which at 746bc882 is in no allowed_file_patterns
of the home, so the fix cannot be pushed at all (default plugin-host -> scope
violation). Its cargo tests live inside ai.rs (#[cfg(test)]); there is no
separate test file to route.

Shape, asserted below:

  * task_routing when_all_files_in = require_all_of = [ai.rs], appended after
    the 14 historical rules (first-match, the neighbours keep priority);
  * allowed_file_patterns = [ai.rs]; NOT a release task (ai.rs matches no
    release_sensitive_paths pattern — asserted mechanically — so a release
    flag would only glue every release_sensitive_path on, finding Н-1 /
    RISKS №224b); no exact_task_file_sets entry;
  * harness_commands = the same ten as mobile-189-native (strictest tier).

Consequences the tests pin down: `ai.rs` alone -> this route, PASS;
`ai.rs + src-tauri/Cargo.toml` -> not this route, FAIL; `ai.rs + dist/index.html`
-> default plugin-host where ai.rs is outside the allowlist -> FAIL. So the №257
fix MUST go as its own push with ai.rs only; a screen change rides a different
route. cv_commands.rs / packages.rs / documents.rs stay closed (STOP line of
the card: they need their own route card).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

GUARD_LOADER = SourceFileLoader("skipi_guard_cli_257", str(GUARD))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
if GUARD_SPEC is None:
    raise RuntimeError(f"cannot load guard module from {GUARD}")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_LOADER.exec_module(GUARD_MODULE)

ROUTE_TASK = "ai-recognize-257"
ROUTE_RULE = "seafarer ai recognize fields fix routing (257)"
ROUTE_FILE = "src-tauri/src/commands/ai.rs"
ROUTE_FILES = [ROUTE_FILE]
SIBLING_TASK = "ios-apple-project-265b"  # the other route of the same task card (R2)

# Same ten as mobile-189-native (and entry-fork-187 / mobile-ime-inset /
# native-share): not a release task, so configured_harnesses() inherits
# nothing and this list is the whole set the route runs.
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

# Deliberately outside the route (STOP lines of the card and the usual
# suspects: the version trio, the front end, sibling Rust commands that were
# NOT requested, the Android platform files, the presence manifest).
ROUTE_FORBIDDEN_FILES = [
    "src-tauri/Cargo.toml",
    "src-tauri/Cargo.lock",
    "src-tauri/tauri.conf.json",
    "dist/index.html",
    "dist/intelligence.js",
    "src-tauri/src/commands/cv_commands.rs",
    "src-tauri/src/commands/packages.rs",
    "src-tauri/src/commands/documents.rs",
    "src-tauri/src/commands/mod.rs",
    "src-tauri/src/lib.rs",
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/gen/apple/skipi_iOS/Info.plist",
    "presence-manifest.json",
    ".github/workflows/skipi-guard.yml",
    "tests/bundled_plugin_isolation_harness.mjs",
    "src/unrelated.txt",
]


class SeafarerAiRecognizeRouteTests(unittest.TestCase):
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
        *,
        task: str | None = None,
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
        if task:
            command.extend(["--task", task])
        else:
            command.append("--auto-task")
        proc = subprocess.run(
            command,
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
        task: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json", task=task)

    def candidate(self, files: list[str]) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in files}

    def load_config(self) -> dict[str, Any]:
        with CONFIG.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_routed_pass(
        self,
        payload: dict[str, Any],
        proc: subprocess.CompletedProcess[str],
        *,
        task_source: str,
    ) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["changed_files"], ROUTE_FILES)
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], task_source)
        self.assertEqual(payload["task_rule"], ROUTE_RULE if task_source == "auto" else None)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(payload["release_changes"], False)
        self.assertEqual(payload["release_paths_touched"], [])
        self.assertEqual(payload["protected_paths_touched"], [])
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(payload["allowed_file_patterns"], ROUTE_FILES)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    # ai.rs alone -> this route, PASS (auto and explicit).
    def test_ai_rs_alone_routes_and_passes(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-257-alone-",
        )
        self.assert_routed_pass(payload, proc, task_source="auto")

    def test_explicit_task_with_ai_rs_alone_passes(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-257-explicit-alone-",
            task=ROUTE_TASK,
        )
        self.assert_routed_pass(payload, proc, task_source="explicit")

    # ai.rs + Cargo.toml (and the rest of the version trio) -> not this route, FAIL.
    def test_ai_rs_plus_version_file_does_not_route_and_fails(self) -> None:
        for extra in ("src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"):
            with self.subTest(extra=extra):
                proc, payload = self.verify_updates(
                    self.candidate([ROUTE_FILE, extra]),
                    prefix="skipi-guard-seafarer-257-version-",
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertIn(ROUTE_FILE, payload["scope_violations"])
                self.assertIn(extra, payload["scope_violations"])
                self.assertTrue(
                    any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
                    payload["errors"],
                )
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    # ai.rs + dist/index.html -> NOT this route: default plugin-host, where
    # ai.rs is outside the allowlist -> FAIL. The №257 fix goes alone.
    def test_ai_rs_plus_dist_index_is_not_this_route_and_fails(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate([ROUTE_FILE, "dist/index.html"]),
            prefix="skipi-guard-seafarer-257-dist-",
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIsNone(payload["task_rule"])
        self.assertEqual(payload["scope_violations"], [ROUTE_FILE])
        self.assertEqual(payload["release_changes"], False)
        self.assertTrue(
            any("changes outside allowed patterns for task 'plugin-host'" in error for error in payload["errors"]),
            payload["errors"],
        )

    # Any other extra: the route stays closed and the push stays RED.
    def test_ai_rs_plus_any_forbidden_file_does_not_route_and_fails(self) -> None:
        for extra in ROUTE_FORBIDDEN_FILES:
            with self.subTest(extra=extra):
                proc, payload = self.verify_updates(
                    self.candidate([ROUTE_FILE, extra]),
                    prefix="skipi-guard-seafarer-257-mixed-",
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertIn(ROUTE_FILE, payload["scope_violations"])

    # Explicit --task cannot widen the route (call site: hand-named task).
    def test_explicit_task_with_dist_only_fails(self) -> None:
        for files in (["dist/index.html"], ["dist/index.html", "tests/bundled_plugin_isolation_harness.mjs"], ["src/unrelated.txt"]):
            with self.subTest(files=files):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-257-explicit-dist-",
                    task=ROUTE_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task_source"], "explicit")
                self.assertEqual(payload["scope_violations"], sorted(files))
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_explicit_task_with_ai_rs_plus_tauri_conf_fails(self) -> None:
        for extra in ("src-tauri/tauri.conf.json", "src-tauri/Cargo.toml", "src-tauri/gen/apple/skipi_iOS/Info.plist", "package.json"):
            with self.subTest(extra=extra):
                proc, payload = self.verify_updates(
                    self.candidate([ROUTE_FILE, extra]),
                    prefix="skipi-guard-seafarer-257-explicit-smuggle-",
                    task=ROUTE_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["scope_violations"], [extra])
                # Not a release task: the release-sensitive stop-line fires
                # too, on top of the scope violation.
                self.assertTrue(
                    any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
                    payload["errors"],
                )
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    # Config shape: literal, single file, not release, no exact set, last-but-one rule.
    def test_route_config_shape(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(routes[0]["require_all_of"], ROUTE_FILES)
        self.assertNotIn("require_any_of", routes[0])
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        for pattern in routes[0]["when_all_files_in"] + routes[0]["require_all_of"] + config["allowed_file_patterns"][ROUTE_TASK]:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
        self.assertTrue(ROUTE_FILE.endswith(".rs"))
        self.assertFalse(ROUTE_FILE.startswith("src-tauri/gen/"))
        for forbidden in ROUTE_FORBIDDEN_FILES:
            self.assertNotIn(forbidden, config["allowed_file_patterns"][ROUTE_TASK])
            self.assertNotIn(forbidden, routes[0]["when_all_files_in"])

        # first-match: appended after the 14 historical rules, before R2.
        routing_tasks = [rule["task"] for rule in config["task_routing"]]
        self.assertEqual(len(routing_tasks), 20)
        # …followed by the two brand-icon routes of wave 0.4.192 (2026-09-12,
        # oracle in tests/test_seafarer_brand_icons_route.py).
        self.assertEqual(routing_tasks[14:], [ROUTE_TASK, SIBLING_TASK, "brand-icons", "guard-pin-bump", "cv-order-282", "career-pattern-302"])
        self.assertEqual(routing_tasks.count(ROUTE_TASK), 1)

    def test_route_is_not_a_release_task_and_needs_no_exact_file_set(self) -> None:
        config = self.load_config()
        pattern_matches = GUARD_MODULE.pattern_matches

        sensitive = GUARD_MODULE.rule_patterns(config["release_sensitive_paths"])
        protected = GUARD_MODULE.rule_patterns(config["protected_paths"])
        self.assertTrue(sensitive and protected)
        for pattern in sensitive:
            self.assertFalse(pattern_matches(ROUTE_FILE, pattern), f"{ROUTE_FILE} matches release-sensitive {pattern}")
        for pattern in protected:
            self.assertFalse(pattern_matches(ROUTE_FILE, pattern), f"{ROUTE_FILE} matches protected {pattern}")
        self.assertNotIn(ROUTE_TASK, config["release_tasks"])
        self.assertFalse(GUARD_MODULE.is_release_task(config, ROUTE_TASK))
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        # Standing invariant (finding Н-1 / RISKS №224b): promoted to a release
        # task, this route MUST get an exact set (see the R2 sibling).
        if ROUTE_TASK in config["release_tasks"]:
            self.assertIn(ROUTE_TASK, config["exact_task_file_sets"])
        # Task card A0: the sibling R2 is the only new exact-set task of this
        # card; brand-icons joined in wave 0.4.192 (release + exact set, 52
        # files, oracle in tests/test_seafarer_brand_icons_route.py).
        self.assertEqual(set(config["exact_task_file_sets"]), {"stack-metadata", SIBLING_TASK, "brand-icons", "cv-order-282", "career-pattern-302"})
        self.assertEqual(GUARD_MODULE.effective_allowed_patterns(config, ROUTE_TASK, []), ROUTE_FILES)

    def test_route_harnesses_are_the_strictest_tier_and_inherit_nothing(self) -> None:
        config = self.load_config()

        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], config["harness_commands"]["mobile-189-native"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        self.assertEqual(len(harness_names), 10)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        configured = GUARD_MODULE.configured_harnesses(config, ROUTE_TASK)
        self.assertEqual([{"name": h["name"], "command": h["command"]} for h in configured], ROUTE_HARNESSES)
        owned_elsewhere = {
            (entry["name"], entry["command"])
            for task, entries in config["harness_commands"].items()
            if task != ROUTE_TASK
            for entry in entries
        }
        for entry in config["harness_commands"][ROUTE_TASK]:
            self.assertIn((entry["name"], entry["command"]), owned_elsewhere)

    def test_route_does_not_weaken_protected_paths_or_stop_lines(self) -> None:
        config = self.load_config()

        self.assertEqual(
            [rule["name"] for rule in config["protected_paths"]],
            [
                "backend/server/prod data",
                "secrets/signing keys",
                "pairing/QR/camera bridge",
                "presence contracts",
            ],
        )
        self.assertEqual(
            config["stop_lines"],
            [
                "no backend/server/prod data",
                "no catalog/latest/release/signing keys",
                "no app version/tag bump",
                "no Tauri/Cargo/mobile generated changes",
                "no pairing/QR/camera bridge changes",
                "no Play/TestFlight/upload/deploy",
            ],
        )
        self.assertEqual(config["default_task"], "plugin-host")
        # The sibling Rust commands that were NOT requested stay closed
        # everywhere except where they already were (packages.rs: native-share).
        for closed in ("src-tauri/src/commands/cv_commands.rs", "src-tauri/src/commands/documents.rs"):
            for task, patterns in config["allowed_file_patterns"].items():
                self.assertNotIn(closed, patterns, f"{closed} opened by {task}")
        opened_by = [task for task, patterns in config["allowed_file_patterns"].items() if "src-tauri/src/commands/packages.rs" in patterns]
        self.assertEqual(opened_by, ["native-share"])

    # Neighbour routes are not shadowed; the default stays the default.
    def test_route_does_not_shadow_neighbour_routes(self) -> None:
        config = self.load_config()
        rule_names = {rule["task"]: rule["name"] for rule in config["task_routing"]}
        existing_routes = {
            "mobile-external-url": [
                "src-tauri/src/commands/vault.rs",
                "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
            ],
            "assistant-nonblocking": ["src-tauri/src/commands/assistant.rs", "tests/no_dead_tauri_invoke_harness.mjs"],
            "mobile-189-native": ["src-tauri/src/commands/vault.rs"],
            "version-bump": config["allowed_file_patterns"]["version-bump"],
            "repo-meta": ["AGENTS.md", "CLAUDE.md"],
        }
        for expected_task, files in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-257-neighbour-{expected_task}-",
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], rule_names[expected_task])
        for files in (["dist/index.html"], ["src-tauri/src/lib.rs"]):
            with self.subTest(default=files):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-257-default-",
                )
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
