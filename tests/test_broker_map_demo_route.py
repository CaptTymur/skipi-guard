"""OWNER422: exact Broker Map/shared Demo route, without activating any pin.

Drive the actual CLI against disposable git/Node fixtures. These scripts prove
selection, invocation and failure propagation only; the future product Demo
harness and browser rendering are NOT implemented or tested by this proposal.
Baseline config: 95fdbdb7ade5c248d5bf8f536434c04cd0716cdb (live SSH 2026-09-08).
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/broker.json"
SCRATCH = ROOT / "scratchpad/broker-map-demo-422-20260908"
TASK = "broker-map-demo-422"
RULE = "broker Map/shared Demo routing (OWNER422, 2026-09-08)"
FILES = [
    "dist/index.html",
    "dist/broker-demo.js",
    "tests/broker_demo_harness.mjs",
    "tests/map_contract_harness.mjs",
]
HARNESSES = [
    {"name": "broker_plugin_isolation", "command": "node tests/broker_plugin_isolation_harness.mjs"},
    {"name": "broker_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "broker_presence_contract", "command": "node tests/broker_presence_contract_harness.mjs"},
    {"name": "broker_map_contract", "command": "node tests/map_contract_harness.mjs"},
    {"name": "broker_trial_gate_wired", "command": "node tests/trial_gate_wired_harness.mjs"},
    {"name": "broker_demo", "command": "node tests/broker_demo_harness.mjs"},
]
BASE_CONFIG_SHA256 = "b76ca5c45b0ff2edd77d64581e9c5be1005da7d97cc8ce2083f5872455301b03"
FOREIGN_FILES = [
    "src-tauri/src/lib.rs",
    ".github/workflows/skipi-guard.yml",
    "dist/plugin-host-bridge.js",
    "tests/unrelated_harness.mjs",
    "keys/fixture-secret.pem",
    "dist/map-module/map.js",
    "vendor/dist/broker-demo.js",
    "dist/broker-demo.js.bak",
]


class BrokerMapDemoRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="fixture-", dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.env = os.environ.copy()
        self.env.pop("SKIPI_GUARD_OVERRIDE_TOKEN", None)
        self.env.pop("SKIPI_GUARD_FIXTURE_FAIL", None)
        self.git("init", "-q")
        self.git("config", "user.name", "Skipi Guard Fixture")
        self.git("config", "user.email", "skipi-guard@example.invalid")
        self.write("dist/index.html", "<main>synthetic Guard fixture</main>\n")
        self.write("dist/broker-demo.js", "// synthetic Guard fixture, not product Demo\n")
        for entry in HARNESSES:
            name = json.dumps(entry["name"])
            # Actual Node processes leave independent receipts. No mocked
            # subprocess/selector, no production code or credential values.
            self.write(entry["command"].split()[1], (
                "import { appendFileSync } from 'node:fs';\n"
                f"const name = {name};\n"
                "appendFileSync('fixture-invocations.jsonl', JSON.stringify(name) + '\\n');\n"
                "if (process.env.SKIPI_GUARD_FIXTURE_FAIL === name) process.exit(23);\n"
                "console.log('GUARD FIXTURE executed: ' + name);\n"
            ))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "seed synthetic Guard fixtures")

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], check=True,
            capture_output=True, text=True, env=self.env,
        )

    def write(self, relative: str, contents: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def candidate(self, files: list[str] | tuple[str, ...]) -> None:
        for relative in files:
            path = self.repo / relative
            previous = path.read_text(encoding="utf-8") if path.exists() else ""
            self.write(relative, previous + "\n// Guard fixture candidate change\n")
        if files:
            self.git("add", "--", *files)
        self.git("commit", "-q", "--allow-empty", "-m", "synthetic route candidate")

    def run_guard(
        self, *, task: str | None = None, run_harness: bool = True,
        guard: Path = GUARD, extra: tuple[str, ...] = (),
    ) -> tuple[subprocess.CompletedProcess[str], dict, list[str]]:
        receipt = self.repo / "fixture-invocations.jsonl"
        receipt.unlink(missing_ok=True)
        result = self.root / "result.json"
        result.unlink(missing_ok=True)
        command = [
            str(guard), "verify", "--home", "broker", "--repo", str(self.repo),
            "--base", "HEAD~1", "--head", "HEAD", "--json", str(result),
        ]
        command.extend(["--task", task] if task else ["--auto-task"])
        if run_harness:
            command.append("--run-harness")
        proc = subprocess.run(command + list(extra), capture_output=True, text=True, env=self.env)
        self.assertTrue(result.exists(), proc.stdout + proc.stderr)
        payload = json.loads(result.read_text(encoding="utf-8"))
        calls = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
        return proc, payload, calls

    def assert_all_six_executed(self, payload: dict, calls: list[str]) -> None:
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            HARNESSES,
        )
        self.assertEqual(calls, [entry["name"] for entry in HARNESSES])
        self.assertEqual([entry["status"] for entry in payload["tests"]], ["pass"] * 6)
        self.assertEqual([entry["exit_code"] for entry in payload["tests"]], [0] * 6)

    def assert_route_pass(self, files: list[str] | tuple[str, ...], *, task: str | None = None) -> None:
        proc, payload, calls = self.run_guard(task=task)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], TASK)
        self.assertEqual(payload["task_rule"], None if task else RULE)
        self.assertEqual(payload["task_source"], "explicit" if task else "auto")
        self.assertEqual(payload["changed_files"], sorted(files))
        self.assertEqual(payload["allowed_file_patterns"], FILES)
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertFalse(payload["override_present"])
        self.assertFalse(payload["release_changes"])
        self.assert_all_six_executed(payload, calls)

    def test_all_15_nonempty_subsets_auto_route_and_execute_all_six(self) -> None:
        count = 0
        for size in range(1, len(FILES) + 1):
            for subset in itertools.combinations(FILES, size):
                with self.subTest(files=subset):
                    self.candidate(subset)
                    self.assert_route_pass(subset)
                    count += 1
        self.assertEqual(count, 15)

    def test_index_only_does_not_need_a_dummy_harness_edit(self) -> None:
        self.candidate(["dist/index.html"])
        self.assert_route_pass(["dist/index.html"])
        self.assert_route_pass(["dist/index.html"], task=TASK)

    def test_full_four_file_candidate_works_as_explicit_task(self) -> None:
        self.candidate(FILES)
        self.assert_route_pass(FILES, task=TASK)

    def test_empty_diff_does_not_auto_authorize_the_route(self) -> None:
        self.candidate([])
        _, payload, _ = self.run_guard(run_harness=False)
        self.assertEqual(payload["changed_files"], [])
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIsNone(payload["task_rule"])

    def test_foreign_files_fail_auto_fallback_and_explicit_route(self) -> None:
        for foreign in FOREIGN_FILES:
            self.candidate(FILES + [foreign])
            for task in (None, TASK):
                with self.subTest(foreign=foreign, task=task):
                    proc, payload, _ = self.run_guard(task=task, run_harness=False)
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertEqual(payload["status"], "fail")
                    self.assertEqual(payload["task"], task or "plugin-host")
                    self.assertTrue(payload["scope_violations"])
                    if task:
                        self.assertIn(foreign, payload["scope_violations"])
                    else:
                        self.assertIn("dist/broker-demo.js", payload["scope_violations"])
                    self.assertFalse(payload["override_present"])

    def test_other_scoped_tasks_cannot_accept_full_feature_set(self) -> None:
        self.candidate(FILES)
        for task in ("plugin-host", "security-escaping-191", "release", "repo-meta", "settings-adopt", "stack-metadata"):
            with self.subTest(task=task):
                proc, payload, _ = self.run_guard(task=task, run_harness=False)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertIn("dist/broker-demo.js", payload["scope_violations"])

    def test_each_nonzero_harness_fails_actual_cli(self) -> None:
        self.candidate(["dist/index.html"])
        for entry in HARNESSES:
            with self.subTest(harness=entry["name"]):
                self.env["SKIPI_GUARD_FIXTURE_FAIL"] = entry["name"]
                proc, payload, calls = self.run_guard()
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(calls, [item["name"] for item in HARNESSES])
                failed = [test for test in payload["tests"] if test["status"] == "fail"]
                self.assertEqual([test["name"] for test in failed], [entry["name"]])
                self.assertEqual(failed[0]["exit_code"], 23)
                self.assertTrue(any(entry["command"] in error for error in payload["errors"]))

    def test_each_missing_harness_file_fails_actual_cli(self) -> None:
        self.candidate(["dist/index.html"])
        for entry in HARNESSES:
            with self.subTest(harness=entry["name"]):
                path = self.repo / entry["command"].split()[1]
                contents = path.read_bytes()
                path.unlink()
                try:
                    proc, payload, calls = self.run_guard()
                finally:
                    path.write_bytes(contents)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(calls, [item["name"] for item in HARNESSES if item != entry])
                failed = [test for test in payload["tests"] if test["status"] == "fail"]
                self.assertEqual([test["name"] for test in failed], [entry["name"]])
                self.assertNotEqual(failed[0]["exit_code"], 0)
                self.assertTrue(any(entry["command"] in error for error in payload["errors"]))

    def test_omitted_command_is_rejected_by_execution_oracle(self) -> None:
        # CLI cannot invent a removed declaration: its exit code can be zero.
        # The exact-list/receipt oracle must reject each such config mutation.
        self.candidate(["dist/index.html"])
        guard_copy = self.root / "guard-copy"
        (guard_copy / "bin").mkdir(parents=True)
        (guard_copy / "configs/homes").mkdir(parents=True)
        shutil.copy2(GUARD, guard_copy / "bin/skipi-guard")
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["harness_commands"].get(TASK), HARNESSES)
        for omitted in HARNESSES:
            with self.subTest(omitted=omitted["name"]):
                mutated = copy.deepcopy(config)
                mutated["harness_commands"][TASK].remove(omitted)
                (guard_copy / "configs/homes/broker.json").write_text(json.dumps(mutated), encoding="utf-8")
                proc, payload, calls = self.run_guard(guard=guard_copy / "bin/skipi-guard")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(len(calls), 5)
                self.assertNotIn(omitted["name"], calls)
                with self.assertRaises(AssertionError):
                    self.assert_all_six_executed(payload, calls)

    def test_config_only_invocation_is_reported_as_not_run(self) -> None:
        self.candidate(FILES)
        proc, payload, calls = self.run_guard(run_harness=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["task"], TASK)
        self.assertEqual([entry["status"] for entry in payload["tests"]], ["not_run"] * 6)
        self.assertEqual(calls, [])

    def test_exact_new_route_and_entire_previous_config_are_preserved(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        routes = [rule for rule in config["task_routing"] if rule["task"] == TASK]
        self.assertEqual(routes, [{
            "name": RULE, "task": TASK, "when_all_files_in": FILES, "require_any_of": FILES,
        }])
        self.assertEqual(config["allowed_file_patterns"][TASK], FILES)
        self.assertEqual(config["harness_commands"][TASK], HARNESSES)
        self.assertNotIn(TASK, config.get("exact_task_file_sets", {}))
        self.assertNotIn(TASK, config["release_tasks"])
        config["task_routing"].remove(routes[0])
        del config["allowed_file_patterns"][TASK]
        del config["harness_commands"][TASK]
        canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), BASE_CONFIG_SHA256)

    def test_old_auto_routes_and_workflow_bootstrap_are_preserved(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cases = [
            (["dist/index.html", "tests/broker_escaping_negative_harness.mjs"], "security-escaping-191", 0, ()),
            (["AGENTS.md", "CLAUDE.md"], "repo-meta", 0, ()),
            (config["exact_task_file_sets"]["stack-metadata"], "stack-metadata", 0, ()),
            (["dist/index.html", "src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"], "release", 0, ()),
            (["dist/index.html", "dist/skipi-settings.js"], "settings-adopt", 0, ()),
            (["src-tauri/gen/android/app/proguard-rules.pro", ".github/workflows/skipi-guard.yml"], "release", 1, ()),
            (["dist/plugin-host-bridge.js"], "plugin-host", 0, ()),
            ([".github/workflows/skipi-guard.yml"], "plugin-host", 1, ()),
            ([".github/workflows/skipi-guard.yml"], "plugin-host", 0, ("--auto-bootstrap-override",)),
        ]
        for files, task, exit_code, extra in cases:
            with self.subTest(files=files, extra=extra):
                self.candidate(files)
                proc, payload, _ = self.run_guard(run_harness=False, extra=extra)
                self.assertEqual(proc.returncode, exit_code, proc.stdout + proc.stderr)
                self.assertEqual(payload["task"], task)
                self.assertEqual(payload["status"], "pass" if exit_code == 0 else "fail")
                self.assertEqual(payload["auto_bootstrap_override"], bool(extra))


if __name__ == "__main__":
    unittest.main()
