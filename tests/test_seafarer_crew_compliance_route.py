"""Seafarer route `crew-compliance-018d`: the pilot's Compliance Profile carried over.

Owner word 25.11.2026 (case 208). Second module of the approved order (Crew Flow, Compliance
Profile, Seafarers DB). On the stub tab: «я не вижу ни одного комплайанс профиля — а должен быть
один». Asked for a route naming the one new Rust file `src-tauri/src/commands/crewing_compliance.rs`
(exact list, no wildcard): «пуш».

The route is deliberately narrow:
  * the files of `crew-pilot-modules-018c` (the branch is stacked on that still-open change) plus
    exactly one new file, `crewing_compliance.rs`. No wildcard: Seafarers DB needs a word of its own;
  * the new commands never move without the frontend and the harness (require_all_of);
  * no existing route — and not the default task `plugin-host` — is widened;
  * it is not a release task and adds no protected or release-sensitive path.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/seafarer.json"
LOADER = SourceFileLoader("guard_crew_compliance", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "crew-compliance-018d"
CORE = ["dist/index.html", "src-tauri/src/commands/crewing_compliance.rs", "tests/role_modules_harness.mjs"]
OPTIONAL = ["src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs", "src-tauri/src/commands/crewing.rs",
            "src-tauri/src/commands/crewing_intake.rs", "src-tauri/src/commands/crewing_contact.rs",
            "tests/no_dead_tauri_invoke_harness.mjs",
            "src-tauri/src/commands/app_login.rs",
            "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/vault.rs"]


class SeafarerCrewComplianceRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE, CORE + OPTIONAL, CORE + OPTIONAL[:2], CORE + OPTIONAL[2:]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_default_task_is_not_widened(self):
        for f in ("src-tauri/src/commands/crewing_compliance.rs", "src-tauri/src/commands/crewing_intake.rs", "tests/role_modules_harness.mjs"):
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "contracts/test.json", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_file_set_is_exactly_the_twelve_files(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 12)

    def test_no_wildcard_and_no_file_of_a_later_module(self):
        for pattern in self.config["allowed_file_patterns"][TASK]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK][0]
        for pattern in routing["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)
        # Compliance Profile and Seafarers DB are carried over later, each under its own word.
        for no in ("src-tauri/src/commands/crewing_seafarers.rs", "src-tauri/src/commands/crewing_db.rs",
                   "src-tauri/src/commands/crewing/x.rs", "src-tauri/src/commands/documents.rs",
                   "src-tauri/src/crewing.rs", "src-tauri/src/db.rs", "src-tauri/src/commands/jobs.rs"):
            self.assertFalse(self.allowed(TASK, no), no)
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + [no])["task"], TASK, no)

    def test_runs_the_same_harnesses_as_the_crew_flow_carry_over(self):
        self.assertEqual(self.config["harness_commands"][TASK], self.config["harness_commands"]["crew-pilot-modules-018c"])

    def test_the_earlier_role_route_is_untouched(self):
        earlier = ["dist/index.html", "src-tauri/src/commands/app_login.rs", "tests/role_modules_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, earlier)["task"], "role-modules-018")
        self.assertFalse(self.allowed("role-modules-018", "src-tauri/src/commands/crewing_intake.rs"))
        flow = ["dist/index.html", "src-tauri/src/commands/crewing.rs", "tests/role_modules_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, flow)["task"], "crew-flow-018b")
        self.assertFalse(self.allowed("crew-flow-018b", "src-tauri/src/commands/crewing_intake.rs"))
        pilot = flow[:1] + ["src-tauri/src/commands/crewing_intake.rs"] + flow[2:]
        self.assertEqual(MODULE.resolve_task(self.config, pilot)["task"], "crew-pilot-modules-018c")
        self.assertFalse(self.allowed("crew-pilot-modules-018c", "src-tauri/src/commands/crewing_compliance.rs"))

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))


if __name__ == "__main__":
    unittest.main()
