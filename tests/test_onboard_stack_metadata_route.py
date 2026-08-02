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
CONFIG_PATH = ROOT / "configs" / "homes" / "onboard.json"
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


class OnboardStackMetadataRouteTests(unittest.TestCase):
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

    def commit_updates(self, repo: Path, message: str, updates: dict[str, str], *, deleted: tuple[str, ...] = ()) -> None:
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
            "dist/index.html": '<meta name="app-version" content="0.1.3">\n',
            "src-tauri/Cargo.lock": 'version = "0.1.3"\n',
            "src-tauri/Cargo.toml": 'version = "0.1.3"\n',
            "src-tauri/src/lib.rs": 'pub const STACK: &str = "old";\n',
            "src-tauri/tauri.conf.json": '{"version":"0.1.3"}\n',
            STACK_BUILD_METADATA: "process.exit(0); // old\n",
            STACK_VERIFICATION_NEGATIVE: "process.exit(0); // old\n",
        }
        for f in ['tests/plugin_isolation_harness.mjs', 'tests/apps_launcher_harness.mjs', 'tests/onboard_presence_contract_harness.mjs']:
            seed[f] = "process.exit(0);\n"
        self.commit_updates(repo, "seed onboard Stage 4 fixture", seed)

    def candidate_updates(self) -> dict[str, str]:
        return {
            "dist/index.html": '<meta name="app-version" content="0.1.4">\n',
            "src-tauri/Cargo.lock": 'version = "0.1.4"\n',
            "src-tauri/Cargo.toml": 'version = "0.1.4"\n',
            "src-tauri/src/lib.rs": 'pub const STACK: &str = "SKIPI-2026.08-R1";\n',
            "src-tauri/tauri.conf.json": '{"version":"0.1.4"}\n',
            STACK_BUILD_METADATA: "process.exit(0); // new\n",
            STACK_VERIFICATION_NEGATIVE: "process.exit(0); // new\n",
        }

    def run_guard(self, repo: Path, result_json: Path, *, task: str | None = None, auto_task: bool = False, run_harness: bool = False):
        command = [str(GUARD), "verify", "--home", "onboard", "--repo", str(repo), "--base", "HEAD~1", "--head", "HEAD", "--json", str(result_json)]
        if auto_task:
            command.append("--auto-task")
        elif task:
            command.extend(["--task", task])
        else:
            raise ValueError("task or auto_task required")
        if run_harness:
            command.append("--run-harness")
        proc = subprocess.run(command, text=True, capture_output=True, env=self.child_env())
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def make_candidate(self, repo: Path, **kwargs) -> None:
        omit = kwargs.get("omit", ())
        deleted = kwargs.get("deleted", ())
        extra = kwargs.get("extra") or {}
        updates = {p: c for p, c in self.candidate_updates().items() if p not in omit and p not in deleted}
        updates.update(extra)
        self.commit_updates(repo, "onboard Stage 4 stack metadata", updates, deleted=deleted)

    def test_exact_seven_auto_routes_stack_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-stack-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo)
            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True, run_harness=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "stack-metadata")
        self.assertEqual(payload["task_rule"], "onboard Stage 4 stack-metadata routing")
        self.assertEqual(sorted(payload["changed_files"]), STACK_METADATA_FILES)

    def test_eighth_path_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-onboard-eighth-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.make_candidate(repo, extra={"README.md": "nope\n"})
            proc, payload = self.run_guard(repo, root / "result.json", auto_task=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")

    def test_route_config_exact(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        rules = {rule["name"]: rule for rule in config["task_routing"]}
        stack_rule = rules["onboard Stage 4 stack-metadata routing"]
        self.assertEqual(stack_rule["task"], "stack-metadata")
        self.assertEqual(stack_rule["when_all_files_in"], STACK_METADATA_FILES)
        self.assertEqual(stack_rule["require_all_of"], STACK_METADATA_FILES)
        self.assertEqual(config["exact_task_file_sets"]["stack-metadata"], STACK_METADATA_FILES)
        self.assertEqual(config["allowed_file_patterns"]["stack-metadata"], STACK_METADATA_FILES)
        names = [e["name"] for e in config["harness_commands"]["stack-metadata"]]
        self.assertEqual(names[:2], ["onboard_stack_build_metadata", "onboard_stack_verification_negative_control"])
        self.assertEqual(names, ['onboard_stack_build_metadata', 'onboard_stack_verification_negative_control', 'onboard_plugin_isolation', 'onboard_apps_launcher', 'onboard_presence_contract'])


if __name__ == "__main__":
    unittest.main()
