"""Seafarer route `plugin-capabilities-020`: plugins get the camera, the microphone, the location,
speech and vibration through the host.

Owner 25.11.2026: «давай расширим набор возможностей заранее одним выпуском» — so that a new plugin
needs no new app build (the next BNWAS is to use the camera to see whether a person is present);
camera, voice, vibration, location and microphone were named.

The change in the home touches twelve named files. Three sit under the release-sensitive
`src-tauri/gen/**`: `AndroidManifest.xml` (the permissions), `MainActivity.kt` (text-to-speech) and
`Info.plist` (the iOS usage strings) — so the task is a release task, like `plugin-motion-019`.

The route is deliberately narrow:
  * exactly twelve files, no wildcard; no version-bearing file, no other path under `src-tauri/gen/**`;
  * the native commands never move without the boot glue and its harness (require_all_of);
  * no existing route is widened, and `plugin-motion-019` keeps its own diffs.
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
LOADER = SourceFileLoader("guard_plugin_capabilities", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "plugin-capabilities-020"
LATER = ("plugin-reviews-021", "empty-slots-212")  # 25.11.2026, oracle in tests/test_seafarer_plugin_reviews_route.py
CORE = ["dist/plugin-remote-boot.js", "src-tauri/src/commands/plugin_device.rs", "tests/remote_prod_delivery_config_harness.mjs"]
MANIFEST = "src-tauri/gen/android/app/src/main/AndroidManifest.xml"
ACTIVITY = "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"
PLIST = "src-tauri/gen/apple/skipi_iOS/Info.plist"
OPTIONAL = ["dist/plugin-host-bridge.js", "dist/plugin-host-config.js", "src-tauri/src/commands/motion.rs",
            "src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs", MANIFEST, ACTIVITY, PLIST,
            "tests/bundled_plugin_isolation_harness.mjs"]


class SeafarerPluginCapabilitiesRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE + OPTIONAL, CORE, CORE + [MANIFEST, ACTIVITY], CORE + OPTIONAL[:5]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_file_set_is_exactly_the_twelve_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))
        self.assertEqual(len(CORE + OPTIONAL), 12)
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
                      "src-tauri/gen/android/app/build.gradle.kts",
                      "src-tauri/gen/apple/skipi.xcodeproj/project.pbxproj",
                      "src-tauri/src/commands/vault.rs", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_default_task_and_the_motion_route_are_not_widened(self):
        for f in ("src-tauri/src/commands/plugin_device.rs", MANIFEST, ACTIVITY, PLIST):
            self.assertFalse(self.allowed("plugin-host", f), f)
        for f in ("src-tauri/src/commands/plugin_device.rs", MANIFEST):
            self.assertFalse(self.allowed("plugin-motion-019", f), f)
        motion = ["dist/plugin-remote-boot.js", "src-tauri/src/commands/motion.rs", "tests/remote_prod_delivery_config_harness.mjs", ACTIVITY]
        self.assertEqual(MODULE.resolve_task(self.config, motion)["task"], "plugin-motion-019")

    def test_release_task_and_no_exact_set(self):
        self.assertEqual(self.config["release_tasks"].count(TASK), 1)
        self.assertEqual(self.config["release_tasks"][-1], TASK)
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_plugin_host_harnesses_and_the_invoke_check(self):
        commands = [h["command"] for h in self.config["harness_commands"][TASK]]
        for needed in ("node tests/bundled_plugin_isolation_harness.mjs", "node tests/remote_prod_delivery_config_harness.mjs",
                       "node tests/no_dead_tauri_invoke_harness.mjs"):
            self.assertIn(needed, commands)

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)


if __name__ == "__main__":
    unittest.main()
