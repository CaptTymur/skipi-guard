"""Seafarer route `plugins-unbundle`: the home ships no bundled plugins.

Owner word 24.11.2026 («сменим архитектуру — у нас вообще не будет встроенных плагинов»,
and, asked about the guard rule for dist/plugins: «Разрешаю оба»). Until this route no
Seafarer task listed `dist/plugins/**`, so a diff that removes the bundled artifacts fell to
the default task `plugin-host` and was refused as out of scope.

The route is deliberately narrow:
  * it is the `plugin-host` file set plus `dist/plugins/**` and the test fixture folder the
    isolation harness now reads its plugin bytes from (`tests/fixtures/plugins/**`);
  * `dist/plugins/**` never moves alone: the diff must also carry `dist/index.html` (the
    registry of bundled plugins) and `tests/bundled_plugin_isolation_harness.mjs`;
  * the default task `plugin-host` is NOT widened — a bundled artifact changed without the
    registry and the harness is still out of scope;
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
LOADER = SourceFileLoader("guard_plugins_unbundle", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "plugins-unbundle"
CORE = ["dist/index.html", "tests/bundled_plugin_isolation_harness.mjs"]
BUNDLE = ["dist/plugins/bnwas-time-anchor/index.js", "dist/plugins/ecdis-position-reminder/plugin.json"]


class SeafarerPluginsUnbundleRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        diff = CORE + BUNDLE + [
            "dist/plugin-host-config.js", "dist/plugin-host-ui.js", "dist/plugin-remote-boot.js",
            "tests/remote_prod_delivery_config_harness.mjs",
            "tests/fixtures/plugins/bnwas-time-anchor/index.js",
        ]
        self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK)
        self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_bundle_alone_or_without_registry_or_harness_is_not_routed(self):
        for diff in (BUNDLE, BUNDLE + CORE[:1], BUNDLE + CORE[1:]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], "plugin-host", diff)

    def test_registry_and_harness_without_a_bundle_change_stay_on_the_default_task(self):
        self.assertEqual(MODULE.resolve_task(self.config, CORE)["task"], "plugin-host")

    def test_default_task_is_not_widened(self):
        for f in BUNDLE + ["tests/fixtures/plugins/bnwas-time-anchor/index.js"]:
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "contracts/test.json", "src-tauri/src/cv.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + BUNDLE + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_file_set_is_plugin_host_plus_two_folders(self):
        self.assertEqual(
            self.config["allowed_file_patterns"][TASK],
            self.config["allowed_file_patterns"]["plugin-host"] + ["dist/plugins/**", "tests/fixtures/plugins/**"],
        )

    def test_runs_the_plugin_host_harnesses(self):
        self.assertEqual(self.config["harness_commands"][TASK], self.config["harness_commands"]["plugin-host"])

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))


if __name__ == "__main__":
    unittest.main()
