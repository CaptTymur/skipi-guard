# C3b2 guard candidate — owner619

Scope: one additive declarative task `crewing-c3b2`, exact guard base
`b2f187b72fc4beed4a8ad5600f02e31de92e5257`. Separate feature branch
`guard/crewing-c3b2-20260922`; no merge or activation authority.

The approved patch SHA256 is
`36210900edc03f763511270439f59a7f915c648164ea2348dd7d870f48a64f08`.
Only its human-readable route name changes from proposal/pending to owner619.
The six-path ceiling, harness-or-genuine-journal trigger, seven checks and
position after security/C3b1 routes match the proposal.

| Product path | Why permitted |
|---|---|
| `dist/index.html` | Candidate detail, facts, comparisons and decisions UI, RU/EN |
| `src-tauri/src/crewing_intake.rs` | Typed existing API operations and expected empty204 |
| `src-tauri/src/lib.rs` | Command registration only |
| `tests/crewing_c3b2_candidate_harness.mjs` | Dedicated new candidate-behavior checks |
| `docs/crewing-pilot-c3b2/WORKLOG.md` | Genuine execution and acceptance journal |
| `.github/workflows/skipi-guard.yml` | Future independently reviewed exact guard pin |

Guard source/test changes: `configs/homes/crewing.json`, new
`tests/test_crewing_c3b2_route.py`, and minimal C3b2-only normalization in
`tests/test_crewing_c3b1_route.py` for its two historical complete-config hashes.
The security test
`tests/test_security_escaping_191_route.py` likewise adds C3b2 to its existing
later-task normalization. All old hashes/assertions remain. Removing only new C3b2 entries yields direct
parsed equality with the entire base config; source hashes are in
`source-receipt.json`. Engine, templates, hooks, workflow, other configs,
protected/release/override policy remain byte-identical to base.

## Validation evidence

- Baseline: 420/420 PASS, 80.686s (`baseline.log`).
- RED before implementation: 8 new test methods, 107 failed subcases and 13
  expected missing-task errors (`red.log`); the original RED count also includes
  the two pure-pin test-oracle mistakes documented below. Real supported CLI shapes resolved
  to old `plugin-host` and were rejected by scope.
- First targeted: 21 methods, two mistaken test expectations about the existing
  pure-pin hook bootstrap (`targeted-first.log`). No implementation defect or
  fix to engine/override; test oracle corrected to preserve existing semantics.
- Final targeted: 21/21 PASS, 46.071s (`targeted.log`).
- First full: 428 tests, one historical security snapshot normalization failure
  (`full-first.log`). Added only C3b2 to the existing later-task exclusion;
  retained all historical security assertions.
- Full candidate suite: 428/428 PASS, 117.616s (`full.log`).
- `git diff --check`: PASS.

New suite covers all64 path subsets and13 forbidden extras. It executes146 real
CLI/rendered-canonical-hook invocations across aggregate and incremental ranges:
24 supported successes,28 individual seven-check failures,8 missing/deleted new
harness failures,78 forbidden-extra failures (auto CLI, explicit task CLI, hook),
and8 unchanged pure-pin/shared-code outcomes. Every routed run records all7
check names/commands and actual fixture HEAD; hook runs execute pushed bytes
while the primary fixture checkout is on main. Temporary worktrees are cleaned.
The previously published incremental boundary differs from origin/main so
incremental resolution cannot silently use the aggregate range.

Synthetic node stubs record and validate the invoked local fixture path, then
return a controlled status. They never execute external product code. No auth or
tenant guard is disabled. The future actual C3b2 product harness DOES NOT EXIST
in this scope and its runtime acceptance is UNKNOWN, not PASS. Existing tests
still cover legacy C3b1, metadata, security and hook behavior. Output-isolation
adapter and exact commands are retained in `commands.md` and `adapter/`.

Pure pin keeps old behavior: CLI rejects; canonical hook uses its existing
workflow-bootstrap acceptance. No new override is provided by C3b2. A push
containing only overlapping old source paths cannot identify C3b2: STOP for that
product increment. Do not fake journal content, manipulate base/env, or claim
C3b2 checks ran. The route can establish only journal path presence, not journal
truth; meaningful content remains an execution/review responsibility.

## Handoff and authority

Two separate external actions authorized by owner619: normal SSH feature push,
then creation of a draft PR. No main push, merge, tag, release, hook installation,
product pin update, provider/account change, server change or activation is
included. Exact committed head, live remote equality, PR URL and hosted CI must
be recorded in the delivery receipt outside this commit; independent final-head
Supervisor acceptance remains required before any future exact owner merge.

No cargo/gradle/build, device, server or product mutation performed. Canonical
checkout/untracked work preserved. Stop after the bounded candidate passes.
