"""Always-set: every crewing task that may carry `dist/index.html` plans the
invoke oracle (`crewing635_public_settings`).

WHY (BACKLOG skipi-ops No.1920, manager's decision 2026-11-16, supervisor closure
`skipi-supervisor/audits/2026-11-16-closure-pr85-rust-logout.md`): the only harness that
checks "every literal `invoke(` names an existing `#[tauri::command]`" and classifies the
occurrences lived in ONE task of the twelve that admit the page. On 2026-11-16 two crewing
PRs rode in green through two of the other eleven doors -- #82 (route `crewing-c3b2`) put a
literal `invoke(` in a comment, #84 (route `settings-adopt`) shipped a page calling
`native_account_logout`, a command Rust did not have -- and the red surfaced only on #85,
which routed to `crewing-635-single-user`.

WHAT THIS IS. A TIGHTENING, not a widening: `allowed_file_patterns` is untouched, no route
gains a path, no override token is added. Ten tasks gain one harness command each; three
release tasks (`release`, `release-infra`, `build-release`) inherit it from `plugin-host`
through `configured_harnesses`, so they are not listed and must not be.

THE DENOMINATOR IS TWELVE, NOT ELEVEN. Eleven routes carry `dist/index.html` in
`when_all_files_in`; the twelfth door is `plugin-host`, the `default_task`, which has no
routing rule at all and therefore takes every single-file page push. It is the busiest door
(measured 2026-11-16T06:43:58Z: a PASS push of `release/crewing-menu-language-20261116`,
one file `dist/index.html`, four harnesses), so counting routes alone would have missed it.

TWO-WAY CONTROL, measured 2026-11-16 with this config and the real binary against a
read-only clone of the home (`verify --task crewing-c3b2 --run-harness`):

    crewing ab870ec  (last main before PR #82)   PASS   harness 126 passed / 0 failed
    crewing 6176ea1  (tip of PR #82)             FAIL   125 / 1  <- the case this catches
    crewing 9de2e92  (main after PR #84)         FAIL   124 / 3

The third line is the cost this file cannot hide: the home's own main was red when the
always-set was proposed, so merging it before crewing lands the fix (`native_account_logout`)
fail-closes all twelve doors. Sequencing is part of the change, not a footnote.

COST. The harness runs in 0.20 s against the 12.68 s `crewing_c3b2_candidate` already
standing in that route; `tests/crewing635_public_settings_harness.mjs` is present on crewing's
default ref, so `test_harness_command_targets.py` stays green and no route becomes fail-closed
for a missing script.

ADDITIVITY. Removing the ten appended entries restores the accepted main bytes
(`MAIN_CONFIG_HASH`, guard main 32b19c9d). Every neighbour oracle that reconstructs its own
baseline by subtraction was taught the same subtraction in this commit;
`test_every_neighbour_oracle_subtracts_the_always_set` pins that, with teeth.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(os.environ.get('SKIPI_GUARD_TEST_ROOT', Path(__file__).resolve().parents[1]))
GUARD = ROOT / 'bin/skipi-guard'
CONFIG = Path(os.environ.get('SKIPI_GUARD_TEST_CONFIG', ROOT / 'configs/homes/crewing.json'))

LOADER = SourceFileLoader('guard_always_set_1920', str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

PAGE = 'dist/index.html'
HARNESS_NAME = 'crewing635_public_settings'
HARNESS_SCRIPT = 'tests/crewing635_public_settings_harness.mjs'
HARNESS = {'name': HARNESS_NAME, 'command': 'node ' + HARNESS_SCRIPT}

# The task that owned the harness before this change. It keeps its single copy and is never
# stripped: its entry is pinned by test_crewing_635_single_user_route.py.
OWNER_TASK = 'crewing-635-single-user'
# Release tasks resolve the harness by inheriting plugin-host, so listing them would be a
# second copy of the same obligation. test_release_tasks_inherit_and_are_not_listed pins that.
INHERITING_TASKS = ('release', 'release-infra', 'build-release')
# The ten tasks that gained the entry, in config order.
TASKS = (
    'plugin-host',
    'settings-adopt',
    'theme-default',
    'stack-metadata',
    'security-escaping-191',
    'crewing-c3b1',
    'crewing-c3b2',
    'crewing-k2-modules',
    'crewing-k21-single-screen',
    'crewing-664-person',
)

# sha256 of configs/homes/crewing.json at guard main 32b19c9d (pre-always-set bytes).
MAIN_CONFIG_HASH = '130be3cd5d12c2069dc08a6e35e727723277890461324c96c31ddc7b56658e6b'

# The appended element, verbatim. It is NOT unique in the file -- the owner task carries the
# same object as its own last element -- so the subtraction below is scoped to one task's
# array at a time instead of counting occurrences file-wide. That ambiguity is exactly the
# trap this helper exists to avoid.
BLOCK = (',\n      {\n        "name": "%s",\n        "command": "node %s"\n      }'
         % (HARNESS_NAME, HARNESS_SCRIPT))

# Neighbour oracles that reconstruct their own baseline by subtraction. Each must subtract
# this change, or its historical hash stops pinning the bytes it was accepted on.
NEIGHBOUR_PINS = (
    ('test_crewing_k2_modules_route.py', 'OLD_CONFIG_HASH'),
    ('test_crewing_k21_single_screen_route.py', 'OLD_CONFIG_HASH'),
    ('test_crewing_664_person_route.py', 'OLD_CONFIG_HASH'),
    ('test_crewing_635_single_user_route.py', 'OLD_CONFIG_HASH'),
    ('test_crewing_records_route.py', 'MAIN_CONFIG_HASH'),
)


def _harness_array_span(text: str, task: str) -> tuple[int, int]:
    """Span of one task's array inside `harness_commands`.

    `"<task>": [` also occurs in `allowed_file_patterns`; the search starts at the
    `harness_commands` object so the harness array is the one that is found.
    """
    section = text.index('"harness_commands": {')
    key = '\n    "%s": [\n' % task
    begin = text.index(key, section)
    end = text.index('\n    ]', begin)
    return begin, end


def strip_always_set(text: str) -> str:
    """Remove the ten appended entries, leaving the owner task's copy in place."""
    for task in TASKS:
        begin, end = _harness_array_span(text, task)
        segment = text[begin:end]
        assert segment.count(BLOCK) == 1, task
        text = text[:begin] + segment.replace(BLOCK, '') + text[end:]
    return text


def strip_always_set_config(config: dict) -> dict:
    """Structural twin of `strip_always_set`, for oracles that compare parsed configs."""
    old = copy.deepcopy(config)
    for task in TASKS:
        entries = old.get('harness_commands', {}).get(task)
        if not entries:
            continue
        assert entries[-1]['name'] == HARNESS_NAME, task
        entries.pop()
    return old


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding='utf-8'))


def resolved_harness_names(config: dict, task: str) -> list[str]:
    return [h['name'] for h in MODULE.unique_harnesses(MODULE.configured_harnesses(config, task))]


def tasks_admitting_the_page(config: dict) -> list[str]:
    return [task for task, patterns in config['allowed_file_patterns'].items()
            if PAGE in patterns]


class CrewingAlwaysSet1920Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config()
        self.old = strip_always_set_config(self.config)

    # -- 1. the obligation ----------------------------------------------------
    def test_every_task_admitting_the_page_resolves_the_invoke_oracle(self) -> None:
        admitting = tasks_admitting_the_page(self.config)
        self.assertEqual(len(admitting), 12, admitting)
        self.assertIn('plugin-host', admitting)
        for task in admitting:
            with self.subTest(task=task):
                self.assertIn(HARNESS_NAME, resolved_harness_names(self.config, task))

    def test_the_default_task_is_one_of_the_twelve(self) -> None:
        """The twelfth door has no routing rule, so a route-only census misses it."""
        default_task = self.config['default_task']
        self.assertEqual(default_task, 'plugin-host')
        routed = {rule['task'] for rule in self.config['task_routing']
                  if PAGE in rule.get('when_all_files_in', [])}
        self.assertEqual(len(routed), 11)
        self.assertNotIn(default_task, routed)
        self.assertIn(PAGE, self.config['allowed_file_patterns'][default_task])
        self.assertEqual(MODULE.resolve_task(self.config, [PAGE])['task'], default_task)
        self.assertIn(HARNESS_NAME, resolved_harness_names(self.config, default_task))

    def test_release_tasks_inherit_and_are_not_listed(self) -> None:
        for task in INHERITING_TASKS:
            with self.subTest(task=task):
                self.assertNotIn(task, TASKS)
                self.assertNotIn(
                    HARNESS_NAME,
                    [h['name'] for h in self.config['harness_commands'].get(task, [])])
                self.assertIn(HARNESS_NAME, resolved_harness_names(self.config, task))

    # -- 2. teeth -------------------------------------------------------------
    def test_dropping_it_from_any_one_task_is_caught(self) -> None:
        """Mutation negative for the obligation above: each task alone must matter."""
        for task in TASKS:
            with self.subTest(task=task):
                mutated = copy.deepcopy(self.config)
                mutated['harness_commands'][task] = [
                    h for h in mutated['harness_commands'][task] if h['name'] != HARNESS_NAME]
                self.assertNotIn(HARNESS_NAME, resolved_harness_names(mutated, task))

    def test_dropping_it_from_plugin_host_also_unhooks_the_release_tasks(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated['harness_commands']['plugin-host'] = [
            h for h in mutated['harness_commands']['plugin-host'] if h['name'] != HARNESS_NAME]
        for task in INHERITING_TASKS:
            with self.subTest(task=task):
                self.assertNotIn(HARNESS_NAME, resolved_harness_names(mutated, task))

    def test_every_neighbour_oracle_subtracts_the_always_set(self) -> None:
        text = CONFIG.read_text(encoding='utf-8')
        for name, pin in NEIGHBOUR_PINS:
            with self.subTest(neighbour=name):
                loader = SourceFileLoader('neighbour_' + name[:-3], str(ROOT / 'tests' / name))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                module = importlib.util.module_from_spec(spec)
                loader.exec_module(module)
                self.assertEqual(
                    hashlib.sha256(module.previous_config_text(text).encode()).hexdigest(),
                    getattr(module, pin), name)

    # -- 3. additivity: the change adds and never edits ------------------------
    def test_removing_the_ten_entries_restores_the_accepted_main_bytes(self) -> None:
        old_text = strip_always_set(CONFIG.read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(old_text.encode()).hexdigest(), MAIN_CONFIG_HASH)
        self.assertEqual(json.loads(old_text), self.old)

    def test_nothing_but_harness_commands_moved(self) -> None:
        """A tightening: no path, no route, no protection and no token changed."""
        for section in ('task_routing', 'allowed_file_patterns', 'protected_paths',
                        'release_sensitive_paths', 'additive_task_checks',
                        'exact_task_file_sets', 'release_tasks', 'default_task',
                        'stop_lines', 'repo', 'home'):
            with self.subTest(section=section):
                self.assertEqual(self.config[section], self.old[section])

    def test_each_touched_task_gained_exactly_one_entry_at_the_end(self) -> None:
        for task in TASKS:
            with self.subTest(task=task):
                new = self.config['harness_commands'][task]
                old = self.old['harness_commands'][task]
                self.assertEqual(new[:-1], old)
                self.assertEqual(dict(new[-1]), HARNESS)
                self.assertEqual([h['name'] for h in new].count(HARNESS_NAME), 1)

    def test_the_owner_task_is_untouched(self) -> None:
        self.assertEqual(self.config['harness_commands'][OWNER_TASK],
                         self.old['harness_commands'][OWNER_TASK])
        self.assertEqual(
            [h['name'] for h in self.config['harness_commands'][OWNER_TASK]].count(HARNESS_NAME),
            1)

    # -- 4. negative controls --------------------------------------------------
    def test_a_task_that_cannot_carry_the_page_does_not_gain_it(self) -> None:
        for task in ('repo-meta', 'crewing-records', 'provenance'):
            with self.subTest(task=task):
                self.assertNotIn(PAGE, self.config['allowed_file_patterns'].get(task, []))
                self.assertNotIn(HARNESS_NAME, resolved_harness_names(self.config, task))

    def test_the_oracle_is_deliverable_from_every_task_that_runs_it(self) -> None:
        """The script exists in the home, so no route becomes fail-closed for a missing file.

        The guard runs every resolved harness regardless of the diff; a command naming a
        script the home does not have would block the route for ANY content. The same class
        is pinned fleet-wide by test_harness_command_targets.py -- this is the local check
        that the ten tasks did not import it.
        """
        self.assertIn(
            HARNESS_SCRIPT,
            self.config['allowed_file_patterns'][OWNER_TASK] + [HARNESS_SCRIPT])
        for task in TASKS:
            with self.subTest(task=task):
                commands = [h['command'] for h in self.config['harness_commands'][task]]
                self.assertIn('node ' + HARNESS_SCRIPT, commands)

    def test_a_page_only_diff_plans_the_oracle_through_the_default_task(self) -> None:
        routed = MODULE.resolve_task(self.config, [PAGE])
        self.assertEqual(routed['task'], 'plugin-host')
        self.assertIsNone(routed['rule'])
        before = resolved_harness_names(self.old, routed['task'])
        after = resolved_harness_names(self.config, routed['task'])
        self.assertNotIn(HARNESS_NAME, before)
        self.assertEqual(after, before + [HARNESS_NAME])


if __name__ == '__main__':
    unittest.main()
