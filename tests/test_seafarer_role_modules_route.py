"""Seafarer route `role-modules-018`: one app, modules by account role.

Owner word 25.11.2026 (case 208: «Приложение теперь будет одно — Skipi… какими модулями оно
будет заполнено — зависит от роли аккаунта»; asked about the guard route for this change:
«да разрешаю новый маршрут»). The change lets crewing / broker accounts sign in to the one
app: the sign-in (`app_login.rs`) keeps the account role, the role cache is created empty
(`vault.rs`), the frontend shows the role's modules (`dist/index.html`), and
`account_sync.rs` carries the test fixtures of the sign-in struct. No existing route holds
that file set, so the diff fell to the default task `plugin-host` and was refused.

The route is deliberately narrow:
  * exactly these four files plus the change's own harness `tests/role_modules_harness.mjs`;
  * the sign-in never moves without the frontend and the harness (require_all_of);
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
LOADER = SourceFileLoader("guard_role_modules", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "role-modules-018"
CORE = ["dist/index.html", "src-tauri/src/commands/app_login.rs", "tests/role_modules_harness.mjs"]
OPTIONAL = ["src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/vault.rs"]


class SeafarerRoleModulesRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text())

    def allowed(self, task, path):
        return any(MODULE.pattern_matches(path, p) for p in self.config["allowed_file_patterns"][task])

    def test_full_change_routes_to_the_task(self):
        for diff in (CORE, CORE + OPTIONAL, CORE + OPTIONAL[:1], CORE + OPTIONAL[1:]):
            self.assertEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, diff)
            self.assertTrue(all(self.allowed(TASK, f) for f in diff))

    def test_a_missing_core_file_is_not_routed(self):
        for missing in CORE:
            diff = [f for f in CORE + OPTIONAL if f != missing]
            self.assertNotEqual(MODULE.resolve_task(self.config, diff)["task"], TASK, missing)

    def test_default_task_is_not_widened(self):
        for f in ("src-tauri/src/commands/app_login.rs", "src-tauri/src/commands/vault.rs", "tests/role_modules_harness.mjs"):
            self.assertFalse(self.allowed("plugin-host", f), f)

    def test_foreign_file_breaks_the_route(self):
        for extra in ("src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", ".github/workflows/skipi-guard.yml",
                      "contracts/test.json", "src-tauri/src/lib.rs", "src-tauri/src/commands/documents.rs"):
            self.assertNotEqual(MODULE.resolve_task(self.config, CORE + OPTIONAL + [extra])["task"], TASK, extra)
            self.assertFalse(self.allowed(TASK, extra), extra)

    def test_file_set_is_exactly_the_five_files(self):
        self.assertEqual(sorted(self.config["allowed_file_patterns"][TASK]), sorted(CORE + OPTIONAL))

    def test_runs_the_plugin_host_harnesses_plus_login_gate_and_its_own(self):
        self.assertEqual(
            self.config["harness_commands"][TASK],
            self.config["harness_commands"]["plugin-host"] + [
                {"name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs"},
                {"name": "seafarer_role_modules", "command": "node tests/role_modules_harness.mjs"},
            ],
        )

    def test_not_a_release_task_and_no_exact_set(self):
        self.assertNotIn(TASK, self.config.get("release_tasks", []))
        self.assertNotIn(TASK, self.config.get("exact_task_file_sets", {}))


if __name__ == "__main__":
    unittest.main()
