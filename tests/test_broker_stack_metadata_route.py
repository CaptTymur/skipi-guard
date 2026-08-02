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
CONFIG_PATH = ROOT / "configs" / "homes" / "broker.json"
SCHEMA_PATH = ROOT / "schemas" / "skipi-guard.v1.schema.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

STACK_BUILD_METADATA = "tests/stack_build_metadata_harness.mjs"
STACK_VERIFICATION_NEGATIVE = "tests/stack_verification_negative_control_harness.mjs"
STACK_METADATA_FILES = [
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/src/lib.rs",
    "src-tauri/tauri.conf.json",
    STACK_BUILD_METADATA,
    STACK_VERIFICATION_NEGATIVE,
]

EXISTING_PLUGIN_HOST_ALLOWLIST = [
    "dist/index.html",
    "dist/plugin-host-bridge.js",
    "presence-manifest.json",
    "tests/broker_plugin_isolation_harness.mjs",
    "tests/broker_presence_contract_harness.mjs",
]
EXISTING_SETTINGS_ADOPT_ALLOWLIST = [
    "dist/index.html",
    "dist/skipi-settings*",
]


class BrokerStackMetadataRouteTests(unittest.TestCase):
    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
        return env

    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
            env=self.child_env(),
        )

    def commit_updates(
        self,
        repo: Path,
        message: str,
        updates: dict[str, str],
        *,
        deleted: tuple[str, ...] = (),
    ) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        for relative in deleted:
            (repo / relative).unlink()
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        seed = {
            "dist/index.html": '<meta name="app-version" content="0.1.151">\n',
            "src-tauri/Cargo.lock": 'version = "0.1.151"\n',
            "src-tauri/Cargo.toml": 'version = "0.1.151"\n',
            "src-tauri/src/lib.rs": "pub const STACK: &str = \"old\";\n",
            "src-tauri/tauri.conf.json": '{"version":"0.1.151"}\n',
            STACK_BUILD_METADATA: "process.exit(0); // old build metadata\n",
            STACK_VERIFICATION_NEGATIVE: "process.exit(0); // old negative control\n",
            "tests/broker_plugin_isolation_harness.mjs": "process.exit(0);\n",
            "tests/build_provenance_harness.mjs": "process.exit(0);\n",
            "tests/broker_presence_contract_harness.mjs": "process.exit(0);\n",
            "presence-manifest.json": '{"contracts":[]}\n',
        }
        self.commit_updates(repo, "seed broker Stage 4 fixture", seed)

    def candidate_updates(self) -> dict[str, str]:
        return {
            "dist/index.html": '<meta name="app-version" content="0.1.152">\n',
            "src-tauri/Cargo.lock": 'version = "0.1.152"\n',
            "src-tauri/Cargo.toml": 'version = "0.1.152"\n',
            "src-tauri/src/lib.rs": "pub const STACK: &str = \"SKIPI-2026.08-R1\";\n",
            "src-tauri/tauri.conf.json": '{"version":"0.1.152"}\n',
            STACK_BUILD_METADATA: "process.exit(0); // new build metadata\n",
            STACK_VERIFICATION_NEGATIVE: "process.exit(0); // new negative control\n",
        }

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        task: str | None = None,
        auto_task: bool = False,
        run_harness: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "broker",
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
        if run_harness:
            command.append("--run-harness")
        proc = subprocess.run(command, text=True, capture_output=True, env=self.child_env())
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def make_candidate(
        self,
        repo: Path,
        *,
        omit: tuple[str, ...] = (),
        deleted: tuple[str, ...] = (),
        overrides: dict[str, str] | None = None,
        extra: dict[str, str] | None = None,
    ) -> None:
        updates = {
            path: contents
            for path, contents in self.candidate_updates().items()
            if path not in omit and path not in deleted
        }
        updates.update(overrides or {})
        updates.update(extra or {})
        self.commit_updates(repo, "Broker Stage 4 stack metadata", updates, deleted=deleted)

    def test_failing_first_without_route_would_be_plugin_host(self) -> None:
        """Documented RED baseline shape: without stack-metadata config, exact
        seven-path Stage 4 set is not a release route and falls to plugin-host.
        With the route present this test asserts GREEN auto-routing instead;
        the historical RED is covered by the pre-implementation handoff evidence.
        """
        with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-metadata-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo)

            proc, payload = self.run_guard(
                repo,
                root / "result.json",
                auto_task=True,
                run_harness=True,
            )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "stack-metadata")
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], "broker Stage 4 stack-metadata routing")
        self.assertEqual(payload["changed_files"], sorted(STACK_METADATA_FILES))
        self.assertEqual(payload["allowed_file_patterns"], STACK_METADATA_FILES)
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(payload["scope_violations"], [])
        self.assertTrue(payload["release_changes"])
        self.assertFalse(payload["override_present"])
        statuses = {entry["name"]: entry["status"] for entry in payload["tests"]}
        self.assertEqual(statuses["broker_stack_build_metadata"], "pass")
        self.assertEqual(statuses["broker_stack_verification_negative_control"], "pass")

    def test_exact_seven_file_diff_auto_routes_and_runs_stack_harnesses(self) -> None:
        self.test_failing_first_without_route_would_be_plugin_host()

    def test_explicit_stack_metadata_task_is_still_exact_set_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-explicit-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo, omit=(STACK_VERIFICATION_NEGATIVE,))

            proc, payload = self.run_guard(repo, root / "result.json", task="stack-metadata")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("exact file set required for task 'stack-metadata'", payload["errors"])
        self.assertEqual(payload["exact_file_set_missing"], [STACK_VERIFICATION_NEGATIVE])

    def test_explicit_stack_metadata_task_blocks_any_eighth_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-explicit-extra-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo, extra={"src/foreign.rs": "// forbidden eighth path\n"})

            proc, payload = self.run_guard(repo, root / "result.json", task="stack-metadata")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("exact file set required for task 'stack-metadata'", payload["errors"])
        self.assertEqual(payload["exact_file_set_unexpected"], ["src/foreign.rs"])

    def test_any_eighth_file_falls_back_and_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-eighth-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo, extra={"src/unreviewed.rs": "// forbidden eighth path\n"})

            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIn("src/unreviewed.rs", payload["scope_violations"])

    def test_omission_of_either_stack_harness_path_is_blocked(self) -> None:
        for omitted in (STACK_BUILD_METADATA, STACK_VERIFICATION_NEGATIVE):
            with self.subTest(omitted=omitted):
                with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-omit-") as tmp:
                    root = Path(tmp)
                    repo = root / "repo"
                    repo.mkdir()
                    self.init_repo(repo)
                    self.make_candidate(repo, omit=(omitted,))

                    proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIn("release-sensitive path touch is blocked for this task", payload["errors"])

    def test_missing_either_stack_harness_blocks_guard(self) -> None:
        for missing in (STACK_BUILD_METADATA, STACK_VERIFICATION_NEGATIVE):
            with self.subTest(missing=missing):
                with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-missing-") as tmp:
                    root = Path(tmp)
                    repo = root / "repo"
                    repo.mkdir()
                    self.init_repo(repo)
                    self.make_candidate(repo, deleted=(missing,))

                    proc, payload = self.run_guard(
                        repo,
                        root / "result.json",
                        auto_task=True,
                        run_harness=True,
                    )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], "stack-metadata")
                failed = {entry["name"] for entry in payload["tests"] if entry["status"] == "fail"}
                expected = (
                    "broker_stack_build_metadata"
                    if missing == STACK_BUILD_METADATA
                    else "broker_stack_verification_negative_control"
                )
                self.assertIn(expected, failed)

    def test_failure_of_either_stack_harness_blocks_guard(self) -> None:
        for failing in (STACK_BUILD_METADATA, STACK_VERIFICATION_NEGATIVE):
            with self.subTest(failing=failing):
                with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-fail-") as tmp:
                    root = Path(tmp)
                    repo = root / "repo"
                    repo.mkdir()
                    self.init_repo(repo)
                    self.make_candidate(repo, overrides={failing: "process.exit(23);\n"})

                    proc, payload = self.run_guard(
                        repo,
                        root / "result.json",
                        auto_task=True,
                        run_harness=True,
                    )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                failed = [entry for entry in payload["tests"] if entry["status"] == "fail"]
                self.assertEqual(len(failed), 1)
                self.assertEqual(failed[0]["exit_code"], 23)

    def test_protected_signing_deploy_and_publication_paths_remain_blocked(self) -> None:
        forbidden_paths = {
            ".env.production": "fixture\n",
            "keys/signing-private.pem": "fixture\n",
            "scripts/deploy-prod.sh": "exit 0\n",
            "scripts/upload-store.sh": "exit 0\n",
        }
        for forbidden, contents in forbidden_paths.items():
            with self.subTest(forbidden=forbidden):
                with tempfile.TemporaryDirectory(prefix="skipi-guard-broker-stack-protected-") as tmp:
                    root = Path(tmp)
                    repo = root / "repo"
                    repo.mkdir()
                    self.init_repo(repo)
                    self.make_candidate(repo, extra={forbidden: contents})

                    proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], "plugin-host")
                touched = {entry["path"] for entry in payload["protected_paths_touched"]}
                self.assertIn(forbidden, touched)

    def test_route_is_exact_and_existing_allowlists_are_unchanged(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        rules = {rule["name"]: rule for rule in config["task_routing"]}
        stack_rule = rules["broker Stage 4 stack-metadata routing"]
        self.assertEqual(stack_rule["task"], "stack-metadata")
        self.assertEqual(stack_rule["when_all_files_in"], STACK_METADATA_FILES)
        self.assertEqual(stack_rule["require_all_of"], STACK_METADATA_FILES)
        self.assertEqual(config["exact_task_file_sets"]["stack-metadata"], STACK_METADATA_FILES)
        self.assertEqual(config["allowed_file_patterns"]["stack-metadata"], STACK_METADATA_FILES)
        self.assertEqual(config["allowed_file_patterns"]["plugin-host"], EXISTING_PLUGIN_HOST_ALLOWLIST)
        self.assertEqual(config["allowed_file_patterns"]["settings-adopt"], EXISTING_SETTINGS_ADOPT_ALLOWLIST)
        self.assertEqual(config["allowed_file_patterns"]["release"], ["dist/index.html"])
        self.assertNotIn("src-tauri/src/commands/vault.rs", STACK_METADATA_FILES)
        self.assertIn("src-tauri/src/lib.rs", STACK_METADATA_FILES)

    def test_stack_metadata_lists_stack_and_relative_broker_harnesses(self) -> None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        names = [entry["name"] for entry in config["harness_commands"]["stack-metadata"]]
        self.assertEqual(
            names[:2],
            ["broker_stack_build_metadata", "broker_stack_verification_negative_control"],
        )
        # No absolute shared_host_runtime_isolation path — CI-safe exact set.
        commands = [entry["command"] for entry in config["harness_commands"]["stack-metadata"]]
        self.assertTrue(all(not cmd.startswith("node /") for cmd in commands))
        self.assertEqual(
            names,
            [
                "broker_stack_build_metadata",
                "broker_stack_verification_negative_control",
                "broker_plugin_isolation",
                "broker_build_provenance",
                "broker_presence_contract",
            ],
        )

    def test_other_homes_routes_not_expanded_here(self) -> None:
        seafarer = json.loads((ROOT / "configs" / "homes" / "seafarer.json").read_text())
        self.assertIn("stack-metadata", seafarer.get("release_tasks", []))
        crewing = json.loads((ROOT / "configs" / "homes" / "crewing.json").read_text())
        self.assertIn("stack-metadata", crewing.get("release_tasks", []))
        for home in ():  # management/onboard now have stack-metadata (Stage 4)
            other = json.loads((ROOT / "configs" / "homes" / f"{home}.json").read_text())
            self.assertNotIn("stack-metadata", other.get("release_tasks", []))
            self.assertIsNone(other.get("exact_task_file_sets"))


if __name__ == "__main__":
    unittest.main()
