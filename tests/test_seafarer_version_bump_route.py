from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"
LOADER = SourceFileLoader("guard_version_bump", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
PLIST = "src-tauri/gen/apple/skipi_iOS/Info.plist"

ROUTE_TASK = "version-bump"
ROUTE_RULE = "seafarer canonical version bump routing (204)"
# Owner-authorized on 2026-09-06 (DECISIONS (309), owner words "маршрут на
# андройд и на бамп даю"). PERMANENT route, closes RISKS №204: the canonical
# seafarer version bump (shape of commit b5cd14a) touches exactly these 5
# files, and until now had no route at all — the four-file "canonical
# version-bump routing" rule does not cover the stack-metadata harness the
# bump has to update, so every real bump fell through to plugin-host and had
# to be smuggled inside a one-off owner route.
ROUTE_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "tests/stack_build_metadata_harness.mjs",
]
# OWNER 2026-09-13, №273: the canonical iOS identity joins this same bump.
# Keep ROUTE_FILES as the previous five-path shape for compatibility tests.
ROUTE_ALLOWED_FILES = ROUTE_FILES + [PLIST]
# require_all_of: a bump is only a bump when the declared version
# (tauri.conf.json) and the harness that verifies it move together. Neither
# half alone may open this route.
ROUTE_CORE_FILES = [
    "src-tauri/tauri.conf.json",
    "tests/stack_build_metadata_harness.mjs",
]
ROUTE_HARNESSES = [
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
]

CANONICAL_FOUR_FILE_BUMP = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
]
ENTRY_FORK_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "tests/bundled_plugin_isolation_harness.mjs",
    "tests/login_gate_first_screen_harness.mjs",
    "tests/stack_build_metadata_harness.mjs",
]
STACK_METADATA_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/src/commands/vault.rs",
    "src-tauri/tauri.conf.json",
    "tests/stack_build_metadata_harness.mjs",
    "tests/stack_verification_negative_control_harness.mjs",
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


class SeafarerVersionBumpRouteTests(unittest.TestCase):
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

    def test_canonical_five_file_bump_routes_to_version_bump(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-version-bump-union5-",
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(ROUTE_FILES))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        # Cargo.toml/Cargo.lock/tauri.conf.json are release-sensitive: the bump
        # is authorized because the task is a release task, not silenced.
        self.assertEqual(payload["release_changes"], True)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_missing_tauri_conf_does_not_route_and_stays_red(self) -> None:
        # No declared version change -> not a bump -> the route stays closed
        # and the release-sensitive Cargo files keep the diff RED.
        files = [path for path in ROUTE_FILES if path != "src-tauri/tauri.conf.json"]
        proc, payload = self.verify_updates(
            self.candidate(files),
            prefix="skipi-guard-seafarer-version-bump-no-conf-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_missing_stack_harness_keeps_the_pre_existing_release_route(self) -> None:
        # The historic four-file "canonical version-bump routing" rule (task
        # `release`) must keep its diff: the new route requires the harness and
        # therefore cannot shadow it.
        proc, payload = self.verify_updates(
            self.candidate(CANONICAL_FOUR_FILE_BUMP),
            prefix="skipi-guard-seafarer-version-bump-no-harness-",
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task"], "release")
        self.assertEqual(payload["task_rule"], "canonical version-bump routing")

    def test_core_files_alone_route_honestly(self) -> None:
        # tauri.conf.json + the harness with no dist/Cargo movement is not the
        # canonical bump shape; it is inside when_all_files_in, so it does open
        # the route -- assert the honest classification rather than a guess.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_CORE_FILES),
            prefix="skipi-guard-seafarer-version-bump-core-",
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["release_changes"], True)

    def test_harness_only_and_dist_only_diffs_do_not_route(self) -> None:
        for label, files in (
            ("harness-only", ["tests/stack_build_metadata_harness.mjs"]),
            ("dist-only", ["dist/index.html"]),
            ("conf-only", ["src-tauri/tauri.conf.json"]),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-version-bump-{label}-",
                )
                self.assertNotEqual(payload["task"], ROUTE_TASK)

    def test_candidate_plus_extra_file_does_not_route_and_stays_red(self) -> None:
        # when_all_files_in is the upper bound: an unlisted extra file falls through and
        # stays RED. A bump route must never carry code.
        for extra in (
            "src-tauri/src/lib.rs",
            "src-tauri/src/commands/vault.rs",
            "src-tauri/src/commands/app_login.rs",
            "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
            "dist/plugin-host-ui.js",
            ".github/workflows/skipi-guard.yml",
            "src/unrelated.txt",
        ):
            with self.subTest(extra=extra):
                updates = self.candidate(ROUTE_FILES)
                updates[extra] = "forbidden extra file\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-version-bump-mixed-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)

    def test_protected_path_still_blocks_inside_the_route(self) -> None:
        updates = self.candidate(ROUTE_FILES)
        updates["presence-manifest.json"] = "{}\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-seafarer-version-bump-protected-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("protected path touch requires" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_route_is_literal_release_task_bounded_by_routing(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_ALLOWED_FILES)
        self.assertEqual(routes[0]["require_all_of"], ROUTE_CORE_FILES)
        self.assertNotIn("require_any_of", routes[0])
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_ALLOWED_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        self.assertIn(ROUTE_TASK, config["release_tasks"])
        # No exact_task_file_sets entry: a bump that leaves dist/index.html or
        # Cargo.lock untouched must still ride the route (exact sets are strict
        # on `missing`); the diff is bounded by when_all_files_in +
        # allowed_file_patterns instead.
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        for required in (
            "seafarer_stack_build_metadata",
            "seafarer_stack_verification_negative_control",
            "seafarer_build_provenance",
        ):
            self.assertIn(required, harness_names)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        self.assertEqual(len(harness_names), len(plugin_host_generic) + 2)
        # Every harness this route runs is the same (name, command) pair an
        # existing task already owns: nothing is redefined here.
        owned_elsewhere = {
            (entry["name"], entry["command"])
            for task, entries in config["harness_commands"].items()
            if task != ROUTE_TASK
            for entry in entries
        }
        for entry in config["harness_commands"][ROUTE_TASK]:
            self.assertIn((entry["name"], entry["command"]), owned_elsewhere)
        # Literal paths only: no glob may widen this route.
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
        # A bump carries no source: no Rust, no plugin-host JS, no Android.
        for pattern in ROUTE_ALLOWED_FILES:
            self.assertFalse(pattern.endswith(".rs"), pattern)
            if pattern.startswith("src-tauri/gen/"):
                self.assertEqual(pattern, PLIST)

    def test_route_does_not_shadow_neighbour_routes(self) -> None:
        existing_routes = {
            "entry-fork-187": (
                "seafarer mobile entry fork + 0.4.187 bump routing (187)",
                self.candidate(ENTRY_FORK_FILES),
            ),
            "login-gate-first-162b": (
                "login gate first screen + 0.4.186 bump routing (162b)",
                self.candidate(LOGIN_GATE_162B_FILES),
            ),
            "stack-metadata": (
                "seafarer Stage 4 stack-metadata routing",
                self.candidate(STACK_METADATA_FILES),
            ),
            "release": (
                "canonical version-bump routing",
                self.candidate(CANONICAL_FOUR_FILE_BUMP),
            ),
            "mobile-external-url": (
                "mobile external-url fix routing",
                {
                    "src-tauri/src/commands/vault.rs": "fixture vault\n",
                    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt": "fixture activity\n",
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
                    prefix=f"skipi-guard-seafarer-version-bump-neighbour-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])

    def previous_config(self) -> dict[str, Any]:
        config = copy.deepcopy(self.load_config())
        route = next(rule for rule in config["task_routing"] if rule["task"] == ROUTE_TASK)
        for paths in (route["when_all_files_in"], config["allowed_file_patterns"][ROUTE_TASK]):
            if PLIST in paths:
                paths.remove(PLIST)
        return config

    def route_outcome(self, config: dict[str, Any], files: list[str]) -> dict[str, Any]:
        route = MODULE.resolve_task(config, files)
        task = route["task"]
        additive = MODULE.additive_task_checks(config, task, files)
        patterns = MODULE.effective_allowed_patterns(config, task, additive)
        scope = MODULE.scope_check_for_task(config, task, files, patterns)
        effective_tasks = list(dict.fromkeys([task] + [entry["task"] for entry in additive]))
        harnesses = MODULE.unique_harnesses([
            harness for effective in effective_tasks
            for harness in MODULE.configured_harnesses(config, effective)
        ])
        return {
            "route": route,
            "scope_violations": scope["scope_violations"] if scope else [],
            "exact": MODULE.exact_file_set_check(config, task, files),
            "additive": additive,
            "release_task": MODULE.is_release_task(config, task),
            "protected": MODULE.classify_paths(files, config["protected_paths"], "protected"),
            "release_paths": MODULE.classify_paths(files, config["release_sensitive_paths"], "release"),
            "harnesses": harnesses,
        }

    def assert_plist_contract(self, config: dict[str, Any]) -> None:
        # Preserve the explicitly reviewed declaration. Release-task scope also
        # inherits release_sensitive_paths (including gen/**), so removing this
        # allowlist literal is a declaration regression, not a runtime rejection.
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_ALLOWED_FILES)
        outcome = self.route_outcome(config, ROUTE_ALLOWED_FILES)
        self.assertEqual(outcome["route"], {"task": ROUTE_TASK, "rule": ROUTE_RULE})
        self.assertEqual(outcome["scope_violations"], [])
        self.assertIsNone(outcome["exact"])
        self.assertEqual(outcome["additive"], [])
        self.assertTrue(outcome["release_task"])
        self.assertTrue(outcome["release_paths"])
        self.assertEqual(outcome["protected"], [])
        self.assertEqual(outcome["harnesses"], ROUTE_HARNESSES)

    def test_canonical_six_file_bump_includes_plist(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_ALLOWED_FILES), prefix="guard-273-six-",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_plist_contract(self.load_config())
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(ROUTE_ALLOWED_FILES))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["errors"], [])
        self.assertTrue(payload["release_changes"])
        self.assertFalse(payload["override_present"])
        self.assertEqual(
            [{k: entry[k] for k in ("name", "command")} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_all_32_previous_path_subsets_keep_route_and_protection_outcomes(self) -> None:
        before, after = self.previous_config(), self.load_config()
        for size in range(len(ROUTE_FILES) + 1):
            for subset in itertools.combinations(ROUTE_FILES, size):
                with self.subTest(files=subset):
                    self.assertEqual(self.route_outcome(before, list(subset)),
                                     self.route_outcome(after, list(subset)))

    def test_plist_neighbours_and_missing_required_paths_keep_rejections(self) -> None:
        cases = {
            "plist-alone": [PLIST],
            **{f"missing-{core}": [p for p in ROUTE_ALLOWED_FILES if p != core]
               for core in ROUTE_CORE_FILES},
            "sibling-apple": ROUTE_FILES + ["src-tauri/gen/apple/skipi_iOS/Other.plist"],
            "android": ROUTE_FILES + ["src-tauri/gen/android/app/src/main/AndroidManifest.xml"],
            "unrelated-rust": ROUTE_ALLOWED_FILES + ["src-tauri/src/commands/cv.rs"],
            "wrong-case": ROUTE_FILES + ["src-tauri/gen/apple/skipi_iOS/info.plist"],
            "protected": ROUTE_ALLOWED_FILES + ["presence-manifest.json"],
        }
        before, after = self.previous_config(), self.load_config()
        for label, files in cases.items():
            with self.subTest(case=label):
                previous = self.route_outcome(before, files)
                current = self.route_outcome(after, files)
                self.assertEqual(previous, current)
                self.assertNotEqual(current["route"]["task"], ROUTE_TASK)
                proc, payload = self.verify_updates(self.candidate(files), prefix="guard-273-negative-")
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], current["route"]["task"])
                self.assertTrue(payload["scope_violations"])
                if label == "protected":
                    self.assertIn("protected path touch requires --override-protected", payload["errors"])

    def test_removing_either_plist_literal_independently_breaks_contract(self) -> None:
        self.assert_plist_contract(self.load_config())
        # Config-only mutations call pure selector/scope functions and assert the
        # declared allowlist. Removing routing breaks selection; removing the
        # allowlist literal breaks declaration preservation, not effective scope.
        # Neither mutation has subprocess or filesystem effects.
        for section in ("routing", "allowlist"):
            with self.subTest(section=section):
                mutated = copy.deepcopy(self.load_config())
                if section == "routing":
                    route = next(r for r in mutated["task_routing"] if r["task"] == ROUTE_TASK)
                    route["when_all_files_in"].remove(PLIST)
                else:
                    mutated["allowed_file_patterns"][ROUTE_TASK].remove(PLIST)
                with self.assertRaises(AssertionError):
                    self.assert_plist_contract(mutated)

    def test_all_seven_harnesses_execute_and_individual_failures_propagate(self) -> None:
        commands = self.route_outcome(self.load_config(), ROUTE_ALLOWED_FILES)["harnesses"]
        self.assertEqual(commands, ROUTE_HARNESSES)
        for fail_index in (None, *range(7)):
            with self.subTest(fail_index=fail_index):
                returns = [subprocess.CompletedProcess([], int(i == fail_index), "fixture", "")
                           for i in range(7)]
                # Stub spawn BEFORE invoking harness execution, including negatives.
                with patch.object(MODULE.subprocess, "run", side_effect=returns) as spawn:
                    results, errors = MODULE.run_harness_commands(ROOT, commands, True)
                self.assertEqual([call.args[0] for call in spawn.call_args_list],
                                 [entry["command"] for entry in ROUTE_HARNESSES])
                self.assertEqual(len(errors), int(fail_index is not None))
                self.assertEqual([entry["exit_code"] for entry in results],
                                 [int(i == fail_index) for i in range(7)])


if __name__ == "__main__":
    unittest.main()
