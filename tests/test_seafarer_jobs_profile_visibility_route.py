"""Bounded route for showing published compliance profiles inside Jobs (P2/S2b).

Policy validation only: the route is checked against the live home config with
the unchanged resolver. No product, network or external effects. The negative
cases matter more than the positive one — a route that cannot refuse is not a
route.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/seafarer.json"
LOADER = SourceFileLoader("guard_jobs_profile_visibility", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = "jobs-profile-visibility-s2"
RULE_NAME = "published compliance profiles inside Jobs (P2/S2b)"
FILES = [
    "dist/index.html",
    "src-tauri/src/commands/jobs.rs",
    "src-tauri/src/lib.rs",
    "tests/jobs_profile_visibility_harness.mjs",
]
REQUIRED = [
    "src-tauri/src/commands/jobs.rs",
    "tests/jobs_profile_visibility_harness.mjs",
]
# Files this route must never carry. Each one is a different way to widen it:
# a sibling command, the gate pin, build metadata, the presence contract, a
# store/release surface, and the Android host.
FORBIDDEN = [
    "src-tauri/src/commands/vault.rs",
    ".github/workflows/skipi-guard.yml",
    "src-tauri/tauri.conf.json",
    "presence-manifest.json",
    "src-tauri/Cargo.toml",
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


class SeafarerJobsProfileVisibilityRouteTests(unittest.TestCase):
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
        baseline = without_route(config)
        # The delta is this task and nothing else, in every section.
        for section in ("task_routing",):
            self.assertEqual(len(config[section]) - len(baseline[section]), 1)
        for section in ("allowed_file_patterns", "harness_commands"):
            self.assertEqual(set(config[section]) - set(baseline[section]), {TASK})
        # The route does not join the exact-set contract of other tasks.
        self.assertNotIn(TASK, config["exact_task_file_sets"])

    def test_protected_paths_untouched_by_this_route(self):
        self.assertEqual(load_config()["protected_paths"], without_route(load_config())["protected_paths"])

    def test_positive_the_exact_set_resolves_here_and_passes_scope(self):
        config = load_config()
        self.assertEqual(MODULE.resolve_task(config, FILES)["task"], TASK)
        allowed = MODULE.effective_allowed_patterns(config, TASK, [])
        self.assertFalse(MODULE.scope_check_for_task(config, TASK, FILES, allowed)["scope_violations"])

    def test_negative_same_set_without_the_route_is_refused(self):
        """The load-bearing negative: today's config must NOT allow this set."""
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

    def test_negative_dropping_a_required_file_does_not_route_here(self):
        config = load_config()
        for missing in REQUIRED:
            with self.subTest(missing=missing):
                files = [f for f in FILES if f != missing]
                self.assertNotEqual(MODULE.resolve_task(config, files)["task"], TASK)


if __name__ == "__main__":
    unittest.main()
