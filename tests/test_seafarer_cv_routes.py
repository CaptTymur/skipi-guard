"""Owner-authorized CV routes: singleton Rust scope, exact sets, seven checks.

Fixtures verify routing and guard outcomes; harness execution is stubbed. This
policy bounds paths, not the meaning of Rust bytes or deletion of a target.
"""
from __future__ import annotations

import copy
import importlib.util
import hashlib
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
LOADER = SourceFileLoader("guard_cv_routes", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
ROUTES = {
    "cv-order-282": "src-tauri/src/db.rs",
    "career-pattern-302": "src-tauri/src/cv.rs",
}
HARNESSES = [
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
]
EXTRAS = [
    *ROUTES.values(), "src-tauri/src/lib.rs", "dist/index.html",
    "src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json",
    ".github/workflows/skipi-guard.yml", "src-tauri/src/cv_commands.rs",
    "src-tauri/src/DB.rs", "src-tauri/src/CV.rs",
]


class SeafarerCvRoutesTests(unittest.TestCase):
    def load_config(self):
        return json.loads(CONFIG.read_text())

    def assert_contract(self, config, task, target):
        self.assertEqual(MODULE.resolve_task(config, [target])["task"], task)
        self.assertFalse(MODULE.is_release_task(config, task))
        patterns = MODULE.effective_allowed_patterns(config, task, [])
        self.assertEqual(patterns, [target])
        self.assertEqual(MODULE.scope_check_for_task(config, task, [target], patterns)["scope_violations"], [])
        exact = MODULE.exact_file_set_check(config, task, [target])
        self.assertIsNotNone(exact)
        self.assertEqual(exact["missing"], [])
        self.assertEqual(exact["unexpected"], [])
        self.assertEqual(MODULE.exact_file_set_check(config, task, [])["missing"], [target])
        self.assertEqual(MODULE.configured_harnesses(config, task), HARNESSES)
        for extra in EXTRAS:
            if extra == target:
                continue
            files = [target, extra]
            self.assertNotEqual(MODULE.resolve_task(config, files)["task"], task)
            self.assertEqual(MODULE.scope_check_for_task(config, task, files, patterns)["scope_violations"], [extra])
            self.assertEqual(MODULE.exact_file_set_check(config, task, files)["unexpected"], [extra])

    def test_each_singleton_has_exact_scope_and_all_seven_harnesses(self):
        for task, target in ROUTES.items():
            with self.subTest(task=task):
                self.assert_contract(self.load_config(), task, target)

    def test_empty_and_unrelated_paths_never_route_to_cv_tasks(self):
        config = self.load_config()
        for files in [[], *([extra] for extra in EXTRAS if extra not in ROUTES.values())]:
            with self.subTest(files=files):
                self.assertNotIn(MODULE.resolve_task(config, files)["task"], ROUTES)
        for task, target in ROUTES.items():
            self.assertEqual(MODULE.exact_file_set_check(config, task, [])["missing"], [target])

    def test_config_adds_only_two_last_routes(self):
        config = self.load_config()
        tasks = [rule["task"] for rule in config["task_routing"]]
        self.assertEqual(len(tasks), 20)
        self.assertEqual(tasks[-2:], list(ROUTES))
        for task, target in ROUTES.items():
            rule = [r for r in config["task_routing"] if r["task"] == task]
            self.assertEqual(len(rule), 1)
            self.assertEqual(rule[0]["when_all_files_in"], [target])
            self.assertEqual(rule[0]["require_all_of"], [target])
            for key in ("protected_paths", "release_sensitive_paths"):
                self.assertEqual(MODULE.classify_paths([target], config[key], key), [])

    def test_retained_config_matches_reviewed_baseline(self):
        config = self.load_config()
        config["task_routing"] = [r for r in config["task_routing"] if r["task"] not in ROUTES]
        for section in ("allowed_file_patterns", "exact_task_file_sets", "harness_commands"):
            for task in ROUTES:
                config[section].pop(task, None)
        # Canonical JSON hash of c9076a9 seafarer.json; works in shallow CI.
        self.assertEqual(hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         "77bee5c4a74fcfb3f8c09428438973ed4060d32dc6bd4cdc025ca8910af713b7")

    def verify_fixture(self, files, task=None, bootstrap=False):
        # All filesystem effects remain in this test's disposable git fixture.
        with tempfile.TemporaryDirectory(prefix="guard-cv-") as tmp:
            repo = Path(tmp)
            env = os.environ.copy()
            env.pop("SKIPI_GUARD_OVERRIDE_TOKEN", None)
            def git(*args):
                subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)
            git("init", "-q")
            git("config", "user.name", "CV guard fixture")
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
            cmd = [str(GUARD), "verify", "--home", "seafarer", "--repo", str(repo),
                   "--base", "HEAD~1", "--head", "HEAD", "--json", str(result)]
            cmd += ["--task", task] if task else ["--auto-task"]
            if bootstrap:
                cmd += ["--auto-bootstrap-override"]
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
            return proc.returncode, json.loads(result.read_text())

    def test_real_verify_singletons_auto_and_explicit(self):
        for task, target in ROUTES.items():
            for explicit in (False, True):
                with self.subTest(task=task, explicit=explicit):
                    code, result = self.verify_fixture([target], task if explicit else None)
                    self.assertEqual(code, 0, result)
                    self.assertEqual(result["task"], task)
                    self.assertEqual(result["effective_tasks"], [task])
                    self.assertEqual(result["errors"], [])
                    self.assertFalse(result["override_present"])
                    self.assertFalse(result["release_changes"])
                    self.assertEqual(result["allowed_file_patterns"], [target])
                    self.assertEqual([{k: t[k] for k in ("name", "command")} for t in result["tests"]], HARNESSES)
                    self.assertTrue(all(t["status"] == "not_run" for t in result["tests"]))

    def test_real_verify_mixed_diffs_fail_scope_and_explicit_exact_sets(self):
        for task, target in ROUTES.items():
            for extra in EXTRAS:
                if target == extra:
                    continue
                for explicit in (False, True):
                    with self.subTest(task=task, extra=extra, explicit=explicit):
                        code, result = self.verify_fixture([target, extra], task if explicit else None)
                        self.assertEqual(code, 1, result)
                        self.assertTrue(result["scope_violations"], result)
                        if explicit:
                            self.assertEqual(result["scope_violations"], [extra])
                            self.assertEqual(result["exact_file_set_unexpected"], [extra])
                        else:
                            self.assertNotIn(result["task"], ROUTES)
                            self.assertIn(target, result["scope_violations"])

    def test_real_verify_empty_explicit_fails_missing_target(self):
        for task, target in ROUTES.items():
            code, result = self.verify_fixture([], task)
            self.assertEqual(code, 1, result)
            self.assertEqual(result["exact_file_set_missing"], [target])

    def test_workflow_only_keeps_pin_route_and_bootstrap_behavior(self):
        for bootstrap in (False, True):
            code, result = self.verify_fixture([".github/workflows/skipi-guard.yml"], bootstrap=bootstrap)
            self.assertEqual(result["task"], "guard-pin-bump")
            self.assertEqual(code, 0, result)
            self.assertEqual(result["auto_bootstrap_override"], bootstrap)
            self.assertEqual([{k: t[k] for k in ("name", "command")} for t in result["tests"]],
                             self.load_config()["harness_commands"]["guard-pin-bump"])

    def test_each_harness_executes_and_each_failure_propagates_with_spawn_stub(self):
        for task in ROUTES:
            commands = MODULE.configured_harnesses(self.load_config(), task)
            self.assertEqual(commands, HARNESSES)
            for fail_index in range(len(HARNESSES)):
                with self.subTest(task=task, fail_index=fail_index):
                    returns = [subprocess.CompletedProcess([], int(i == fail_index), "stub", "") for i in range(7)]
                    with patch.object(MODULE.subprocess, "run", side_effect=returns) as spawn:
                        results, errors = MODULE.run_harness_commands(ROOT, commands, True)
                    self.assertEqual([c.args[0] for c in spawn.call_args_list], [h["command"] for h in HARNESSES])
                    self.assertEqual(len(errors), 1)
                    self.assertEqual(results[fail_index]["status"], "fail")

    def test_contract_detects_route_harness_exact_and_allowlist_mutations_per_rule(self):
        for task, target in ROUTES.items():
            for mutation in ("remove_rule", "remove_harness", "widen_exact", "widen_allowlist", "remove_exact"):
                with self.subTest(task=task, mutation=mutation):
                    config = copy.deepcopy(self.load_config())
                    if mutation == "remove_rule":
                        config["task_routing"] = [r for r in config["task_routing"] if r["task"] != task]
                    elif mutation == "remove_harness":
                        config["harness_commands"][task].pop()
                    elif mutation == "widen_exact":
                        config["exact_task_file_sets"][task] = ["src-tauri/src/*.rs"]
                    elif mutation == "widen_allowlist":
                        config["allowed_file_patterns"][task].append("src-tauri/src/lib.rs")
                    else:
                        del config["exact_task_file_sets"][task]
                    with self.assertRaises(AssertionError):
                        self.assert_contract(config, task, target)


if __name__ == "__main__":
    unittest.main()
