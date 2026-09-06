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
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

ROUTE_TASK = "mobile-ime-inset"
ROUTE_RULE = "seafarer mobile IME inset fix routing (308)"
# Owner-authorized on 2026-09-06 (DECISIONS (309), owner words "маршрут на
# андройд и на бамп даю"): the "keyboard covers the composer" defect (308) is
# NOT fixable from dist/ — the WebView window runs with the Android default
# softInputMode=adjustPan, so the fix has to land in the checked-in (not
# regenerated) Android sources: the manifest attribute and/or the ime()
# WindowInsets listener in MainActivity. dist/index.html carries the feed
# scroll-on-focus half, the isolation harness carries the drill.
ROUTE_FILES = [
    "dist/index.html",
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
    "tests/bundled_plugin_isolation_harness.mjs",
]
# require_any_of: the route only opens for a diff that carries at least one
# platform file. A dist-only (or dist+harness) diff must stay on the default
# plugin-host task exactly as it does today — the route must not swallow it.
ROUTE_PLATFORM_FILES = [
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
]
ROUTE_HARNESSES = [
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
    {"name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs"},
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
    {"name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs"},
    {"name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs"},
]

ENTRY_FORK_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "tests/bundled_plugin_isolation_harness.mjs",
    "tests/login_gate_first_screen_harness.mjs",
    "tests/stack_build_metadata_harness.mjs",
]


class SeafarerMobileImeRouteTests(unittest.TestCase):
    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
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
        self.commit_files(repo, "seed fixture", {"fixture.txt": "seed\n"})

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "seafarer",
                "--auto-task",
                "--repo",
                str(repo),
                "--base",
                "HEAD~1",
                "--head",
                "HEAD",
                "--json",
                str(result_json),
            ],
            text=True,
            capture_output=True,
            env=self.child_env(),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def verify_updates(
        self,
        updates: dict[str, str],
        *,
        prefix: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json")

    def candidate(self, files: list[str]) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in files}

    def load_config(self) -> dict[str, Any]:
        with CONFIG.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_routed_pass(
        self,
        payload: dict[str, Any],
        proc: subprocess.CompletedProcess[str],
        files: list[str],
        *,
        release_changes: bool,
    ) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(files))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        # src-tauri/gen/** is release-sensitive: the Android sources are
        # authorized because the task is a release task, not silenced.
        self.assertEqual(payload["release_changes"], release_changes)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_full_set_of_4_routes_to_mobile_ime(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-mobile-ime-union4-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES, release_changes=True)

    def test_platform_only_diffs_route(self) -> None:
        # The fix may be manifest-only (adjustResize) or MainActivity-only
        # (ime() insets listener on Android 15+), or both: each is inside
        # when_all_files_in and carries a require_any_of file.
        for label, files in (
            ("manifest-only", [ROUTE_PLATFORM_FILES[0]]),
            ("activity-only", [ROUTE_PLATFORM_FILES[1]]),
            ("both-platform", ROUTE_PLATFORM_FILES),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-mobile-ime-{label}-",
                )
                self.assert_routed_pass(payload, proc, files, release_changes=True)

    def test_diff_without_platform_file_stays_on_default_plugin_host(self) -> None:
        # require_any_of is the point of this route: without a platform file it
        # must NOT open, and the dist-side diff keeps the classification it has
        # today (default plugin-host), not a silently widened Android route.
        for label, files in (
            ("dist-and-harness", ["dist/index.html", "tests/bundled_plugin_isolation_harness.mjs"]),
            ("dist-only", ["dist/index.html"]),
            ("harness-only", ["tests/bundled_plugin_isolation_harness.mjs"]),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-mobile-ime-nonplatform-{label}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertEqual(payload["release_changes"], False)

    def test_candidate_plus_extra_file_does_not_route_and_stays_red(self) -> None:
        # when_all_files_in is the upper bound: any 5th file falls through to
        # the default plugin-host task and stays RED. In particular the route
        # does NOT open src-tauri/gen/** wholesale (build.gradle.kts, the
        # generated Rust glue) and does not authorize a version bump.
        for extra in (
            "src-tauri/gen/android/app/build.gradle.kts",
            "src-tauri/gen/android/app/src/main/res/values/strings.xml",
            "src-tauri/Cargo.toml",
            "src-tauri/tauri.conf.json",
            "src-tauri/src/lib.rs",
            "src-tauri/src/commands/vault.rs",
            ".github/workflows/skipi-guard.yml",
            "src/unrelated.txt",
        ):
            with self.subTest(extra=extra):
                updates = self.candidate(ROUTE_FILES)
                updates[extra] = "forbidden extra file\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-mobile-ime-mixed-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_protected_path_still_blocks_inside_the_route(self) -> None:
        # presence-manifest.json is a protected path; the route does not and
        # must not lift --override-protected.
        updates = self.candidate(ROUTE_FILES)
        updates["presence-manifest.json"] = "{}\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-seafarer-mobile-ime-protected-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(
            any("protected path touch requires" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_route_is_literal_release_task_bounded_by_routing(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(routes[0]["require_any_of"], ROUTE_PLATFORM_FILES)
        self.assertNotIn("require_all_of", routes[0])
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        # src-tauri/gen/** is release-sensitive -> the task must be a release
        # task or the touch is blocked. No exact_task_file_sets entry: a
        # manifest-only fix must still ride the route (exact sets are strict on
        # `missing`); the diff is bounded by when_all_files_in +
        # allowed_file_patterns instead (mirrors entry-fork-187).
        self.assertIn(ROUTE_TASK, config["release_tasks"])
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        for required in (
            "seafarer_no_dead_tauri_invoke",
            "seafarer_stack_build_metadata",
            "seafarer_stack_verification_negative_control",
            "seafarer_build_provenance",
            "seafarer_login_gate_first_screen",
            "seafarer_demo_vault_contract",
        ):
            self.assertIn(required, harness_names)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        # The harness list is exactly the entry-fork-187 one (DECISIONS (309)).
        self.assertEqual(
            config["harness_commands"][ROUTE_TASK],
            config["harness_commands"]["entry-fork-187"],
        )
        # Every harness this route runs is the same (name, command) pair an
        # existing task already owns: nothing is redefined here.
        owned_elsewhere = {
            (entry["name"], entry["command"])
            for task, entries in config["harness_commands"].items()
            if task != ROUTE_TASK
            for entry in entries
        }
        for entry in config["harness_commands"][ROUTE_TASK]:
            self.assertIn((entry["name"], entry["command"]), owned_elsewhere)
        # Literal paths only: no glob may widen this route.
        for pattern in (
            routes[0]["when_all_files_in"]
            + routes[0]["require_any_of"]
            + config["allowed_file_patterns"][ROUTE_TASK]
        ):
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
        for platform in ROUTE_PLATFORM_FILES:
            self.assertIn(platform, ROUTE_FILES)
        # No Rust source and no version file is opened by this route: the IME
        # fix is manifest/Kotlin/dist only, the bump rides version-bump.
        for pattern in ROUTE_FILES:
            self.assertFalse(pattern.endswith(".rs"), pattern)
        for version_file in ("src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"):
            self.assertNotIn(version_file, ROUTE_FILES)

    def test_route_does_not_shadow_neighbour_routes(self) -> None:
        existing_routes = {
            "mobile-external-url": (
                "mobile external-url fix routing",
                {
                    "src-tauri/src/commands/vault.rs": "fixture vault\n",
                    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt": "fixture activity\n",
                },
            ),
            "assistant-nonblocking": (
                "assistant non-blocking fix routing (140)",
                {
                    "src-tauri/src/commands/assistant.rs": "fixture assistant\n",
                    "tests/no_dead_tauri_invoke_harness.mjs": "fixture harness\n",
                },
            ),
            "entry-fork-187": (
                "seafarer mobile entry fork + 0.4.187 bump routing (187)",
                self.candidate(ENTRY_FORK_FILES),
            ),
            "release": (
                "canonical version-bump routing",
                {
                    "dist/index.html": "fixture dist\n",
                    "src-tauri/Cargo.lock": "fixture lock\n",
                    "src-tauri/Cargo.toml": "fixture toml\n",
                    "src-tauri/tauri.conf.json": "fixture conf\n",
                },
            ),
            "repo-meta": (
                "repo-meta routing",
                {"AGENTS.md": "fixture agents\n", "CLAUDE.md": "fixture claude\n"},
            ),
        }
        for expected_task, (expected_rule, updates) in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    updates,
                    prefix=f"skipi-guard-seafarer-mobile-ime-neighbour-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
