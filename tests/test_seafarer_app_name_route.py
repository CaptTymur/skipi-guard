"""Seafarer route `app-name-skipi`: the app is called just «Skipi», not «Skipi Seafarer».

Owner 26.11.2026: «давай убедимся что следующие выпуски приложения будут просто Skipi а не Skipi Seafarer»
(the product rule of the same day: one app Skipi — web, desktop, mobile; the profile type decides the content).

The change in the home touches eleven named files: the visible name in dist/index.html, the bundle name
and window title in tauri.conf.json (productName, plus deb Conflicts/Replaces and rpm Obsoletes of the old
package `skipi-seafarer`, plus the NSIS hook that removes the old «Skipi Seafarer» install on Windows),
Cargo.toml's description, the Android launcher label (values + values-ru), the iOS display name and usage
strings (Info.plist), the asset-stem fallback in vault.rs, and the three harnesses that pin those strings.
The route:
  * exactly eleven named files, no wildcard, all of them required (require_all_of = the whole set), so a
    plain version bump or any other subset never lands here;
  * a release task (it carries src-tauri/gen/** and tauri.conf.json), like plugin-motion-019 and
    plugin-capabilities-020; no exact set — an exact set would turn the two extra harness scripts into
    version pins for every other door;
  * it runs the stack-metadata tier (including the version pin) plus jobs_profile_visibility;
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
LOADER = SourceFileLoader("guard_app_name", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "app-name-skipi"
LATER = ("my-vessel-029",)  # 27.11.2026, oracle in tests/test_seafarer_my_vessel_route.py
FILES = [
    "dist/index.html",
    "src-tauri/Cargo.toml",
    "src-tauri/gen/android/app/src/main/res/values-ru/strings.xml",
    "src-tauri/gen/android/app/src/main/res/values/strings.xml",
    "src-tauri/gen/apple/skipi_iOS/Info.plist",
    "src-tauri/src/commands/vault.rs",
    "src-tauri/tauri.conf.json",
    "src-tauri/windows/hooks.nsh",
    "tests/bundled_plugin_isolation_harness.mjs",
    "tests/jobs_profile_visibility_harness.mjs",
    "tests/stack_build_metadata_harness.mjs",
]


class SeafarerAppNameRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        self.assertEqual(MODULE.resolve_task(self.config, FILES)["task"], TASK)
        self.assertTrue(all(self.allowed(TASK, f) for f in FILES))

    def test_any_subset_is_not_routed(self):
        for missing in FILES:
            diff = [f for f in FILES if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)
        bump = ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json",
                "tests/stack_build_metadata_harness.mjs", "src-tauri/gen/apple/skipi_iOS/Info.plist"]
        self.assertNotEqual(MODULE.resolve_task(self.config, bump)["task"], TASK)

    def test_file_set_is_exactly_the_eleven_files_without_wildcards(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(FILES))
        self.assertEqual(len(FILES), 11)
        routing = [r for r in self.config["task_routing"] if r["task"] == TASK]
        self.assertEqual(len(routing), 1)
        self.assertEqual(sorted(routing[0]["when_all_files_in"]), sorted(FILES))
        self.assertEqual(sorted(routing[0]["require_all_of"]), sorted(FILES))
        for pattern in self.config["allowed_file_patterns"][TASK] + routing[0]["when_all_files_in"]:
            self.assertFalse(any(ch in pattern for ch in "*?["), pattern)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.lock", ".github/workflows/skipi-guard.yml", ".github/workflows/release.yml",
                      "presence-manifest.json", "src-tauri/gen/apple/project.yml",
                      "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
                      "src-tauri/src/commands/account_sync.rs", "src-tauri/src/db.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, FILES + [extra])["task"], TASK, extra)

    def test_default_task_is_not_widened(self):
        for path in FILES:
            if path.startswith("src-tauri/"):
                self.assertFalse(self.allowed("plugin-host", path), path)

    def test_release_task_without_exact_set(self):
        self.assertEqual(self.config["release_tasks"].count(TASK), 1)
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))

    def test_runs_the_stack_tier_with_the_version_pin_and_jobs(self):
        names = [h["command"] for h in MODULE.configured_harnesses(self.config, TASK)]
        for command in ("node tests/stack_build_metadata_harness.mjs",
                        "node tests/stack_verification_negative_control_harness.mjs",
                        "node tests/bundled_plugin_isolation_harness.mjs",
                        "node tests/jobs_profile_visibility_harness.mjs"):
            self.assertIn(command, names)
        self.assertEqual([], MODULE.unpinned_version_moves(self.config, FILES, MODULE.configured_harnesses(self.config, TASK)))

    def test_appended_last(self):
        self.assertEqual([r["task"] for r in self.config["task_routing"] if r["task"] not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["allowed_file_patterns"] if t not in LATER][-1], TASK)
        self.assertEqual([t for t in self.config["harness_commands"] if t not in LATER][-1], TASK)
        self.assertEqual(self.config["release_tasks"][-1], TASK)


if __name__ == "__main__":
    unittest.main()
