import hashlib, json, pathlib

p = pathlib.Path('configs/homes/crewing.json')
text = p.read_text()
assert hashlib.sha256(text.encode()).hexdigest() == '7edf6021057702e0dd73ddf803e1781f0e190f6d3526a13b5fdd0b54fbfe5ffd'
before = json.loads(text)

FILES = [
    "dist/index.html",
    "tests/crewing_crew_flow_demo_harness.mjs",
    "tests/crewing_plugin_isolation_harness.mjs",
    "tests/crewing_c3b1_pilot_harness.mjs",
    "tests/crewing_c3b2_candidate_harness.mjs",
    "tests/crewing_presence_contract_harness.mjs",
    "docs/crewing-pilot-c3b2/WORKLOG.md",
    ".github/workflows/skipi-guard.yml",
]
REQUIRE_ANY = [
    "docs/crewing-pilot-c3b2/WORKLOG.md",
    "tests/crewing_crew_flow_demo_harness.mjs",
]
COMMANDS = [
    ("crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"),
    ("shared_host_runtime_isolation", "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"),
    ("crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"),
    ("crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"),
    ("crewing_c3b1_pilot", "node tests/crewing_c3b1_pilot_harness.mjs"),
    ("crewing_csp_inline_handlers", "node tests/csp_inline_handlers_harness.mjs"),
    ("crewing_c3b2_candidate", "node tests/crewing_c3b2_candidate_harness.mjs"),
    ("crewing_mailbox_contract", "node tests/crewing_mailbox_contract_harness.mjs"),
    ("crewing_mail_cv_intake_demo", "node tests/crewing_mail_cv_intake_demo_harness.mjs"),
    ("crewing_compliance_manual_flow", "node tests/crewing_compliance_manual_flow_harness.mjs"),
    ("crewing_theme_default", "node tests/crewing_theme_default_harness.mjs"),
    ("settings5_preview_gated", "node tests/settings5_preview_gated_harness.mjs"),
    ("trial_activate_unconnected", "node tests/trial_activate_unconnected_harness.mjs"),
    ("trial_gate_wired", "node tests/trial_gate_wired_harness.mjs"),
]

def arr(paths, ind):
    pad = ' ' * ind
    inner = ' ' * (ind + 2)
    body = ',\n'.join(f'{inner}{json.dumps(v)}' for v in paths)
    return '[\n' + body + '\n' + pad + ']'

route_block = (
    '    {\n'
    '      "name": "crewing K2 Crew Flow queue + module composition routing (owner654/658, 2026-09-24)",\n'
    '      "task": "crewing-k2-modules",\n'
    '      "when_all_files_in": ' + arr(FILES, 6) + ',\n'
    '      "require_any_of": ' + arr(REQUIRE_ANY, 6) + '\n'
    '    },\n'
)

harness_entries = ',\n'.join(
    '      {\n'
    f'        "name": {json.dumps(name)},\n'
    f'        "command": {json.dumps(cmd)}\n'
    '      }' for name, cmd in COMMANDS
)
harness_block = ',\n    "crewing-k2-modules": [\n' + harness_entries + '\n    ]'

allowed_block = ',\n    "crewing-k2-modules": ' + arr(FILES, 4)

# A. task_routing: insert right AFTER the crewing-c3b2 rule (PREP §0 F2).
anchor_route = (
    '      "require_any_of": [\n'
    '        "tests/crewing_c3b2_candidate_harness.mjs",\n'
    '        "docs/crewing-pilot-c3b2/WORKLOG.md"\n'
    '      ]\n'
    '    },\n'
)
assert text.count(anchor_route) == 1
text = text.replace(anchor_route, anchor_route + route_block, 1)

# B. harness_commands: append after the crewing-c3b2 entry (last in the map).
anchor_harness = (
    '      {\n'
    '        "name": "crewing_c3b2_candidate",\n'
    '        "command": "node tests/crewing_c3b2_candidate_harness.mjs"\n'
    '      }\n'
    '    ]\n'
    '  },\n'
)
assert text.count(anchor_harness) == 1
text = text.replace(anchor_harness,
                    anchor_harness.replace('    ]\n  },\n', '    ]' + harness_block + '\n  },\n'), 1)

# C. allowed_file_patterns: append after the crewing-c3b2 entry (last in the map).
anchor_allowed = (
    '    "crewing-c3b2": [\n'
    '      "dist/index.html",\n'
    '      "src-tauri/src/crewing_intake.rs",\n'
    '      "src-tauri/src/lib.rs",\n'
    '      "tests/crewing_c3b2_candidate_harness.mjs",\n'
    '      "docs/crewing-pilot-c3b2/WORKLOG.md",\n'
    '      ".github/workflows/skipi-guard.yml"\n'
    '    ]\n'
    '  }\n'
    '}\n'
)
assert text.count(anchor_allowed) == 1
text = text.replace(anchor_allowed,
                    anchor_allowed.replace('    ]\n  }\n}\n', '    ]' + allowed_block + '\n  }\n}\n'), 1)

after = json.loads(text)

# structural expectations
assert [r['task'] for r in after['task_routing'][:6]] == [
    'security-escaping-191', 'crewing-c3b1', 'crewing-c3b1-metadata', 'crewing-c3b2',
    'crewing-k2-modules', 'repo-meta'], [r['task'] for r in after['task_routing'][:6]]
new_rule = after['task_routing'][4]
assert new_rule['when_all_files_in'] == FILES
assert new_rule['require_any_of'] == REQUIRE_ANY
assert 'require_all_of' not in new_rule
assert after['allowed_file_patterns']['crewing-k2-modules'] == FILES
assert [(c['name'], c['command']) for c in after['harness_commands']['crewing-k2-modules']] == COMMANDS
assert after['harness_commands']['crewing-k2-modules'][:7] == after['harness_commands']['crewing-c3b2']

# purely additive at parse level
stripped = json.loads(json.dumps(after))
stripped['task_routing'] = [r for r in stripped['task_routing'] if r['task'] != 'crewing-k2-modules']
for section in ('allowed_file_patterns', 'harness_commands'):
    stripped[section].pop('crewing-k2-modules', None)
assert stripped == before, 'non-additive change detected'
for key in ('protected_paths', 'release_sensitive_paths', 'stop_lines', 'release_tasks',
            'default_task', 'exact_task_file_sets', 'additive_task_checks'):
    assert after[key] == before[key], key

p.write_text(text)
print('written; new sha256 =', hashlib.sha256(text.encode()).hexdigest())
