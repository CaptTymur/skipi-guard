"""Seafarer route `plugin-motion-019`: plugins get motion sensors and keep-awake through the host.

Owner 25.11.2026 (marine-clinometer #2): the Clinometer is to run as a Skipi plugin on the phone's
sensors. The plugin frame is isolated and cannot read sensors, so the home serves them: host-runtime
1.2 (`dist/plugin-host-bridge.js`), native commands (`src-tauri/src/commands/motion.rs`), the Android
side in `MainActivity.kt`, and the iOS usage string in `Info.plist`.

The route is deliberately narrow:
  * exactly ten named files, no wildcard;
  * the native commands never move without the boot glue and its harness (require_all_of);
  * `MainActivity.kt` and `Info.plist` sit under the release-sensitive `src-tauri/gen/**`, so the task
    is a release task — the same way `mobile-ime-inset` carries `MainActivity.kt`; it admits no other
    file under `src-tauri/gen/**` and no version-bearing file;
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
LOADER = SourceFileLoader("guard_plugin_motion", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "plugin-motion-019"
LATER = ("plugin-capabilities-020", "plugin-reviews-021")  # 25.11.2026, oracles in tests/test_seafarer_plugin_capabilities_route.py and test_seafarer_plugin_reviews_route.py
CORE = ["dist/plugin-remote-boot.js", "src-tauri/src/commands/motion.rs", "tests/remote_prod_delivery_config_harness.mjs"]
ANDROID = "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"
PLIST = "src-tauri/gen/apple/skipi_iOS/Info.plist"
OPTIONAL = ["dist/plugin-host-bridge.js", "dist/plugin-host-config.js", "src-tauri/src/commands/mod.rs",
            "src-tauri/src/lib.rs", ANDROID, PLIST, "tests/bundled_plugin_isolation_harness.mjs"]


class SeafarerPluginMotionRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE + OPTIONAL, CORE, CORE + OPTIONAL[:4], CORE + [ANDROID]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_file_set_is_exactly_the_ten_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 10)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["when_all_files_in"]), sorted(CORE + OPTIONAL))
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(CORE))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json",
                      "dist/index.html", "dist/plugin-loader.js", "dist/plugin-host-ui.js",
                      ".github/workflows/skipi-guard.yml", "presence-manifest.json",
                      "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
                      "src-tauri/gen/android/app/build.gradle.kts",
                      "src-tauri/gen/apple/skipi.xcodeproj/project.pbxproj",
                      "src-tauri/src/commands/vault.rs", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_is_not_widened(self):
        for f in ("src-tauri/src/commands/motion.rs", ANDROID, PLIST):
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_release_task_because_of_the_generated_mobile_sources_and_no_exact_set(self):
        self.assertEqual(self.config["release_tasks"].count(TASK), 1)
        # later release tasks are appended after it (plugin-capabilities-020)
        self.assertEqual([t for t in self.config["release_tasks"] if t not in LATER][-1], TASK)
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_neighbour_routes_keep_their_diffs(self):
        ime = ["dist/index.html", ANDROID, "tests/bundled_plugin_isolation_harness.mjs"]
        self.assertEqual(MODULE.resolve_task(self.config, ime)["task"], "mobile-ime-inset")
        host_only = ["dist/plugin-host-bridge.js", "dist/plugin-remote-boot.js", "tests/bundled_plugin_isolation_harness.mjs"]
        self.assertNotEqual(MODULE.resolve_task(self.config, host_only)["task"], TASK)

    def test_runs_the_plugin_host_harnesses_and_the_invoke_check(self):
        commands = [h["command"] for h in self.config["harness_commands"][TASK]]
        for needed in ("node tests/bundled_plugin_isolation_harness.mjs", "node tests/remote_prod_delivery_config_harness.mjs",
                       "node tests/no_dead_tauri_invoke_harness.mjs", "node tests/seafarer_presence_contract_harness.mjs"):
            self.assertIn(needed, commands)

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)


if __name__ == "__main__":
    unittest.main()
