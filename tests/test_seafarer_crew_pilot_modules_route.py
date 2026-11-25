"""Seafarer route `crew-pilot-modules-018c`: the crewing role's modules are the pilot's, carried over.

Owner word 25.11.2026 (case 208). On seeing the simplified Crew Flow: «это совершенно не то что мы
сделали в крюинг пилот. посмотри в репе skipi crewing как выглядят модули crewflow and seafarers DB
and compliance profile». Asked about the order (Crew Flow, Compliance Profile, Seafarers DB) and the
guard route for carrying the pilot's Rust files over: «утверждаю твой порядок переноса… по пункту 3
разрешаю. гоу».

The carry-over adds two Rust files of the pilot beside `crewing.rs` (`crewing_intake.rs`,
`crewing_contact.rs`), the pilot's Crew Flow screen in
`dist/index.html`, and teaches `tests/no_dead_tauri_invoke_harness.mjs` to see `pub(crate)` commands.

The route is deliberately narrow:
  * exactly the Rust files of THIS carry-over — `crewing.rs`, `crewing_intake.rs`,
    `crewing_contact.rs` — plus the two registration files. No wildcard: the files of the next
    two modules are not named here and need the owner's word of their own;
  * the three other files of `role-modules-018` are allowed only because the branch is stacked on
    that still-open change and a push range may carry both;
  * the pilot's commands never move without the frontend and the harness (require_all_of);
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
LOADER = SourceFileLoader("guard_crew_pilot_modules", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "crew-pilot-modules-018c"
CORE = ["dist/index.html", "src-tauri/src/commands/crewing_intake.rs", "tests/role_modules_harness.mjs"]
OPTIONAL = ["src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs", "src-tauri/src/commands/crewing.rs",
            "src-tauri/src/commands/crewing_contact.rs", "tests/no_dead_tauri_invoke_harness.mjs",
            "src-tauri/src/commands/app_login.rs",
            "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/vault.rs"]


class SeafarerCrewPilotModulesRouteTests(unittest.TestCase):
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
        for f in ("src-tauri/src/commands/crewing_intake.rs", "src-tauri/src/commands/crewing_contact.rs", "tests/role_modules_harness.mjs"):
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "contracts/test.json", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_file_set_is_exactly_the_eleven_files(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 11)

    def test_no_wildcard_and_no_file_of_a_later_module(self):
        for pattern in self.config["allowed_file_patterns"][TASK]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK][0]
        for pattern in routing["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)
        # Compliance Profile and Seafarers DB are carried over later, each under its own word.
        for no in ("src-tauri/src/commands/crewing_compliance.rs", "src-tauri/src/commands/crewing_seafarers.rs",
                   "src-tauri/src/commands/crewing/x.rs", "src-tauri/src/commands/documents.rs",
                   "src-tauri/src/crewing.rs", "src-tauri/src/db.rs", "src-tauri/src/commands/jobs.rs"):
            self.assertFalse(self.allowed(TASK, no), no)
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + [no])["task"], TASK, no)

    def test_runs_the_crew_flow_harnesses_plus_the_dead_command_check(self):
        self.assertEqual(
            self.config["harness_commands"][TASK],
            self.config["harness_commands"]["crew-flow-018b"] + [
                {"name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs"},
            ],
        )

    def test_the_earlier_role_route_is_untouched(self):
        earlier = ["dist/index.html", "src-tauri/src/commands/app_login.rs", "tests/role_modules_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, earlier)["task"], "role-modules-018")
        self.assertFalse(self.allowed("role-modules-018", "src-tauri/src/commands/crewing_intake.rs"))
        flow = ["dist/index.html", "src-tauri/src/commands/crewing.rs", "tests/role_modules_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, flow)["task"], "crew-flow-018b")
        self.assertFalse(self.allowed("crew-flow-018b", "src-tauri/src/commands/crewing_intake.rs"))

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))


if __name__ == "__main__":
    unittest.main()
