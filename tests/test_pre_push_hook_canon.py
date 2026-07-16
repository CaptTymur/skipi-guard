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
TEMPLATE = ROOT / "templates" / "git-hooks" / "pre-push.skipi-guard.sh"
ZERO_SHA = "0" * 40
HOOKED_HOMES = ["seafarer", "crewing", "broker", "onboard", "management"]

GUARD_LOADER = SourceFileLoader("skipi_guard_cli_hooks", str(GUARD))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
if GUARD_SPEC is None:
    raise RuntimeError(f"cannot load guard module from {GUARD}")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_LOADER.exec_module(GUARD_MODULE)


# Fixture replica of the pre-2026-07-16 deployed hook construction (broker),
# reproducing SKI-INC-2026-07-16: it diffs origin/main...HEAD of the current
# checkout and never reads the pre-push stdin refs.
OLD_STYLE_HOOK = """#!/usr/bin/env bash
set -euo pipefail

export SKIPI_GUARD_HOME="broker"
export SKIPI_GUARD_TASK="${SKIPI_GUARD_TASK:-plugin-host}"

SKIPI_GUARD_BIN="__BIN__"
SKIPI_GUARD_BASE="${SKIPI_GUARD_BASE:-origin/main}"
SKIPI_GUARD_HEAD="${SKIPI_GUARD_HEAD:-HEAD}"
SKIPI_GUARD_JSON="${SKIPI_GUARD_JSON:-__JSON__}"
SKIPI_GUARD_REPO="$(git rev-parse --show-toplevel)"
OVERRIDE_ARGS=()
mapfile -t GUARD_CHANGED_FILES < <(
  git diff --name-only --diff-filter=ACDMRTUXB "$SKIPI_GUARD_BASE...$SKIPI_GUARD_HEAD" 2>/dev/null ||
  git diff --name-only --diff-filter=ACDMRTUXB "$SKIPI_GUARD_BASE..$SKIPI_GUARD_HEAD"
)
if [[ "${#GUARD_CHANGED_FILES[@]}" -eq 1 && "${GUARD_CHANGED_FILES[0]}" == ".github/workflows/skipi-guard.yml" ]]; then
  OVERRIDE_ARGS=(--override-protected skipi-guard-workflow-bootstrap)
fi

exec "$SKIPI_GUARD_BIN" verify \\
  --home "$SKIPI_GUARD_HOME" \\
  --task "$SKIPI_GUARD_TASK" \\
  "${OVERRIDE_ARGS[@]}" \\
  --run-harness \\
  --repo "$SKIPI_GUARD_REPO" \\
  --base "$SKIPI_GUARD_BASE" \\
  --head "$SKIPI_GUARD_HEAD" \\
  --json "$SKIPI_GUARD_JSON"
"""

BROKER_SEED = {
    "README.md": "# fixture\n",
    "tests/broker_plugin_isolation_harness.mjs": "process.exit(0);\n",
    "tests/build_provenance_harness.mjs": "process.exit(0);\n",
    "tests/broker_presence_contract_harness.mjs": "process.exit(0);\n",
}


class PrePushHookCanonTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)

    def rev(self, repo: Path, ref: str) -> str:
        return self.run_git(repo, "rev-parse", ref).stdout.strip()

    def run_guard(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(GUARD), *args], text=True, capture_output=True, cwd=cwd)

    def make_fixture(self, root: Path, seed: dict[str, str]) -> tuple[Path, Path]:
        origin = root / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True, text=True, capture_output=True)
        clone = root / "clone"
        clone.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True, text=True, capture_output=True)
        self.run_git(clone, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(clone, "config", "user.name", "Skipi Guard Fixture")
        self.commit_files(clone, "seed", seed)
        self.run_git(clone, "remote", "add", "origin", str(origin))
        self.run_git(clone, "push", "-q", "-u", "origin", "main")
        return origin, clone

    def commit_files(self, repo: Path, message: str, updates: dict[str, str]) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def make_branch(self, repo: Path, name: str, message: str, updates: dict[str, str]) -> str:
        """Create a branch with a commit, then return the checkout to main (branch is NOT checked out)."""
        self.run_git(repo, "checkout", "-q", "-b", name)
        self.commit_files(repo, message, updates)
        sha = self.rev(repo, name)
        self.run_git(repo, "checkout", "-q", "main")
        return sha

    def install_canon_hook(self, home: str, repo: Path) -> Path:
        proc = self.run_guard("hooks", "install", "--home", home, "--repo", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        hook = repo / ".git" / "hooks" / "pre-push"
        self.assertTrue(hook.exists(), "hook not installed")
        return hook

    def install_old_style_hook(self, repo: Path, json_path: Path) -> Path:
        hook = repo / ".git" / "hooks" / "pre-push"
        hook.parent.mkdir(parents=True, exist_ok=True)
        body = OLD_STYLE_HOOK.replace("__BIN__", str(GUARD)).replace("__JSON__", str(json_path))
        hook.write_text(body, encoding="utf-8")
        hook.chmod(0o755)
        return hook

    def remote_has_branch(self, origin: Path, branch: str) -> bool:
        proc = subprocess.run(
            ["git", "ls-remote", "--heads", str(origin), branch],
            text=True,
            capture_output=True,
            check=True,
        )
        return branch in proc.stdout

    # --- SKI-INC-2026-07-16 incident repro -------------------------------

    def test_incident_repro_old_hook_blind_pass_canon_hook_blocks(self) -> None:
        """Push of a non-checked-out branch with a protected-path change:
        the old deployed construction PASSes blindly (0 checked files),
        the canonical stdin-refs hook must FAIL the push."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-inc-repro-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(root, BROKER_SEED)
            self.make_branch(
                clone,
                "protected-change",
                "touch protected path",
                {"keys/signing.pem": "not-a-real-key\n"},
            )
            self.assertEqual(self.rev(clone, "HEAD"), self.rev(clone, "main"), "fixture must sit on main")

            # Old deployed construction: blind PASS (the incident).
            old_json = root / "old-guard.json"
            self.install_old_style_hook(clone, old_json)
            push_old = self.run_git(clone, "push", "origin", "protected-change", check=False)
            self.assertEqual(
                push_old.returncode,
                0,
                "old-style hook is expected to PASS blindly (incident repro): " + push_old.stdout + push_old.stderr,
            )
            with old_json.open("r", encoding="utf-8") as handle:
                old_payload = json.load(handle)
            self.assertEqual(old_payload["status"], "pass")
            self.assertEqual(old_payload["changed_files"], [], "old hook validated an empty checkout diff")
            self.run_git(clone, "push", "-q", "origin", ":protected-change")

            # Canonical hook: validates pushed bytes, must block.
            self.install_canon_hook("broker", clone)
            push_canon = self.run_git(clone, "push", "origin", "protected-change", check=False)
            self.assertNotEqual(
                push_canon.returncode,
                0,
                "canonical hook must FAIL a pushed protected-path change: " + push_canon.stdout + push_canon.stderr,
            )
            combined = push_canon.stdout + push_canon.stderr
            self.assertIn("keys/signing.pem", combined)
            self.assertFalse(self.remote_has_branch(origin, "protected-change"), "push must be blocked")

    # --- stdin-refs semantics --------------------------------------------

    def test_pre_push_ref_deleted_ref_is_skipped(self) -> None:
        proc = self.run_guard(
            "pre-push-ref",
            "--home",
            "broker",
            "--repo",
            "/nonexistent-not-touched",
            "--local-ref",
            "(delete)",
            "--local-sha",
            ZERO_SHA,
            "--remote-ref",
            "refs/heads/gone",
            "--remote-sha",
            "1234567890123456789012345678901234567890",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_branch_deletion_push_passes_through_canon_hook(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-delete-ref-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(root, BROKER_SEED)
            self.make_branch(clone, "meta", "meta change", {"AGENTS.md": "# fixture agents\n"})
            self.install_canon_hook("broker", clone)
            push = self.run_git(clone, "push", "origin", "meta", check=False)
            self.assertEqual(push.returncode, 0, push.stdout + push.stderr)
            delete = self.run_git(clone, "push", "origin", ":meta", check=False)
            self.assertEqual(delete.returncode, 0, delete.stdout + delete.stderr)
            self.assertFalse(self.remote_has_branch(origin, "meta"))

    def test_pre_push_ref_new_branch_uses_merge_base_with_origin_main(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-merge-base-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)
            branch_sha = self.make_branch(clone, "meta", "meta change", {"AGENTS.md": "# fixture agents\n"})
            main_sha = self.rev(clone, "main")
            result_json = root / "result.json"
            proc = self.run_guard(
                "pre-push-ref",
                "--home",
                "broker",
                "--repo",
                str(clone),
                "--local-ref",
                "refs/heads/meta",
                "--local-sha",
                branch_sha,
                "--remote-ref",
                "refs/heads/meta",
                "--remote-sha",
                ZERO_SHA,
                "--json",
                str(result_json),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            with result_json.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["base"], main_sha, "new branch must be based on merge-base with origin/main")
            self.assertEqual(payload["head"], branch_sha, "head must be the pushed local sha, not checkout HEAD")
            self.assertEqual(payload["changed_files"], ["AGENTS.md"])
            self.assertEqual(payload["task"], "repo-meta")
            self.assertEqual(payload["status"], "pass")

    def test_pre_push_ref_uses_remote_sha_as_base_when_known(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-remote-base-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)
            first_sha = self.make_branch(clone, "meta", "meta change", {"AGENTS.md": "# fixture agents\n"})
            self.run_git(clone, "push", "-q", "origin", "meta")
            self.run_git(clone, "checkout", "-q", "meta")
            self.commit_files(clone, "meta change 2", {"AGENTS.md": "# fixture agents v2\n"})
            second_sha = self.rev(clone, "meta")
            self.run_git(clone, "checkout", "-q", "main")
            result_json = root / "result.json"
            proc = self.run_guard(
                "pre-push-ref",
                "--home",
                "broker",
                "--repo",
                str(clone),
                "--local-ref",
                "refs/heads/meta",
                "--local-sha",
                second_sha,
                "--remote-ref",
                "refs/heads/meta",
                "--remote-sha",
                first_sha,
                "--json",
                str(result_json),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            with result_json.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["base"], first_sha, "known remote sha must be the base")
            self.assertEqual(payload["head"], second_sha)
            self.assertEqual(payload["changed_files"], ["AGENTS.md"])
            self.assertEqual(payload["status"], "pass")

    def test_pre_push_ref_fails_closed_without_base(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-no-base-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, text=True, capture_output=True)
            self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
            self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
            self.commit_files(repo, "seed", {"README.md": "# fixture\n"})
            sha = self.rev(repo, "HEAD")
            proc = self.run_guard(
                "pre-push-ref",
                "--home",
                "broker",
                "--repo",
                str(repo),
                "--local-ref",
                "refs/heads/main",
                "--local-sha",
                sha,
                "--remote-ref",
                "refs/heads/main",
                "--remote-sha",
                ZERO_SHA,
            )
            self.assertNotEqual(proc.returncode, 0, "no origin/main and no remote sha must fail closed")

    def test_multiple_refs_all_pass_and_any_fail_blocks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-multi-ref-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(root, BROKER_SEED)
            self.make_branch(clone, "meta1", "meta1", {"AGENTS.md": "# fixture agents one\n"})
            self.make_branch(clone, "meta2", "meta2", {"CLAUDE.md": "# fixture claude two\n"})
            self.make_branch(clone, "bad", "protected", {"keys/signing.pem": "not-a-real-key\n"})
            self.install_canon_hook("broker", clone)

            push_good = self.run_git(clone, "push", "origin", "meta1", "meta2", check=False)
            self.assertEqual(push_good.returncode, 0, push_good.stdout + push_good.stderr)
            self.assertTrue(self.remote_has_branch(origin, "meta1"))
            self.assertTrue(self.remote_has_branch(origin, "meta2"))

            self.make_branch(clone, "meta3", "meta3", {"AGENTS.md": "# fixture agents three\n"})
            push_mixed = self.run_git(clone, "push", "origin", "meta3", "bad", check=False)
            self.assertNotEqual(push_mixed.returncode, 0, push_mixed.stdout + push_mixed.stderr)
            self.assertFalse(self.remote_has_branch(origin, "bad"))
            self.assertFalse(self.remote_has_branch(origin, "meta3"), "pre-push failure aborts the whole push")

    def test_empty_stdin_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-empty-stdin-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)
            hook = self.install_canon_hook("broker", clone)
            proc = subprocess.run(
                [str(hook), "origin", "file:///dev/null"],
                cwd=clone,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    # --- bootstrap override from the pushed diff ---------------------------

    def test_bootstrap_override_applies_to_pushed_workflow_only_diff(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-bootstrap-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(root, BROKER_SEED)
            self.make_branch(
                clone,
                "wf-only",
                "workflow bootstrap",
                {".github/workflows/skipi-guard.yml": "name: skipi-guard\n"},
            )
            self.install_canon_hook("broker", clone)
            push = self.run_git(clone, "push", "origin", "wf-only", check=False)
            self.assertEqual(push.returncode, 0, push.stdout + push.stderr)
            self.assertTrue(self.remote_has_branch(origin, "wf-only"))

    def test_bootstrap_override_not_applied_to_mixed_pushed_diff(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-bootstrap-mixed-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(root, BROKER_SEED)
            self.make_branch(
                clone,
                "wf-plus",
                "workflow plus payload",
                {
                    ".github/workflows/skipi-guard.yml": "name: skipi-guard\n",
                    "dist/index.html": "<main>payload</main>\n",
                },
            )
            self.install_canon_hook("broker", clone)
            push = self.run_git(clone, "push", "origin", "wf-plus", check=False)
            self.assertNotEqual(push.returncode, 0, push.stdout + push.stderr)
            self.assertFalse(self.remote_has_branch(origin, "wf-plus"))

    # --- declarative task routing (decision а/г) ---------------------------

    def test_repo_meta_routing_for_all_hooked_homes(self) -> None:
        for home in HOOKED_HOMES:
            config = GUARD_MODULE.load_home_config(home)
            routed = GUARD_MODULE.resolve_task(config, ["AGENTS.md", "CLAUDE.md"])
            self.assertEqual(routed["task"], "repo-meta", f"{home}: meta-only diff must route to repo-meta")
            mixed = GUARD_MODULE.resolve_task(config, ["AGENTS.md", "dist/index.html"])
            self.assertEqual(mixed["task"], "plugin-host", f"{home}: mixed diff must fall back to default")

    def test_empty_diff_routes_to_default_task(self) -> None:
        config = GUARD_MODULE.load_home_config("broker")
        routed = GUARD_MODULE.resolve_task(config, [])
        self.assertEqual(routed["task"], "plugin-host")

    def test_crewing_provenance_routing_is_all_files_in_set(self) -> None:
        config = GUARD_MODULE.load_home_config("crewing")
        self.assertEqual(GUARD_MODULE.resolve_task(config, ["src-tauri/build.rs"])["task"], "provenance")
        self.assertEqual(
            GUARD_MODULE.resolve_task(
                config, ["tests/build_provenance_harness.mjs", "src-tauri/src/lib.rs"]
            )["task"],
            "provenance",
        )
        # Old deployed crewing semantics ("at least one file") is abolished:
        # a mixed diff stays on the default task.
        self.assertEqual(
            GUARD_MODULE.resolve_task(config, ["src-tauri/build.rs", "dist/index.html"])["task"],
            "plugin-host",
        )

    def test_broker_settings_adopt_routing(self) -> None:
        """BACKLOG п.47: a settings-module adopt diff (vendored dist/skipi-settings*
        bytes + dist/index.html wiring) routes to settings-adopt; anything mixed
        with a foreign file falls back to the default task and is blocked by the
        plugin-host allowlist (fail closed)."""
        config = GUARD_MODULE.load_home_config("broker")
        adopt_files = [
            "dist/index.html",
            "dist/skipi-settings.js",
            "dist/skipi-settings.css",
            "dist/skipi-settings.inline.html",
            "dist/skipi-settings.SETTINGS_VERSION",
        ]
        self.assertEqual(GUARD_MODULE.resolve_task(config, adopt_files)["task"], "settings-adopt")
        self.assertEqual(
            GUARD_MODULE.resolve_task(config, ["dist/skipi-settings.js"])["task"], "settings-adopt"
        )
        # index.html alone is a plugin-host change, not an adopt (require_any_of).
        self.assertEqual(GUARD_MODULE.resolve_task(config, ["dist/index.html"])["task"], "plugin-host")
        # Mixed diff with a foreign file: default task...
        mixed = ["dist/skipi-settings.js", "src/other.js"]
        self.assertEqual(GUARD_MODULE.resolve_task(config, mixed)["task"], "plugin-host")
        # ...and blocked by the plugin-host allowed patterns.
        scope = GUARD_MODULE.scope_check_for_task(config, "plugin-host", mixed)
        self.assertIn("src/other.js", scope["scope_violations"])
        self.assertIn("dist/skipi-settings.js", scope["scope_violations"])
        # settings-adopt itself must not smuggle foreign files either.
        adopt_scope = GUARD_MODULE.scope_check_for_task(config, "settings-adopt", mixed)
        self.assertIn("src/other.js", adopt_scope["scope_violations"])

    def test_management_provenance_routing_requires_provenance_file(self) -> None:
        config = GUARD_MODULE.load_home_config("management")
        self.assertEqual(GUARD_MODULE.resolve_task(config, ["dist/index.html"])["task"], "plugin-host")
        self.assertEqual(
            GUARD_MODULE.resolve_task(config, ["dist/index.html", "src-tauri/build.rs"])["task"],
            "provenance",
        )
        self.assertEqual(
            GUARD_MODULE.resolve_task(
                config,
                [
                    "dist/index.html",
                    "src-tauri/build.rs",
                    "src-tauri/src/lib.rs",
                    "tests/build_provenance_harness.mjs",
                ],
            )["task"],
            "provenance",
        )
        self.assertEqual(
            GUARD_MODULE.resolve_task(config, ["src-tauri/build.rs", "src/other.js"])["task"],
            "plugin-host",
        )

    # --- harness runs on pushed bytes (decision в) --------------------------

    def test_run_harness_executes_pushed_bytes_not_checkout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-pushed-bytes-") as tmp:
            root = Path(tmp)
            origin, clone = self.make_fixture(
                root,
                {
                    "README.md": "# fixture\n",
                    # Checkout (main) version of the harness fails; the pushed
                    # branch fixes it. Only a pushed-bytes run can pass.
                    "tests/build_provenance_harness.mjs": "process.exit(1);\n",
                },
            )
            self.make_branch(
                clone,
                "prov-fix",
                "fix provenance harness",
                {"tests/build_provenance_harness.mjs": "process.exit(0);\n"},
            )
            self.install_canon_hook("crewing", clone)
            push = self.run_git(clone, "push", "origin", "prov-fix", check=False)
            self.assertEqual(
                push.returncode,
                0,
                "harness must run against pushed bytes (branch fixes it): " + push.stdout + push.stderr,
            )
            self.assertTrue(self.remote_has_branch(origin, "prov-fix"))
            result_json = Path("/tmp/skipi-guard-pre-push-crewing.json")
            with result_json.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["task"], "provenance")
            self.assertEqual(payload["status"], "pass")
            harness_status = {entry["name"]: entry["status"] for entry in payload["tests"]}
            self.assertEqual(harness_status.get("crewing_build_provenance"), "pass")
            worktrees = self.run_git(clone, "worktree", "list", "--porcelain").stdout
            self.assertEqual(
                worktrees.count("worktree "),
                1,
                "temporary pushed-bytes worktree must be removed after the run",
            )

    # --- harness worktree placement (BACKLOG п.40, variant А) ----------------

    def test_run_harness_worktree_sits_next_to_repo_and_resolves_sibling_imports(self) -> None:
        """Harnesses in crewing/broker/management import sibling-repo modules
        via `../../<sibling>/...` relative to the repo root. The pushed-bytes
        worktree therefore must be a direct sibling of the real repo (variant
        А, decision 2026-07-16), not a nested /tmp path where the sibling does
        not exist and node dies with ERR_MODULE_NOT_FOUND."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-sibling-import-") as tmp:
            root = Path(tmp)
            sibling = root / "sibling-runtime"
            sibling.mkdir()
            (sibling / "isolation-contract.mjs").write_text(
                "export const contract = \"fixture\";\n", encoding="utf-8"
            )
            seed = dict(BROKER_SEED)
            # Same import shape as tests/*_plugin_isolation_harness.mjs in the
            # three affected homes: relative resolve through the repo parent.
            seed["tests/broker_plugin_isolation_harness.mjs"] = (
                'import { contract } from "../../sibling-runtime/isolation-contract.mjs";\n'
                'if (contract !== "fixture") process.exit(1);\n'
                "process.exit(0);\n"
            )
            _origin, clone = self.make_fixture(root, seed)
            branch_sha = self.make_branch(
                clone, "host-change", "plugin-host change", {"dist/index.html": "<main>v2</main>\n"}
            )
            result_json = root / "result.json"
            proc = self.run_guard(
                "pre-push-ref",
                "--home",
                "broker",
                "--repo",
                str(clone),
                "--local-ref",
                "refs/heads/host-change",
                "--local-sha",
                branch_sha,
                "--remote-ref",
                "refs/heads/host-change",
                "--remote-sha",
                ZERO_SHA,
                "--json",
                str(result_json),
            )
            self.assertEqual(
                proc.returncode,
                0,
                "harness with a sibling-relative import must pass from the pushed-bytes worktree: "
                + proc.stdout
                + proc.stderr,
            )
            with result_json.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["status"], "pass")
            harness_status = {entry["name"]: entry["status"] for entry in payload["tests"]}
            self.assertEqual(harness_status.get("broker_plugin_isolation"), "pass")
            worktree_repo = Path(payload["repo"])
            self.assertEqual(
                worktree_repo.parent,
                clone.parent,
                f"pushed-bytes worktree must be a direct sibling of the real repo, got {worktree_repo}",
            )
            leftovers = [path for path in clone.parent.iterdir() if path.name.startswith(".skipi-guard")]
            self.assertEqual(leftovers, [], "harness worktree must be cleaned up after the run")
            worktrees = self.run_git(clone, "worktree", "list", "--porcelain").stdout
            self.assertEqual(
                worktrees.count("worktree "),
                1,
                "temporary pushed-bytes worktree must be deregistered after the run",
            )

    def test_run_harness_worktree_is_cleaned_up_after_harness_failure(self) -> None:
        """Fail-closed path keeps the parent directory clean: a failing harness
        must not leave `.skipi-guard-*` worktree litter beside the real repo."""
        with tempfile.TemporaryDirectory(prefix="skipi-guard-sibling-cleanup-") as tmp:
            root = Path(tmp)
            seed = dict(BROKER_SEED)
            seed["tests/broker_plugin_isolation_harness.mjs"] = "process.exit(1);\n"
            _origin, clone = self.make_fixture(root, seed)
            branch_sha = self.make_branch(
                clone, "host-change", "plugin-host change", {"dist/index.html": "<main>v2</main>\n"}
            )
            proc = self.run_guard(
                "pre-push-ref",
                "--home",
                "broker",
                "--repo",
                str(clone),
                "--local-ref",
                "refs/heads/host-change",
                "--local-sha",
                branch_sha,
                "--remote-ref",
                "refs/heads/host-change",
                "--remote-sha",
                ZERO_SHA,
            )
            self.assertNotEqual(proc.returncode, 0, "failing harness must fail the guard")
            leftovers = [path for path in clone.parent.iterdir() if path.name.startswith(".skipi-guard")]
            self.assertEqual(leftovers, [], "harness worktree must be cleaned up on failure too")
            worktrees = self.run_git(clone, "worktree", "list", "--porcelain").stdout
            self.assertEqual(worktrees.count("worktree "), 1)

    # --- canon render / install / drift check ------------------------------

    def test_render_is_deterministic_and_fully_parameterized(self) -> None:
        for home in HOOKED_HOMES:
            first = self.run_guard("hooks", "render", "--home", home)
            second = self.run_guard("hooks", "render", "--home", home)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(first.stdout, second.stdout, f"{home}: render must be deterministic")
            self.assertIn(f'SKIPI_GUARD_HOME="{home}"', first.stdout)
            self.assertIn(str(GUARD), first.stdout)
            self.assertNotIn("__SKIPI_GUARD_", first.stdout, "unrendered placeholder left")
            # Decision (б): stdin is authoritative, no env base/head overrides.
            self.assertNotIn("SKIPI_GUARD_BASE", first.stdout)
            self.assertNotIn("SKIPI_GUARD_HEAD", first.stdout)

    def test_render_honors_guard_bin_override(self) -> None:
        proc = self.run_guard("hooks", "render", "--home", "broker", "--guard-bin", "/custom/skipi-guard")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('SKIPI_GUARD_BIN="/custom/skipi-guard"', proc.stdout)

    def test_render_unknown_home_fails(self) -> None:
        proc = self.run_guard("hooks", "render", "--home", "no-such-home")
        self.assertNotEqual(proc.returncode, 0)

    def test_install_writes_executable_render(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-install-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)
            hook = self.install_canon_hook("broker", clone)
            self.assertTrue(os.access(hook, os.X_OK), "installed hook must be executable")
            rendered = self.run_guard("hooks", "render", "--home", "broker").stdout
            self.assertEqual(hook.read_text(encoding="utf-8"), rendered, "deployed must equal render(canon)")

    def test_check_detects_match_drift_and_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-check-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)

            missing = self.run_guard("hooks", "check", "--home", "broker", "--repo", str(clone))
            self.assertNotEqual(missing.returncode, 0, "missing hook must be reported as non-zero")

            hook = self.install_canon_hook("broker", clone)
            match = self.run_guard("hooks", "check", "--home", "broker", "--repo", str(clone))
            self.assertEqual(match.returncode, 0, match.stdout + match.stderr)

            with hook.open("a", encoding="utf-8") as handle:
                handle.write("# drifted\n")
            drift = self.run_guard("hooks", "check", "--home", "broker", "--repo", str(clone))
            self.assertNotEqual(drift.returncode, 0, "byte drift must be reported as non-zero")

    # --- verify --auto-task (CI parity, decision г) --------------------------

    def test_verify_auto_task_resolves_repo_meta(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-auto-task-") as tmp:
            root = Path(tmp)
            _origin, clone = self.make_fixture(root, BROKER_SEED)
            self.commit_files(clone, "meta change", {"AGENTS.md": "# fixture agents\n"})
            result_json = root / "result.json"
            proc = self.run_guard(
                "verify",
                "--home",
                "broker",
                "--auto-task",
                "--repo",
                str(clone),
                "--base",
                "origin/main",
                "--head",
                "HEAD",
                "--json",
                str(result_json),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            with result_json.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["task"], "repo-meta")
            self.assertEqual(payload["status"], "pass")

    def test_verify_requires_exactly_one_task_source(self) -> None:
        neither = self.run_guard("verify", "--home", "broker", "--repo", str(ROOT))
        self.assertNotEqual(neither.returncode, 0)
        both = self.run_guard(
            "verify", "--home", "broker", "--task", "plugin-host", "--auto-task", "--repo", str(ROOT)
        )
        self.assertNotEqual(both.returncode, 0)


if __name__ == "__main__":
    unittest.main()
