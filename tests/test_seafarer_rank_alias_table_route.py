"""Bounded route for the rank alias table of the seafarer profile (P2/R3).

Policy validation only: the route is checked against the live home config with
the unchanged resolver and the unchanged CLI on synthetic Git fixtures. No
product, network or external effects. The negative cases matter more than the
positive one - a route that cannot refuse is not a route, and a route appended
last must be proven to shadow nothing that was already there.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/seafarer.json"
LOADER = SourceFileLoader("guard_rank_alias_table", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = "seafarer-rank-alias-table"
RULE_NAME = "rank alias table of the seafarer profile (P2/R3)"
FILES = [
    "dist/index.html",
    "src-tauri/src/profiles.rs",
    "tests/jobs_profile_visibility_harness.mjs",
]
REQUIRED = [
    "src-tauri/src/profiles.rs",
    "tests/jobs_profile_visibility_harness.mjs",
]
# The rank alias table is proved by the same harness as the sibling P2 route,
# so this route runs the identical command list - never fewer.
SIBLING_TASK = "jobs-profile-visibility-s2"
# Files this route must never carry. Each one is a different way to widen it:
# the sibling command, the host wiring, the gate pin, build metadata, the
# presence contract, a store/release surface, and the Android host.
FORBIDDEN = [
    "src-tauri/src/commands/jobs.rs",
    "src-tauri/src/lib.rs",
    ".github/workflows/skipi-guard.yml",
    "src-tauri/Cargo.toml",
    "presence-manifest.json",
    "src-tauri/tauri.conf.json",
    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
]


def load_config():
    return json.loads(CONFIG.read_text())


def without_route(config):
    """The config as it was before this route, to prove the route is the delta."""
    config = copy.deepcopy(config)
    config["task_routing"] = [r for r in config["task_routing"] if r["task"] != TASK]
    for section in ("exact_task_file_sets", "allowed_file_patterns", "harness_commands"):
        config[section].pop(TASK, None)
    return config


class SeafarerRankAliasTableRouteTests(unittest.TestCase):
    def test_route_shape_is_exact_and_carries_no_globs(self):
        config = load_config()
        rules = [r for r in config["task_routing"] if r.get("task") == TASK]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], RULE_NAME)
        self.assertEqual(rules[0]["when_all_files_in"], FILES)
        self.assertEqual(rules[0]["require_all_of"], REQUIRED)
        self.assertNotIn("require_any_of", rules[0])
        self.assertEqual(config["allowed_file_patterns"][TASK], FILES)
        for pattern in rules[0]["when_all_files_in"] + rules[0]["require_all_of"] + config["allowed_file_patterns"][TASK]:
            for glob in ("*", "?", "["):
                self.assertNotIn(glob, pattern)

    def test_route_is_appended_last_and_adds_nothing_else(self):
        config = load_config()
        self.assertEqual(config["task_routing"][-1]["task"], TASK)
        self.assertEqual(list(config["allowed_file_patterns"])[-1], TASK)
        self.assertEqual(list(config["harness_commands"])[-1], TASK)
        baseline = without_route(config)
        # The delta is this task and nothing else, in every section.
        self.assertEqual(len(config["task_routing"]) - len(baseline["task_routing"]), 1)
        self.assertEqual(config["task_routing"][:-1], baseline["task_routing"])
        for section in ("allowed_file_patterns", "harness_commands"):
            self.assertEqual(set(config[section]) - set(baseline[section]), {TASK})
        # The route joins neither the exact-set contract nor the release tasks:
        # it opens no release-sensitive path (finding H-1, RISKS No224b).
        self.assertNotIn(TASK, config["exact_task_file_sets"])
        self.assertNotIn(TASK, config["release_tasks"])
        self.assertFalse(MODULE.is_release_task(config, TASK))

    def test_protected_paths_untouched_by_this_route(self):
        config = load_config()
        self.assertEqual(config["protected_paths"], without_route(config)["protected_paths"])
        self.assertEqual(config["release_sensitive_paths"], without_route(config)["release_sensitive_paths"])
        for section in ("protected_paths", "release_sensitive_paths"):
            self.assertEqual(MODULE.classify_paths(FILES, config[section], section), [])

    def test_route_runs_the_same_harness_list_as_its_sibling_p2_route(self):
        config = load_config()
        harnesses = MODULE.configured_harnesses(config, TASK)
        self.assertEqual(harnesses, config["harness_commands"][SIBLING_TASK])
        self.assertEqual(len(harnesses), 10)
        # The test the route makes mandatory in the diff is the one it runs.
        self.assertIn(
            {"name": "seafarer_jobs_profile_visibility", "command": "node tests/jobs_profile_visibility_harness.mjs"},
            harnesses,
        )

    def test_positive_the_exact_set_resolves_here_and_passes_scope(self):
        config = load_config()
        routed = MODULE.resolve_task(config, FILES)
        self.assertEqual(routed["task"], TASK)
        self.assertEqual(routed["rule"], RULE_NAME)
        allowed = MODULE.effective_allowed_patterns(config, TASK, [])
        self.assertEqual(allowed, FILES)
        self.assertFalse(MODULE.scope_check_for_task(config, TASK, FILES, allowed)["scope_violations"])

    def test_negative_same_set_without_the_route_is_refused(self):
        """The load-bearing negative: the pre-route config must NOT allow this set."""
        baseline = without_route(load_config())
        task = MODULE.resolve_task(baseline, FILES)["task"]
        self.assertNotEqual(task, TASK)
        allowed = MODULE.effective_allowed_patterns(baseline, task, [])
        self.assertTrue(MODULE.scope_check_for_task(baseline, task, FILES, allowed)["scope_violations"])

    def test_negative_each_foreign_file_breaks_the_route_on_its_own(self):
        config = load_config()
        for extra in FORBIDDEN:
            with self.subTest(extra=extra):
                self.assertNotIn(extra, config["allowed_file_patterns"][TASK])
                files = FILES + [extra]
                allowed = MODULE.effective_allowed_patterns(config, TASK, [])
                self.assertTrue(MODULE.scope_check_for_task(config, TASK, files, allowed)["scope_violations"])
                # Auto-routing never lands on this task with the foreign file.
                self.assertNotEqual(MODULE.resolve_task(config, files)["task"], TASK)

    def test_negative_dropping_a_required_file_does_not_route_here(self):
        config = load_config()
        for missing in REQUIRED:
            with self.subTest(missing=missing):
                files = [f for f in FILES if f != missing]
                self.assertNotEqual(MODULE.resolve_task(config, files)["task"], TASK)

    def test_appended_last_route_shadows_no_existing_route(self):
        """Every rule that existed before keeps resolving its own file set."""
        config = load_config()
        baseline = without_route(config)
        for rule in baseline["task_routing"]:
            with self.subTest(rule=rule["task"]):
                files = list(rule["when_all_files_in"])
                self.assertEqual(
                    MODULE.resolve_task(config, files)["task"],
                    MODULE.resolve_task(baseline, files)["task"],
                )
                required = list(rule.get("require_all_of", []))
                if required:
                    self.assertEqual(
                        MODULE.resolve_task(config, required)["task"],
                        MODULE.resolve_task(baseline, required)["task"],
                    )

    def verify_fixture(self, files, explicit=False):
        return self.verify_fixture_for(TASK, files, explicit)

    def verify_fixture_for(self, task, files, explicit=False):
        scratch = ROOT / "scratchpad/rank-alias-table-20260929"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fixture-", dir=scratch) as tmp:
            repo = Path(tmp)
            env = os.environ.copy()
            env.pop("SKIPI_GUARD_OVERRIDE_TOKEN", None)

            def git(*args):
                subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)

            git("init", "-q")
            git("config", "user.name", "Rank alias route fixture")
            git("config", "user.email", "guard@example.invalid")
            (repo / "seed.txt").write_text("seed\n")
            git("add", "seed.txt")
            git("commit", "-qm", "seed")
            for relative in files:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic candidate\n")
            git("add", "-A")
            git("commit", "--allow-empty", "-qm", "candidate")
            result = repo / "result.json"
            command = [str(GUARD), "verify", "--home", "seafarer", "--repo", str(repo),
                       "--base", "HEAD~1", "--head", "HEAD", "--json", str(result)]
            command += ["--task", task] if explicit else ["--auto-task"]
            proc = subprocess.run(command, text=True, capture_output=True, env=env)
            return proc.returncode, json.loads(result.read_text())

    def test_real_cli_exact_set_is_green_auto_and_explicit_without_override(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                code, result = self.verify_fixture(FILES, explicit)
                self.assertEqual(code, 0, result)
                self.assertEqual(result["task"], TASK)
                self.assertEqual(result["effective_tasks"], [TASK])
                self.assertEqual(result["errors"], [])
                self.assertFalse(result["override_present"])
                self.assertFalse(result["release_changes"])
                self.assertEqual(result["protected_paths_touched"], [])
                self.assertEqual(result["allowed_file_patterns"], FILES)
                self.assertEqual([{k: t[k] for k in ("name", "command")} for t in result["tests"]],
                                 MODULE.configured_harnesses(load_config(), TASK))
                self.assertTrue(all(t["status"] == "not_run" for t in result["tests"]))

    def test_real_cli_without_the_mandatory_harness_is_red_on_the_routed_path(self):
        """require_all_of is what makes the test mandatory rather than optional.

        The routed path is the one the deployed pre-push hook uses: the task is
        resolved from the pushed diff, there is no task override (README,
        SKI-INC-2026-07-16). Dropping either required file leaves the route and
        lands on the default task, where the same files are out of scope.
        """
        for missing in REQUIRED:
            with self.subTest(missing=missing):
                files = [f for f in FILES if f != missing]
                code, result = self.verify_fixture(files, explicit=False)
                self.assertEqual(code, 1, result)
                self.assertEqual(result["status"], "fail")
                self.assertNotEqual(result["task"], TASK)
                self.assertTrue(
                    any("outside allowed patterns" in error for error in result["errors"]),
                    result["errors"],
                )

    def test_explicit_task_boundary_is_no_weaker_than_the_reviewed_sibling(self):
        """Boundary, stated instead of hidden: require_all_of is a ROUTING
        predicate, so an explicitly named task (--task, or vars.SKIPI_GUARD_TASK
        in CI) is not held to it; only tasks with an exact_task_file_sets entry
        refuse a subset that way. An exact set cannot express this route, whose
        dist/index.html is deliberately optional. This test therefore pins no
        engine behaviour as desirable - it pins that this route behaves exactly
        like the already reviewed sibling P2 route, so it can never become the
        weaker of the two without failing here.
        """
        sibling_files = load_config()["allowed_file_patterns"][SIBLING_TASK]
        for missing, sibling_missing in (
            (REQUIRED[0], "src-tauri/src/commands/jobs.rs"),
            (REQUIRED[1], "tests/jobs_profile_visibility_harness.mjs"),
        ):
            with self.subTest(missing=missing):
                mine = self.verify_fixture([f for f in FILES if f != missing], explicit=True)[0]
                sibling = self.verify_fixture_for(
                    SIBLING_TASK, [f for f in sibling_files if f != sibling_missing], explicit=True
                )[0]
                self.assertEqual(mine, sibling)

    def test_real_cli_each_foreign_file_is_red(self):
        for extra in FORBIDDEN:
            for explicit in (False, True):
                with self.subTest(extra=extra, explicit=explicit):
                    code, result = self.verify_fixture(FILES + [extra], explicit)
                    self.assertEqual(code, 1, result)
                    self.assertFalse(result["override_present"])
                    self.assertTrue(result["errors"], result)
                    if explicit:
                        self.assertEqual(result["scope_violations"], [extra])
                    else:
                        self.assertNotEqual(result["task"], TASK)


if __name__ == "__main__":
    unittest.main()
