"""Exact four-file explicit consent route; synthetic Git and stubbed harness effects.

This is policy validation, not proof of native sync behavior. The unchanged
pre-push/verify implementation is exercised without product or external effects.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/seafarer.json"
LOADER = SourceFileLoader("guard_consent193", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "consent193"
FILES = [
    "dist/index.html",
    "src-tauri/src/commands/account_sync.rs",
    "tests/bundled_plugin_isolation_harness.mjs",
    "tests/one_account_sync_harness.mjs",
]
SYNC_HARNESSES = [
    {"name": "seafarer_account_profile_sync", "command": "node tests/account_profile_sync_harness.mjs"},
    {"name": "seafarer_one_account_sync", "command": "node tests/one_account_sync_harness.mjs"},
]
EXTRAS = [
    "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json",
    ".github/workflows/skipi-guard.yml", "src-tauri/src/cv.rs",
    "src-tauri/src/commands/mod.rs", "contracts/test.json",
    "keys/demo.pem", "src-tauri/gen/android/app/build.gradle.kts",
]


def without_sync(config):
    config = copy.deepcopy(config)
    config["task_routing"] = [r for r in config["task_routing"] if r["task"] != TASK]
    for section in ("exact_task_file_sets", "allowed_file_patterns", "harness_commands"):
        config[section].pop(TASK, None)
    return config


class SeafarerConsent193RouteTests(unittest.TestCase):
    def load_config(self):
        return json.loads(CONFIG.read_text())

    def assert_contract(self, config):
        rules = [r for r in config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0], {
            "name": "seafarer explicit two-checkbox account sync consent (193)",
            "task": TASK, "when_all_files_in": FILES, "require_all_of": FILES,
        })
        self.assertEqual(config["exact_task_file_sets"][TASK], FILES)
        self.assertEqual(config["allowed_file_patterns"][TASK], FILES)
        self.assertEqual(MODULE.resolve_task(config, FILES)["task"], TASK)
        self.assertFalse(MODULE.is_release_task(config, TASK))
        for section in ("protected_paths", "release_sensitive_paths"):
            self.assertEqual(MODULE.classify_paths(FILES, config[section], section), [])
        self.assertEqual(MODULE.effective_allowed_patterns(config, TASK, []), FILES)
        self.assertEqual(MODULE.scope_check_for_task(config, TASK, FILES, FILES)["scope_violations"], [])
        exact = MODULE.exact_file_set_check(config, TASK, FILES)
        self.assertEqual(exact["missing"], [])
        self.assertEqual(exact["unexpected"], [])
        retained = config["harness_commands"]["mobile-189-native"]
        self.assertEqual(len(retained), 10)
        self.assertEqual(MODULE.configured_harnesses(config, TASK), retained + SYNC_HARNESSES)

    def test_exact_route_and_retained_ten_plus_two_harnesses(self):
        self.assert_contract(self.load_config())

    def test_only_new_task_delta_preserves_pr61_baseline(self):
        baseline = without_sync(self.load_config())
        # Full parsed config at 6fb4072, including the exact13 sync route.
        self.assertEqual(hashlib.sha256(json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         "43baca039e91fd8cccd7d44d6a0b8e6bda349ec3395b4d7fc6452f8d0849ad7c")
        old_task = MODULE.resolve_task(baseline, FILES)["task"]
        self.assertNotEqual(old_task, TASK)
        self.assertTrue(MODULE.scope_check_for_task(baseline, old_task, FILES,
                            MODULE.effective_allowed_patterns(baseline, old_task, []))["scope_violations"])

    def verify_fixture(self, files, explicit=False):
        scratch = ROOT / "scratchpad/scratch193-consent-route"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fixture-", dir=scratch) as tmp:
            repo = Path(tmp)
            env = os.environ.copy()
            env.pop("SKIPI_GUARD_OVERRIDE_TOKEN", None)
            def git(*args):
                subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)
            git("init", "-q")
            git("config", "user.name", "Sync route fixture")
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
            command += ["--task", TASK] if explicit else ["--auto-task"]
            proc = subprocess.run(command, text=True, capture_output=True, env=env)
            return proc.returncode, json.loads(result.read_text())

    def test_real_cli_exact_auto_and_explicit_are_green_without_override(self):
        for explicit in (False, True):
            code, result = self.verify_fixture(FILES, explicit)
            self.assertEqual(code, 0, result)
            self.assertEqual(result["task"], TASK)
            self.assertEqual(result["effective_tasks"], [TASK])
            self.assertEqual(result["errors"], [])
            self.assertFalse(result["override_present"])
            self.assertFalse(result["release_changes"])
            self.assertEqual(result["allowed_file_patterns"], FILES)
            self.assertEqual([{k: t[k] for k in ("name", "command")} for t in result["tests"]],
                             MODULE.configured_harnesses(self.load_config(), TASK))
            self.assertTrue(all(t["status"] == "not_run" for t in result["tests"]))

    def test_real_cli_each_missing_and_empty_auto_and_explicit_are_red(self):
        for absent in FILES + [None]:
            files = [p for p in FILES if p != absent] if absent else []
            for explicit in (False, True):
                with self.subTest(absent=absent, explicit=explicit):
                    code, result = self.verify_fixture(files, explicit)
                    if explicit:
                        self.assertEqual(code, 1, result)
                        self.assertEqual(result["exact_file_set_missing"], [absent] if absent else FILES)
                    elif files:
                        # The subset without the sync harness retains the existing
                        # plugin-host route; consent193 must never claim a subset.
                        self.assertNotEqual(result["task"], TASK)
                        if absent != "tests/one_account_sync_harness.mjs":
                            self.assertEqual(code, 1, result)
                    else:
                        self.assertNotEqual(result["task"], TASK)

    def test_real_cli_each_unrelated_protected_release_extra_is_red(self):
        for extra in EXTRAS:
            for explicit in (False, True):
                with self.subTest(extra=extra, explicit=explicit):
                    code, result = self.verify_fixture(FILES + [extra], explicit)
                    self.assertEqual(code, 1, result)
                    self.assertTrue(result["scope_violations"], result)
                    self.assertFalse(result["override_present"])
                    if explicit:
                        self.assertEqual(result["scope_violations"], [extra])
                        self.assertEqual(result["exact_file_set_unexpected"], [extra])
                    else:
                        self.assertNotEqual(result["task"], TASK)

    def test_every_harness_failure_propagates_with_spawn_stub(self):
        config = self.load_config()
        self.assert_contract(config)
        commands = MODULE.configured_harnesses(config, TASK)
        for fail_index in range(12):
            with self.subTest(fail_index=fail_index):
                returns = [subprocess.CompletedProcess([], int(i == fail_index), "stub", "") for i in range(12)]
                with patch.object(MODULE.subprocess, "run", side_effect=returns) as spawn:
                    results, errors = MODULE.run_harness_commands(ROOT, commands, True)
                self.assertEqual([c.args[0] for c in spawn.call_args_list], [h["command"] for h in commands])
                self.assertEqual(len(errors), 1)
                self.assertEqual(results[fail_index]["status"], "fail")

    def test_contract_detects_route_scope_exact_harness_and_release_mutations(self):
        for mutation in ("remove_rule", "partial_route", "widen_scope", "remove_exact", "widen_exact", "drop_harness", "release"):
            with self.subTest(mutation=mutation):
                config = self.load_config()
                self.assert_contract(config)
                if mutation == "remove_rule":
                    config["task_routing"] = [r for r in config["task_routing"] if r["task"] != TASK]
                elif mutation == "partial_route":
                    next(r for r in config["task_routing"] if r["task"] == TASK)["require_all_of"].pop()
                elif mutation == "widen_scope":
                    config["allowed_file_patterns"][TASK].append("src-tauri/src/**")
                elif mutation == "remove_exact":
                    config["exact_task_file_sets"][TASK] = []
                elif mutation == "widen_exact":
                    config["exact_task_file_sets"][TASK].append(EXTRAS[0])
                elif mutation == "drop_harness":
                    config["harness_commands"][TASK].pop()
                else:
                    config["release_tasks"].append(TASK)
                with self.assertRaises(AssertionError):
                    self.assert_contract(config)


if __name__ == "__main__":
    unittest.main()
