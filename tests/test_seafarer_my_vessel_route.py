"""Seafarer route `my-vessel-029`: My Vessel — check in on a vessel by IMO, crew aboard, notice board.

Owner 27.11.2026 (case 265): «моряк может зачекиниться на судне. и судно становится общим пространством
для тех кто на нем зачекинен»; «судно будет только одно по имо номеру. и один моряк будет зарегистрирован
на одном судне»; «базовую функцию можно сделать — доска объявлений»; «модулю судно можно сделать
отдельный репо».

The change vendors the module @skipi/vessel with its pin (dist/skipi-vessel.js, dist/skipi-vessel.css,
dist/VESSEL_VERSION), adds the native commands (src-tauri/src/commands/vessel_space.rs) and a harness,
and routes the My Vessel tab to the module. The route is deliberately narrow:
  * exactly nine named files, no wildcard;
  * the module, its pin, the commands and the harness always move together (require_all_of);
  * not a release task, no exact set;
  * no existing route — and not the default task `plugin-host` — is widened.
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
LOADER = SourceFileLoader("guard_my_vessel", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "my-vessel-029"
LATER = ("chartering-031",)  # 27.11.2026, oracle in tests/test_seafarer_chartering_route.py
CORE = ["dist/VESSEL_VERSION", "dist/skipi-vessel.js", "src-tauri/src/commands/vessel_space.rs", "tests/my_vessel_harness.mjs"]
OPTIONAL = ["dist/index.html", "dist/skipi-vessel.css", "src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"]
NEW_FILES = ["dist/VESSEL_VERSION", "dist/skipi-vessel.css", "dist/skipi-vessel.js", "src-tauri/src/commands/vessel_space.rs", "tests/my_vessel_harness.mjs"]


class SeafarerMyVesselRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE + OPTIONAL, CORE + ["dist/index.html"]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_file_set_is_exactly_the_nine_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 9)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["when_all_files_in"]), sorted(CORE + OPTIONAL))
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(CORE))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "presence-manifest.json", "dist/plugin-host-ui.js", "dist/vessel-db.js", "dist/port-db.js", "src-tauri/src/commands/messaging.rs", "tests/jobs_profile_visibility_harness.mjs",
                      "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/app_login.rs", "src-tauri/src/db.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_is_not_widened(self):
        for path in NEW_FILES:
            if path.startswith("src-tauri/") or path == "dist/VESSEL_VERSION":
                self.assertFalse(self.allowed("plugin-host", path), path)

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_default_harnesses_and_its_own(self):
        names = [h["command"] for h in self.config["harness_commands"][TASK]]
        for h in self.config["harness_commands"]["plugin-host"]:
            self.assertIn(h["command"], names)
        self.assertIn("node tests/my_vessel_harness.mjs", names)

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)


if __name__ == "__main__":
    unittest.main()
