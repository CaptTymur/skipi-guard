from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

GUARD_LOADER = SourceFileLoader("skipi_guard_cli_189", str(GUARD))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
if GUARD_SPEC is None:
    raise RuntimeError(f"cannot load guard module from {GUARD}")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_LOADER.exec_module(GUARD_MODULE)

ROUTE_TASK = "mobile-189-native"
ROUTE_RULE = "seafarer 0.4.189 mobile native routing"
# Owner word 2026-09-06: "я даю тебе разрешение найти маршрут и исполнить что
# нужно". One literal, glob-free route for the native half of 0.4.189, in the
# composition fixed by the manager. The three defects behind it cannot be
# fixed from dist/ alone:
#   * src-tauri/src/commands/vault.rs        external links dead on iOS (№205)
#   * src-tauri/src/feedback.rs              telemetry DB path (№220b); note
#                                            it lives in src/, NOT in commands/
#   * src-tauri/src/commands/account_delete.rs  NEW file, account deletion
#                                            required by Apple 5.1.1(v)
# plus their registration in lib.rs and the two front-end surfaces they need
# (dist/intelligence.js — the mute "source" link on iOS, №221b; dist/index.html
# — the delete-account confirmation screen) and the drill harness.
ROUTE_FILES = [
    "dist/index.html",
    "dist/intelligence.js",
    "src-tauri/src/commands/account_delete.rs",
    "src-tauri/src/commands/vault.rs",
    "src-tauri/src/feedback.rs",
    "src-tauri/src/lib.rs",
    "tests/bundled_plugin_isolation_harness.mjs",
]
# require_any_of: the route only opens for a diff that carries at least one of
# the three Rust files. A dist-only diff must NOT ride this route — dist edits
# have entry-fork-187 (and the default plugin-host) already, and a route that
# swallowed them would let a screen land over an unimplemented native layer.
ROUTE_RUST_FILES = [
    "src-tauri/src/commands/vault.rs",
    "src-tauri/src/feedback.rs",
    "src-tauri/src/commands/account_delete.rs",
]
# Deliberately outside the route. The first four are the files that turn a
# path gate into a platform gate (defect 212b); the version trio is what makes
# a route a release route; presence-manifest.json goes as its own presence-only
# push (the token stays presence-only), exactly as for native-share.
ROUTE_FORBIDDEN_FILES = [
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
    "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml",
    "src-tauri/gen/android/app/build.gradle.kts",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.toml",
    "src-tauri/Cargo.lock",
    "presence-manifest.json",
]
# Not a release task, so configured_harnesses() inherits nothing: this list is
# the whole set the route runs. It is the strictest tier in the home (the same
# ten as entry-fork-187 / mobile-ime-inset / native-share) and a superset of
# the default plugin-host set the diff would otherwise get.
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

# native-share minus its protected presence manifest: the shape that route is
# actually pushed in.
NATIVE_SHARE_FILES = [
    "dist/index.html",
    "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml",
    "src-tauri/src/commands/mail_intent.rs",
    "src-tauri/src/commands/packages.rs",
    "src-tauri/src/lib.rs",
    "tests/bundled_plugin_isolation_harness.mjs",
]


class SeafarerMobile189RouteTests(unittest.TestCase):
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
        task: str | None = None,
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
        if task:
            command.extend(["--task", task])
        else:
            command.append("--auto-task")
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
        task: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json", task=task)

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
        # No file of this route is release-sensitive, so no release-sensitive
        # touch may ever be reported for it. This is exactly why the task does
        # not need to be (and is not) a release task.
        self.assertEqual(payload["release_changes"], False)
        self.assertEqual(payload["release_paths_touched"], [])
        self.assertEqual(payload["protected_paths_touched"], [])
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    # 1. The exact route set routes to the task and passes.
    def test_full_route_set_routes_to_mobile_189_native(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-189-full-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES)

    def test_rust_subsets_route(self) -> None:
        # Each Rust file alone, and the realistic per-defect slices, are inside
        # when_all_files_in and carry a require_any_of file.
        for label, files in (
            ("vault-only", ["src-tauri/src/commands/vault.rs"]),
            ("feedback-only", ["src-tauri/src/feedback.rs"]),
            ("account-delete-only", ["src-tauri/src/commands/account_delete.rs"]),
            (
                "account-delete-slice",
                [
                    "src-tauri/src/commands/account_delete.rs",
                    "src-tauri/src/lib.rs",
                    "dist/index.html",
                    "tests/bundled_plugin_isolation_harness.mjs",
                ],
            ),
            (
                "ios-links-slice",
                [
                    "src-tauri/src/commands/vault.rs",
                    "dist/intelligence.js",
                ],
            ),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-189-{label}-",
                )
                self.assert_routed_pass(payload, proc, files)

    # 2. A diff without a single Rust file must not open the route.
    def test_diff_without_rust_file_does_not_open_the_route(self) -> None:
        # require_any_of is the narrowing: the front-end half alone keeps the
        # classification it has today (default plugin-host) and the gate that
        # comes with it. dist/index.html stays green because plugin-host
        # already allows it; dist/intelligence.js stays RED because nothing
        # allows it without a Rust file — in both cases the route is not used.
        for label, files, expect_pass in (
            ("dist-index-only", ["dist/index.html"], True),
            ("dist-and-harness", ["dist/index.html", "tests/bundled_plugin_isolation_harness.mjs"], True),
            ("dist-lib-harness", ["dist/index.html", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"], True),
            ("lib-only", ["src-tauri/src/lib.rs"], True),
            ("harness-only", ["tests/bundled_plugin_isolation_harness.mjs"], True),
            ("intelligence-only", ["dist/intelligence.js"], False),
            ("dist-pair-no-rust", ["dist/index.html", "dist/intelligence.js"], False),
        ):
            with self.subTest(case=label):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-189-norust-{label}-",
                )

                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertEqual(payload["status"], "pass" if expect_pass else "fail")
                self.assertEqual(proc.returncode, 0 if expect_pass else 1, proc.stdout + proc.stderr)

    # 3 + 4. Any file outside the seven falls through and stays RED.
    def test_route_set_plus_extra_file_does_not_route_and_stays_red(self) -> None:
        # when_all_files_in is the upper bound. In particular the route does
        # NOT open src-tauri/src/** wholesale, does not reach the Android
        # platform files (212b), does not authorize a version bump, and cannot
        # be used to sneak the presence manifest through.
        for extra in ROUTE_FORBIDDEN_FILES + [
            "src-tauri/src/commands/mod.rs",
            "src-tauri/src/commands/packages.rs",
            "src-tauri/src/cv.rs",
            "dist/plugin-loader.js",
            ".github/workflows/skipi-guard.yml",
            "src/unrelated.txt",
        ]:
            with self.subTest(extra=extra):
                updates = self.candidate(ROUTE_FILES)
                updates[extra] = "forbidden extra file\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-189-mixed-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(payload["errors"], payload)

    def test_extra_tauri_conf_is_rejected_by_scope(self) -> None:
        # Named separately because it is the single most tempting extra: a
        # version bump riding a bugfix route.
        updates = self.candidate(ROUTE_FILES)
        updates["src-tauri/tauri.conf.json"] = "forbidden extra file\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-seafarer-189-tauri-conf-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertIn("src-tauri/tauri.conf.json", payload["scope_violations"])
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_extra_android_manifest_is_rejected(self) -> None:
        manifest = "src-tauri/gen/android/app/src/main/AndroidManifest.xml"
        updates = self.candidate(ROUTE_FILES)
        updates[manifest] = "forbidden extra file\n"
        proc, payload = self.verify_updates(
            updates,
            prefix="skipi-guard-seafarer-189-manifest-",
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertIn(manifest, payload["scope_violations"])
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )
        # It is release-sensitive too, and the fallback task is not a release
        # task, so the second stop-line fires as well.
        self.assertTrue(
            any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_explicit_task_cannot_smuggle_release_sensitive_files(self) -> None:
        # Counterpart to finding Н-1 (RISKS №224b): an explicit --task for a
        # task that IS in release_tasks but not in exact_task_file_sets pulls
        # in every release_sensitive_path. This route is deliberately NOT a
        # release task, so both stop-lines stay closed even when the task is
        # named by hand.
        for smuggled in (
            "src-tauri/tauri.conf.json",
            "src-tauri/Cargo.lock",
            "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
            "package.json",
        ):
            with self.subTest(smuggled=smuggled):
                proc, payload = self.verify_updates(
                    self.candidate(["src-tauri/src/commands/vault.rs", smuggled]),
                    prefix="skipi-guard-seafarer-189-explicit-",
                    task=ROUTE_TASK,
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task_source"], "explicit")
                self.assertIn(smuggled, payload["scope_violations"])
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    def test_explicit_task_still_requires_a_route_file(self) -> None:
        # The other half of Н-1: with an explicit --task the routing rule is
        # not consulted at all, so require_any_of cannot help. What holds the
        # line is allowed_file_patterns, and it must hold: a diff with no route
        # file at all stays RED under --task.
        proc, payload = self.verify_updates(
            self.candidate(["src/unrelated.txt"]),
            prefix="skipi-guard-seafarer-189-explicit-empty-",
            task=ROUTE_TASK,
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["scope_violations"], ["src/unrelated.txt"])

    # 5 + 6. Config shape: literal paths, exact set, release-task question.
    def test_route_is_literal_and_bounded_by_routing(self) -> None:
        config = self.load_config()

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        # Named path-by-path, in both places the guard reads them.
        self.assertEqual(
            routes[0]["when_all_files_in"],
            [
                "dist/index.html",
                "dist/intelligence.js",
                "src-tauri/src/commands/account_delete.rs",
                "src-tauri/src/commands/vault.rs",
                "src-tauri/src/feedback.rs",
                "src-tauri/src/lib.rs",
                "tests/bundled_plugin_isolation_harness.mjs",
            ],
        )
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(len(routes[0]["when_all_files_in"]), 7)
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)
        # The narrowing: require_any_of on the three Rust files, no
        # require_all_of (a one-file fix must still ride the route).
        self.assertEqual(routes[0]["require_any_of"], ROUTE_RUST_FILES)
        self.assertNotIn("require_all_of", routes[0])
        for rust in ROUTE_RUST_FILES:
            self.assertIn(rust, ROUTE_FILES)
            self.assertTrue(rust.endswith(".rs"), rust)
        # Literal paths only: no glob may widen this route.
        for pattern in (
            routes[0]["when_all_files_in"]
            + routes[0]["require_any_of"]
            + config["allowed_file_patterns"][ROUTE_TASK]
        ):
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
        # Nothing from the forbidden list leaked in, and nothing under gen/.
        for forbidden in ROUTE_FORBIDDEN_FILES:
            self.assertNotIn(forbidden, ROUTE_FILES)
            self.assertNotIn(forbidden, config["allowed_file_patterns"][ROUTE_TASK])
        for path in ROUTE_FILES:
            self.assertFalse(path.startswith("src-tauri/gen/"), path)

    def test_route_is_not_a_release_task_and_needs_no_exact_file_set(self) -> None:
        config = self.load_config()

        # No file of the route matches any release_sensitive_paths pattern —
        # that is the mechanical reason the task is not a release task.
        sensitive = [
            str(pattern)
            for rule in config["release_sensitive_paths"]
            for pattern in rule.get("patterns", [])
        ]
        pattern_matches = GUARD_MODULE.pattern_matches
        for path in ROUTE_FILES:
            for pattern in sensitive:
                self.assertFalse(pattern_matches(path, pattern), f"{path} matches {pattern}")
        self.assertNotIn(ROUTE_TASK, config["release_tasks"])
        # Standing invariant (finding Н-1 / RISKS №224b): if this route is
        # ever promoted to a release task, it MUST also get an
        # exact_task_file_sets entry, otherwise every release_sensitive_path
        # is glued onto its allowed patterns.
        if ROUTE_TASK in config["release_tasks"]:
            self.assertIn(ROUTE_TASK, config["exact_task_file_sets"])
        # ios-apple-project-265b joined as the only other exact-set task: task
        # card A0 of wave 0.4.191 (skipi-ops/handoffs/seafarer-0-4-191/TASKCARD-A0-guard-routes.md),
        # oracle in tests/test_seafarer_ios_apple_route.py.
        self.assertEqual(set(config["exact_task_file_sets"]), {"stack-metadata", "ios-apple-project-265b"})

    def test_route_harnesses_are_the_strictest_tier_and_inherit_nothing(self) -> None:
        config = self.load_config()

        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        harness_names = [entry["name"] for entry in config["harness_commands"][ROUTE_TASK]]
        self.assertEqual(len(harness_names), 10)
        self.assertEqual(len(harness_names), len(set(harness_names)))
        # Not a release task -> configured_harnesses() inherits nothing, so the
        # list must itself cover the default plugin-host set.
        plugin_host_generic = {entry["name"] for entry in config["harness_commands"]["plugin-host"]}
        self.assertTrue(plugin_host_generic <= set(harness_names))
        # Same tier as the neighbouring owner routes; nothing is redefined.
        self.assertEqual(
            config["harness_commands"][ROUTE_TASK],
            config["harness_commands"]["mobile-ime-inset"],
        )
        owned_elsewhere = {
            (entry["name"], entry["command"])
            for task, entries in config["harness_commands"].items()
            if task != ROUTE_TASK
            for entry in entries
        }
        for entry in config["harness_commands"][ROUTE_TASK]:
            self.assertIn((entry["name"], entry["command"]), owned_elsewhere)

    def test_route_does_not_weaken_protected_paths_or_stop_lines(self) -> None:
        config = self.load_config()

        presence_rules = [
            rule for rule in config["protected_paths"] if rule.get("name") == "presence contracts"
        ]
        self.assertEqual(len(presence_rules), 1)
        self.assertIn("presence-manifest.json", presence_rules[0]["patterns"])
        self.assertEqual(
            [rule["name"] for rule in config["protected_paths"]],
            [
                "backend/server/prod data",
                "secrets/signing keys",
                "pairing/QR/camera bridge",
                "presence contracts",
            ],
        )
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
        self.assertEqual(config["default_task"], "plugin-host")

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
            "native-share": (
                "seafarer native share routing (332)",
                self.candidate(NATIVE_SHARE_FILES),
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
                    prefix=f"skipi-guard-seafarer-189-neighbour-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
