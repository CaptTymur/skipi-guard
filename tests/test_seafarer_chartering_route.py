"""Seafarer route `chartering-031`: the chartering account opens the module @skipi/chartering.

Owner 27.11.2026 (case 280, tasks/031): «да, подтверждаю» — the module @skipi/chartering 0.5.0 is connected
to the app; «маршрут разрешаю» — for exactly the fourteen files of the change.

The change vendors the module with its pin (dist/skipi-chartering.js, dist/skipi-chartering.css,
dist/CHARTERING_VERSION), adds the native commands (src-tauri/src/commands/chartering.rs) and a harness,
and opens the module as the first tab of the chartering role. It rides on the role framework of
`role-modules-018` (not merged yet), so that route's five files are part of this one. Deliberately narrow:
  * exactly fourteen named files, no wildcard;
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
LOADER = SourceFileLoader("guard_chartering", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "chartering-031"
LATER = ()
CORE = ["dist/CHARTERING_VERSION", "dist/skipi-chartering.js", "src-tauri/src/commands/chartering.rs", "tests/chartering_harness.mjs"]
OPTIONAL = ["dist/index.html", "dist/skipi-chartering.css", "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/app_login.rs",
            "src-tauri/src/commands/mod.rs", "src-tauri/src/commands/plugin_reviews.rs", "src-tauri/src/commands/vault.rs", "src-tauri/src/lib.rs",
            "tests/bundled_plugin_isolation_harness.mjs", "tests/role_modules_harness.mjs"]
NEW_FILES = ["dist/CHARTERING_VERSION", "dist/skipi-chartering.css", "dist/skipi-chartering.js", "src-tauri/src/commands/chartering.rs", "tests/chartering_harness.mjs"]


class SeafarerCharteringRouteTests(unittest.TestCase):
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

    def test_file_set_is_exactly_the_fourteen_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 14)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["when_all_files_in"]), sorted(CORE + OPTIONAL))
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(CORE))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "presence-manifest.json", "dist/plugin-host-ui.js", "dist/vessel-db.js", "dist/skipi-vessel.js", "src-tauri/src/commands/messaging.rs",
                      "tests/jobs_profile_visibility_harness.mjs", "src-tauri/src/commands/crewing_intake.rs", "src-tauri/src/commands/mail_intent.rs", "src-tauri/src/db.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_is_not_widened(self):
        for path in NEW_FILES:
            if path.startswith("src-tauri/") or path == "dist/CHARTERING_VERSION":
                self.assertFalse(self.allowed("plugin-host", path), path)

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_default_harnesses_and_its_own(self):
        names = [h["command"] for h in self.config["harness_commands"][TASK]]
        for h in self.config["harness_commands"]["plugin-host"]:
            self.assertIn(h["command"], names)
        self.assertIn("node tests/chartering_harness.mjs", names)
        self.assertIn("node tests/role_modules_harness.mjs", names)

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)


if __name__ == "__main__":
    unittest.main()
