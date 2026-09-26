"""C3b2 declarative route contract, real CLI/hook, isolated recording stubs.

These tests prove dispatch and enforcement, not the future product harness.
No auth/tenant guard is changed. The node stub only records invocation, checks
that the invoked local fixture exists, and returns a requested failure.
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
GUARD = ROOT / 'bin/skipi-guard'
CONFIG = ROOT / 'configs/homes/crewing.json'
LOADER = SourceFileLoader('guard_crewing_c3b2', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = 'crewing-c3b2'
FILES = ['dist/index.html', 'src-tauri/src/crewing_intake.rs', 'src-tauri/src/lib.rs',
         'tests/crewing_c3b2_candidate_harness.mjs', 'docs/crewing-pilot-c3b2/WORKLOG.md',
         '.github/workflows/skipi-guard.yml']
COMMANDS = [
    ('crewing_plugin_isolation', 'node tests/crewing_plugin_isolation_harness.mjs'),
    ('shared_host_runtime_isolation', 'node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs'),
    ('crewing_presence_contract', 'node tests/crewing_presence_contract_harness.mjs'),
    ('crewing_crew_flow_demo', 'node tests/crewing_crew_flow_demo_harness.mjs'),
    ('crewing_c3b1_pilot', 'node tests/crewing_c3b1_pilot_harness.mjs'),
    ('crewing_csp_inline_handlers', 'node tests/csp_inline_handlers_harness.mjs'),
    ('crewing_c3b2_candidate', 'node ' + FILES[3]),
]
EXTRAS = ['src-tauri/src/other.rs', 'server/intake.rs', 'src-tauri/Cargo.toml',
          'src-tauri/Cargo.lock', 'src-tauri/tauri.conf.json', 'keys/signing.pem',
          'presence-manifest.json', 'tests/other.mjs', 'docs/other.md',
          'dist/latest.json', '.github/workflows/other.yml',
          'tests/crewing_c3b1_pilot_harness.mjs', 'docs/crewing-pilot-c3b1/WORKLOG.md']
OLD_CONFIG_HASH = '5b99a9088dc66c9b5970d6fa9b294448dbb48810fa2304a65b3288cda3d2c1e3'


LATER_TASKS = ('crewing-k2-modules', 'crewing-k21-single-screen')


def previous_config(config):
    old = copy.deepcopy(config)
    # Routes merged after C3b2 are frozen by their own oracles
    # (test_crewing_k2_modules_route.py). Subtract them too, so this hash keeps
    # pinning the exact pre-C3b2 config instead of drifting with every addition.
    drop = (TASK, *LATER_TASKS)
    old['task_routing'] = [r for r in old['task_routing'] if r['task'] not in drop]
    for section in ('allowed_file_patterns', 'harness_commands'):
        for task in drop:
            old[section].pop(task, None)
    return old


class CrewingC3b2RouteTests(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text())

    def test_exact_ceiling_checks_and_order(self):
        config = self.config()
        route = [r for r in config['task_routing'] if r['task'] == TASK]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]['when_all_files_in'], FILES)
        self.assertEqual(route[0]['require_any_of'], FILES[3:5])
        self.assertNotIn('require_all_of', route[0])
        self.assertEqual(config['allowed_file_patterns'][TASK], FILES)
        self.assertEqual([(c['name'], c['command']) for c in MODULE.configured_harnesses(config, TASK)], COMMANDS)
        self.assertEqual(config['harness_commands'][TASK][:6], config['harness_commands']['crewing-c3b1'])
        self.assertFalse(MODULE.is_release_task(config, TASK))
        self.assertEqual([r['task'] for r in config['task_routing'][:4]],
                         ['security-escaping-191', 'crewing-c3b1', 'crewing-c3b1-metadata', TASK])

    def test_entire_old_parsed_config_and_legacy_routes_preserved(self):
        config = self.config()
        old = previous_config(config)
        self.assertEqual(hashlib.sha256(json.dumps(old, sort_keys=True, separators=(',', ':')).encode()).hexdigest(), OLD_CONFIG_HASH)
        samples = [[], [FILES[0]], [FILES[5]], FILES[:3]]
        samples += [r['when_all_files_in'] for r in old['task_routing']]
        for files in samples:
            with self.subTest(files=files):
                self.assertEqual(MODULE.resolve_task(config, files), MODULE.resolve_task(old, files))
                task = MODULE.resolve_task(old, files)['task']
                self.assertEqual(MODULE.configured_harnesses(config, task), MODULE.configured_harnesses(old, task))
                self.assertEqual(MODULE.scope_check_for_task(config, task, files), MODULE.scope_check_for_task(old, task, files))

    def test_all_64_subsets_and_forbidden_extras(self):
        config = self.config()
        for size in range(7):
            for files in itertools.combinations(FILES, size):
                with self.subTest(files=files):
                    self.assertEqual(MODULE.resolve_task(config, list(files))['task'] == TASK,
                                     any(p in files for p in FILES[3:5]))
        for extra in EXTRAS:
            with self.subTest(extra=extra):
                self.assertNotEqual(MODULE.resolve_task(config, FILES + [extra])['task'], TASK)
                self.assertIn(extra, MODULE.scope_check_for_task(config, TASK, FILES + [extra])['scope_violations'])

    @contextmanager
    def fixture(self, files, *, incremental=False, fail=None, missing=False, deleted=False):
        scratch = ROOT / 'scratchpad/guard-crewing-c3b2-20260922'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='fixture-', dir=scratch) as tmp:
            root = Path(tmp)
            repo = root / 'repo'
            repo.mkdir()
            env = os.environ.copy()
            env.pop('SKIPI_GUARD_OVERRIDE_TOKEN', None)
            env['TMPDIR'] = str(root)
            def git(*args):
                return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                      text=True, capture_output=True, env=env).stdout.strip()
            def write(path, value):
                dest = repo / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(value)
            git('init', '-q', '-b', 'main')
            git('config', 'user.name', 'C3b2 isolated fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            for path in FILES + [cmd.split(' ', 1)[1] for _, cmd in COMMANDS if not cmd.split(' ', 1)[1].startswith('/')]:
                if path != FILES[3] or not missing:
                    write(path, 'synthetic baseline fixture; not product acceptance\n')
            git('add', '-A')
            git('commit', '-qm', 'synthetic published baseline')
            main = git('rev-parse', 'HEAD')
            git('update-ref', 'refs/remotes/origin/main', main)
            git('checkout', '-qb', 'candidate')
            if incremental:
                write(FILES[4], 'Previous candidate step: synthetic controls prepared; runtime remains unknown.\n')
                git('add', FILES[4])
                git('commit', '-qm', 'previous published candidate step')
            base = git('rev-parse', 'HEAD')
            for path in files:
                if path != FILES[3] or not missing:
                    write(path, 'Candidate step: facts and decision control cases recorded; synthetic only.\n')
            if deleted:
                git('rm', FILES[3])
            git('add', '-A')
            git('commit', '--allow-empty', '-qm', 'candidate increment')
            head = git('rev-parse', 'HEAD')
            calls = root / 'calls.jsonl'
            stubbin = root / 'stubbin'
            stubbin.mkdir()
            node = stubbin / 'node'
            node.write_text('#!/usr/bin/env python3\nimport json,sys,subprocess\nfrom pathlib import Path\n'
                f"with Path({str(calls)!r}).open('a') as out: out.write(json.dumps({{'args':sys.argv[1:],'cwd':str(Path.cwd()),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}})+'\\n')\n"
                "path=Path(sys.argv[1])\n"
                "if not path.is_absolute() and not path.is_file(): sys.exit(83)\n"
                f"sys.exit(19 if sys.argv[1:] == {[fail] if fail else []!r} else 0)\n")
            node.chmod(0o755)
            env['PATH'] = str(stubbin) + os.pathsep + env['PATH']
            output = root / 'hook.json'
            adapter = root / 'capture-guard'
            adapter.write_text('#!/usr/bin/env python3\nimport os,sys\n'
                f"os.execv({str(GUARD)!r}, [{str(GUARD)!r}, *sys.argv[1:], '--json', {str(output)!r}])\n")
            adapter.chmod(0o755)
            hook = root / 'pre-push'
            hook.write_text(MODULE.render_hook('crewing', str(adapter)))
            yield dict(repo=repo, root=root, env=env, git=git, main=main, base=base, head=head,
                       calls=calls, hook=hook, output=output, incremental=incremental)

    def invoke(self, f, hook=False, explicit=False):
        f['calls'].unlink(missing_ok=True)
        if hook:
            f['git']('checkout', '-q', 'main')
            remote = f['base'] if f['incremental'] else '0' * 40
            stdin = f"refs/heads/candidate {f['head']} refs/heads/candidate {remote}\n"
            proc = subprocess.run(['bash', str(f['hook'])], input=stdin, cwd=f['repo'],
                                  text=True, capture_output=True, env=f['env'])
            report = json.loads(f['output'].read_text())
        else:
            f['git']('checkout', '-q', 'candidate')
            output = f['root'] / 'ci.json'
            args = [str(GUARD), 'verify', '--home', 'crewing', '--repo', str(f['repo']),
                    '--base', f['base'], '--head', f['head'], '--run-harness', '--json', str(output)]
            args += ['--task', TASK] if explicit else ['--auto-task']
            proc = subprocess.run(args, text=True, capture_output=True, env=f['env'])
            report = json.loads(output.read_text())
        return proc, report

    def assert_seven(self, f, report, hook):
        self.assertEqual(report['task'], TASK)
        self.assertEqual(report['effective_tasks'], [TASK])
        self.assertFalse(report['override_present'])
        self.assertEqual([(t['name'], t['command']) for t in report['tests']], COMMANDS)
        calls = [json.loads(line) for line in f['calls'].read_text().splitlines()]
        self.assertEqual([c['args'] for c in calls], [[cmd.split(' ', 1)[1]] for _, cmd in COMMANDS])
        self.assertTrue(all(c['head'] == f['head'] for c in calls))
        if hook:
            self.assertTrue(all(Path(c['cwd']) != f['repo'] for c in calls))
            self.assertEqual(report['push_ref']['local_sha'], f['head'])
            self.assertEqual(report['push_ref']['remote_sha'], f['base'] if f['incremental'] else '0' * 40)
        self.assertEqual(f['git']('worktree', 'list', '--porcelain').count('worktree '), 1)

    def test_supported_shapes_cli_and_hook_aggregate_and_incremental(self):
        shapes = [FILES, [FILES[3]], [FILES[4]], FILES[4:], [FILES[0], FILES[3]], [FILES[1], FILES[4]]]
        for files, incremental in itertools.product(shapes, (False, True)):
            with self.subTest(files=files, incremental=incremental), self.fixture(files, incremental=incremental) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(proc.returncode, 0, report)
                    self.assertEqual(report['changed_files'], sorted(files))
                    self.assertEqual(report['errors'], [])
                    self.assert_seven(f, report, hook)

    def test_each_of_seven_failures_rejects_cli_and_hook_both_ranges(self):
        for (name, command), incremental in itertools.product(COMMANDS, (False, True)):
            with self.subTest(name=name, incremental=incremental), self.fixture(FILES, incremental=incremental, fail=command.split(' ', 1)[1]) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assert_seven(f, report, hook)
                    self.assertEqual([t['name'] for t in report['tests'] if t['status'] == 'fail'], [name])
                    self.assertTrue(any(e.startswith('harness failed: ' + name) for e in report['errors']))

    def test_missing_and_deleted_new_harness_fail_both_ranges(self):
        for mode, incremental in itertools.product(('missing', 'deleted'), (False, True)):
            with self.subTest(mode=mode, incremental=incremental), self.fixture([FILES[4]], incremental=incremental, **{mode: True}) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assert_seven(f, report, hook)
                    self.assertEqual([t['name'] for t in report['tests'] if t['status'] == 'fail'], ['crewing_c3b2_candidate'])

    def test_forbidden_extras_rejected_real_cli_and_hook(self):
        for extra, incremental in itertools.product(EXTRAS, (False, True)):
            with self.subTest(extra=extra, incremental=incremental), self.fixture(FILES + [extra], incremental=incremental) as f:
                for hook, explicit in ((False, False), (False, True), (True, False)):
                    proc, report = self.invoke(f, hook, explicit)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assertFalse(report['override_present'])
                    if explicit:
                        self.assertIn(extra, report['scope_violations'])
                    else:
                        self.assertNotEqual(report['task'], TASK)

    def test_pin_only_and_ambiguous_shared_code_keep_old_real_behavior(self):
        # A pure shared-code push is NOT recognized as C3b2. Product execution
        # must STOP rather than fake a journal touch or manipulate base/env.
        old = previous_config(self.config())
        for files, incremental in itertools.product(([FILES[5]], FILES[:3]), (False, True)):
            with self.subTest(files=files, incremental=incremental), self.fixture(files, incremental=incremental) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(report['task'], MODULE.resolve_task(old, files)['task'])
                    self.assertNotEqual(report['task'], TASK)
                    # The existing hook auto-bootstrap for pure guard workflow
                    # pins is retained; plain verify has no such bootstrap.
                    bootstrap = hook and files == [FILES[5]]
                    self.assertEqual(proc.returncode, 0 if bootstrap else 1, report)
                    self.assertEqual(report['override_present'], bootstrap)
                    self.assertEqual(report['auto_bootstrap_override'], bootstrap)


if __name__ == '__main__':
    unittest.main()
