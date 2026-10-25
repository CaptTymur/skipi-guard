"""№635 single-user route: dispatch, ceiling, additivity, and the door that stays shut.

Owner decision: skipi-ops DECISIONS (1482), 2026-10-21, `owner1482-2026-10-21`.
Handoff: HANDOFF-2026-10-20-crewing-635-guard-route.md. Coordinator basis:
reports/20261021-E35-CREWING635-GUARD-SCOPE-RESOLUTION01.json, sha256
e83d20fbba91e43367f061fdccd323022659e356864c7794983834b0dd5791e5.

The route is additive: appended LAST to `task_routing`, so all fourteen existing
rules keep priority (first match wins). Its safety rests on the MARKER THEOREM:
`require_any_of` is exactly the fifteen new №635 files, and every one of them is
absent from the whole pre-change config. Therefore any diff this rule can claim
routed to `default_task` = plugin-host before, where it failed on scope. The rule
converts guaranteed failures only; it cannot change the outcome of any diff that
passes today, nor of any diff another rule legitimately owns.

The 664 precedent proves its ceiling by enumerating 2**8 subsets. Here 2**31 is
not enumerable, so the ceiling is proven by structure instead: all singletons,
all pairs, all full-minus-one sets, the full set, a seeded sample, and a negative
control that adds one foreign path to each.

The ceiling is the COMMITTED set of 31, including src-tauri/Cargo.{toml,lock}
(manager decision A, 2026-10-22, superseding O3 of 2026-10-21). Listing those two
in a non-release task's allowlist grants nothing: the release-sensitive check at
bin/skipi-guard:509 runs over the raw file list, independent of task, route and
allowlist, so it still refuses them. The allowlist only removes the scope failure.
test_cargo_delta_is_still_blocked and test_exactly_one_named_blocker_remains pin
exactly that, and they are the reason this widening is not a weakening.

Nothing is relaxed. stop_lines, protected_paths, release_sensitive_paths,
release_tasks, additive_task_checks, exact_task_file_sets, default_task and the
override surface come back deep-equal to the pre-change config, and
`test_cargo_delta_is_still_blocked` pins the one thing a route must not buy:
src-tauri/Cargo.toml and src-tauri/Cargo.lock remain release-sensitive and
remain refused for this non-release task (owner choice O3, 2026-10-21).
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import os
import random
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

# The three SKIPI_GUARD_TEST_* overrides default to this checkout, so CI and a
# plain `python -m unittest discover -s tests` are unaffected. They exist so the
# whole suite can be run against a PROPOSED config before it is committed, which
# is how this route was reviewed (read-only; the overrides cannot relax a check).
ROOT = Path(os.environ.get('SKIPI_GUARD_TEST_ROOT', Path(__file__).resolve().parents[1]))
GUARD = ROOT / 'bin/skipi-guard'
CONFIG = Path(os.environ.get('SKIPI_GUARD_TEST_CONFIG', ROOT / 'configs/homes/crewing.json'))
RUNS_AGAINST_REPO_CONFIG = CONFIG == ROOT / 'configs/homes/crewing.json'

LOADER = SourceFileLoader('guard_crewing_635', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

TASK = 'crewing-635-single-user'
RULE_NAME = 'crewing №635 single-user native account and private store (owner1482, 2026-10-21)'

# The fifteen new №635 files. Each is absent from the entire pre-change config,
# which is what makes them markers (test_marker_theorem).
MARKERS = [
    'src-tauri/src/native_account.rs',
    'src-tauri/src/native_binding.rs',
    'src-tauri/src/native_database.rs',
    'src-tauri/src/native_database_probe.rs',
    'src-tauri/src/native_fresh.rs',
    'src-tauri/src/native_keys.rs',
    'src-tauri/src/native_lifecycle.rs',
    'src-tauri/src/native_local_commit.rs',
    'src-tauri/src/native_local_joint_tests.rs',
    'src-tauri/src/native_profile.rs',
    'src-tauri/src/native_session_record.rs',
    'src-tauri/src/private_json.rs',
    'src-tauri/src/private_store.rs',
    'tests/crewing635_public_settings_harness.mjs',
    'tests/fixtures/crewing_public_settings.mjs',
]
# The fourteen already-tracked files №635 modifies. Not markers: they are not
# specific to №635, and making them markers would hand the route diffs that
# have nothing to do with this work.
CARRIED = [
    'dist/index.html',
    'src-tauri/Cargo.lock',
    'src-tauri/Cargo.toml',
    'src-tauri/src/crewing_intake.rs',
    'src-tauri/src/db.rs',
    'src-tauri/src/lib.rs',
    'src-tauri/src/messaging.rs',
    'tests/crewing_c3b1_pilot_harness.mjs',
    'tests/crewing_c3b2_candidate_harness.mjs',
    'tests/crewing_compliance_manual_flow_harness.mjs',
    'tests/crewing_crew_flow_demo_harness.mjs',
    'tests/crewing_mailbox_contract_harness.mjs',
    'tests/crewing_presence_contract_harness.mjs',
    'tests/crewing_theme_default_harness.mjs',
    'tests/trial_activate_unconnected_harness.mjs',
    'tests/trial_gate_wired_harness.mjs',
]
CEILING = sorted(CARRIED + MARKERS)

# Deliberately outside the ceiling. The twelve scratchpad/ paths are the
# writer's agent machinery (supervisor/worker scripts, progress JSON, worklog);
# scratchpad/ is not gitignored in that repo, so a stray `git add` is held out
# by the allowlist and nothing else.
SCRATCHPAD = [
    'scratchpad/crewing-635-single-user/visible-01a148e9/PREP.md',
    'scratchpad/crewing-635-single-user/visible-01a148e9/PR_BODY.md',
    'scratchpad/crewing-635-single-user/visible-01a148e9/SERVER-DEPENDENCIES.md',
    'scratchpad/crewing-635-single-user/visible-01a148e9/WORKLOG.md',
    'scratchpad/crewing-635-single-user/visible-01a148e9/build-03-supervisor.py',
    'scratchpad/crewing-635-single-user/visible-01a148e9/build-03-worker.py',
    'scratchpad/crewing-635-single-user/visible-01a148e9/commit-push-progress.json',
    'scratchpad/crewing-635-single-user/visible-01a148e9/commit-push-supervisor.py',
    'scratchpad/crewing-635-single-user/visible-01a148e9/commit-push-worker.py',
    'scratchpad/crewing-635-single-user/visible-01a148e9/owner-04-launcher.py',
    'scratchpad/crewing-635-single-user/visible-01a148e9/pre-push-guard.json',
    'scratchpad/crewing-635-single-user/visible-01a148e9/source-pins.json',
]
CARGO = ['src-tauri/Cargo.toml', 'src-tauri/Cargo.lock']
# The three (path, rule) release-sensitive touches the committed set carries.
# Two files, three touches: Cargo.lock matches in two different groups.
CARGO_RELEASE_TOUCHES = {
    ('src-tauri/Cargo.lock', 'versions/tags'),
    ('src-tauri/Cargo.lock', 'Tauri/Cargo/mobile generated files'),
    ('src-tauri/Cargo.toml', 'versions/tags'),
}
FOREIGN = SCRATCHPAD + [
    '.github/workflows/skipi-guard.yml',
    'presence-manifest.json',
    'keys/signing.pem',
    'src-tauri/tauri.conf.json',
    'src-tauri/src/contact.rs',
    'docs/crewing-pilot-c3b2/WORKLOG.md',
]

HARNESS_PLAN = [
    ('crewing_plugin_isolation', 'node tests/crewing_plugin_isolation_harness.mjs'),
    ('shared_host_runtime_isolation',
     'node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs'),
    ('crewing_presence_contract', 'node tests/crewing_presence_contract_harness.mjs'),
    ('crewing_crew_flow_demo', 'node tests/crewing_crew_flow_demo_harness.mjs'),
    ('crewing_build_provenance', 'node tests/build_provenance_harness.mjs'),
    ('crewing_theme_default', 'node tests/crewing_theme_default_harness.mjs'),
    ('crewing_csp_inline_handlers', 'node tests/csp_inline_handlers_harness.mjs'),
    ('crewing_mailbox_contract', 'node tests/crewing_mailbox_contract_harness.mjs'),
    ('crewing_escaping_negative', 'node tests/crewing_escaping_negative_harness.mjs'),
    ('crewing_compliance_manual_flow', 'node tests/crewing_compliance_manual_flow_harness.mjs'),
    ('crewing_mail_cv_intake_demo', 'node tests/crewing_mail_cv_intake_demo_harness.mjs'),
    ('crewing_settings5_preview_gated', 'node tests/settings5_preview_gated_harness.mjs'),
    ('crewing_trial_gate_wired', 'node tests/trial_gate_wired_harness.mjs'),
    ('crewing_trial_activate_unconnected', 'node tests/trial_activate_unconnected_harness.mjs'),
    ('crewing_stack_build_metadata', 'node tests/stack_build_metadata_harness.mjs'),
    ('crewing_stack_verification_negative_control',
     'node tests/stack_verification_negative_control_harness.mjs'),
    ('crewing_c3b1_pilot', 'node tests/crewing_c3b1_pilot_harness.mjs'),
    ('crewing_c3b2_candidate', 'node tests/crewing_c3b2_candidate_harness.mjs'),
    ('crewing635_public_settings', 'node tests/crewing635_public_settings_harness.mjs'),
]

PROTECTION_SECTIONS = (
    'home', 'repo', 'stop_lines', 'release_tasks', 'default_task',
    'exact_task_file_sets', 'protected_paths', 'release_sensitive_paths',
    'additive_task_checks',
)


# sha256 of configs/homes/crewing.json at guard main ab97a092 (pre-route bytes).
# Removing the three anchored blocks below must restore exactly these bytes, which
# is the proof that this change adds and never edits.
OLD_CONFIG_HASH = '087f7b03e4e901e007255d5e4d0388783b98a39af0061ce77a9c6d002553ff3f'
BLOCKS = (
    ('    {\n      "name": "%s",\n' % RULE_NAME, '\n    },\n'),
    (',\n    "%s": [\n      {\n' % TASK, '\n    ]'),
    (',\n    "%s": [\n      "dist/index.html"' % TASK, '\n    ]'),
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

    Reading `HEAD` was the first version's defect: before the commit it meant the
    config without this route, after the commit it means the config with it, so
    every old-versus-new assertion silently compared the change with itself. The
    baseline is pinned by bytes instead, so these assertions stand after merge.
    """
    return json.loads(previous_config_text(CONFIG.read_text(encoding='utf-8')))


def every_pattern(config: dict) -> set[str]:
    """Every path pattern the config mentions anywhere."""
    patterns: set[str] = set()
    for rule in config.get('task_routing', []):
        for key in ('when_all_files_in', 'require_any_of', 'require_all_of'):
            patterns.update(rule.get(key, []))
    for task_patterns in config.get('allowed_file_patterns', {}).values():
        patterns.update(task_patterns)
    for file_set in config.get('exact_task_file_sets', {}).values():
        patterns.update(file_set)
    for rule in config.get('additive_task_checks', []):
        patterns.update(rule.get('patterns', []))
    for section in ('protected_paths', 'release_sensitive_paths'):
        for rule in config.get(section, []):
            patterns.update(rule.get('patterns', []))
    return patterns


def refusal_reasons(config: dict, files: list[str]) -> list[str]:
    """The reasons verify() would refuse this diff, without an override token.

    Mirrors the three refusal paths of verify(): a protected-path touch needs
    --override-protected, a release-sensitive touch is refused unless the task
    is a release task, and anything outside the allowlist is a scope violation.
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


class Crewing635SingleUserRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.new = json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.old = old_config()

    # -- 1. dispatch ----------------------------------------------------------
    def test_declared_set_routes_to_the_new_task_with_no_violation(self):
        routed = MODULE.resolve_task(self.new, CEILING)
        self.assertEqual(routed['task'], TASK)
        self.assertEqual(routed['rule'], RULE_NAME)
        allowed = MODULE.effective_allowed_patterns(self.new, TASK, [])
        self.assertEqual(sorted(allowed), CEILING)
        scope = MODULE.scope_check_for_task(self.new, TASK, CEILING, allowed)
        self.assertEqual(scope['scope_violations'], [])
        self.assertEqual(MODULE.classify_paths(CEILING, self.new['protected_paths'], 'p'), [])
        self.assertFalse(MODULE.is_release_task(self.new, TASK))
        # Deliberately NOT asserting that the set is release-clean: it is not.
        # That is test_cargo_delta_is_still_blocked's subject.
        self.assertIn(TASK, MODULE.configured_tasks(self.new))

    def test_the_name_does_not_accidentally_buy_release_privileges(self):
        # is_release_task() matches by NAME: `release`, `release-*`, `*-release`.
        # Such a name would also pull every release_sensitive pattern into the
        # allowlist via effective_allowed_patterns.
        self.assertFalse(MODULE.is_release_task(self.new, TASK))
        self.assertNotIn(TASK, self.new['release_tasks'])
        self.assertFalse(TASK.startswith('release-') or TASK.endswith('-release'))

    # -- 2. marker theorem ----------------------------------------------------
    def test_marker_theorem_every_marker_was_absent_from_the_old_config(self):
        patterns = every_pattern(self.old)
        for marker in MARKERS:
            hits = [p for p in patterns if MODULE.pattern_matches(marker, p)]
            self.assertEqual(hits, [], f'{marker} already matched {hits} before this route')

    def test_every_diff_the_route_can_claim_used_to_fail(self):
        rng = random.Random(635)
        samples = [list(MARKERS), [MARKERS[0]], CEILING]
        samples += [rng.sample(CEILING, rng.randint(1, 31)) for _ in range(200)]
        for files in samples:
            if not any(f in MARKERS for f in files):
                continue
            routed = MODULE.resolve_task(self.old, files)
            self.assertEqual(routed['task'], self.old['default_task'])
            self.assertIsNone(routed['rule'])
            scope = MODULE.scope_check_for_task(
                self.old, routed['task'], files,
                MODULE.effective_allowed_patterns(self.old, routed['task'], []))
            self.assertTrue(scope['scope_violations'], files)

    # -- 3. additivity --------------------------------------------------------
    def test_route_sits_after_664_and_leaves_every_other_rule_untouched(self):
        """The house convention: each new crewing route is INSERTED after the
        previous crewing route, not appended at the end. The neighbour chain
        depends on it - every earlier route's test splices *LATER_TASKS into the
        crewing block, before 'repo-meta'. Appending last was this change's first
        design and it was wrong here, behaviourally equivalent but inconsistent
        with the mechanism the house uses to restore its own history."""
        tasks = [r['task'] for r in self.new['task_routing']]
        self.assertEqual(len(tasks), len(self.old['task_routing']) + 1)
        self.assertEqual(tasks.index(TASK), 7)
        self.assertEqual(tasks[6], 'crewing-664-person')
        self.assertEqual(tasks[8], 'repo-meta')
        self.assertEqual([r for r in self.new['task_routing'] if r['task'] != TASK],
                         self.old['task_routing'])

    def test_stripping_the_insertions_restores_the_old_config_exactly(self):
        stripped = copy.deepcopy(self.new)
        stripped['task_routing'] = [r for r in stripped['task_routing'] if r['task'] != TASK]
        del stripped['allowed_file_patterns'][TASK]
        del stripped['harness_commands'][TASK]
        self.assertEqual(stripped, self.old)

    def test_every_existing_rule_still_owns_its_own_declared_set(self):
        for rule in self.old['task_routing']:
            files = sorted(set(rule['when_all_files_in']))
            before = MODULE.resolve_task(self.old, files)
            after = MODULE.resolve_task(self.new, files)
            self.assertEqual(after, before, rule['name'])

    # -- 4. ceiling -----------------------------------------------------------
    def test_ceiling_holds_for_singletons_pairs_full_and_full_minus_one(self):
        subsets = [[f] for f in CEILING]
        subsets += [list(pair) for pair in itertools.combinations(CEILING, 2)]
        subsets += [[f for f in CEILING if f != drop] for drop in CEILING]
        subsets.append(list(CEILING))
        rng = random.Random(1482)
        subsets += [rng.sample(CEILING, rng.randint(3, 30)) for _ in range(2000)]
        self.assertEqual(len(subsets), 31 + 465 + 31 + 1 + 2000)
        allowed = MODULE.effective_allowed_patterns(self.new, TASK, [])
        for files in subsets:
            routed = MODULE.resolve_task(self.new, files)
            if routed['task'] != TASK:
                # An earlier rule owns it; that is additivity, not a leak.
                self.assertEqual(routed, MODULE.resolve_task(self.old, files), files)
                continue
            self.assertTrue(any(f in MARKERS for f in files), files)
            scope = MODULE.scope_check_for_task(self.new, TASK, files, allowed)
            self.assertEqual(scope['scope_violations'], [], files)

    def test_one_foreign_path_is_always_refused(self):
        allowed = MODULE.effective_allowed_patterns(self.new, TASK, [])
        for foreign in FOREIGN:
            files = sorted(CEILING + [foreign])
            self.assertTrue(refusal_reasons(self.new, files), foreign)
            routed = MODULE.resolve_task(self.new, files)
            # The route never claims a diff carrying a path outside its ceiling.
            self.assertNotEqual(routed['task'], TASK, foreign)
            self.assertEqual(routed['task'], self.new['default_task'], foreign)
            # And the foreign path is never allowed under this task.
            self.assertFalse(
                any(MODULE.pattern_matches(foreign, pattern) for pattern in allowed), foreign)

    def test_adding_a_foreign_path_also_loses_the_whole_set(self):
        # Mechanically important for the writer: when_all_files_in means one
        # unaccounted name drops the entire diff to the default task, so the 29
        # paths stop being allowed too. The route tolerates fewer paths, never more.
        for foreign in FOREIGN:
            files = sorted(CEILING + [foreign])
            routed = MODULE.resolve_task(self.new, files)
            scope = MODULE.scope_check_for_task(
                self.new, routed['task'], files,
                MODULE.effective_allowed_patterns(self.new, routed['task'], []))
            self.assertGreaterEqual(len(scope['scope_violations']), 20, foreign)

    def test_scratchpad_machinery_can_never_ride_along(self):
        for path in SCRATCHPAD:
            self.assertNotIn(path, CEILING)
            self.assertEqual(
                [p for p in every_pattern(self.new) if MODULE.pattern_matches(path, p)], [], path)

    # -- 5. require_any_of negative control -----------------------------------
    def test_marker_free_diffs_keep_exactly_their_old_outcome(self):
        subsets = [[f] for f in CARRIED]
        subsets += [list(pair) for pair in itertools.combinations(CARRIED, 2)]
        subsets.append(list(CARRIED))
        for files in subsets:
            self.assertEqual(MODULE.resolve_task(self.new, files),
                             MODULE.resolve_task(self.old, files), files)
            self.assertNotEqual(MODULE.resolve_task(self.new, files)['task'], TASK, files)

    # -- 6. protection surface ------------------------------------------------
    def test_protection_surface_is_deep_equal_to_the_old_config(self):
        for section in PROTECTION_SECTIONS:
            self.assertEqual(self.new[section], self.old[section], section)

    def test_no_existing_allowlist_or_harness_entry_moved(self):
        for task, patterns in self.old['allowed_file_patterns'].items():
            self.assertEqual(self.new['allowed_file_patterns'][task], patterns, task)
        for task, commands in self.old['harness_commands'].items():
            self.assertEqual(self.new['harness_commands'][task], commands, task)

    def test_override_surface_is_unchanged(self):
        for include_workflow in (False, True):
            self.assertEqual(
                MODULE.presence_override_allowed_patterns(self.new, include_workflow=include_workflow),
                MODULE.presence_override_allowed_patterns(self.old, include_workflow=include_workflow))
        for token in ('skipi-guard-workflow-bootstrap', 'crewing-presence-contracts-bootstrap',
                      'crewing-theme-default-bootstrap', f'{TASK}-bootstrap'):
            self.assertEqual(MODULE.bootstrap_override_allowed_patterns(self.new, token),
                             MODULE.bootstrap_override_allowed_patterns(self.old, token), token)

    # -- 7. the door that stays shut --------------------------------------
    def test_cargo_delta_is_still_blocked(self):
        """The pin that makes ceiling 31 a widening of scope, not of permission.

        Manager decision A was made conditional on this test asserting the strong
        form: the route MATCHES the committed set, scope is clean, and the
        release-sensitive check refuses it anyway.
        """
        routed = MODULE.resolve_task(self.new, CEILING)
        self.assertEqual(routed['task'], TASK)                      # route matched
        allowed = MODULE.effective_allowed_patterns(self.new, TASK, [])
        scope = MODULE.scope_check_for_task(self.new, TASK, CEILING, allowed)
        self.assertEqual(scope['scope_violations'], [])             # scope clean
        touches = {(t['path'], t['rule'])
                   for t in MODULE.classify_paths(CEILING, self.new['release_sensitive_paths'], 'r')}
        self.assertEqual(touches, CARGO_RELEASE_TOUCHES)            # still classified
        self.assertFalse(MODULE.is_release_task(self.new, TASK))    # and not exempt
        self.assertEqual(refusal_reasons(self.new, CEILING), ['release-sensitive'])
        # The allowlist entry alone must not create an exemption anywhere.
        for path in CARGO:
            self.assertTrue(MODULE.classify_paths([path], self.new['release_sensitive_paths'], 'r'), path)
            self.assertIn(path, allowed)

    def test_exactly_one_named_blocker_remains(self):
        """The stage's acceptance criterion: one named blocker, not 'push passes'."""
        self.assertEqual(refusal_reasons(self.new, CEILING), ['release-sensitive'])
        old_task = MODULE.resolve_task(self.old, CEILING)['task']
        self.assertEqual(old_task, self.old['default_task'])
        self.assertEqual(sorted(refusal_reasons(self.old, CEILING)), ['release-sensitive', 'scope'])
        # And the count the manager's decision turns on: 27 scope failures before,
        # zero after, with the one release blocker surviving both.
        before = MODULE.scope_check_for_task(
            self.old, old_task, CEILING,
            MODULE.effective_allowed_patterns(self.old, old_task, []))
        self.assertEqual(len(before['scope_violations']), 27)
        after = MODULE.scope_check_for_task(
            self.new, TASK, CEILING, MODULE.effective_allowed_patterns(self.new, TASK, []))
        self.assertEqual(after['scope_violations'], [])

    def test_the_route_is_not_and_cannot_become_a_release_task(self):
        self.assertFalse(MODULE.is_release_task(self.new, TASK))
        self.assertNotIn(TASK, self.new['release_tasks'])
        self.assertNotIn(TASK, self.new['exact_task_file_sets'])
        self.assertFalse(TASK.startswith('release-') or TASK.endswith('-release'))
        self.assertNotEqual(TASK.lower(), 'release')
        # An exact-set release task would pass release-sensitive without widening
        # the allowlist (:280-296 guards the widening with `not exact_task`).
        # Forbidden by manager decision (1502); pinned so it cannot arrive quietly.
        patterns = MODULE.effective_allowed_patterns(self.new, TASK, [])
        for pattern in ('latest.json', 'catalog/**', 'fastlane/**', 'release/**'):
            self.assertNotIn(pattern, patterns)

    def test_only_the_two_cargo_paths_are_release_sensitive(self):
        for path in CEILING:
            hits = MODULE.classify_paths([path], self.new['release_sensitive_paths'], 'r')
            self.assertEqual(bool(hits), path in CARGO, path)
            self.assertEqual(MODULE.classify_paths([path], self.new['protected_paths'], 'p'), [], path)

    # -- 8. harness plan ------------------------------------------------------
    def test_harness_plan_is_the_verbatim_union_plus_one_new_harness(self):
        planned = [(h['name'], h['command']) for h in self.new['harness_commands'][TASK]]
        self.assertEqual(planned, HARNESS_PLAN)
        self.assertEqual(len({c for _, c in planned}), len(planned), 'no command may run twice')
        known = {(h['name'], h['command'])
                 for commands in self.old['harness_commands'].values() for h in commands}
        for entry in planned[:-1]:
            self.assertIn(entry, known, f'{entry[0]} is not a verbatim existing harness')
        self.assertNotIn(planned[-1], known)
        self.assertEqual(planned[-1][1], 'node tests/crewing635_public_settings_harness.mjs')

    def test_plan_is_a_superset_of_every_existing_crewing_task(self):
        planned = {h['command'] for h in self.new['harness_commands'][TASK]}
        for task in self.old['harness_commands']:
            self.assertTrue(
                {h['command'] for h in MODULE.configured_harnesses(self.old, task)} <= planned, task)
        self.assertEqual(
            len(MODULE.unique_harnesses(MODULE.configured_harnesses(self.new, TASK))), len(HARNESS_PLAN))

    # -- 9. real CLI ----------------------------------------------------------
    @unittest.skipUnless(RUNS_AGAINST_REPO_CONFIG,
                         'the CLI reads configs from its own checkout; draft review runs the library tests')
    def test_real_cli_routes_the_declared_set_and_rejects_a_foreign_path(self):
        import tempfile
        with tempfile.TemporaryDirectory(prefix='skipi-guard-635-fixture-') as tmp:
            repo = Path(tmp)
            def git(*args: str) -> None:
                subprocess.run(['git', '-C', str(repo), *args], check=True,
                               capture_output=True, text=True)
            git('init', '-q', '-b', 'main')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'fixture')
            (repo / 'README.md').write_text('fixture\n', encoding='utf-8')
            git('add', 'README.md')
            git('commit', '-qm', 'base')
            base = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, check=True).stdout.strip()
            for path in CEILING:
                target = repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('fixture\n', encoding='utf-8')
            git('add', '--', *CEILING)
            git('commit', '-qm', '635 fixture')
            head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, check=True).stdout.strip()
            report = repo / 'guard.json'
            # No --run-harness: verify never creates a worktree and never executes.
            proc = subprocess.run(
                [str(GUARD), 'verify', '--home', 'crewing', '--auto-task', '--repo', str(repo),
                 '--base', base, '--head', head, '--json', str(report)],
                capture_output=True, text=True)
            # The committed set is refused - on release-sensitive ONLY, never scope.
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            result = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(result['task'], TASK)
            self.assertEqual(result['task_rule'], RULE_NAME)
            self.assertEqual(result['scope_violations'], [])
            self.assertEqual(sorted(result['changed_files']), CEILING)
            self.assertEqual(len(result['tests']), len(HARNESS_PLAN))
            self.assertTrue(result['release_paths_touched'])
            # The guard reports protected_paths_touched as protected + release-sensitive
            # (bin/skipi-guard:506-507), so it is non-empty here. What must hold is
            # that NOTHING in it comes from a protected_paths rule.
            self.assertEqual({t['kind'] for t in result['protected_paths_touched']},
                             {'release-sensitive'})
            self.assertEqual(len(result['protected_paths_touched']), 3)
            self.assertFalse(result['override_present'])
            self.assertEqual(result['errors'],
                             ['release-sensitive path touch is blocked for this task'])
            self.assertEqual({(t['path'], t['rule']) for t in result['release_paths_touched']},
                             CARGO_RELEASE_TOUCHES)

            foreign = repo / SCRATCHPAD[0]
            foreign.parent.mkdir(parents=True, exist_ok=True)
            foreign.write_text('machinery\n', encoding='utf-8')
            git('add', '--', SCRATCHPAD[0])
            git('commit', '-qm', 'stray scratchpad add')
            head2 = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                   capture_output=True, text=True, check=True).stdout.strip()
            proc = subprocess.run(
                [str(GUARD), 'verify', '--home', 'crewing', '--auto-task', '--repo', str(repo),
                 '--base', base, '--head', head2, '--json', str(report)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            result = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(result['status'], 'fail')
            self.assertIn(SCRATCHPAD[0], result['scope_violations'])

    def test_assert_config_superset_accepts_this_change_and_has_teeth(self):
        """old -> new on a two-commit fixture repo: the old commit is the config
        reconstructed by subtraction, the new one is the live file. Reading a ref
        of this checkout would compare the change with itself after merge."""
        with tempfile.TemporaryDirectory(prefix='c635-superset-') as tmp:
            repo = Path(tmp) / 'repo'
            (repo / 'configs/homes').mkdir(parents=True)

            def git(*args):
                return subprocess.run(['git', '-C', str(repo), *args], check=True, text=True,
                                      capture_output=True).stdout.strip()

            git('init', '-q', '-b', 'main')
            git('config', 'user.name', '635 superset fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            target = repo / 'configs/homes/crewing.json'
            target.write_text(previous_config_text(CONFIG.read_text(encoding='utf-8')), encoding='utf-8')
            git('add', '-A')
            git('commit', '-qm', 'accepted guard config')
            old_ref = git('rev-parse', 'HEAD')
            target.write_text(CONFIG.read_text(encoding='utf-8'), encoding='utf-8')
            git('add', '-A')
            git('commit', '-qm', 'proposed guard config')
            new_ref = git('rev-parse', 'HEAD')
            self.assertNotEqual(old_ref, new_ref)
            proc = subprocess.run(
                [str(GUARD), 'assert-config-superset', '--home', 'crewing',
                 '--old-ref', old_ref, '--new-ref', new_ref, '--repo', str(repo)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            # Teeth, CLI level: the reverse direction removes the task and fails.
            proc = subprocess.run(
                [str(GUARD), 'assert-config-superset', '--home', 'crewing',
                 '--old-ref', new_ref, '--new-ref', old_ref, '--repo', str(repo)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        # Teeth: dropping a neighbour's pattern must be caught by the same check.
        mutated = copy.deepcopy(self.new)
        mutated['allowed_file_patterns']['crewing-664-person'] = \
            mutated['allowed_file_patterns']['crewing-664-person'][:-1]
        self.assertTrue(MODULE.missing_allowed_patterns(self.old, mutated))
        mutated = copy.deepcopy(self.new)
        mutated['harness_commands']['plugin-host'] = mutated['harness_commands']['plugin-host'][:-1]
        self.assertTrue(MODULE.harness_commands_by_task(self.old)['plugin-host'].items()
                        - MODULE.harness_commands_by_task(mutated)['plugin-host'].items())
        mutated = copy.deepcopy(self.new)
        mutated['additive_task_checks'] = []
        self.assertTrue(MODULE.missing_additive_checks(self.old, mutated))
        mutated = copy.deepcopy(self.new)
        mutated['release_sensitive_paths'][1]['patterns'].remove('Cargo.toml')
        self.assertTrue(MODULE.missing_named_rule_patterns(self.old, mutated, 'release_sensitive_paths'))


if __name__ == '__main__':
    unittest.main()
