#!/bin/bash
# Mutation drills on the NEW SHA: each mutation must turn the new test red.
set -u
CFG=configs/homes/crewing.json
FAST="tests.test_crewing_k2_modules_route.CrewingK2ModulesRouteTests"
run() { python3 -m unittest "$@" 2>&1 | tail -3 | tr '\n' ' '; echo; }

echo "--- m1: route moved BEFORE crewing-c3b2 (precedence flipped) ---"
python3 - <<'PY'
import json,pathlib,re
p=pathlib.Path('configs/homes/crewing.json'); t=p.read_text()
start=t.index('    {\n      "name": "crewing K2 Crew Flow queue')
end=t.index('\n    },\n',start)+len('\n    },\n')
block=t[start:end]; t=t[:start]+t[end:]
anchor='    {\n      "name": "crewing C3b2 candidate facts and decisions routing (owner619, 2026-09-22)",\n'
t=t.replace(anchor, block+anchor,1); p.write_text(t)
PY
run $FAST.test_exact_ceiling_checks_and_position_after_c3b2 $FAST.test_all_256_subsets_and_c3b2_precedence
git -c gc.auto=0 checkout -- $CFG

echo "--- m2: presence-manifest.json added to the K2 allowlist ---"
python3 - <<'PY'
import pathlib
p=pathlib.Path('configs/homes/crewing.json'); t=p.read_text()
old=',\n    "crewing-k2-modules": [\n      "dist/index.html",'
t=t.replace(old, old+'\n      "presence-manifest.json",',1); p.write_text(t)
PY
run $FAST.test_exact_ceiling_checks_and_position_after_c3b2 $FAST.test_protections_and_override_surface_are_untouched $FAST.test_require_any_of_negative_and_forbidden_extras
git -c gc.auto=0 checkout -- $CFG

echo "--- m3: one of the 14 harness checks dropped ---"
python3 - <<'PY'
import pathlib
p=pathlib.Path('configs/homes/crewing.json'); t=p.read_text()
old='      {\n        "name": "trial_gate_wired",\n        "command": "node tests/trial_gate_wired_harness.mjs"\n      }\n'
assert t.count(old)==1
t=t.replace(',\n'+old,'\n',1) if ',\n'+old in t else t.replace(old,'',1)
p.write_text(t)
PY
run $FAST.test_exact_ceiling_checks_and_position_after_c3b2
git -c gc.auto=0 checkout -- $CFG

echo "--- m4: unrelated byte edited outside the three added blocks ---"
python3 - <<'PY'
import pathlib
p=pathlib.Path('configs/homes/crewing.json'); t=p.read_text()
t=t.replace('"name": "repo-meta routing"','"name": "repo-meta routing "',1); p.write_text(t)
PY
run $FAST.test_entire_old_config_preserved_byte_for_byte_and_parsed
git -c gc.auto=0 checkout -- $CFG

echo "--- m5: require_any_of dropped (route would swallow bare dist+pin) ---"
python3 - <<'PY'
import pathlib
p=pathlib.Path('configs/homes/crewing.json'); t=p.read_text()
old='      ],\n      "require_any_of": [\n        "docs/crewing-pilot-c3b2/WORKLOG.md",\n        "tests/crewing_crew_flow_demo_harness.mjs"\n      ]\n'
assert t.count(old)==1
t=t.replace(old,'      ]\n',1); p.write_text(t)
PY
run $FAST.test_exact_ceiling_checks_and_position_after_c3b2 $FAST.test_require_any_of_negative_and_forbidden_extras $FAST.test_all_256_subsets_and_c3b2_precedence
git -c gc.auto=0 checkout -- $CFG

echo "--- restored ---"
git -c gc.auto=0 status --porcelain $CFG; sha256sum $CFG
