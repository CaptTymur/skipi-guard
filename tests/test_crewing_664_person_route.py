"""№664 person-keyed save route: exhaustive dispatch, ceiling, additivity.

The route is additive: it is inserted AFTER `crewing-k21-single-screen` (first
match wins), so every diff an earlier rule already owns keeps routing there, and
this route only claims diffs that used to fall back to the default task. These
tests prove dispatch, ceiling and additivity; they are not the product harness.
No protection, override token or protected path is changed or relaxed.

Declared surface (handoff HANDOFF-2026-10-03-guard-route-crewing-664.md,
owner-authorized DECISIONS (995), widened by DECISIONS (996)): eight paths, the
same eight in `allowed_file_patterns`, and the thirteen harness commands of the
preceding crewing route, copied verbatim. `src-tauri/src/db.rs` is the marker:
it appears in no other rule of this home, so every subset this route claims
used to fall through to `plugin-host` and fail on scope.

The widening of 2026-10-04 adds exactly two paths,
`docs/crewing-pilot-c3b2/WORKLOG.md` and `.github/workflows/skipi-guard.yml`,
both already declared by `crewing-k21-single-screen`: the live Crewing range
carries them and the guard scores the whole branch against main. Nothing else
moved - `require_any_of`, the thirteen commands, the neighbours and every
protection line come back byte for byte once the two insertions are stripped
(PRE_WIDEN_CONFIG_HASH).
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
LOADER = SourceFileLoader('guard_crewing_664_person', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = 'crewing-664-person'
PREVIOUS_TASK = 'crewing-k21-single-screen'
DEFAULT_TASK = 'plugin-host'
# Every rule that precedes this one, in declared order. The literal order is the
# oracle: moving the new rule earlier changes what these rules still own.
EARLIER_TASKS = ('security-escaping-191', 'crewing-c3b1', 'crewing-c3b1-metadata',
                 'crewing-c3b2', 'crewing-k2-modules', PREVIOUS_TASK)
# The eight declared paths, in declared order. The last two were added by the
# widening of 2026-10-04 (owner (996)); the first six are the accepted route.
FILES = ['dist/index.html',
         'src-tauri/src/db.rs',
         'src-tauri/src/lib.rs',
         'src-tauri/src/crewing_intake.rs',
         'tests/crewing_c3b2_candidate_harness.mjs',
         'tests/crewing_crew_flow_demo_harness.mjs',
         'docs/crewing-pilot-c3b2/WORKLOG.md',
         '.github/workflows/skipi-guard.yml']
MARKER = 'src-tauri/src/db.rs'
REQUIRE_ANY = [MARKER]
# Thirteen commands, copied verbatim from the preceding crewing route. The
# handoff text says "16 node harnesses + cargo test"; no crewing route and no
# guard config in this repo has ever carried a cargo command, and the two routes
# the card names as the model carry 13 (k21) and 7 (c3b2). This list is the
# strictest of the two models; widening it is a separate, visible edit that
# test_thirteen_harness_commands_are_the_previous_route_verbatim will catch.
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
# Outside the declared ceiling on purpose. presence-manifest.json is protected;
# the plugin/presence contract harnesses stay closed so a PR that changes the
# receiver cannot "optimise" its own contracts green; contact.rs and messaging.rs
# belong to K2.1 and to the security route; Cargo/gen/android are
# release-sensitive; signing keys and foreign test/doc files were never in scope.
# The C3b2 journal and the guard pin left this list on 2026-10-04: owner (996)
# moved exactly those two into the route, and NEW_PATHS below pins that move.
EXTRAS = ['presence-manifest.json',
          'tests/crewing_plugin_isolation_harness.mjs',
          'tests/crewing_presence_contract_harness.mjs',
          'src-tauri/src/contact.rs',
          'src-tauri/src/messaging.rs',
          'src-tauri/Cargo.toml',
          'src-tauri/Cargo.lock',
          'src-tauri/gen/android/app/src/main/java/app/skipi/crewing/mobile/MainActivity.kt',
          'keys/signing.pem',
          'tests/other.mjs',
          'docs/other.md']
# sha256 of configs/homes/crewing.json at guard main 93833fac (pre-route bytes).
OLD_CONFIG_HASH = 'e72d4ec047eb0ced68116bb21973f616c831e6bddcde608ca4fc75b2f8451072'
# Exact anchors of the three additive text blocks; removing them must restore the
# pre-route file byte for byte (proves the change adds and never edits).
BLOCKS = (
    ('    {\n      "name": "crewing №664 person-keyed save: receiver retires the letter-keyed row,'
     ' mode for documents (owner995, 2026-10-04)",\n', '\n    },\n'),
    (',\n    "crewing-664-person": [\n      {\n', '\n    ]'),
    (',\n    "crewing-664-person": [\n      "dist/index.html"', '\n    ]'),
)
# This PR's own delta (owner-authorized DECISIONS (996)): the route is widened by
# exactly these two paths, in `when_all_files_in` and in `allowed_file_patterns`,
# and by nothing else.
NEW_PATHS = ['docs/crewing-pilot-c3b2/WORKLOG.md', '.github/workflows/skipi-guard.yml']
# sha256 of configs/homes/crewing.json at guard main 37ff9581 (pre-widen bytes).
PRE_WIDEN_CONFIG_HASH = 'ddcb72ce024e1ad94e2710b4ec3b50b940be36e83f315ddd9d6c5de8ef6b5207'
# Anchored insertions. Each anchor is the six-path tail of one list, so the two
# inserted lines are addressed uniquely even though the very same two lines also
# appear, verbatim and at the same indent, in the K2.1 route above. Stripping
# both must restore the accepted main byte for byte.
WIDEN_INSERTS = (
    ('      "when_all_files_in": [\n        "dist/index.html",\n'
     '        "src-tauri/src/db.rs",\n        "src-tauri/src/lib.rs",\n'
     '        "src-tauri/src/crewing_intake.rs",\n'
     '        "tests/crewing_c3b2_candidate_harness.mjs",\n'
     '        "tests/crewing_crew_flow_demo_harness.mjs"',
     ',\n        "docs/crewing-pilot-c3b2/WORKLOG.md",\n'
     '        ".github/workflows/skipi-guard.yml"'),
    ('    "crewing-664-person": [\n      "dist/index.html",\n'
     '      "src-tauri/src/db.rs",\n      "src-tauri/src/lib.rs",\n'
     '      "src-tauri/src/crewing_intake.rs",\n'
     '      "tests/crewing_c3b2_candidate_harness.mjs",\n'
     '      "tests/crewing_crew_flow_demo_harness.mjs"',
     ',\n      "docs/crewing-pilot-c3b2/WORKLOG.md",\n'
     '      ".github/workflows/skipi-guard.yml"'),
)
# Neighbour oracles that must subtract this task, or their historical hashes stop
# pinning the bytes they were accepted on. Dropping a pin is caught below.
NEIGHBOUR_PINS = ('test_crewing_c3b1_route.py',
                  'test_crewing_c3b2_route.py',
                  'test_crewing_k2_modules_route.py',
                  'test_crewing_k21_single_screen_route.py',
                  'test_security_escaping_191_route.py')
# Protections as accepted at 93833fac. A route PR must not touch them at all
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
# Declared outcome for all 2**8 subsets of the eight paths: which task owns how
# many of them. Sums to 256; the 128 this route claims are exactly the subsets
# carrying the marker, and all 128 were falling back to the default task before
# the route existed. 96 of them were still falling back there before the
# widening, which is this PR's whole delta (test below counts them).
EXPECTED_SUBSET_COUNTS = {
    'crewing-c3b2': 48,
    'crewing-k2-modules': 16,
    'crewing-k21-single-screen': 24,
    'provenance': 1,
    TASK: 128,
    DEFAULT_TASK: 39,
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


def pre_widen_text(text):
    """The accepted main text: the two insertions of this PR removed."""
    for anchor, insert in WIDEN_INSERTS:
        assert text.count(anchor + insert) == 1, anchor[:48]
        text = text.replace(anchor + insert, anchor)
    return text


def widened(config, extra):
    """The same route with one more path declared - the mutation to catch."""
    bad = copy.deepcopy(config)
    for rule in bad['task_routing']:
        if rule['task'] == TASK:
            rule['when_all_files_in'] = [*rule['when_all_files_in'], extra]
    bad['allowed_file_patterns'][TASK] = [*bad['allowed_file_patterns'][TASK], extra]
    return bad


class Crewing664PersonRouteTests(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text())

    # ------------------------------------------------------------------
    # shared oracles - the positive tests and the negatives use the same code
    # ------------------------------------------------------------------
    def assert_declared_ceiling(self, config):
        route = [r for r in config['task_routing'] if r['task'] == TASK]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]['when_all_files_in'], FILES)
        self.assertEqual(len(FILES), 8)
        self.assertEqual(route[0]['require_any_of'], REQUIRE_ANY)
        self.assertNotIn('require_all_of', route[0])
        self.assertEqual(config['allowed_file_patterns'][TASK], FILES)

    def assert_subset_table(self, config):
        # The universe is read back from the config, not from the constant, so
        # a route widened by one path produces a bigger table and this oracle
        # reddens instead of silently testing the six paths it used to declare.
        route = [r for r in config['task_routing'] if r['task'] == TASK][0]
        universe = list(dict.fromkeys([*FILES, *route['when_all_files_in'],
                                       *config['allowed_file_patterns'][TASK]]))
        old = previous_config(config)
        seen = Counter()
        for size in range(len(universe) + 1):
            for files in itertools.combinations(universe, size):
                expected = self.expected_task(old, files)
                self.assertEqual(MODULE.resolve_task(config, list(files))['task'], expected, files)
                seen[expected] += 1
        self.assertEqual(dict(seen), EXPECTED_SUBSET_COUNTS)
        self.assertEqual(sum(seen.values()), 2 ** len(FILES))

    def expected_task(self, old, files):
        """Declared expectation, from literal data only.

        Earlier rules keep everything they already owned (their literal order is
        the oracle); of the rest, this route claims exactly the subsets carrying
        the marker; anything else keeps its old task.
        """
        before = MODULE.resolve_task(old, list(files))['task']
        if before in EARLIER_TASKS:
            return before
        if MARKER in files:
            return TASK
        return before

    # ------------------------------------------------------------------
    # declared ceiling: eight paths, thirteen commands, position after K2.1
    # ------------------------------------------------------------------
    def test_exact_ceiling_checks_and_position_after_k21(self):
        config = self.config()
        self.assert_declared_ceiling(config)
        self.assertFalse(MODULE.is_release_task(config, TASK))
        self.assertEqual([r['task'] for r in config['task_routing'][:8]],
                         [*EARLIER_TASKS, TASK, 'repo-meta'])
        # The marker belongs to this rule alone: no other rule in the home
        # declares db.rs, which is why nothing is taken from an earlier route.
        other_rules = [r for r in config['task_routing'] if r['task'] != TASK]
        for rule in other_rules:
            self.assertNotIn(MARKER, rule.get('when_all_files_in', []), rule['task'])
        for task, patterns in config['allowed_file_patterns'].items():
            if task != TASK:
                self.assertNotIn(MARKER, patterns, task)
        # presence-manifest.json stays protected and outside the ceiling.
        protected = [p for rule in config['protected_paths'] for p in rule['patterns']]
        self.assertTrue(any(MODULE.pattern_matches('presence-manifest.json', p) for p in protected))
        self.assertNotIn('presence-manifest.json', config['allowed_file_patterns'][TASK])
        # The marker itself is neither protected nor release-sensitive.
        self.assertFalse(any(MODULE.pattern_matches(MARKER, p) for p in protected))
        release = [p for rule in config['release_sensitive_paths'] for p in rule['patterns']]
        self.assertFalse(any(MODULE.pattern_matches(MARKER, p) for p in release))

    def test_thirteen_harness_commands_are_the_previous_route_verbatim(self):
        config = self.config()
        self.assertEqual(len(COMMANDS), 13)
        self.assertEqual([(c['name'], c['command']) for c in MODULE.configured_harnesses(config, TASK)],
                         COMMANDS)
        self.assertEqual([(c['name'], c['command']) for c in config['harness_commands'][TASK]], COMMANDS)
        self.assertEqual([(c['name'], c['command']) for c in config['harness_commands'][PREVIOUS_TASK]],
                         COMMANDS)
        # Strictly more than the default task this diff used to fall into.
        self.assertEqual(len(config['harness_commands'][DEFAULT_TASK]), 4)
        names = [name for name, _ in COMMANDS]
        self.assertEqual(len(set(names)), len(names))
        # No command in this home runs a build toolchain at pre-push time.
        for _, command in COMMANDS:
            self.assertTrue(command.startswith('node '), command)

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
        samples = [[], [FILES[0]], [FILES[2]], [FILES[4]], [FILES[0], FILES[5]], FILES[2:4]]
        samples += [r['when_all_files_in'] for r in old['task_routing']]
        for files in samples:
            with self.subTest(files=files):
                before = MODULE.resolve_task(old, files)
                if before['task'] in EARLIER_TASKS or MARKER not in files:
                    self.assertEqual(MODULE.resolve_task(config, files), before)
                task = before['task']
                self.assertEqual(MODULE.configured_harnesses(config, task),
                                 MODULE.configured_harnesses(old, task))
                self.assertEqual(MODULE.scope_check_for_task(config, task, files),
                                 MODULE.scope_check_for_task(old, task, files))

    # ------------------------------------------------------------------
    # this PR's own delta: exactly two paths, nothing else moved
    # ------------------------------------------------------------------
    def test_widening_adds_exactly_two_paths_and_restores_main_byte_for_byte(self):
        """Strip the two insertions and guard main 37ff9581 comes back exactly.

        This is the only honest proof that `require_any_of`, the thirteen
        commands, the neighbour rules, their pins and every protection line were
        not touched while the ceiling grew: the rest of the file is identical.
        """
        text = CONFIG.read_text()
        self.assertEqual(hashlib.sha256(pre_widen_text(text).encode()).hexdigest(),
                         PRE_WIDEN_CONFIG_HASH)
        pre = json.loads(pre_widen_text(text))
        config = self.config()
        route = [r for r in config['task_routing'] if r['task'] == TASK][0]
        pre_route = [r for r in pre['task_routing'] if r['task'] == TASK][0]
        self.assertEqual(len(pre_route['when_all_files_in']), 6)
        self.assertEqual(route['when_all_files_in'], [*pre_route['when_all_files_in'], *NEW_PATHS])
        self.assertEqual(config['allowed_file_patterns'][TASK],
                         [*pre['allowed_file_patterns'][TASK], *NEW_PATHS])
        self.assertEqual(route['require_any_of'], pre_route['require_any_of'])
        self.assertEqual(route['name'], pre_route['name'])
        self.assertNotIn('require_all_of', route)
        # Everything outside this one task's two lists is identical to main.
        for key in ('protected_paths', 'release_sensitive_paths', 'stop_lines', 'release_tasks',
                    'default_task', 'exact_task_file_sets', 'additive_task_checks',
                    'harness_commands'):
            with self.subTest(key=key):
                self.assertEqual(config[key], pre[key])
        self.assertEqual([r for r in config['task_routing'] if r['task'] != TASK],
                         [r for r in pre['task_routing'] if r['task'] != TASK])
        self.assertEqual({t: v for t, v in config['allowed_file_patterns'].items() if t != TASK},
                         {t: v for t, v in pre['allowed_file_patterns'].items() if t != TASK})
        for include_workflow in (False, True):
            self.assertEqual(MODULE.presence_override_allowed_patterns(config, include_workflow=include_workflow),
                             MODULE.presence_override_allowed_patterns(pre, include_workflow=include_workflow))
        for token in ('skipi-guard-workflow-bootstrap', 'crewing-presence-contracts-bootstrap',
                      'crewing-theme-default-bootstrap'):
            with self.subTest(token=token):
                self.assertEqual(MODULE.bootstrap_override_allowed_patterns(config, token),
                                 MODULE.bootstrap_override_allowed_patterns(pre, token))
        # The widening is real and bounded: exactly 96 of the 256 subsets move,
        # every one of them carries the marker, and every one came from the
        # default task - nothing is taken from a neighbour rule.
        moved = [files for size in range(len(FILES) + 1)
                 for files in itertools.combinations(FILES, size)
                 if MODULE.resolve_task(config, list(files))['task']
                 != MODULE.resolve_task(pre, list(files))['task']]
        self.assertEqual(len(moved), 96)
        for files in moved:
            with self.subTest(files=files):
                self.assertIn(MARKER, files)
                self.assertEqual(MODULE.resolve_task(pre, list(files))['task'], DEFAULT_TASK)
                self.assertEqual(MODULE.resolve_task(config, list(files))['task'], TASK)
                self.assertEqual(MODULE.scope_check_for_task(config, TASK, list(files))['scope_violations'], [])
        # Teeth: the accepted six-path route no longer satisfies the ceiling.
        with self.assertRaises(AssertionError):
            self.assert_declared_ceiling(pre)

    def test_the_two_new_paths_were_scope_violations_before_and_need_the_marker_now(self):
        config = self.config()
        pre = json.loads(pre_widen_text(CONFIG.read_text()))
        live = sorted(FILES)  # the live Crewing range, as the guard sees it
        before = MODULE.scope_check_for_task(pre, TASK, live)
        self.assertEqual(sorted(before['scope_violations']), sorted(NEW_PATHS))
        self.assertNotEqual(MODULE.resolve_task(pre, live)['task'], TASK)
        after = MODULE.scope_check_for_task(config, TASK, live)
        self.assertEqual(after['scope_violations'], [])
        self.assertEqual(MODULE.resolve_task(config, live)['task'], TASK)
        for path in NEW_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, config['allowed_file_patterns'][TASK])
                self.assertNotIn(path, EXTRAS)
                # Both were already declared by the preceding route, so this
                # widening opens no path the home had not already opened.
                self.assertIn(path, config['allowed_file_patterns'][PREVIOUS_TASK])
                # The marker still gates the route: neither path rides alone.
                self.assertEqual(MODULE.resolve_task(config, [MARKER, path])['task'], TASK)
                self.assertNotEqual(MODULE.resolve_task(config, [path])['task'], TASK)
                self.assertNotEqual(MODULE.resolve_task(pre, [MARKER, path])['task'], TASK)
                # Still neither protected nor release-sensitive.
                protected = [q for rule in config['protected_paths'] for q in rule['patterns']]
                release = [q for rule in config['release_sensitive_paths'] for q in rule['patterns']]
                self.assertFalse(any(MODULE.pattern_matches(path, q) for q in protected))
                self.assertFalse(any(MODULE.pattern_matches(path, q) for q in release))

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
    # exhaustive dispatch: all 2**8 subsets against a declared table
    # ------------------------------------------------------------------
    def test_all_256_subsets_match_the_declared_table(self):
        config = self.config()
        old = previous_config(config)
        self.assert_subset_table(config)
        claimed = 0
        for size in range(len(FILES) + 1):
            for files in itertools.combinations(FILES, size):
                if MODULE.resolve_task(config, list(files))['task'] != TASK:
                    continue
                claimed += 1
                with self.subTest(files=files):
                    # Nothing is taken from an earlier rule: every diff this
                    # route claims used to fall back to the default task.
                    self.assertEqual(MODULE.resolve_task(old, list(files))['task'], DEFAULT_TASK)
                    self.assertEqual(MODULE.scope_check_for_task(config, TASK, list(files))['scope_violations'],
                                     [])
                    self.assertIn(MARKER, files)
        self.assertEqual(claimed, EXPECTED_SUBSET_COUNTS[TASK])

    def test_require_any_of_negative_and_forbidden_extras(self):
        config = self.config()
        unmarked = [path for path in FILES if path != MARKER]
        # Without db.rs the diff is not this route's business.
        for files in (unmarked, [FILES[0]], [FILES[2]], [FILES[0], FILES[2], FILES[3]],
                      [FILES[0], FILES[4]], [FILES[5]]):
            with self.subTest(files=files):
                self.assertNotEqual(MODULE.resolve_task(config, files)['task'], TASK)
        # Diffs an earlier rule already owns keep routing there, marker or not.
        self.assertEqual(MODULE.resolve_task(config, [FILES[0], FILES[2], FILES[3], FILES[4]])['task'],
                         'crewing-c3b2')
        self.assertEqual(MODULE.resolve_task(config, [FILES[0], FILES[5]])['task'],
                         'crewing-k2-modules')
        self.assertEqual(MODULE.resolve_task(config, [FILES[2]])['task'], 'provenance')
        for extra in EXTRAS:
            with self.subTest(extra=extra):
                self.assertNotEqual(MODULE.resolve_task(config, FILES + [extra])['task'], TASK)
                self.assertNotEqual(MODULE.resolve_task(config, [MARKER, extra])['task'], TASK)
                self.assertIn(extra, MODULE.scope_check_for_task(config, TASK, FILES + [extra])['scope_violations'])
                self.assertNotIn(extra, config['allowed_file_patterns'][TASK])

    # ------------------------------------------------------------------
    # negatives that must redden: widening the route, dropping a neighbour pin
    # ------------------------------------------------------------------
    def test_widening_the_route_by_one_path_is_caught(self):
        config = self.config()
        self.assert_declared_ceiling(config)
        self.assert_subset_table(config)
        for extra in ('src-tauri/Cargo.toml', 'presence-manifest.json', 'src-tauri/src/messaging.rs'):
            with self.subTest(extra=extra):
                bad = widened(config, extra)
                # The widening is real, not cosmetic: the extra file would ride
                # this route with no scope violation at all.
                self.assertNotEqual(MODULE.resolve_task(config, [MARKER, extra])['task'], TASK)
                self.assertEqual(MODULE.resolve_task(bad, [MARKER, extra])['task'], TASK)
                self.assertEqual(MODULE.scope_check_for_task(bad, TASK, [MARKER, extra])['scope_violations'], [])
                # And the declared oracles refuse it.
                with self.assertRaises(AssertionError):
                    self.assert_declared_ceiling(bad)
                with self.assertRaises(AssertionError):
                    self.assert_subset_table(bad)

    def test_dropping_a_neighbour_pin_is_caught(self):
        # Every neighbour oracle subtracts this task by name.
        for name in NEIGHBOUR_PINS:
            with self.subTest(neighbour=name):
                self.assertIn(TASK, (ROOT / 'tests' / name).read_text(), name)
        text = CONFIG.read_text()
        config = self.config()
        # Teeth, text level (test_crewing_k2_modules_route.py): drop this
        # route's three anchors from the neighbour's subtraction and its
        # historical hash stops reproducing the bytes it pinned.
        k2 = self.load_neighbour('test_crewing_k2_modules_route.py')
        self.assertEqual(hashlib.sha256(k2.previous_config_text(text).encode()).hexdigest(),
                         k2.OLD_CONFIG_HASH)
        kept = tuple(block for block in k2.LATER_BLOCKS if block not in BLOCKS)
        self.assertEqual(len(kept), len(k2.LATER_BLOCKS) - len(BLOCKS))
        with self.assertRaises(AssertionError):
            self.strip_blocks(text, kept + k2.BLOCKS, k2.OLD_CONFIG_HASH)
        # Teeth, structural level (test_crewing_c3b2_route.py): drop this task
        # from LATER_TASKS and the neighbour's canonical-JSON hash breaks.
        c3b2 = self.load_neighbour('test_crewing_c3b2_route.py')
        self.assertIn(TASK, c3b2.LATER_TASKS)
        self.assertEqual(self.canonical_hash(c3b2.previous_config(config)), c3b2.OLD_CONFIG_HASH)
        thinner = self.subtract(config, (c3b2.TASK, *(t for t in c3b2.LATER_TASKS if t != TASK)))
        self.assertNotEqual(self.canonical_hash(thinner), c3b2.OLD_CONFIG_HASH)

    @staticmethod
    def load_neighbour(name):
        loader = SourceFileLoader('neighbour_' + name[:-3], str(ROOT / 'tests' / name))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module

    @staticmethod
    def canonical_hash(config):
        return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    @staticmethod
    def subtract(config, tasks):
        old = copy.deepcopy(config)
        old['task_routing'] = [r for r in old['task_routing'] if r['task'] not in tasks]
        for section in ('allowed_file_patterns', 'harness_commands'):
            for task in tasks:
                old[section].pop(task, None)
        return old

    def strip_blocks(self, text, blocks, expected_hash):
        for start, end in blocks:
            assert text.count(start) == 1, start
            begin = text.index(start)
            stop = text.index(end, begin + len(start)) + len(end)
            text = text[:begin] + text[stop:]
        assert hashlib.sha256(text.encode()).hexdigest() == expected_hash, 'pin broken'
        return text

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
        git('config', 'user.name', '664 isolated fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        for path in FILES + EXTRAS:
            write(path, 'synthetic baseline fixture; not product acceptance\n')
        git('add', '-A')
        git('commit', '-qm', 'synthetic published baseline')
        base = git('rev-parse', 'HEAD')
        for path in files:
            write(path, 'Candidate step: person-keyed save in the receiver; synthetic only.\n')
        git('add', '-A')
        git('commit', '-qm', 'candidate increment')
        return repo, base, git('rev-parse', 'HEAD'), env

    def run_verify(self, repo, base, head, env, out, *, task=None):
        args = [str(GUARD), 'verify', '--home', 'crewing', '--repo', str(repo),
                '--base', base, '--head', head, '--json', str(out)]
        args += ['--task', task] if task else ['--auto-task']
        proc = subprocess.run(args, text=True, capture_output=True, env=env)
        return proc, json.loads(Path(out).read_text())

    def test_real_cli_routes_the_declared_eight_paths_and_plans_thirteen(self):
        """Exactly the live Crewing range eaa54c4f..d4b29952: all eight paths."""
        with tempfile.TemporaryDirectory(prefix='c664-cli-') as tmp:
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

    def test_real_cli_routes_the_s2b_diff_of_the_card(self):
        """The exact file set the card has to push: dist + db.rs + c3b2 harness."""
        wanted = ['dist/index.html', MARKER, 'tests/crewing_c3b2_candidate_harness.mjs']
        with tempfile.TemporaryDirectory(prefix='c664-cli-s2b-') as tmp:
            repo, base, head, env = self.synthetic_repo(tmp, wanted)
            proc, report = self.run_verify(repo, base, head, env, Path(tmp) / 's2b.json')
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report['status'], 'pass')
            self.assertEqual(report['task'], TASK)
            self.assertEqual(report['changed_files'], sorted(wanted))
            self.assertEqual(report['scope_violations'], [])
            self.assertEqual(report['protected_paths_touched'], [])
            self.assertFalse(report['override_present'])

    def test_real_cli_rejects_a_file_outside_the_ceiling(self):
        extra = 'src-tauri/Cargo.toml'
        with tempfile.TemporaryDirectory(prefix='c664-cli-neg-') as tmp:
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
        git('config', 'user.name', '664 superset fixture')
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
        with tempfile.TemporaryDirectory(prefix='c664-superset-') as tmp:
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
        with tempfile.TemporaryDirectory(prefix='c664-superset-neg-') as tmp:
            weakened = json.loads(CONFIG.read_text())
            weakened['harness_commands'][PREVIOUS_TASK] = weakened['harness_commands'][PREVIOUS_TASK][:-1]
            repo, old_ref, new_ref = self.superset_repo(tmp, json.dumps(weakened, indent=2) + '\n')
            code, payload = self.run_superset(repo, old_ref, new_ref, Path(tmp) / 'bad.json')
            self.assertEqual(code, 1, payload)
            self.assertEqual(payload['status'], 'fail')
            self.assertTrue(payload['missing_harnesses'])


if __name__ == '__main__':
    unittest.main()
