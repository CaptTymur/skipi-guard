"""`crewing-records` route: a door for stage records, and the code it keeps shut.

Request: BACKLOG skipi-ops №975, relayed by the manager session 2026-11-06. The
crewing home had no route for its own records: a one-file push of
`reports/CROSSCHECK-973-2026-11-06.md` fell to `default_task` = plugin-host and
died on `changes outside allowed patterns`, and so did the 158 records files of
`feature/crewing-930-red-active-session`. Measured on main 4a103333: `reports/`
and `scratchpad/` appear ZERO times in configs/homes/crewing.json, and zero
times in any of the other seven home configs.

NOT YET OWNER-AUTHORIZED. Merging a route is the owner's button (AGENTS.md); the
manager carries the question to DECISIONS with this PR's number. The route is
written so the decision is about the door, not about the tests.

WHAT THE ROUTE IS. Six glob patterns, `.json`/`.md`/`.txt` under `reports/` and
`scratchpad/` at any depth, in `when_all_files_in` and in the allowlist, and
nothing else: no `harness_commands` entry (the `repo-meta` precedent - a
text-only route runs no product harness), no change to `protected_paths`,
`release_sensitive_paths`, `release_tasks`, `stop_lines`, `default_task`,
`exact_task_file_sets`, `additive_task_checks` or the override surface.

WHY EXTENSIONS AND NOT `reports/**`. The working name in the request was
`when_all_files_in reports/** и scratchpad/**` with the qualifier «только текст
и json/md, без кода и dist». Those two halves disagree on the real branch, and
the qualifier wins here: `scratchpad/**` is a prefix door, and the 930 branch
carries 9 `.rs` files under it - four of them verbatim copies of product source
(`evidence/patched-slice-A/lib.rs` and friends) - plus 11 `.py`, 13 `.sh` and a
`.bin`. A prefix door would hand all of that a route with no harness. Narrow is
the safe direction in a gate, so the door is cut to the three extensions the
request named, and `test_a_prefix_door_would_have_taken_the_real_code` is the
mutation negative proving that choice is load-bearing rather than decorative.
The cost is stated in the PR: 52 of the 930 branch's 158 records files still do
not pass, and widening the set is a second owner decision, not this one.

WHAT IT CANNOT DO. The ceiling is six globs under two directory prefixes, so:

  * `when_all_files_in` means a records-ONLY push. One product file in the same
    diff and the whole thing falls back to plugin-host and fails on scope - the
    door cannot be used to smuggle a product change past the harnesses.
  * code and `dist/` are outside the three extensions, at any depth.
  * `protected_paths` and `release_sensitive_paths` are classified over the raw
    file list, before and independently of routing, so a records-shaped path
    that is also protected (`**/*token*`, `**/*secret*`, `**/*pair*`, `**/*qr*`)
    or release-sensitive (`scratchpad/package.json`, `scratchpad/version.txt`)
    is refused exactly as it is today. Two tests pin this; it is the reason this
    widening is not a weakening.
  * the task is not and cannot become a release task, so it inherits no release
    allowlist and buys no release privilege from its name.

ADDITIVITY. The two inserted text blocks subtract back to the accepted main
bytes (`MAIN_CONFIG_HASH`, guard main 4a103333), and the route is INSERTED after
№635 and before `repo-meta` per the house convention, so first-match-wins leaves
every existing rule's diffs where they were. The seven neighbour oracles that
reconstruct their own baselines by subtraction were extended in the same commit;
`test_every_neighbour_oracle_subtracts_this_route` pins that, with teeth.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

# The three SKIPI_GUARD_TEST_* overrides default to this checkout, so CI and a
# plain `python -m unittest discover -s tests` are unaffected. They exist so the
# whole suite can be run against a PROPOSED config before it is committed
# (read-only; the overrides cannot relax a check).
ROOT = Path(os.environ.get('SKIPI_GUARD_TEST_ROOT', Path(__file__).resolve().parents[1]))
GUARD = ROOT / 'bin/skipi-guard'
CONFIG = Path(os.environ.get('SKIPI_GUARD_TEST_CONFIG', ROOT / 'configs/homes/crewing.json'))
RUNS_AGAINST_REPO_CONFIG = CONFIG == ROOT / 'configs/homes/crewing.json'

LOADER = SourceFileLoader('guard_crewing_records', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = 'crewing-records'
RULE_NAME = ('crewing records routing: reports/ and scratchpad/ text records'
             ' (BACKLOG skipi-ops №975, 2026-11-06)')
PREVIOUS_TASK = 'crewing-635-single-user'
PATTERNS = [
    'reports/*.json',
    'reports/*.md',
    'reports/*.txt',
    'scratchpad/*.json',
    'scratchpad/*.md',
    'scratchpad/*.txt',
]

# The push that prompted the request: one file, one branch, refused on main.
BLOCKED_SINGLE_FILE = 'reports/CROSSCHECK-973-2026-11-06.md'

# Records paths measured in skipi-crewing f145c601..f59e4aa
# (`feature/crewing-930-red-active-session`, 158 files under scratchpad/, read
# only). These eight are the shapes: worklog, stage evidence, probe output,
# push transcript, calibration note, nested directories, and a .txt rc/log pair.
REAL_RECORDS = [
    'scratchpad/crewing-930/WORKLOG.md',
    'scratchpad/crewing-930/evidence/ACK_START-930-s1.json',
    'scratchpad/crewing-930/evidence/MANIFEST-slice-A-evidence.json',
    'scratchpad/crewing-930/evidence/SPLIT-930-two-piles.md',
    'scratchpad/crewing-930/live-probe-20261105/LIVE_PROBE_RESULT.json',
    'scratchpad/crewing-930/push-a-20261106/gate-check.txt',
    'scratchpad/crewing-930/push-b-20261106/push-transcript.txt',
    'scratchpad/crewing-930/sB2-tickets-20261106/calibration-930-sB2.md',
]

# The other half of the same measurement: 52 of the 158 are NOT .json/.md/.txt.
# These are the extensions, one real path each. This route takes none of them,
# which is the whole of its narrowness.
REAL_NON_TEXT = [
    'scratchpad/crewing-930/evidence/patched-slice-A/lib.rs',
    'scratchpad/crewing-930/evidence/snippet-930-red-test.rs',
    'scratchpad/crewing-930/evidence/cut-blocks.py',
    'scratchpad/crewing-930/evidence/run-930-s1.sh',
    'scratchpad/crewing-930/evidence/s2-out/check-product.log',
    'scratchpad/crewing-930/evidence/s2-out/check-product.rc',
    'scratchpad/crewing-930/evidence/s4-out/attempts',
    'scratchpad/crewing-930/live-probe-20261105/owner-authorization.jsonl',
    'scratchpad/crewing-930/live-probe-20261105/prod-body.bin',
    'scratchpad/crewing-930/push-a-20261106/harness-prerun-results.tsv',
    'scratchpad/crewing-930/rules-20261106/AGENTS.md.before',
]

# The product half of that same branch (5 files), plus the home's other product
# shapes. Each must lose a records diff it is mixed into.
REAL_PRODUCT = [
    'AGENTS.md',
    'src-tauri/src/lib.rs',
    'src-tauri/src/native_lifecycle.rs',
    'src-tauri/src/native_local_commit.rs',
    'src-tauri/src/native_local_joint_tests.rs',
]
FOREIGN = REAL_PRODUCT + REAL_NON_TEXT + [
    'dist/index.html',
    'presence-manifest.json',
    'keys/signing.pem',
    'src-tauri/Cargo.toml',
    'src-tauri/tauri.conf.json',
    '.github/workflows/skipi-guard.yml',
    'docs/crewing-pilot-c3b2/WORKLOG.md',
    'reports.md',                       # the prefix is a directory, not a stem
    'myreports/note.md',
    'docs/reports/note.md',             # the two prefixes are anchored at root
    'scratchpad.md',
    'scratchpad/deep.md/evil.rs',       # a .md DIRECTORY is not a .md file
    'dist/scratchpad/app.json',
]

# Records-shaped paths that are ALSO protected, so they stay refused. Each pair
# is (path, the protected rule it trips). Classification runs over the raw file
# list in verify(), before routing, so the route is irrelevant to the refusal.
PROTECTED_RECORDS = [
    ('reports/prod-token-dump.md', 'secrets/signing keys'),
    ('scratchpad/crewing-930/evidence/client-secret-notes.md', 'secrets/signing keys'),
    ('reports/qr-handshake-2026-11-06.md', 'pairing/QR/camera bridge'),
    ('scratchpad/crewing-930/evidence/pairing-trace.json', 'pairing/QR/camera bridge'),
    ('scratchpad/camera-permission-log.txt', 'pairing/QR/camera bridge'),
]
# Records-shaped paths that are ALSO release-sensitive. `version.txt` and
# `package.json` are literal patterns with no `/`, and pattern_matches() matches
# a literal on any path tail, so these land inside the records globs AND inside
# `versions/tags`. A non-release task refuses them.
RELEASE_RECORDS = [
    ('scratchpad/version.txt', 'versions/tags'),
    ('scratchpad/crewing-930/package.json', 'versions/tags'),
    ('reports/package-lock.json', 'versions/tags'),
]

PROTECTION_SECTIONS = (
    'home', 'repo', 'stop_lines', 'release_tasks', 'default_task',
    'exact_task_file_sets', 'protected_paths', 'release_sensitive_paths',
    'additive_task_checks',
)

# sha256 of configs/homes/crewing.json at guard main 4a103333 (pre-route bytes).
# Removing the two anchored blocks below must restore exactly these bytes, which
# is the proof that this change adds and never edits.
MAIN_CONFIG_HASH = '80905d0c4d11a2ab6825f11cae23518016656d08a78ba014bc890f7e2bd6ffba'
BLOCKS = (
    ('    {\n      "name": "%s",\n' % RULE_NAME, '\n    },\n'),
    (',\n    "%s": [\n      "reports/*.json"' % TASK, '\n    ]'),
)
# Neighbour oracles that reconstruct their own baseline by subtraction. Each must
# subtract this task, or its historical hash stops pinning the bytes it was
# accepted on. Dropping a pin is caught by the test at the bottom of this file.
NEIGHBOUR_PINS = (
    'test_security_escaping_191_route.py',
    'test_crewing_c3b1_route.py',
    'test_crewing_c3b2_route.py',
    'test_crewing_k2_modules_route.py',
    'test_crewing_k21_single_screen_route.py',
    'test_crewing_664_person_route.py',
    'test_crewing_635_single_user_route.py',
)


def previous_config_text(text: str) -> str:
    for start, end in BLOCKS:
        assert text.count(start) == 1, start
        begin = text.index(start)
        stop = text.index(end, begin + len(start)) + len(end)
        text = text[:begin] + text[stop:]
    return text


def old_config() -> dict:
    """The pre-change config, reconstructed by subtraction - never from a ref.

    Reading `HEAD` would mean the config without this route before the commit and
    with it after, so every old-versus-new assertion would silently compare the
    change with itself. The baseline is pinned by bytes instead, so these
    assertions still stand after merge.
    """
    return json.loads(previous_config_text(CONFIG.read_text(encoding='utf-8')))


def refusal_reasons(config: dict, files: list[str]) -> list[str]:
    """The reasons verify() would refuse this diff, without an override token.

    Mirrors the three refusal paths of verify(): a protected-path touch needs
    --override-protected, a release-sensitive touch is refused unless the task is
    a release task, and anything outside the allowlist is a scope violation.
    """
    task = MODULE.resolve_task(config, files)['task']
    reasons: list[str] = []
    if MODULE.classify_paths(files, config['protected_paths'], 'p'):
        reasons.append('protected')
    if (MODULE.classify_paths(files, config['release_sensitive_paths'], 'r')
            and not MODULE.is_release_task(config, task)):
        reasons.append('release-sensitive')
    scope = MODULE.scope_check_for_task(
        config, task, files, MODULE.effective_allowed_patterns(config, task, []))
    if scope and scope['scope_violations']:
        reasons.append('scope')
    return reasons


class CrewingRecordsRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.new = json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.old = old_config()

    def rule(self, config: dict | None = None) -> dict:
        config = self.new if config is None else config
        rules = [r for r in config['task_routing'] if r['task'] == TASK]
        self.assertEqual(len(rules), 1)
        return rules[0]

    # -- 1. the declared shape ------------------------------------------------
    def test_declared_shape_is_six_globs_and_nothing_else(self):
        rule = self.rule()
        self.assertEqual(rule['name'], RULE_NAME)
        self.assertEqual(rule['when_all_files_in'], PATTERNS)
        self.assertNotIn('require_any_of', rule)
        self.assertNotIn('require_all_of', rule)
        self.assertEqual(sorted(rule), ['name', 'task', 'when_all_files_in'])
        self.assertEqual(self.new['allowed_file_patterns'][TASK], PATTERNS)
        self.assertEqual(MODULE.effective_allowed_patterns(self.new, TASK, []), PATTERNS)
        # Two prefixes, three extensions, no exceptions.
        self.assertEqual({p.split('/')[0] for p in PATTERNS}, {'reports', 'scratchpad'})
        self.assertEqual({p.rsplit('.', 1)[1] for p in PATTERNS}, {'json', 'md', 'txt'})

    def test_the_route_runs_no_harness_and_that_is_the_repo_meta_precedent(self):
        self.assertNotIn(TASK, self.new['harness_commands'])
        self.assertEqual(MODULE.configured_harnesses(self.new, TASK), [])
        # Same shape as the home's other text-only route, which has no entry
        # either. A records push changes no product file, so there is nothing for
        # a product harness to check - and enrolling one would fail-close the
        # route the moment that script moved (test_harness_command_targets.py).
        self.assertNotIn('repo-meta', self.new['harness_commands'])
        # A harness-free task is only safe while the task is not a release task:
        # verify() refuses a release task with no harness_commands.
        self.assertFalse(MODULE.is_release_task(self.new, TASK))
        self.assertIn(TASK, MODULE.configured_tasks(self.new))

    def test_the_name_does_not_accidentally_buy_release_privileges(self):
        self.assertNotIn(TASK, self.new['release_tasks'])
        self.assertNotIn(TASK, self.new['exact_task_file_sets'])
        self.assertFalse(TASK.lower().startswith('release-'))
        self.assertFalse(TASK.lower().endswith('-release'))
        self.assertFalse(MODULE.is_release_task(self.new, TASK))
        # No release inheritance, so no release-sensitive pattern reaches the
        # allowlist through the back door of effective_allowed_patterns().
        allowed = MODULE.effective_allowed_patterns(self.new, TASK, [])
        for pattern in ('latest.json', 'catalog/**', 'release/**', 'fastlane/**',
                        'Cargo.toml', 'Cargo.lock', 'src-tauri/gen/**'):
            self.assertNotIn(pattern, allowed)

    # -- 2. positive: the push that was refused now routes and passes ---------
    def test_the_blocked_single_file_branch_passes(self):
        files = [BLOCKED_SINGLE_FILE]
        routed = MODULE.resolve_task(self.new, files)
        self.assertEqual(routed['task'], TASK)
        self.assertEqual(routed['rule'], RULE_NAME)
        self.assertEqual(refusal_reasons(self.new, files), [])
        # ... and was refused on exactly one count before this route existed.
        self.assertEqual(MODULE.resolve_task(self.old, files)['task'],
                         self.old['default_task'])
        self.assertEqual(refusal_reasons(self.old, files), ['scope'])

    def test_every_records_only_subset_of_the_real_930_branch_passes(self):
        subsets = [[path] for path in REAL_RECORDS]
        subsets += [REAL_RECORDS[:i] for i in range(2, len(REAL_RECORDS) + 1)]
        subsets += [[BLOCKED_SINGLE_FILE, *REAL_RECORDS], sorted(REAL_RECORDS)]
        for files in subsets:
            with self.subTest(files=files):
                routed = MODULE.resolve_task(self.new, files)
                self.assertEqual(routed['task'], TASK, files)
                self.assertEqual(refusal_reasons(self.new, files), [], files)
                self.assertEqual(refusal_reasons(self.old, files), ['scope'], files)

    def test_an_empty_diff_still_falls_to_the_default_task(self):
        self.assertEqual(MODULE.resolve_task(self.new, []),
                         MODULE.resolve_task(self.old, []))
        self.assertIsNone(MODULE.resolve_task(self.new, [])['rule'])

    # -- 3. negative: one file outside the two directories loses the push -----
    def test_one_foreign_path_in_the_same_branch_loses_the_whole_diff(self):
        for foreign in FOREIGN:
            with self.subTest(foreign=foreign):
                files = sorted([BLOCKED_SINGLE_FILE, foreign])
                routed = MODULE.resolve_task(self.new, files)
                self.assertNotEqual(routed['task'], TASK, files)
                self.assertIn('scope', refusal_reasons(self.new, files), files)
                # The mixed diff keeps EXACTLY the outcome it had before.
                self.assertEqual(routed, MODULE.resolve_task(self.old, files), files)
                self.assertEqual(refusal_reasons(self.new, files),
                                 refusal_reasons(self.old, files), files)

    def test_the_whole_930_branch_as_pushed_is_still_refused(self):
        """The 163-file push stays refused; splitting it is the home's job.

        Measured: records 158, product 5. The route is a door for the records
        pile alone, so the branch as it stands keeps failing, and the records
        half only passes once it is pushed on its own.
        """
        files = sorted([*REAL_RECORDS, *REAL_NON_TEXT, *REAL_PRODUCT])
        self.assertNotEqual(MODULE.resolve_task(self.new, files)['task'], TASK)
        self.assertIn('scope', refusal_reasons(self.new, files))
        self.assertEqual(refusal_reasons(self.new, files), refusal_reasons(self.old, files))

    def test_code_and_dist_are_outside_the_route_at_any_depth(self):
        for path in REAL_NON_TEXT + ['scratchpad/x.rs', 'scratchpad/a/b/c.sh',
                                     'reports/gen.py', 'scratchpad/dist/index.html',
                                     'reports/dist/bundle.js', 'scratchpad/a.mjs']:
            with self.subTest(path=path):
                self.assertEqual([p for p in PATTERNS if MODULE.pattern_matches(path, p)], [], path)
                self.assertNotEqual(MODULE.resolve_task(self.new, [path])['task'], TASK, path)
                self.assertIn('scope', refusal_reasons(self.new, [path]), path)

    def test_the_two_prefixes_are_anchored_at_the_repo_root(self):
        for path in ('docs/reports/note.md', 'myreports/note.md', 'src/scratchpad/a.json',
                     'reports.md', 'scratchpad.md', 'xreports/a.txt'):
            with self.subTest(path=path):
                self.assertEqual([p for p in PATTERNS if MODULE.pattern_matches(path, p)], [], path)

    # -- 4. fail-closed: the two checks that run before routing ---------------
    def test_a_records_shaped_protected_path_is_still_refused(self):
        """`**/*token*`, `**/*secret*`, `**/*pair*`, `**/*qr*`, `**/*camera*` are
        classified over the raw file list in verify(), before and independently of
        the resolved task, so the new door cannot open them."""
        for path, rule_name in PROTECTED_RECORDS:
            with self.subTest(path=path):
                # inside the route's own ceiling ...
                self.assertTrue(any(MODULE.pattern_matches(path, p) for p in PATTERNS), path)
                self.assertEqual(MODULE.resolve_task(self.new, [path])['task'], TASK, path)
                # ... and refused anyway, by the same rule as before.
                hits = MODULE.classify_paths([path], self.new['protected_paths'], 'p')
                self.assertEqual(sorted({h['rule'] for h in hits}), [rule_name], path)
                self.assertIn('protected', refusal_reasons(self.new, [path]), path)
                self.assertIn('protected', refusal_reasons(self.old, [path]), path)

    def test_a_records_shaped_release_sensitive_path_is_still_refused(self):
        for path, rule_name in RELEASE_RECORDS:
            with self.subTest(path=path):
                self.assertTrue(any(MODULE.pattern_matches(path, p) for p in PATTERNS), path)
                self.assertEqual(MODULE.resolve_task(self.new, [path])['task'], TASK, path)
                hits = MODULE.classify_paths([path], self.new['release_sensitive_paths'], 'r')
                self.assertEqual(sorted({h['rule'] for h in hits}), [rule_name], path)
                self.assertIn('release-sensitive', refusal_reasons(self.new, [path]), path)
                self.assertIn('release-sensitive', refusal_reasons(self.old, [path]), path)

    def test_the_eight_real_records_paths_are_neither_protected_nor_release(self):
        """Positive control for the two tests above: the measured records set is
        clean, so their refusals come from the named collisions and not from every
        path under those directories tripping something."""
        for path in [BLOCKED_SINGLE_FILE, *REAL_RECORDS]:
            with self.subTest(path=path):
                self.assertEqual(MODULE.classify_paths([path], self.new['protected_paths'], 'p'), [])
                self.assertEqual(
                    MODULE.classify_paths([path], self.new['release_sensitive_paths'], 'r'), [])

    # -- 5. mutation negative: the narrow door is load-bearing ----------------
    def test_a_prefix_door_would_have_taken_the_real_code(self):
        """The design decision, stated as a failing mutation.

        Widen the ceiling to the two prefixes the working name proposed and the
        930 branch's 9 `.rs`, 11 `.py`, 13 `.sh` and `.bin` files - product source
        copies among them - route to a task with no harness and pass. That is the
        weakening this route is cut narrow to avoid; if someone widens it, this
        test is the one that says what was given away.
        """
        wide = copy.deepcopy(self.new)
        for rule in wide['task_routing']:
            if rule['task'] == TASK:
                rule['when_all_files_in'] = ['reports/**', 'scratchpad/**']
        wide['allowed_file_patterns'][TASK] = ['reports/**', 'scratchpad/**']
        for path in REAL_NON_TEXT:
            with self.subTest(path=path):
                self.assertEqual(MODULE.resolve_task(wide, [path])['task'], TASK, path)
                self.assertEqual(refusal_reasons(wide, [path]), [], path)
                # The committed route refuses the same path.
                self.assertIn('scope', refusal_reasons(self.new, [path]), path)

    def test_the_route_still_cannot_carry_a_product_file_even_widened(self):
        """Negative control for the mutation above: a prefix door is wider, but
        `when_all_files_in` still means records-ONLY, so even the wide form cannot
        smuggle `src-tauri/src/lib.rs`. The harm of widening is what it admits
        under the two prefixes, not a new way into the product tree."""
        wide = copy.deepcopy(self.new)
        for rule in wide['task_routing']:
            if rule['task'] == TASK:
                rule['when_all_files_in'] = ['reports/**', 'scratchpad/**']
        wide['allowed_file_patterns'][TASK] = ['reports/**', 'scratchpad/**']
        files = sorted([REAL_RECORDS[0], 'src-tauri/src/lib.rs'])
        self.assertNotEqual(MODULE.resolve_task(wide, files)['task'], TASK)
        self.assertIn('scope', refusal_reasons(wide, files))

    # -- 6. additivity --------------------------------------------------------
    def test_removing_the_two_blocks_restores_the_accepted_main_bytes(self):
        old_text = previous_config_text(CONFIG.read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(old_text.encode()).hexdigest(), MAIN_CONFIG_HASH)
        stripped = copy.deepcopy(self.new)
        stripped['task_routing'] = [r for r in stripped['task_routing'] if r['task'] != TASK]
        del stripped['allowed_file_patterns'][TASK]
        self.assertEqual(json.loads(old_text), stripped)
        self.assertEqual(stripped, self.old)

    def test_route_sits_after_635_and_leaves_every_other_rule_untouched(self):
        """The house convention: each new crewing route is INSERTED after the
        previous crewing route and before `repo-meta`, not appended at the end,
        because every earlier route's oracle splices *LATER_TASKS into the crewing
        block at exactly that position."""
        tasks = [r['task'] for r in self.new['task_routing']]
        self.assertEqual(len(tasks), len(self.old['task_routing']) + 1)
        self.assertEqual(tasks.index(TASK), 8)
        self.assertEqual(tasks[7], PREVIOUS_TASK)
        self.assertEqual(tasks[9], 'repo-meta')
        self.assertEqual([r for r in self.new['task_routing'] if r['task'] != TASK],
                         self.old['task_routing'])

    def test_every_existing_rule_still_owns_its_own_declared_set(self):
        for rule in self.old['task_routing']:
            files = sorted(set(rule['when_all_files_in']))
            with self.subTest(rule=rule['name']):
                self.assertEqual(MODULE.resolve_task(self.new, files),
                                 MODULE.resolve_task(self.old, files), rule['name'])
                self.assertEqual(refusal_reasons(self.new, files),
                                 refusal_reasons(self.old, files), rule['name'])

    def test_every_diff_the_route_can_claim_used_to_fail(self):
        """The route converts guaranteed failures only.

        No allowlist in the pre-change config matched any path under the six
        globs, so every diff this rule can claim routed to `default_task` and died
        on scope. The rule therefore cannot change the outcome of a diff that
        passes today, nor of one another rule legitimately owns.
        """
        samples = [[BLOCKED_SINGLE_FILE], *[[p] for p in REAL_RECORDS], sorted(REAL_RECORDS)]
        for files in samples:
            with self.subTest(files=files):
                self.assertEqual(MODULE.resolve_task(self.old, files)['task'],
                                 self.old['default_task'], files)
                self.assertEqual(refusal_reasons(self.old, files), ['scope'], files)
        for path in [BLOCKED_SINGLE_FILE, *REAL_RECORDS]:
            for task, patterns in self.old['allowed_file_patterns'].items():
                hits = [p for p in patterns if MODULE.pattern_matches(path, p)]
                self.assertEqual(hits, [], (task, path))

    def test_protection_surface_is_deep_equal_to_the_accepted_config(self):
        for section in PROTECTION_SECTIONS:
            with self.subTest(section=section):
                self.assertEqual(self.new[section], self.old[section], section)

    def test_no_existing_allowlist_or_harness_entry_moved(self):
        for task, patterns in self.old['allowed_file_patterns'].items():
            self.assertEqual(self.new['allowed_file_patterns'][task], patterns, task)
        self.assertEqual(self.new['harness_commands'], self.old['harness_commands'])
        self.assertEqual(sorted(self.new['allowed_file_patterns']),
                         sorted([*self.old['allowed_file_patterns'], TASK]))

    def test_override_surface_is_unchanged(self):
        """None of the six patterns contains `presence`, so the presence override
        set does not grow, and no bootstrap token learns a new path."""
        for include_workflow in (False, True):
            self.assertEqual(
                MODULE.presence_override_allowed_patterns(self.new, include_workflow=include_workflow),
                MODULE.presence_override_allowed_patterns(self.old, include_workflow=include_workflow))
        for token in ('skipi-guard-workflow-bootstrap', 'crewing-presence-contracts-bootstrap',
                      'crewing-theme-default-bootstrap', 'crewing-records-bootstrap', 'nonsense'):
            self.assertEqual(MODULE.bootstrap_override_allowed_patterns(self.new, token),
                             MODULE.bootstrap_override_allowed_patterns(self.old, token), token)
        # An unknown token still fails closed, records diff or not.
        self.assertEqual(
            MODULE.override_policy_errors(self.new, 'crewing-records-approved', REAL_RECORDS),
            ['unknown override token'])

    # -- 7. neighbour oracles -------------------------------------------------
    def test_every_neighbour_oracle_subtracts_this_route(self):
        """Seven oracles reconstruct their own baseline from the live config. Each
        must subtract this task by name, or its historical hash stops pinning the
        bytes it was accepted on. The teeth are below: put the pin back wrong and
        the neighbour's own hash breaks."""
        for name in NEIGHBOUR_PINS:
            with self.subTest(neighbour=name):
                self.assertIn(TASK, (ROOT / 'tests' / name).read_text(encoding='utf-8'), name)

    def test_dropping_this_route_from_a_neighbour_pin_is_caught(self):
        text = CONFIG.read_text(encoding='utf-8')
        # Text level: the 635 oracle subtracts this route's two anchors before its
        # own three. Drop them and its pre-635 byte hash stops reproducing.
        later = self.load_neighbour('test_crewing_635_single_user_route.py')
        self.assertEqual(later.LATER_TASKS, (TASK,))
        self.assertEqual(
            hashlib.sha256(later.previous_config_text(text).encode()).hexdigest(),
            later.OLD_CONFIG_HASH)
        thinner = text
        for start, end in later.BLOCKS:
            begin = thinner.index(start)
            stop = thinner.index(end, begin + len(start)) + len(end)
            thinner = thinner[:begin] + thinner[stop:]
        self.assertNotEqual(hashlib.sha256(thinner.encode()).hexdigest(), later.OLD_CONFIG_HASH)
        # Structural level: drop this task from the c3b2 oracle's LATER_TASKS and
        # its canonical-JSON hash breaks.
        c3b2 = self.load_neighbour('test_crewing_c3b2_route.py')
        self.assertIn(TASK, c3b2.LATER_TASKS)
        self.assertEqual(self.canonical_hash(c3b2.previous_config(self.new)), c3b2.OLD_CONFIG_HASH)
        config = copy.deepcopy(self.new)
        drop = (c3b2.TASK, *(t for t in c3b2.LATER_TASKS if t != TASK))
        config['task_routing'] = [r for r in config['task_routing'] if r['task'] not in drop]
        for section in ('allowed_file_patterns', 'harness_commands'):
            for task in drop:
                config[section].pop(task, None)
        self.assertNotEqual(self.canonical_hash(config), c3b2.OLD_CONFIG_HASH)

    @staticmethod
    def load_neighbour(name: str):
        loader = SourceFileLoader('records_neighbour_' + name[:-3], str(ROOT / 'tests' / name))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module

    @staticmethod
    def canonical_hash(config: dict) -> str:
        return hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    # -- 8. real CLI ----------------------------------------------------------
    @unittest.skipUnless(RUNS_AGAINST_REPO_CONFIG,
                         'the CLI reads configs from its own checkout; draft review runs the library tests')
    def test_real_cli_passes_the_single_file_branch_and_fails_a_foreign_one(self):
        with tempfile.TemporaryDirectory(prefix='skipi-guard-records-fixture-') as tmp:
            repo = Path(tmp)

            def git(*args: str) -> str:
                return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                      capture_output=True, text=True).stdout.strip()

            def commit(paths: list[str], message: str) -> str:
                for path in paths:
                    target = repo / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('fixture\n', encoding='utf-8')
                git('add', '--', *paths)
                git('commit', '-qm', message)
                return git('rev-parse', 'HEAD')

            def guard(base: str, head: str, name: str) -> dict:
                report = repo / name
                # No --run-harness: verify never creates a worktree and never executes.
                proc = subprocess.run(
                    [str(GUARD), 'verify', '--home', 'crewing', '--auto-task', '--repo', str(repo),
                     '--base', base, '--head', head, '--json', str(report)],
                    capture_output=True, text=True)
                result = json.loads(report.read_text(encoding='utf-8'))
                self.assertEqual(proc.returncode, 0 if result['status'] == 'pass' else 1,
                                 proc.stdout + proc.stderr)
                return result

            git('init', '-q', '-b', 'main')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'fixture')
            base = commit(['README.md'], 'base')

            # positive: the branch that was refused on main
            head = commit([BLOCKED_SINGLE_FILE], 'records: crosscheck 973')
            result = guard(base, head, 'guard-records.json')
            self.assertEqual(result['status'], 'pass', result['errors'])
            self.assertEqual(result['task'], TASK)
            self.assertEqual(result['task_rule'], RULE_NAME)
            self.assertEqual(result['changed_files'], [BLOCKED_SINGLE_FILE])
            self.assertEqual(result['scope_violations'], [])
            self.assertEqual(result['protected_paths_touched'], [])
            self.assertEqual(result['release_paths_touched'], [])
            self.assertFalse(result['release_changes'])
            self.assertEqual(result['tests'], [])
            self.assertEqual(result['errors'], [])

            # negative: one file outside the two directories, same branch
            head = commit(['src-tauri/src/lib.rs'], 'records + product')
            result = guard(base, head, 'guard-mixed.json')
            self.assertEqual(result['status'], 'fail')
            self.assertEqual(result['task'], self.new['default_task'])
            self.assertIsNone(result['task_rule'])
            self.assertEqual(sorted(result['changed_files']),
                             sorted([BLOCKED_SINGLE_FILE, 'src-tauri/src/lib.rs']))
            self.assertEqual(sorted(result['scope_violations']),
                             sorted([BLOCKED_SINGLE_FILE, 'src-tauri/src/lib.rs']))
            self.assertIn("changes outside allowed patterns for task 'plugin-host'",
                          result['errors'])

    @unittest.skipUnless(RUNS_AGAINST_REPO_CONFIG,
                         'the CLI reads configs from its own checkout; draft review runs the library tests')
    def test_real_cli_refuses_a_records_shaped_protected_path(self):
        """The fail-closed claim, through the CLI rather than the library."""
        with tempfile.TemporaryDirectory(prefix='skipi-guard-records-protected-') as tmp:
            repo = Path(tmp)

            def git(*args: str) -> str:
                return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                      capture_output=True, text=True).stdout.strip()

            git('init', '-q', '-b', 'main')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'fixture')
            (repo / 'README.md').write_text('fixture\n', encoding='utf-8')
            git('add', 'README.md')
            git('commit', '-qm', 'base')
            base = git('rev-parse', 'HEAD')

            path = PROTECTED_RECORDS[0][0]
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixture\n', encoding='utf-8')
            git('add', '--', path)
            git('commit', '-qm', 'records: protected shape')
            head = git('rev-parse', 'HEAD')

            report = repo / 'guard.json'
            proc = subprocess.run(
                [str(GUARD), 'verify', '--home', 'crewing', '--auto-task', '--repo', str(repo),
                 '--base', base, '--head', head, '--json', str(report)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            result = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(result['task'], TASK)
            self.assertEqual(result['scope_violations'], [])
            self.assertEqual([t['path'] for t in result['protected_paths_touched']], [path])
            self.assertTrue(any('protected' in error for error in result['errors']), result['errors'])


if __name__ == '__main__':
    unittest.main()
