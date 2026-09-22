# C3b1 incremental metadata guard follow-up

READY_FOR_INDEPENDENT_REVIEW; merge and activation not authorized here.
Base: `071eea0c3679c8b35bad2bd62adb2df4c3b17746` (live main checked at entry).
Source implementation: `40e3a0633a05ec764f4852053c945a29fbc9a6b3`.
The following evidence-only commit does not change tested config or test bytes.

## Concrete problem and scope

A normal feature push d6298ce9a4d5358e92884c54e73868058881871c ->
f743a8e04611e1b5ae1e91a7ad33b23a3df6474b changed only
`docs/crewing-pilot-c3b1/WORKLOG.md`, selected plugin-host, and failed its scope.
The previously authorized full route correctly requires module+harness+(index|lib).
Those predicates must remain intact.

Add only `crewing-c3b1-metadata`: WORKLOG required, exact workflow path optional.
Both paths already belong to owner612's six-path ceiling. WORKLOG is needed for
required resumable handoff; `.github/workflows/skipi-guard.yml` is needed to adopt
the reviewed guard pin together with that journal. Workflow-only retains its old
behavior: existing hook/CI accepts it through the built-in bootstrap override;
there is no override-free workflow-only route. Splitting the two pushes therefore
would not meet the requested no-override metadata path.

The new task runs identical six C3b1 checks: four inherited plugin-host checks,
pilot, CSP. First security route, all previous routes/checks/predicates,
protected/release rules, tokens, and enforcement source remain unchanged.
Only three source files change. Historical-security test filter adds exactly the
new task; a new SHA-256 oracle verifies the entire parsed previous config after
removing this task. Prior full-route subset and failure tests remain active.

Authority judgment: bounded follow-up to owner612, ordinary feature push/PR only.
Owner613 authorized only PR63; it confers no merge authority on this candidate.
No installation, canonical main change, product mutation, production, cargo,
Gradle, force-push, or no-verify operation occurred. Synthetic negative harness
failures use recording stubs. Actual harness runs use their existing fake DOM/VM
fixtures in disposable clones; shared runtime dependency is read-only. Fixture
journal additions use git add -f because old product main ignores docs; this is
only isolated test data, not a product staging operation or guard override.

## Evidence and commands

- `python3 -m unittest discover -s tests`: baseline rc0, 414 tests, 77.448s.
- Before config fix: same targeted discovery, 11 tests, rc1, 2 failures + 1 error
  (new route absent). `regression-red.log` preserves this genuine RED.
- `python3 -m unittest discover -s tests -p test_crewing_c3b1_route.py`:
  final rc0, 13 tests, 7.117s.
- Full final discovery: rc0, 420 tests, 80.485s. No prior test removed.
- `replay_actual_refs.py red`: old config real original refs, hook+CLI rc1,
  plugin-host scope error while four actual checks PASS.
- `replay_actual_refs.py green`: new config, same actual refs, hook+CLI rc0,
  metadata task, all six actual checks PASS.
- `replay_actual_refs.py docs-pin <product-f743> <guard-40e3a>`: isolated clone
  adds only a pin replacement; d629 -> rehearsal commit includes journal+pin,
  hook+CLI rc0, six actual checks PASS. `pin-only.diff` shows exact pin change.
- `replay_actual_refs.py future-journal <product-f743> <guard-40e3a>`:
  journal-only commit after the rehearsal pin, hook+CLI rc0, all six PASS.
- `replay_actual_refs.py main-negative`: isolated product main12a7ce4 plus
  journal only, hook+CLI rc1, pilot missing, other five actual checks PASS.
- `bin/skipi-guard assert-config-superset --home crewing --old-ref 071eea0c3679c8b35bad2bd62adb2df4c3b17746 --new-ref 40e3a0633a05ec764f4852053c945a29fbc9a6b3 --repo . --json <config-superset.json>`: rc0.

All ten replay reports have override_present=false and auto_bootstrap_override=false.
Canonical hook is rendered without installation; only output destination is adapted.
Replay clones preserve actual Git object IDs. Hook starts with checkout at old
main12a7ce4 so PASS proves pushed bytes, not working checkout bytes. Clone and
hook worktrees are removed automatically. Replay pin hashes are rehearsals, not
an approved product pin. Source-rejection transcript is preserved separately.

Tests also reject unrelated docs/native/other workflows and partial source
subsets via auto and explicit CLI; reject all six individual harness failures;
preserve full-route predicates over every subset of the six-path ceiling.
Local CLI matches the workflow's final --auto-task --run-harness invocation;
these local replays are not hosted-CI acceptance.

## Acceptance and next gate

The workflow allowlist controls paths, not contents. A mixed journal+workflow
change skips existing workflow-only assert-config-superset logic. Before product
acceptance, reviewer must verify pin-only diff and explicitly run superset from
current071 to the exact reviewed candidate being pinned. No claim of a mechanical
pin-only predicate is made.

Manager may prepare a product pin to the final reviewed guard HEAD. Only after
separate owner authorization may that exact guard HEAD be merged. Verify API and
live SSH main, exact expected-head, reviewed HEAD ancestry, and merged tree equal
to the reviewed candidate tree (ancestry alone is insufficient). Then canonical
fast-forward and normal product push/PR must pass local guard and hosted CI.
Any changed candidate requires exact review again. This report grants none of
those later actions. Supervisor verdict, manager secret scan and hosted guard CI
are separate receipts; pending until observed.
