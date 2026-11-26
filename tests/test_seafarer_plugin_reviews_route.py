"""Seafarer route `plugin-reviews-021`: ratings and reviews of plugins in Apps.

Owner 25.11.2026: «давай помимо этого добавим в новый выпуск возможность публиковать отзывы на
плагины и давать оценку»; «текст можно не модерировать, публиковать сразу».

The change in the home touches six named files; the one new file is
`src-tauri/src/commands/plugin_reviews.rs` (the native commands that hold the account token so the
page never does). The route is deliberately narrow:
  * exactly six files, no wildcard;
  * the commands never move without the Apps module and its harness (require_all_of);
  * not a release task: nothing under `src-tauri/gen/**`, no version-bearing file;
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
LOADER = SourceFileLoader("guard_plugin_reviews", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "plugin-reviews-021"
CORE = ["dist/plugin-host-ui.js", "src-tauri/src/commands/plugin_reviews.rs", "tests/bundled_plugin_isolation_harness.mjs"]
OPTIONAL = ["dist/index.html", "src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs"]


class SeafarerPluginReviewsRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE + OPTIONAL, CORE, CORE + OPTIONAL[:1], CORE + OPTIONAL[1:]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_file_set_is_exactly_the_six_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 6)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(CORE))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "presence-manifest.json", "dist/plugin-loader.js", "dist/plugin-remote-boot.js",
                      "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
                      "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/app_login.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_is_not_widened_and_keeps_its_diffs(self):
        self.assertFalse(self.allowed("plugin-host", "src-tauri/src/commands/plugin_reviews.rs"))
        host_only = ["dist/index.html", "dist/plugin-host-ui.js", "tests/bundled_plugin_isolation_harness.mjs"]
        self.assertNotEqual(MODULE.resolve_task(self.config, host_only)["task"], TASK)

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_apps_harnesses_and_the_invoke_check(self):
        commands = [h["command"] for h in self.config["harness_commands"][TASK]]
        for needed in ("node tests/bundled_plugin_isolation_harness.mjs", "node tests/plugin_remote_over_bundled_harness.mjs",
                       "node tests/no_dead_tauri_invoke_harness.mjs"):
            self.assertIn(needed, commands)

    def test_appended_last(self):
        self.assertEqual(self.config["task_routing"][-1]["task"], TASK)
        self.assertEqual(list(self.config["allowed_file_patterns"])[-1], TASK)
        self.assertEqual(list(self.config["harness_commands"])[-1], TASK)


if __name__ == "__main__":
    unittest.main()
