"""K2 declarative route contract, real CLI/hook, isolated recording stubs.

The route is additive: it is inserted AFTER `crewing-c3b2` (first match wins),
so every diff C3b2 already owns keeps routing to C3b2, and K2 only claims
diffs that touch the Crew Flow / module-composition surface. These tests prove
dispatch, ceiling and enforcement; they are not the product harness. No
protection, override token or protected path is changed or relaxed.
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
LOADER = SourceFileLoader('guard_crewing_k2_modules', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
TASK = 'crewing-k2-modules'
PREVIOUS_TASK = 'crewing-c3b2'
FILES = ['dist/index.html',
         'tests/crewing_crew_flow_demo_harness.mjs',
         'tests/crewing_plugin_isolation_harness.mjs',
         'tests/crewing_c3b1_pilot_harness.mjs',
         'tests/crewing_c3b2_candidate_harness.mjs',
         'tests/crewing_presence_contract_harness.mjs',
         'docs/crewing-pilot-c3b2/WORKLOG.md',
         '.github/workflows/skipi-guard.yml']
REQUIRE_ANY = [FILES[6], FILES[1]]
COMMANDS = [
    ('crewing_plugin_isolation', 'node tests/crewing_plugin_isolation_harness.mjs'),
    ('shared_host_runtime_isolation', 'node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs'),
    ('crewing_presence_contract', 'node tests/crewing_presence_contract_harness.mjs'),
    ('crewing_crew_flow_demo', 'node tests/crewing_crew_flow_demo_harness.mjs'),
    ('crewing_c3b1_pilot', 'node tests/crewing_c3b1_pilot_harness.mjs'),
    ('crewing_csp_inline_handlers', 'node tests/csp_inline_handlers_harness.mjs'),
    ('crewing_c3b2_candidate', 'node tests/crewing_c3b2_candidate_harness.mjs'),
    ('crewing_mailbox_contract', 'node tests/crewing_mailbox_contract_harness.mjs'),
    ('crewing_mail_cv_intake_demo', 'node tests/crewing_mail_cv_intake_demo_harness.mjs'),
    ('crewing_compliance_manual_flow', 'node tests/crewing_compliance_manual_flow_harness.mjs'),
    ('crewing_theme_default', 'node tests/crewing_theme_default_harness.mjs'),
    ('settings5_preview_gated', 'node tests/settings5_preview_gated_harness.mjs'),
    ('trial_activate_unconnected', 'node tests/trial_activate_unconnected_harness.mjs'),
    ('trial_gate_wired', 'node tests/trial_gate_wired_harness.mjs'),
]
# presence-manifest.json stays out of the route on purpose: it is protected and
# only PR-P may touch it. Rust, Cargo, signing keys and foreign test/doc/workflow
# files are outside the declared ceiling as well.
EXTRAS = ['presence-manifest.json', 'src-tauri/src/lib.rs', 'src-tauri/Cargo.toml',
          'keys/signing.pem', 'tests/other.mjs', 'docs/other.md',
          '.github/workflows/other.yml']
# sha256 of configs/homes/crewing.json at guard main 83f5dad8 (pre-K2 bytes).
OLD_CONFIG_HASH = '7edf6021057702e0dd73ddf803e1781f0e190f6d3526a13b5fdd0b54fbfe5ffd'
# Exact anchors of the three additive text blocks; removing them must restore
# the pre-K2 file byte for byte (proves the change adds and never edits).
BLOCKS = (
    ('    {\n      "name": "crewing K2 Crew Flow queue + module composition routing'
     ' (owner654/658, 2026-09-24)",\n', '\n    },\n'),
    (',\n    "crewing-k2-modules": [\n      {\n', '\n    ]'),
    (',\n    "crewing-k2-modules": [\n      "dist/index.html"', '\n    ]'),
)


def previous_config(config):
    old = copy.deepcopy(config)
    old['task_routing'] = [r for r in old['task_routing'] if r['task'] != TASK]
    for section in ('allowed_file_patterns', 'harness_commands'):
        old[section].pop(TASK, None)
    return old


def previous_config_text(text):
    for start, end in BLOCKS:
        assert text.count(start) == 1, start
        begin = text.index(start)
        stop = text.index(end, begin + len(start)) + len(end)
        text = text[:begin] + text[stop:]
    return text


class CrewingK2ModulesRouteTests(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text())

    def test_exact_ceiling_checks_and_position_after_c3b2(self):
        config = self.config()
        route = [r for r in config['task_routing'] if r['task'] == TASK]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]['when_all_files_in'], FILES)
        self.assertEqual(route[0]['require_any_of'], REQUIRE_ANY)
        self.assertNotIn('require_all_of', route[0])
        self.assertEqual(config['allowed_file_patterns'][TASK], FILES)
        self.assertEqual([(c['name'], c['command']) for c in MODULE.configured_harnesses(config, TASK)], COMMANDS)
        self.assertEqual(len(COMMANDS), 14)
        self.assertEqual(config['harness_commands'][TASK][:7], config['harness_commands'][PREVIOUS_TASK])
        self.assertFalse(MODULE.is_release_task(config, TASK))
        self.assertEqual([r['task'] for r in config['task_routing'][:6]],
                         ['security-escaping-191', 'crewing-c3b1', 'crewing-c3b1-metadata',
                          PREVIOUS_TASK, TASK, 'repo-meta'])

    def test_entire_old_config_preserved_byte_for_byte_and_parsed(self):
        text = CONFIG.read_text()
        old_text = previous_config_text(text)
        self.assertEqual(hashlib.sha256(old_text.encode()).hexdigest(), OLD_CONFIG_HASH)
        config = self.config()
        old = previous_config(config)
        self.assertEqual(json.loads(old_text), old)
        # Samples without the K2 marker (plus the C3b2-owned journal shape).
        samples = [[], [FILES[0]], [FILES[7]], [FILES[6]], [FILES[0], FILES[2]]]
        samples += [r['when_all_files_in'] for r in old['task_routing']]
        for files in samples:
            with self.subTest(files=files):
                self.assertEqual(MODULE.resolve_task(config, files), MODULE.resolve_task(old, files))
                task = MODULE.resolve_task(old, files)['task']
                self.assertEqual(MODULE.configured_harnesses(config, task), MODULE.configured_harnesses(old, task))
                self.assertEqual(MODULE.scope_check_for_task(config, task, files),
                                 MODULE.scope_check_for_task(old, task, files))

    def test_protections_and_override_surface_are_untouched(self):
        config = self.config()
        old = previous_config(config)
        for key in ('protected_paths', 'release_sensitive_paths', 'stop_lines', 'release_tasks',
                    'default_task', 'exact_task_file_sets', 'additive_task_checks'):
            with self.subTest(key=key):
                self.assertEqual(config[key], old[key])
        for include_workflow in (False, True):
            self.assertEqual(MODULE.presence_override_allowed_patterns(config, include_workflow=include_workflow),
                             MODULE.presence_override_allowed_patterns(old, include_workflow=include_workflow))
        for token in ('skipi-guard-workflow-bootstrap', 'crewing-presence-contracts-bootstrap',
                      'crewing-theme-default-bootstrap'):
            self.assertEqual(MODULE.bootstrap_override_allowed_patterns(config, token),
                             MODULE.bootstrap_override_allowed_patterns(old, token))
        protected = [p for rule in config['protected_paths'] for p in rule['patterns']]
        self.assertTrue(any(MODULE.pattern_matches('presence-manifest.json', p) for p in protected))
        self.assertNotIn('presence-manifest.json', config['allowed_file_patterns'][TASK])

    def test_all_256_subsets_and_c3b2_precedence(self):
        config = self.config()
        c3b2 = [r for r in config['task_routing'] if r['task'] == PREVIOUS_TASK][0]
        for size in range(len(FILES) + 1):
            for files in itertools.combinations(FILES, size):
                with self.subTest(files=files):
                    marked = any(p in files for p in REQUIRE_ANY)
                    shadowed = (set(files) <= set(c3b2['when_all_files_in'])
                                and any(p in files for p in c3b2['require_any_of']))
                    resolved = MODULE.resolve_task(config, list(files))['task']
                    self.assertEqual(resolved == TASK, marked and not shadowed)
                    if shadowed:
                        self.assertEqual(resolved, PREVIOUS_TASK)
                    if not marked:
                        self.assertNotEqual(resolved, TASK)

    def test_require_any_of_negative_and_forbidden_extras(self):
        config = self.config()
        # dist + guard pin alone carry no Crew Flow marker: not this route.
        for files in ([FILES[0], FILES[7]], [FILES[0]], [FILES[7]], [FILES[0], FILES[2], FILES[7]]):
            with self.subTest(files=files):
                self.assertNotEqual(MODULE.resolve_task(config, files)['task'], TASK)
        for extra in EXTRAS:
            with self.subTest(extra=extra):
                self.assertNotEqual(MODULE.resolve_task(config, FILES + [extra])['task'], TASK)
                self.assertIn(extra, MODULE.scope_check_for_task(config, TASK, FILES + [extra])['scope_violations'])

    @contextmanager
    def fixture(self, files, *, incremental=False, fail=None, missing=False):
        scratch = ROOT / 'scratchpad/guard-crewing-k2-20260924'
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
            git('config', 'user.name', 'K2 isolated fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            for path in FILES + [cmd.split(' ', 1)[1] for _, cmd in COMMANDS if not cmd.split(' ', 1)[1].startswith('/')]:
                if path != FILES[1] or not missing:
                    write(path, 'synthetic baseline fixture; not product acceptance\n')
            git('add', '-A')
            git('commit', '-qm', 'synthetic published baseline')
            main = git('rev-parse', 'HEAD')
            git('update-ref', 'refs/remotes/origin/main', main)
            git('checkout', '-qb', 'candidate')
            if incremental:
                write(FILES[6], 'Previous candidate step: synthetic controls prepared; runtime remains unknown.\n')
                git('add', FILES[6])
                git('commit', '-qm', 'previous published candidate step')
            base = git('rev-parse', 'HEAD')
            for path in files:
                if path != FILES[1] or not missing:
                    write(path, 'Candidate step: Crew Flow queue and module composition; synthetic only.\n')
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

    def assert_fourteen(self, f, report, hook):
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
        shapes = [FILES, [FILES[1]], [FILES[0], FILES[1], FILES[6]], [FILES[1], FILES[7]]]
        for files, incremental in itertools.product(shapes, (False, True)):
            with self.subTest(files=files, incremental=incremental), self.fixture(files, incremental=incremental) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(proc.returncode, 0, report)
                    self.assertEqual(report['changed_files'], sorted(files))
                    self.assertEqual(report['errors'], [])
                    self.assert_fourteen(f, report, hook)

    def test_each_of_fourteen_failures_rejects_cli_and_hook(self):
        for name, command in COMMANDS:
            with self.subTest(name=name), self.fixture(FILES, fail=command.split(' ', 1)[1]) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assert_fourteen(f, report, hook)
                    self.assertEqual([t['name'] for t in report['tests'] if t['status'] == 'fail'], [name])
                    self.assertTrue(any(e.startswith('harness failed: ' + name) for e in report['errors']))

    def test_missing_crew_flow_harness_fails_both_ranges(self):
        with self.fixture([FILES[5], FILES[6]], missing=True) as f:
            for hook in (False, True):
                proc, report = self.invoke(f, hook)
                self.assertEqual(proc.returncode, 1, report)
                self.assert_fourteen(f, report, hook)
                self.assertEqual([t['name'] for t in report['tests'] if t['status'] == 'fail'],
                                 ['crewing_crew_flow_demo'])

    def test_forbidden_extras_rejected_real_cli_and_hook(self):
        for extra in EXTRAS:
            with self.subTest(extra=extra), self.fixture(FILES + [extra]) as f:
                for hook, explicit in ((False, False), (False, True), (True, False)):
                    proc, report = self.invoke(f, hook, explicit)
                    self.assertEqual(proc.returncode, 1, report)
                    self.assertFalse(report['override_present'])
                    if explicit:
                        self.assertIn(extra, report['scope_violations'])
                    else:
                        self.assertNotEqual(report['task'], TASK)

    def test_c3b2_and_pin_only_shapes_keep_old_real_behavior(self):
        # C3b2-owned diffs and a bare guard pin must behave exactly as before.
        old = previous_config(self.config())
        for files in ([FILES[6]], [FILES[0], FILES[6]], [FILES[7]]):
            with self.subTest(files=files), self.fixture(files) as f:
                for hook in (False, True):
                    proc, report = self.invoke(f, hook)
                    self.assertEqual(report['task'], MODULE.resolve_task(old, files)['task'])
                    self.assertNotEqual(report['task'], TASK)
                    bootstrap = hook and files == [FILES[7]]
                    self.assertEqual(report['override_present'], bootstrap)
                    self.assertEqual(report['auto_bootstrap_override'], bootstrap)

    def superset_repo(self, tmp, new_text):
        repo = Path(tmp) / 'repo'
        (repo / 'configs/homes').mkdir(parents=True)
        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                  text=True, capture_output=True).stdout.strip()
        git('init', '-q', '-b', 'main')
        git('config', 'user.name', 'K2 superset fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        target = repo / 'configs/homes/crewing.json'
        target.write_text(previous_config_text(CONFIG.read_text()))
        git('add', '-A')
        git('commit', '-qm', 'accepted guard config')
        old_ref = git('rev-parse', 'HEAD')
        target.write_text(new_text)
        git('add', '-A')
        git('commit', '-qm', 'proposed guard config')
        return repo, old_ref, git('rev-parse', 'HEAD')

    def run_superset(self, repo, old_ref, new_ref, result):
        proc = subprocess.run([str(GUARD), 'assert-config-superset', '--home', 'crewing',
                               '--repo', str(repo), '--old-ref', old_ref, '--new-ref', new_ref,
                               '--json', str(result)], text=True, capture_output=True)
        return proc.returncode, json.loads(result.read_text())

    def test_assert_config_superset_old_to_new_passes_and_has_teeth(self):
        with tempfile.TemporaryDirectory(prefix='k2-superset-') as tmp:
            repo, old_ref, new_ref = self.superset_repo(tmp, CONFIG.read_text())
            code, payload = self.run_superset(repo, old_ref, new_ref, Path(tmp) / 'ok.json')
            self.assertEqual(code, 0, payload)
            self.assertEqual(payload['status'], 'pass')
            self.assertEqual(payload['errors'], [])
            for key in ('missing_harnesses', 'missing_additive_task_checks', 'missing_allowed_file_patterns',
                        'missing_release_sensitive_paths', 'missing_protected_paths'):
                self.assertEqual(payload[key], [], key)
            self.assertIn(TASK, payload['new_tasks'])
            self.assertNotIn(TASK, payload['old_tasks'])
        with tempfile.TemporaryDirectory(prefix='k2-superset-neg-') as tmp:
            weakened = json.loads(CONFIG.read_text())
            weakened['harness_commands'][PREVIOUS_TASK] = weakened['harness_commands'][PREVIOUS_TASK][:-1]
            repo, old_ref, new_ref = self.superset_repo(tmp, json.dumps(weakened, indent=2) + '\n')
            code, payload = self.run_superset(repo, old_ref, new_ref, Path(tmp) / 'bad.json')
            self.assertEqual(code, 1, payload)
            self.assertEqual(payload['status'], 'fail')
            self.assertTrue(payload['missing_harnesses'])


if __name__ == '__main__':
    unittest.main()
