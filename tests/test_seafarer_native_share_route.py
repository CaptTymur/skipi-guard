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

ROUTE_TASK = "native-share"
ROUTE_RULE = "seafarer native share routing (332)"
# Owner-authorized on 2026-09-06 (DECISIONS (332), owner words "маршрут на
# поделиться даю"), in the composition narrowed by the supervisor audit (329)
# and extended with the CV path by (331). Native "Share" cannot be built from
# dist/ alone: the system share sheet needs a Rust command (share_package /
# share_cv), the existing mail_intent bridge reused from inside Rust, its
# registration in lib.rs, and a NARROWED FileProvider path list. The route is
# literal — no glob — and deliberately does NOT include AndroidManifest.xml or
# MainActivity.kt (the bridge already ships; under a path gate these are the
# most dangerous files, defect 212b).
ROUTE_FILES = [
    "dist/index.html",
    "presence-manifest.json",
    "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml",
    "src-tauri/src/commands/mail_intent.rs",
    "src-tauri/src/commands/packages.rs",
    "src-tauri/src/lib.rs",
    "tests/bundled_plugin_isolation_harness.mjs",
]
# presence-manifest.json is inside the route (mobile_navigation entry, 215b)
# BUT it stays a protected path: the route changes routing, never the
# protected stop-line. See test_presence_manifest_inside_the_route_still_...
PROTECTED_ROUTE_FILE = "presence-manifest.json"
# The subset of the route that carries no protected path: this is what an
# ordinary slice push looks like.
ROUTE_FILES_UNPROTECTED = [path for path in ROUTE_FILES if path != PROTECTED_ROUTE_FILE]
# require_any_of: the route only opens for a diff that carries at least one
# platform file. A dist-only (or dist+lib.rs+harness) diff must stay on the
# default plugin-host task exactly as it does today — the route must not
# swallow it and must not turn "a button over an unfixed layer" into a green
# push.
ROUTE_PLATFORM_FILES = [
    "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml",
    "src-tauri/src/commands/packages.rs",
    "src-tauri/src/commands/mail_intent.rs",
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

MOBILE_IME_FILES = [
    "dist/index.html",
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
    "tests/bundled_plugin_isolation_harness.mjs",
]


class SeafarerNativeShareRouteTests(unittest.TestCase):
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
        *,
        override: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
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
        ]
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

    def verify_updates(
        self,
        updates: dict[str, str],
        *,
        prefix: str,
        override: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json", override=override)

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
        # src-tauri/gen/** is release-sensitive: file_paths.xml is authorized
        # because the task is a release task, not because it was silenced.
        self.assertEqual(payload["release_changes"], release_changes)
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    def test_unprotected_full_set_routes_to_native_share(self) -> None:
        # The whole owner-authorized set minus the protected presence manifest:
        # the slice as it can actually be pushed in one go.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES_UNPROTECTED),
            prefix="skipi-guard-seafarer-native-share-union6-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES_UNPROTECTED, release_changes=True)

    def test_platform_subsets_route(self) -> None:
        # Each platform file on its own (and the realistic Rust-side subset)
        # is inside when_all_files_in and carries a require_any_of file.
        for label, files in (
            ("file-paths-only", ["src-tauri/gen/android/app/src/main/res/xml/file_paths.xml"]),
            ("packages-only", ["src-tauri/src/commands/packages.rs"]),
            ("mail-intent-only", ["src-tauri/src/commands/mail_intent.rs"]),
            (
                "rust-and-dist",
                [
                    "src-tauri/src/commands/packages.rs",
                    "src-tauri/src/lib.rs",
                    "dist/index.html",
                    "tests/bundled_plugin_isolation_harness.mjs",
                ],
            ),
            (
                "share-and-mail-bridge",
                [
                    "src-tauri/src/commands/packages.rs",
                    "src-tauri/src/commands/mail_intent.rs",
                    "src-tauri/src/lib.rs",
                ],
            ),
        ):
            with self.subTest(case=label):
                release_changes = any(path.startswith("src-tauri/gen/") for path in files)
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-native-share-{label}-",
                )
                self.assert_routed_pass(payload, proc, files, release_changes=release_changes)

    def test_diff_without_platform_file_stays_on_default_plugin_host(self) -> None:
        # require_any_of is the point of this route: a dist-only (or
        # dist+lib.rs+harness) diff must NOT open the native-share route and
        # must keep the classification it has today (default plugin-host).
        # This is exactly the "button over an unfixed layer" case the
        # supervisor flagged (СТОП-A′): the UI half alone stays where it is.
        for label, files in (
            ("dist-and-harness", ["dist/index.html", "tests/bundled_plugin_isolation_harness.mjs"]),
            ("dist-only", ["dist/index.html"]),
            ("dist-lib-harness", ["dist/index.html", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"]),
            ("harness-only", ["tests/bundled_plugin_isolation_harness.mjs"]),
            ("lib-only", ["src-tauri/src/lib.rs"]),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-native-share-nonplatform-{label}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertEqual(payload["release_changes"], False)

    def test_candidate_plus_extra_file_does_not_route_and_stays_red(self) -> None:
        # when_all_files_in is the upper bound: any file outside the seven
        # falls through to the default plugin-host task and stays RED. In
        # particular the route does NOT open src-tauri/src/** wholesale, does
        # NOT open src-tauri/gen/** wholesale, does not reach
        # AndroidManifest.xml / MainActivity.kt (212b) and does not authorize
        # a version bump.
        for extra in (
            "src-tauri/src/cv.rs",
            "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
            "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
            "src-tauri/gen/android/app/build.gradle.kts",
            "src-tauri/gen/android/app/src/main/res/values/strings.xml",
            "src-tauri/Cargo.toml",
            "src-tauri/Cargo.lock",
            "src-tauri/tauri.conf.json",
            "src-tauri/src/commands/vault.rs",
            "src-tauri/src/commands/mod.rs",
            ".github/workflows/skipi-guard.yml",
            "src/unrelated.txt",
        ):
            with self.subTest(extra=extra):
                updates = self.candidate(ROUTE_FILES_UNPROTECTED)
                updates[extra] = "forbidden extra file\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-native-share-mixed-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_presence_manifest_inside_the_route_still_needs_override_protected(self) -> None:
        # FINDING, recorded as a test: putting presence-manifest.json inside
        # the route changes ROUTING only. The protected stop-line
        # ("presence contracts") is evaluated independently of the task, so a
        # diff that touches the manifest is still RED without
        # --override-protected. The route neither lifts nor weakens it.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-native-share-protected-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        # Routing DOES resolve to the route (that is what the path buys):
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_rule"], ROUTE_RULE)
        # ...and the only complaint is the protected stop-line, not scope.
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["errors"], ["protected path touch requires --override-protected"])
        self.assertIn(
            PROTECTED_ROUTE_FILE,
            [touch["path"] for touch in payload["protected_paths_touched"]],
        )

    def test_presence_override_token_still_refuses_a_mixed_share_diff(self) -> None:
        # The existing presence token is presence-only by policy: it does not
        # become a way to push the whole share slice. Nothing here widens it.
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-native-share-presence-token-",
            override="seafarer-presence-modification-approved",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertTrue(
            any("presence override requires presence-only changes" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_presence_manifest_alone_does_not_open_the_route(self) -> None:
        # A presence-only diff carries no require_any_of file, so it keeps its
        # current classification (plugin-host) and its current protected gate.
        proc, payload = self.verify_updates(
            self.candidate([PROTECTED_ROUTE_FILE]),
            prefix="skipi-guard-seafarer-native-share-presence-only-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["task"], "plugin-host")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["errors"], ["protected path touch requires --override-protected"])

    def test_route_is_literal_release_task_bounded_by_routing(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(len(routes[0]["when_all_files_in"]), 7)
        self.assertEqual(routes[0]["require_any_of"], ROUTE_PLATFORM_FILES)
        self.assertNotIn("require_all_of", routes[0])
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        # src-tauri/gen/** is release-sensitive -> the task must be a release
        # task or file_paths.xml is blocked. No exact_task_file_sets entry: a
        # packages.rs-only fix must still ride the route (exact sets are strict
        # on `missing`); the diff is bounded by when_all_files_in +
        # allowed_file_patterns instead (mirrors entry-fork-187 / ime).
        self.assertIn(ROUTE_TASK, config["release_tasks"])
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        self.assertEqual(len(harness_names), 10)
        for required in (
            "seafarer_bundled_plugin_isolation",
            "seafarer_build_provenance",
            "seafarer_presence_contract",
            "seafarer_theme_default",
            "seafarer_remote_prod_delivery_config",
            "seafarer_no_dead_tauri_invoke",
            "seafarer_stack_build_metadata",
            "seafarer_stack_verification_negative_control",
            "seafarer_login_gate_first_screen",
            "seafarer_demo_vault_contract",
        ):
            self.assertIn(required, harness_names)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        # The harness list is exactly the mobile-ime-inset one (DECISIONS (332)).
        self.assertEqual(
            config["harness_commands"][ROUTE_TASK],
            config["harness_commands"]["mobile-ime-inset"],
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
        # The two files the supervisor excluded (212b) are NOT in the route,
        # and no version file is opened by it.
        for excluded in (
            "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
            "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
            "src-tauri/Cargo.toml",
            "src-tauri/Cargo.lock",
            "src-tauri/tauri.conf.json",
        ):
            self.assertNotIn(excluded, ROUTE_FILES)
        # Exactly one file from src-tauri/gen/** is opened, and it is the
        # FileProvider path list (СТОП-A′), nothing else under gen/.
        gen_files = [path for path in ROUTE_FILES if path.startswith("src-tauri/gen/")]
        self.assertEqual(gen_files, ["src-tauri/gen/android/app/src/main/res/xml/file_paths.xml"])

    def test_route_does_not_weaken_protected_paths(self) -> None:
        config = self.load_config()

        presence_rules = [
            rule for rule in config["protected_paths"] if rule.get("name") == "presence contracts"
        ]
        self.assertEqual(len(presence_rules), 1)
        self.assertIn(PROTECTED_ROUTE_FILE, presence_rules[0]["patterns"])
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])
        # The route adds no protected-path exception and no override token.
        self.assertEqual(
            config["stop_lines"],
            [
                "no backend/server/prod data",
                "no catalog/latest/release/signing keys",
                "no app version/tag bump",
                "no Tauri/Cargo/mobile generated changes",
                "no pairing/QR/camera bridge changes",
                "no Play/TestFlight/upload/deploy",
            ],
        )

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
            "mobile-ime-inset": (
                "seafarer mobile IME inset fix routing (308)",
                self.candidate(MOBILE_IME_FILES),
            ),
            "version-bump": (
                "seafarer canonical version bump routing (204)",
                self.candidate(
                    [
                        "dist/index.html",
                        "src-tauri/Cargo.lock",
                        "src-tauri/Cargo.toml",
                        "src-tauri/tauri.conf.json",
                        "tests/stack_build_metadata_harness.mjs",
                    ]
                ),
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
                    prefix=f"skipi-guard-seafarer-native-share-neighbour-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
