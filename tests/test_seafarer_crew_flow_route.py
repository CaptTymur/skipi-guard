"""Seafarer route `crew-flow-018b`: the crewing role's live Crew Flow in the one Skipi app.

Owner word 25.11.2026 (case 208, the goal: «чтобы я мог залогиниться в skipi с аккаунтом
crewing@skipi.app … и продолжать пилот»; one sign-in chosen; asked about the server deploys and
the guard route for the client branch: «1,2,3 разрешаю»). The change adds the Rust command
`crewing_flow_overview` (new `src-tauri/src/commands/crewing.rs`, registered in `mod.rs` and
`lib.rs`) and the Crew Flow screen in `dist/index.html`, pinned by `tests/role_modules_harness.mjs`.

The route is deliberately narrow:
  * these five files; the three other files of `role-modules-018` are allowed only because the
    branch is stacked on that still-open change and a push range may carry both;
  * the command never moves without the frontend and the harness (require_all_of);
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
LOADER = SourceFileLoader("guard_crew_flow", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "crew-flow-018b"
CORE = ["dist/index.html", "src-tauri/src/commands/crewing.rs", "tests/role_modules_harness.mjs"]
OPTIONAL = ["src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs", "src-tauri/src/commands/app_login.rs",
            "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/vault.rs"]


class SeafarerCrewFlowRouteTests(unittest.TestCase):
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
        for f in ("src-tauri/src/commands/crewing.rs", "src-tauri/src/commands/app_login.rs", "tests/role_modules_harness.mjs"):
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "contracts/test.json", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_file_set_is_exactly_the_eight_files(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))

    def test_runs_the_plugin_host_harnesses_plus_login_gate_and_its_own(self):
        self.assertEqual(
            self.config["harness_commands"][TASK],
            self.config["harness_commands"]["plugin-host"] + [
                {"name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs"},
                {"name": "seafarer_role_modules", "command": "node tests/role_modules_harness.mjs"},
            ],
        )

    def test_the_earlier_role_route_is_untouched(self):
        earlier = ["dist/index.html", "src-tauri/src/commands/app_login.rs", "tests/role_modules_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, earlier)["task"], "role-modules-018")
        self.assertFalse(self.allowed("role-modules-018", "src-tauri/src/commands/crewing.rs"))

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))


if __name__ == "__main__":
    unittest.main()
