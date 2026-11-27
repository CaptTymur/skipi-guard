"""Seafarer route `empty-slots-212`: an empty document slot is not duplicated between devices.

Owner 26.11.2026 (case 212): «давай теперь 212»; «разрешаю маршрут на frameworks.rs».

Every new template slot got an expiry date the app made up, so the slot never counted as empty and
each device uploaded its own copy. The fix touches three named files; the default task
`plugin-host` already lets two of them through, `src-tauri/src/frameworks.rs` (where the made-up
date is written) is the one this route adds. The route is deliberately narrow:
  * exactly three files, no wildcard;
  * `frameworks.rs` never moves without the sync rule (require_all_of);
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
LOADER = SourceFileLoader("guard_empty_slots", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "empty-slots-212"
CORE = ["src-tauri/src/commands/account_sync.rs", "src-tauri/src/frameworks.rs"]
OPTIONAL = ["src-tauri/src/commands/profile.rs"]
LATER = ("port-db-024", "app-name-skipi", "my-vessel-029")  # 26.11.2026, oracles in tests/test_seafarer_port_db_route.py and test_seafarer_app_name_route.py


class SeafarerEmptySlotsRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE + OPTIONAL, CORE):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_file_set_is_exactly_the_three_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 3)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(CORE))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "presence-manifest.json", "dist/index.html", "src-tauri/src/lib.rs",
                      "src-tauri/src/commands/documents.rs", "src-tauri/src/profiles.rs", "src-tauri/src/db.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_is_not_widened(self):
        self.assertFalse(self.allowed("plugin-host", "src-tauri/src/frameworks.rs"))

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_default_harnesses(self):
        self.assertEqual(self.config["harness_commands"][TASK], self.config["harness_commands"]["plugin-host"])

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)


if __name__ == "__main__":
    unittest.main()
