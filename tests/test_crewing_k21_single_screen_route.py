"""K2.1 declarative route contract: exhaustive dispatch table, ceiling, additivity.

The route is additive: it is inserted AFTER `crewing-k2-modules` (first match
wins), so every diff an earlier rule already owns keeps routing there, and K2.1
only claims diffs that used to fall back to the default task. These tests prove
dispatch, ceiling and additivity; they are not the product harness. No
protection, override token or protected path is changed or relaxed.

Declared surface (card D1 / OWNER 739, revision 2 R7/R8/R10): eleven paths, the
same eleven in `allowed_file_patterns`, and thirteen harness commands — the K2
list minus `crewing_mail_cv_intake_demo`. `crewing_mailbox_contract` stays,
because K2.1 inverts that harness instead of deleting it.
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
from collections import Counter
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / 'bin/skipi-guard'
CONFIG = ROOT / 'configs/homes/crewing.json'
LOADER = SourceFileLoader('guard_crewing_k21_single_screen', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = 'crewing-k21-single-screen'
PREVIOUS_TASK = 'crewing-k2-modules'
DEFAULT_TASK = 'plugin-host'
# Every rule that precedes this one, in declared order. The literal order is the
# oracle: moving the new rule earlier changes what these rules still own.
EARLIER_TASKS = ('security-escaping-191', 'crewing-c3b1', 'crewing-c3b1-metadata',
                 'crewing-c3b2', PREVIOUS_TASK)
# The eleven declared paths, in declared order.
FILES = ['dist/index.html',
         'tests/crewing_crew_flow_demo_harness.mjs',
         'tests/crewing_plugin_isolation_harness.mjs',
         'tests/crewing_c3b2_candidate_harness.mjs',
         'tests/crewing_mailbox_contract_harness.mjs',
         'tests/crewing_mail_cv_intake_demo_harness.mjs',
         'docs/crewing-pilot-c3b2/WORKLOG.md',
         '.github/workflows/skipi-guard.yml',
         'src-tauri/src/lib.rs',
         'src-tauri/src/crewing_intake.rs',
         'src-tauri/src/contact.rs']
REQUIRE_ANY = [FILES[6], FILES[10]]
COMMANDS = [
    ('crewing_plugin_isolation', 'node tests/crewing_plugin_isolation_harness.mjs'),
    ('shared_host_runtime_isolation', 'node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs'),
    ('crewing_presence_contract', 'node tests/crewing_presence_contract_harness.mjs'),
    ('crewing_crew_flow_demo', 'node tests/crewing_crew_flow_demo_harness.mjs'),
    ('crewing_c3b1_pilot', 'node tests/crewing_c3b1_pilot_harness.mjs'),
    ('crewing_csp_inline_handlers', 'node tests/csp_inline_handlers_harness.mjs'),
    ('crewing_c3b2_candidate', 'node tests/crewing_c3b2_candidate_harness.mjs'),
    ('crewing_mailbox_contract', 'node tests/crewing_mailbox_contract_harness.mjs'),
    ('crewing_compliance_manual_flow', 'node tests/crewing_compliance_manual_flow_harness.mjs'),
    ('crewing_theme_default', 'node tests/crewing_theme_default_harness.mjs'),
    ('settings5_preview_gated', 'node tests/settings5_preview_gated_harness.mjs'),
    ('trial_activate_unconnected', 'node tests/trial_activate_unconnected_harness.mjs'),
    ('trial_gate_wired', 'node tests/trial_gate_wired_harness.mjs'),
]
# Dropped from the K2 list because the demo harness reads the retired mail block
# end to end (21/21 assertions) and is deleted by K2.1.
DROPPED_COMMAND = 'crewing_mail_cv_intake_demo'
# Outside the declared ceiling on purpose. presence-manifest.json is protected
# and only the presence-only PR may touch it; the presence and C3b1 harnesses are
# kept closed so a PR that retires a module cannot "optimise" its own contracts
# green; Cargo/gen/android are release-sensitive; messaging.rs, signing keys and
# foreign test/doc/workflow files were never in scope.
EXTRAS = ['presence-manifest.json',
          'tests/crewing_presence_contract_harness.mjs',
          'tests/crewing_c3b1_pilot_harness.mjs',
          'src-tauri/Cargo.toml',
          'src-tauri/Cargo.lock',
          'src-tauri/gen/android/app/src/main/java/app/skipi/crewing/mobile/MainActivity.kt',
          'src-tauri/src/messaging.rs',
          'keys/signing.pem',
          'tests/other.mjs',
          'docs/other.md',
          '.github/workflows/other.yml']
# sha256 of configs/homes/crewing.json at guard main b72a59ca (pre-K2.1 bytes).
OLD_CONFIG_HASH = '4fb83721e0ababcc6c327a6f9df1fdc89a3dfbb9f6a62d658087b72dd959da44'
# Exact anchors of the three additive text blocks; removing them must restore the
# pre-K2.1 file byte for byte (proves the change adds and never edits).
BLOCKS = (
    ('    {\n      "name": "crewing K2.1 single screen: mail module retired,'
     ' card + contact link (owner739, 2026-09-26)",\n', '\n    },\n'),
    (',\n    "crewing-k21-single-screen": [\n      {\n', '\n    ]'),
    (',\n    "crewing-k21-single-screen": [\n      "dist/index.html"', '\n    ]'),
)
# Protections as accepted at b72a59ca. A route PR must not touch them at all
# (AGENTS.md: narrowing protected_paths needs its own PR, per path).
PROTECTED_PATHS = {
    'backend/server/prod data': ['backend/**', 'server/**', 'api/**', 'data/prod/**', 'prod/**',
                                 'production/**', 'media/**', 'uploads/**'],
    'secrets/signing keys': ['.env', '.env.*', '**/.env', '**/.env.*', 'keys/**', 'signing/**',
                             '**/*.pem', '**/*.p12', '**/*.keystore', '**/*secret*', '**/*token*'],
    'pairing/QR/camera bridge': ['**/*pair*', '**/*Pair*', '**/*qr*', '**/*QR*', '**/*camera*',
                                 '**/*Camera*', '**/*barcode*', '**/*Barcode*'],
    'presence contracts': ['presence-manifest.json'],
}
RELEASE_SENSITIVE_PATHS = {
    'catalog/latest/release manifests': ['latest.json', '**/latest.json', 'catalog/**',
                                         '**/catalog/**', 'release/**', 'releases/**',
                                         'downloads/**', 'manifest*.json', '**/manifest*.json'],
    'versions/tags': ['VERSION', 'version.txt', 'package.json', 'package-lock.json',
                      'pnpm-lock.yaml', 'src-tauri/tauri.conf.json', 'Cargo.toml', 'Cargo.lock'],
    'Tauri/Cargo/mobile generated files': ['src-tauri/gen/**', 'src-tauri/target/**',
                                           'src-tauri/Cargo.lock', 'android/**', 'ios/**',
                                           'build/**', '*.apk', '*.aab', '*.ipa',
                                           'dist/**/*.apk'],
    'Play/TestFlight/upload/deploy': ['fastlane/**', 'play/**', 'testflight/**', 'scripts/deploy*',
                                      'scripts/upload*', 'scripts/*testflight*', 'scripts/*play*',
                                      '.github/workflows/*release*', '.github/workflows/*deploy*'],
}
# Declared outcome for all 2**11 subsets of the eleven paths: which task owns
# how many of them. Sums to 2048; the 1480 the new route claims were all falling
# back to the default task before it existed.
EXPECTED_SUBSET_COUNTS = {
    'crewing-c3b2': 48,
    PREVIOUS_TASK: 40,
    TASK: 1480,
    DEFAULT_TASK: 479,
    'provenance': 1,
}


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


class CrewingK21SingleScreenRouteTests(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text())

    # ------------------------------------------------------------------
    # declared ceiling: eleven paths, thirteen commands, position after K2
    # ------------------------------------------------------------------
    def test_exact_ceiling_checks_and_position_after_k2(self):
        config = self.config()
        route = [r for r in config['task_routing'] if r['task'] == TASK]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]['when_all_files_in'], FILES)
        self.assertEqual(len(FILES), 11)
        self.assertEqual(route[0]['require_any_of'], REQUIRE_ANY)
        self.assertNotIn('require_all_of', route[0])
        self.assertEqual(config['allowed_file_patterns'][TASK], FILES)
        self.assertFalse(MODULE.is_release_task(config, TASK))
        self.assertEqual([r['task'] for r in config['task_routing'][:7]],
                         [*EARLIER_TASKS, TASK, 'repo-meta'])
        # presence-manifest.json stays protected and outside the ceiling.
        protected = [p for rule in config['protected_paths'] for p in rule['patterns']]
        self.assertTrue(any(MODULE.pattern_matches('presence-manifest.json', p) for p in protected))
        self.assertNotIn('presence-manifest.json', config['allowed_file_patterns'][TASK])

    def test_thirteen_harness_commands_are_k2_minus_the_retired_demo(self):
        config = self.config()
        self.assertEqual(len(COMMANDS), 13)
        self.assertEqual([(c['name'], c['command']) for c in MODULE.configured_harnesses(config, TASK)],
                         COMMANDS)
        self.assertEqual([(c['name'], c['command']) for c in config['harness_commands'][TASK]], COMMANDS)
        k2_commands = [(c['name'], c['command']) for c in config['harness_commands'][PREVIOUS_TASK]]
        self.assertEqual(len(k2_commands), 14)
        self.assertEqual([c for c in k2_commands if c[0] != DROPPED_COMMAND], COMMANDS)
        names = [name for name, _ in COMMANDS]
        self.assertNotIn(DROPPED_COMMAND, names)
        # Inverted, not deleted: the mailbox contract keeps running on this route.
        self.assertIn('crewing_mailbox_contract', names)
        self.assertEqual(len(set(names)), len(names))

    # ------------------------------------------------------------------
    # additivity: the accepted config comes back byte for byte
    # ------------------------------------------------------------------
    def test_entire_old_config_preserved_byte_for_byte_and_parsed(self):
        text = CONFIG.read_text()
        old_text = previous_config_text(text)
        self.assertEqual(hashlib.sha256(old_text.encode()).hexdigest(), OLD_CONFIG_HASH)
        config = self.config()
        old = previous_config(config)
        self.assertEqual(json.loads(old_text), old)
        samples = [[], [FILES[0]], [FILES[7]], [FILES[6]], [FILES[0], FILES[2]], FILES[:3]]
        samples += [r['when_all_files_in'] for r in old['task_routing']]
        for files in samples:
            with self.subTest(files=files):
                before = MODULE.resolve_task(old, files)
                if before['task'] in EARLIER_TASKS or not any(p in files for p in REQUIRE_ANY):
                    self.assertEqual(MODULE.resolve_task(config, files), before)
                task = before['task']
                self.assertEqual(MODULE.configured_harnesses(config, task),
                                 MODULE.configured_harnesses(old, task))
                self.assertEqual(MODULE.scope_check_for_task(config, task, files),
                                 MODULE.scope_check_for_task(old, task, files))

    def test_protections_and_override_surface_are_untouched(self):
        config = self.config()
        old = previous_config(config)
        self.assertEqual({rule['name']: rule['patterns'] for rule in config['protected_paths']},
                         PROTECTED_PATHS)
        self.assertEqual({rule['name']: rule['patterns'] for rule in config['release_sensitive_paths']},
                         RELEASE_SENSITIVE_PATHS)
        for key in ('protected_paths', 'release_sensitive_paths', 'stop_lines', 'release_tasks',
                    'default_task', 'exact_task_file_sets', 'additive_task_checks'):
            with self.subTest(key=key):
                self.assertEqual(config[key], old[key])
        self.assertEqual(config['default_task'], DEFAULT_TASK)
        for include_workflow in (False, True):
            self.assertEqual(MODULE.presence_override_allowed_patterns(config, include_workflow=include_workflow),
                             MODULE.presence_override_allowed_patterns(old, include_workflow=include_workflow))
        for token in ('skipi-guard-workflow-bootstrap', 'crewing-presence-contracts-bootstrap',
                      'crewing-theme-default-bootstrap'):
            with self.subTest(token=token):
                self.assertEqual(MODULE.bootstrap_override_allowed_patterns(config, token),
                                 MODULE.bootstrap_override_allowed_patterns(old, token))

    # ------------------------------------------------------------------
    # exhaustive dispatch: all 2**11 subsets against a declared table
    # ------------------------------------------------------------------
    def expected_task(self, old, files):
        """Declared expectation, from literal data only.

        Earlier rules keep everything they already owned (their literal order is
        the oracle); of the rest, this route claims exactly the non-empty subsets
        carrying a require_any_of marker; anything else keeps its old task.
        """
        before = MODULE.resolve_task(old, list(files))['task']
        if before in EARLIER_TASKS:
            return before
        if files and any(path in files for path in REQUIRE_ANY):
            return TASK
        return before

    def test_all_2048_subsets_match_the_declared_table(self):
        config = self.config()
        old = previous_config(config)
        seen = Counter()
        for size in range(len(FILES) + 1):
            for files in itertools.combinations(FILES, size):
                expected = self.expected_task(old, files)
                with self.subTest(files=files):
                    self.assertEqual(MODULE.resolve_task(config, list(files))['task'], expected)
                    if expected == TASK:
                        # Nothing is taken from an earlier rule: every diff this
                        # route claims used to fall back to the default task.
                        self.assertEqual(MODULE.resolve_task(old, list(files))['task'], DEFAULT_TASK)
                        self.assertEqual(MODULE.scope_check_for_task(config, TASK, list(files))['scope_violations'],
                                         [])
                seen[expected] += 1
        self.assertEqual(dict(seen), EXPECTED_SUBSET_COUNTS)
        self.assertEqual(sum(seen.values()), 2 ** len(FILES))

    def test_require_any_of_negative_and_forbidden_extras(self):
        config = self.config()
        unmarked = [path for path in FILES if path not in REQUIRE_ANY]
        # dist + lib.rs + guard pin carry no K2.1 marker: not this route.
        for files in ([FILES[0], FILES[8], FILES[7]], [FILES[0]], [FILES[7]],
                      [FILES[0], FILES[4]], unmarked):
            with self.subTest(files=files):
                self.assertNotEqual(MODULE.resolve_task(config, files)['task'], TASK)
        for extra in EXTRAS:
            with self.subTest(extra=extra):
                self.assertNotEqual(MODULE.resolve_task(config, FILES + [extra])['task'], TASK)
                self.assertIn(extra, MODULE.scope_check_for_task(config, TASK, FILES + [extra])['scope_violations'])
                self.assertNotIn(extra, config['allowed_file_patterns'][TASK])

    # ------------------------------------------------------------------
    # real CLI: the declared diff dispatches and plans thirteen checks
    # ------------------------------------------------------------------
    def synthetic_repo(self, tmp, files):
        repo = Path(tmp) / 'repo'
        repo.mkdir()
        env = os.environ.copy()
        env.pop('SKIPI_GUARD_OVERRIDE_TOKEN', None)

        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True, text=True,
                                  capture_output=True, env=env).stdout.strip()

        def write(path, value):
            dest = repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(value)

        git('init', '-q', '-b', 'main')
        git('config', 'user.name', 'K2.1 isolated fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        for path in FILES + EXTRAS:
            write(path, 'synthetic baseline fixture; not product acceptance\n')
        git('add', '-A')
        git('commit', '-qm', 'synthetic published baseline')
        base = git('rev-parse', 'HEAD')
        for path in files:
            write(path, 'Candidate step: single screen, retired mail module; synthetic only.\n')
        git('add', '-A')
        git('commit', '-qm', 'candidate increment')
        return repo, base, git('rev-parse', 'HEAD'), env

    def run_verify(self, repo, base, head, env, out, *, task=None):
        args = [str(GUARD), 'verify', '--home', 'crewing', '--repo', str(repo),
                '--base', base, '--head', head, '--json', str(out)]
        args += ['--task', task] if task else ['--auto-task']
        proc = subprocess.run(args, text=True, capture_output=True, env=env)
        return proc, json.loads(Path(out).read_text())

    def test_real_cli_routes_the_declared_eleven_paths_and_plans_thirteen(self):
        with tempfile.TemporaryDirectory(prefix='k21-cli-') as tmp:
            repo, base, head, env = self.synthetic_repo(tmp, FILES)
            proc, report = self.run_verify(repo, base, head, env, Path(tmp) / 'ok.json')
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report['status'], 'pass')
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['changed_files'], sorted(FILES))
            self.assertEqual(report['task'], TASK)
            self.assertEqual(report['task_source'], 'auto')
            self.assertEqual(report['effective_tasks'], [TASK])
            self.assertFalse(report['override_present'])
            self.assertFalse(report['auto_bootstrap_override'])
            self.assertEqual(report['scope_violations'], [])
            self.assertEqual(report['protected_paths_touched'], [])
            self.assertEqual(report['release_paths_touched'], [])
            self.assertEqual(report['allowed_file_patterns'], FILES)
            self.assertEqual([(t['name'], t['command']) for t in report['tests']], COMMANDS)

    def test_real_cli_rejects_a_file_outside_the_ceiling(self):
        extra = 'src-tauri/Cargo.toml'
        with tempfile.TemporaryDirectory(prefix='k21-cli-neg-') as tmp:
            repo, base, head, env = self.synthetic_repo(tmp, FILES + [extra])
            proc, report = self.run_verify(repo, base, head, env, Path(tmp) / 'auto.json')
            self.assertEqual(proc.returncode, 1, report)
            self.assertNotEqual(report['task'], TASK)
            self.assertFalse(report['override_present'])
            proc, report = self.run_verify(repo, base, head, env, Path(tmp) / 'explicit.json', task=TASK)
            self.assertEqual(proc.returncode, 1, report)
            self.assertEqual(report['status'], 'fail')
            self.assertIn(extra, report['scope_violations'])
            self.assertFalse(report['override_present'])

    # ------------------------------------------------------------------
    # assert-config-superset: old -> new adds and never removes
    # ------------------------------------------------------------------
    def superset_repo(self, tmp, new_text):
        repo = Path(tmp) / 'repo'
        (repo / 'configs/homes').mkdir(parents=True)

        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True, text=True,
                                  capture_output=True).stdout.strip()

        git('init', '-q', '-b', 'main')
        git('config', 'user.name', 'K2.1 superset fixture')
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
        with tempfile.TemporaryDirectory(prefix='k21-superset-') as tmp:
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
            self.assertIn(PREVIOUS_TASK, payload['old_tasks'])
        with tempfile.TemporaryDirectory(prefix='k21-superset-neg-') as tmp:
            weakened = json.loads(CONFIG.read_text())
            weakened['harness_commands'][PREVIOUS_TASK] = weakened['harness_commands'][PREVIOUS_TASK][:-1]
            repo, old_ref, new_ref = self.superset_repo(tmp, json.dumps(weakened, indent=2) + '\n')
            code, payload = self.run_superset(repo, old_ref, new_ref, Path(tmp) / 'bad.json')
            self.assertEqual(code, 1, payload)
            self.assertEqual(payload['status'], 'fail')
            self.assertTrue(payload['missing_harnesses'])


if __name__ == '__main__':
    unittest.main()
