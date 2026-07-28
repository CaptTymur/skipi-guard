from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG_PATH = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

# Literal file set of the seafarer Android-Back wave fix
# (worktree seafarer-back-fix-20260728 @ 78ca4448, diff vs seafarer main
# d4b8fd20): the unified-settings overlay fix touches only the host page and
# its fallback harness, without any dist/skipi-settings* byte change.
BACK_FIX_SET = [
    "dist/index.html",
    "tests/unified_settings_fallback_harness.mjs",
]


class SeafarerSettingsAdoptRouteTests(unittest.TestCase):
    """Defect Д2 of the settings-wave 5x2: the settings-adopt route only
    triggered on dist/skipi-settings*, so a legitimate two-file wave fix
    {dist/index.html + tests/unified_settings_fallback_harness.mjs} fell into
    plugin-host and failed scope on the harness file (live repro 78ca4448).
    The fix extends require_any_of with the harness file; the allowed scope of
    the task is unchanged."""

    def child_env(self, *, override_env: str | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
        if override_env is not None:
            env[OVERRIDE_ENV] = override_env
        return env

    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
            env=self.child_env(),
        )

    def commit_files(self, repo: Path, message: str, updates: dict[str, str]) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        self.commit_files(
            repo,
            "seed seafarer home",
            {
                "dist/index.html": '<meta name="app-version" content="0.4.178">\n',
                "dist/skipi-settings.js": "export const settings = 'unified';\n",
                "tests/unified_settings_fallback_harness.mjs": "console.log('ok');\n",
                "presence-manifest.json": '{"contracts":[]}\n',
            },
        )

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        task: str | None = None,
        auto_task: bool = False,
        override: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "seafarer",
            "--repo",
            str(repo),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
            "--json",
            str(result_json),
        ]
        if auto_task:
            command.append("--auto-task")
        elif task:
            command.extend(["--task", task])
        else:
            raise ValueError("task or auto_task is required")
        if override:
            command.extend(["--override-protected", override])
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            env=self.child_env(),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def back_fix_change(self) -> dict[str, str]:
        return {
            "dist/index.html": '<meta name="app-version" content="0.4.178"> <!-- back fix -->\n',
            "tests/unified_settings_fallback_harness.mjs": "console.log('back fix');\n",
        }

    # --- Д2 fix -------------------------------------------------------------

    def test_back_fix_two_file_diff_routes_to_settings_adopt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-back-fix-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "android back closes settings overlay", self.back_fix_change())

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "settings-adopt")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "settings-adopt routing")
        self.assertEqual(payload["changed_files"], sorted(BACK_FIX_SET))
        self.assertEqual(payload["scope_violations"], [])
        self.assertFalse(payload["release_changes"])
        harnesses = {entry["name"]: entry["command"] for entry in payload["tests"]}
        self.assertEqual(
            harnesses["seafarer_unified_settings_fallback"],
            "node tests/unified_settings_fallback_harness.mjs",
        )

    def test_settings_bundle_trigger_still_routes_to_settings_adopt(self) -> None:
        """Regression control: the original dist/skipi-settings* trigger keeps
        working after the require_any_of extension."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-settings-bundle-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "settings bundle update",
                {
                    "dist/index.html": "<main>settings</main>\n",
                    "dist/skipi-settings.js": "export const settings = 'unified-2';\n",
                },
            )

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "settings-adopt")
        self.assertEqual(payload["task_rule"], "settings-adopt routing")
        self.assertEqual(payload["scope_violations"], [])

    # --- negative controls ---------------------------------------------------

    def test_index_plus_unrelated_file_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-unrelated-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "index plus unrelated source",
                {
                    "dist/index.html": "<main>changed</main>\n",
                    "src/unreviewed.js": "console.log('must stay blocked');\n",
                },
            )

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIn("src/unreviewed.js", payload["scope_violations"])
        self.assertIn("changes outside allowed patterns for task 'plugin-host'", payload["errors"])

    def test_index_only_diff_stays_plugin_host(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-index-only-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "host change", {"dist/index.html": "<main>changed</main>\n"})

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertEqual(payload["scope_violations"], [])

    def test_settings_adopt_task_cannot_touch_presence_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-seafarer-settings-presence-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(
                repo,
                "change protected presence contract",
                {"presence-manifest.json": '{"contracts":["changed"]}\n'},
            )

            proc, payload = self.run_guard(repo, root / "result.json", task="settings-adopt")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("protected path touch requires --override-protected", payload["errors"])

    # --- config contracts -----------------------------------------------------

    def test_settings_adopt_allowed_scope_is_unchanged(self) -> None:
        """Д2 changes the routing trigger only; the allowed file scope of the
        settings-adopt task must stay exactly as accepted before the fix."""
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(
            config["allowed_file_patterns"]["settings-adopt"],
            [
                "dist/index.html",
                "dist/skipi-settings*",
                "dist/SETTINGS_VERSION",
                "tests/unified_settings_fallback_harness.mjs",
            ],
        )

    def test_settings_adopt_trigger_includes_bundle_and_fallback_harness(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        rules = {rule["name"]: rule for rule in config["task_routing"]}
        self.assertEqual(
            rules["settings-adopt routing"]["require_any_of"],
            ["dist/skipi-settings*", "tests/unified_settings_fallback_harness.mjs"],
        )


if __name__ == "__main__":
    unittest.main()
