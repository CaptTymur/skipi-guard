"""Bounded C3b1 route: real Git/CLI/hook entry points, stubbed harness effects.

The six paths are a ceiling, not a required exact set. Synthetic node records
every requested command and checks the pushed bytes; no product hooks are
installed, network requests made, or product files changed by these tests.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin/skipi-guard"
CONFIG = ROOT / "configs/homes/crewing.json"
LOADER = SourceFileLoader("guard_crewing_c3b1", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = "crewing-c3b1"
JOURNAL_TASK = "crewing-c3b1-metadata"
# Additive routes merged after C3b1; each is frozen by its own oracle.
LATER_TASKS = ("crewing-c3b2", "crewing-k2-modules")
FILES = [
    "dist/index.html",
    "src-tauri/src/crewing_intake.rs",
    "src-tauri/src/lib.rs",
    "tests/crewing_c3b1_pilot_harness.mjs",
    "docs/crewing-pilot-c3b1/WORKLOG.md",
    ".github/workflows/skipi-guard.yml",
]
REQUIRED = [FILES[1], FILES[3]]
ANY = [FILES[0], FILES[2]]
EXTRAS = [
    "src-tauri/src/other.rs", "server/intake.rs", "src-tauri/Cargo.toml",
    "keys/signing.pem", "presence-manifest.json", "tests/other.mjs",
    "docs/other.md", "dist/latest.json",
]
COMMANDS = [
    ("crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"),
    ("shared_host_runtime_isolation", "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"),
    ("crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"),
    ("crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"),
    ("crewing_c3b1_pilot", "node tests/crewing_c3b1_pilot_harness.mjs"),
    ("crewing_csp_inline_handlers", "node tests/csp_inline_handlers_harness.mjs"),
]


class CrewingC3b1RouteTests(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text())

    def test_candidate_routes_and_preserves_all_six_checks(self):
        config = self.config()
        for files in (FILES[:5], FILES):
            self.assertEqual(MODULE.resolve_task(config, files)["task"], TASK)
        self.assertEqual(config["allowed_file_patterns"][TASK], FILES)
        checks = MODULE.configured_harnesses(config, TASK)
        self.assertEqual([(c["name"], c["command"]) for c in checks], COMMANDS)
        self.assertEqual(checks[:4], config["harness_commands"]["plugin-host"])
        self.assertFalse(MODULE.is_release_task(config, TASK))

    def test_old_config_is_unchanged_after_removing_only_new_task(self):
        config = self.config()
        # C3b2 and the later K2 route are independently frozen by
        # test_crewing_c3b2_route / test_crewing_k2_modules_route. Strip only
        # those additive tasks for the unchanged historical C3b1 hash oracle.
        config["task_routing"] = [r for r in config["task_routing"] if r["task"] not in LATER_TASKS]
        for section in ("allowed_file_patterns", "harness_commands"):
            for task in LATER_TASKS:
                config[section].pop(task, None)
        old = copy.deepcopy(config)
        old["task_routing"] = [r for r in old["task_routing"] if r["task"] not in (TASK, JOURNAL_TASK)]
        for section in ("allowed_file_patterns", "harness_commands"):
            old[section].pop(TASK, None)
            old[section].pop(JOURNAL_TASK, None)
        self.assertEqual(hashlib.sha256(json.dumps(old, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         "4f53d45cf2bfc8e08b6d172f55e97be57daa736531d2c6d9444bdfc3a47938cc")
        old_task = MODULE.resolve_task(old, FILES[:5])["task"]
        self.assertEqual(old_task, "plugin-host")
        self.assertTrue(MODULE.scope_check_for_task(old, old_task, FILES[:5],
                            MODULE.effective_allowed_patterns(old, old_task, []))["scope_violations"])
        # Preserve the resolver result for every legacy rule's declared surface,
        # as well as the high frequency index-only/default/settings/release sets.
        samples = [[], [FILES[0]], [FILES[5]],
                   ["dist/index.html", "dist/SETTINGS_VERSION", "dist/skipi-settings.js"],
                   ["dist/index.html", "src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"]]
        samples += [r["when_all_files_in"] for r in old["task_routing"]]
        for files in samples:
            with self.subTest(files=files):
                self.assertEqual(MODULE.resolve_task(config, files), MODULE.resolve_task(old, files))

    def test_every_subset_has_precise_required_and_any_semantics(self):
        config = self.config()
        for count in range(7):
            for files in itertools.combinations(FILES, count):
                with self.subTest(files=files):
                    expected = all(p in files for p in REQUIRED) and any(p in files for p in ANY)
                    self.assertEqual(MODULE.resolve_task(config, list(files))["task"] == TASK, expected)

    @contextmanager
    def journal_fixture(self, missing_pilot=False, pin=False, fail_command=None):
        # The published product already contains all source files. Only the
        # journal changes in the next push (nonzero remote SHA).
        with self.fixture(FILES[:5]) as f:
            repo, root, env, git, base, old_head, calls, hook, result = f
            if missing_pilot:
                git("rm", FILES[3])
                git("commit", "-qm", "base without pilot")
                old_head = git("rev-parse", "HEAD")
            (repo / FILES[4]).write_text("incremental journal update\n")
            git("add", FILES[4])
            if pin:
                workflow = repo / FILES[5]
                workflow.parent.mkdir(parents=True, exist_ok=True)
                workflow.write_text("guard pin update\n")
                git("add", FILES[5])
            git("commit", "-qm", "journal update")
            head = git("rev-parse", "HEAD")
            # Check the invoked local script, rather than treating harnesses
            # as always green. Other checks are stubbed without side effects.
            (root / "stubbin/node").write_text(
                "#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
                f"with Path({str(calls)!r}).open('a') as out: out.write(json.dumps({{'args':sys.argv[1:],'cwd':str(Path.cwd())}})+'\\n')\n"
                f"sys.exit(83 if sys.argv[1:] == [{FILES[3]!r}] and not Path({FILES[3]!r}).is_file() else (19 if sys.argv[1:] == {[fail_command] if fail_command else []!r} else 0))\n")
            yield repo, root, env, git, old_head, head, calls, hook, result

    def test_journal_incremental_hook_and_ci_execute_all_six_checks(self):
        for pin in (False, True):
            with self.subTest(pin=pin), self.journal_fixture(pin=pin) as f:
                ci_proc, ci = self.invoke_ci(f, run=True)
                self.assertEqual(ci_proc.returncode, 0, ci)
                self.assert_calls(f)
                f[6].unlink()
                hook_proc, hook = self.invoke_hook(f, incremental=True)
                self.assertEqual(hook_proc.returncode, 0, hook)
                self.assert_calls(f)
                for report in (ci, hook):
                    self.assertEqual(report["changed_files"], sorted([FILES[4], FILES[5]] if pin else [FILES[4]]))
                    self.assertEqual(report["task"], JOURNAL_TASK)
                    self.assertEqual(report["effective_tasks"], [JOURNAL_TASK])
                    self.assertFalse(report["override_present"])
                    self.assertEqual(report["errors"], [])
                    self.assertEqual([(t["name"], t["command"]) for t in report["tests"]], COMMANDS)
                self.assertEqual(hook["push_ref"]["remote_sha"], f[4])
                self.assertEqual(hook["push_ref"]["local_sha"], f[5])

    def test_journal_missing_pilot_fails_instead_of_false_green(self):
        with self.journal_fixture(missing_pilot=True) as f:
            for invoke in (lambda: self.invoke_ci(f, run=True),
                           lambda: self.invoke_hook(f, incremental=True)):
                proc, report = invoke()
                self.assertEqual(proc.returncode, 1, report)
                self.assertEqual(report["task"], JOURNAL_TASK)
                self.assert_calls(f)
                f[6].unlink()
                self.assertEqual([t["name"] for t in report["tests"] if t["status"] == "fail"],
                                 ["crewing_c3b1_pilot"])

    def test_journal_each_of_six_failures_rejects_incremental_hook_and_ci(self):
        for name, command in COMMANDS:
            with self.subTest(name=name), self.journal_fixture(fail_command=command.split(" ", 1)[1]) as f:
                for invoke in (lambda: self.invoke_ci(f, run=True),
                               lambda: self.invoke_hook(f, incremental=True)):
                    proc, report = invoke()
                    self.assertEqual(proc.returncode, 1, report)
                    self.assertEqual(report["task"], JOURNAL_TASK)
                    self.assert_calls(f)
                    f[6].unlink()
                    self.assertEqual([t["name"] for t in report["tests"] if t["status"] == "fail"], [name])

    def test_journal_exact_scope_and_all_checks(self):
        config = self.config()
        self.assertEqual(config["allowed_file_patterns"][JOURNAL_TASK], FILES[4:])
        self.assertEqual(config["harness_commands"][JOURNAL_TASK], config["harness_commands"][TASK])
        self.assertEqual(MODULE.resolve_task(config, [FILES[4]])["task"], JOURNAL_TASK)
        self.assertNotEqual(MODULE.resolve_task(config, [])["task"], JOURNAL_TASK)
        self.assertEqual(MODULE.resolve_task(config, FILES[4:])["task"], JOURNAL_TASK)
        self.assertNotEqual(MODULE.resolve_task(config, [FILES[5]])["task"], JOURNAL_TASK)
        for extra in [*EXTRAS, *FILES[:4], FILES[4] + ".bak"]:
            with self.subTest(extra=extra):
                self.assertNotEqual(MODULE.resolve_task(config, [FILES[4], extra])["task"], JOURNAL_TASK)
                self.assertIn(extra, MODULE.scope_check_for_task(config, JOURNAL_TASK,
                              [FILES[4], extra])["scope_violations"])

    def test_journal_real_cli_rejects_other_docs_native_and_workflows(self):
        for extra in ["docs/other.md", "src-tauri/src/other.rs", ".github/workflows/other.yml",
                      FILES[1], FILES[3], FILES[0]]:
            for explicit in (False, JOURNAL_TASK):
                with self.subTest(extra=extra, explicit=explicit), self.fixture([FILES[4], extra]) as f:
                    proc, report = self.invoke_ci(f, explicit=explicit)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assertFalse(report["override_present"])
                    if explicit:
                        self.assertIn(extra, report["scope_violations"])
                    else:
                        self.assertNotEqual(report["task"], JOURNAL_TASK)

    def test_journal_addition_preserves_entire_previous_config(self):
        config = self.config()
        # Keep the historical hash oracle unchanged after the additive C3b2/K2.
        config["task_routing"] = [r for r in config["task_routing"] if r["task"] not in LATER_TASKS]
        for section in ("allowed_file_patterns", "harness_commands"):
            for task in LATER_TASKS:
                config[section].pop(task, None)
        config["task_routing"] = [r for r in config["task_routing"] if r["task"] != JOURNAL_TASK]
        for section in ("allowed_file_patterns", "harness_commands"):
            config[section].pop(JOURNAL_TASK, None)
        self.assertEqual(hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         "fd7fc6f187cfb85a41c7a34a93ac17ae27a7970136d2dd13696464249eaf310c")

    @contextmanager
    def fixture(self, files, fail_command=None):
        scratch = ROOT / "scratchpad/guard-crewing-c3b1-journal-20260922"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fixture-", dir=scratch) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            env = os.environ.copy()
            env.pop("SKIPI_GUARD_OVERRIDE_TOKEN", None)
            def git(*args):
                return subprocess.run(["git", "-C", str(repo), *args], check=True,
                                      text=True, capture_output=True, env=env).stdout.strip()
            git("init", "-q", "-b", "main")
            git("config", "user.name", "C3b1 fixture")
            git("config", "user.email", "guard@example.invalid")
            (repo / "seed.txt").write_text("seed\n")
            git("add", "seed.txt")
            git("commit", "-qm", "seed")
            base = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/origin/main", base)
            git("checkout", "-qb", "candidate")
            for relative in files:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("candidate bytes\n")
            git("add", "-A")
            git("commit", "--allow-empty", "-qm", "candidate")
            head = git("rev-parse", "HEAD")
            # Stub the only harness effect boundary. Record cwd and arguments;
            # fail if pre-push accidentally executes the main checkout bytes.
            stubbin = root / "stubbin"
            stubbin.mkdir()
            calls = root / "calls.jsonl"
            node = stubbin / "node"
            node.write_text("#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
                f"with Path({str(calls)!r}).open('a') as f: f.write(json.dumps({{'args':sys.argv[1:],'cwd':str(Path.cwd())}})+'\\n')\n"
                f"required = {REQUIRED!r}\n"
                "if not all((Path.cwd()/p).is_file() for p in required): sys.exit(83)\n"
                f"sys.exit(19 if sys.argv[1:] == {[fail_command] if fail_command else []!r} else 0)\n")
            node.chmod(0o755)
            env["PATH"] = str(stubbin) + os.pathsep + env["PATH"]
            # The capture adapter changes only the output location, avoiding
            # the canonical CLI's fixed /tmp JSON during a synthetic hook run.
            result = root / "hook.json"
            adapter = root / "capture-guard"
            adapter.write_text("#!/usr/bin/env python3\nimport os,sys\n"
                f"os.execv({str(GUARD)!r}, [{str(GUARD)!r}, *sys.argv[1:], '--json', {str(result)!r}])\n")
            adapter.chmod(0o755)
            hook = root / "pre-push"
            hook.write_text(MODULE.render_hook("crewing", str(adapter)))
            yield repo, root, env, git, base, head, calls, hook, result

    def invoke_ci(self, fixture, explicit=False, run=False):
        repo, root, env, git, base, head, calls, hook, result = fixture
        output = root / "ci.json"
        cmd = [str(GUARD), "verify", "--home", "crewing", "--repo", str(repo),
               "--base", base, "--head", head, "--json", str(output)]
        cmd += ["--task", explicit if isinstance(explicit, str) else TASK] if explicit else ["--auto-task"]
        if run:
            cmd.append("--run-harness")
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
        return proc, json.loads(output.read_text())

    def invoke_hook(self, fixture, incremental=False):
        repo, root, env, git, base, head, calls, hook, result = fixture
        git("checkout", "-q", "main")
        remote_sha = base if incremental else "0" * 40
        stdin = f"refs/heads/candidate {head} refs/heads/candidate {remote_sha}\n"
        proc = subprocess.run(["bash", str(hook)], input=stdin, cwd=repo,
                              text=True, capture_output=True, env=env)
        return proc, json.loads(result.read_text())

    def assert_calls(self, fixture):
        calls = [json.loads(line) for line in fixture[6].read_text().splitlines()]
        self.assertEqual([c["args"] for c in calls], [[cmd.split(" ", 1)[1]] for _, cmd in COMMANDS])
        return calls

    def test_real_cli_each_missing_required_or_any_does_not_route(self):
        for missing in ([REQUIRED[0]], [REQUIRED[1]], ANY):
            with self.subTest(missing=missing), self.fixture([p for p in FILES if p not in missing]) as f:
                proc, report = self.invoke_ci(f)
                self.assertNotEqual(report["task"], TASK)
                self.assertEqual(proc.returncode, 1, report)

    def test_real_cli_unrelated_native_server_release_protected_extras_stay_red(self):
        for extra in EXTRAS:
            for explicit in (False, True):
                with self.subTest(extra=extra, explicit=explicit), self.fixture(FILES[:5] + [extra]) as f:
                    proc, report = self.invoke_ci(f, explicit=explicit)
                    self.assertEqual(proc.returncode, 1, report)
                    if extra == "presence-manifest.json" and not explicit:
                        # Legacy plugin-host scope includes this manifest;
                        # its independent protected-path gate must still stop it.
                        self.assertIn("protected path touch requires --override-protected", report["errors"])
                    else:
                        self.assertIn(extra, report["scope_violations"])
                    self.assertFalse(report["override_present"])
                    if not explicit:
                        self.assertNotEqual(report["task"], TASK)

    def test_hook_stdin_and_ci_same_five_and_six_paths_run_all_checks(self):
        for files in (FILES[:5], FILES):
            with self.subTest(files=files), self.fixture(files) as f:
                ci_proc, ci = self.invoke_ci(f, run=True)
                self.assertEqual(ci_proc.returncode, 0, ci)
                self.assert_calls(f)
                f[6].unlink()
                hook_proc, hook = self.invoke_hook(f)
                self.assertEqual(hook_proc.returncode, 0, hook)
                calls = self.assert_calls(f)
                self.assertTrue(all(Path(c["cwd"]) != f[0] for c in calls))
                for report in (ci, hook):
                    self.assertEqual(report["changed_files"], sorted(files))
                    self.assertEqual(report["task"], TASK)
                    self.assertEqual(report["effective_tasks"], [TASK])
                    self.assertEqual(report["errors"], [])
                    self.assertFalse(report["override_present"])
                    self.assertEqual([(t["name"], t["command"]) for t in report["tests"]], COMMANDS)
                    self.assertTrue(all(t["status"] == "pass" for t in report["tests"]))
                self.assertEqual(hook["push_ref"]["local_sha"], f[5])
                self.assertEqual(len(f[3]("worktree", "list", "--porcelain").split("worktree ")) - 1, 1)

    def test_each_of_six_check_failures_rejects_ci_and_hook(self):
        for name, command in COMMANDS:
            with self.subTest(name=name), self.fixture(FILES[:5], command.split(" ", 1)[1]) as f:
                for invoke in (lambda: self.invoke_ci(f, run=True), lambda: self.invoke_hook(f)):
                    proc, report = invoke()
                    self.assertEqual(proc.returncode, 1, report)
                    self.assert_calls(f)
                    f[6].unlink()
                    self.assertEqual([t["name"] for t in report["tests"] if t["status"] == "fail"], [name])
                    self.assertTrue(any(e.startswith("harness failed: " + name) for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
