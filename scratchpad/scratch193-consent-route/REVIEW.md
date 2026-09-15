# Seafarer consent193 guard route — reviewable PREP

Baseline: `6fb407234c64a11019dda6f001d117fe0c7a8f4e` (PR61, verified live main 2026-09-15).
Native candidate recorded by ops handoff: `6df86db9b1601a0540e7e00d29fdf9f7a4c69a6e`.

The required explicit two-checkbox notice changes its real UI fixture and sync regression. The four-file candidate falls through to plugin-host, which rejects tests/one_account_sync_harness.mjs; one-account-sync-192 requires thirteen files. This separate policy PR adds exactly one non-release task, consent193. It does not add unrelated native changes to satisfy routing.

| Literal mandatory path | Reason |
| --- | --- |
| dist/index.html | Explicit consent notice with two independent checkboxes and guarded actions. |
| src-tauri/src/commands/account_sync.rs | Classify explicit server consent rejection for JSON and attachment downloads so revoked consent stops sync. |
| tests/bundled_plugin_isolation_harness.mjs | Existing bundled UI mock fixture must support the changed consent controls. |
| tests/one_account_sync_harness.mjs | Existing sync regression must exercise the new notice and both consent checkboxes. |

All four literals occur in routing scope, require_all_of, exact_task_file_sets and allowed_file_patterns. Auto-routing never selects consent193 for a subset or superset. Explicit consent193 rejects every missing/extra path, including an empty diff. Auto-routing preserves prior behavior for subsets: the three paths without one_account_sync_harness.mjs remain a legitimate plugin-host change, not consent193. No existing route, order, protected path, release policy, override, executable, hook template, workflow or pin is changed.

The new task retains all twelve one-account-sync-192 harness commands verbatim. Seven new regression tests exercise real CLI auto/explicit routing on synthetic Git fixtures, all missing paths, eight unrelated/protected/release extras, exact configuration preservation by canonical JSON hash, every harness failure via subprocess stubs, and seven in-memory policy mutations. Product execution and side effects are stubbed: this proves guard policy, not native consent behavior. Historical route snapshots omit only this independently hash-checked additive task; their prior expectations remain intact.

Evidence: baseline-red.log reproduces plugin-host rejection on the exact four-file candidate before config changes; focused-pass.log records the same seven tests passing after the route addition. `seafarer-regression.log`: 168 tests PASS. `regression-first.log`: 407 tests with 13 historical snapshot failures before the narrow historical exclusions. `regression-pass.log`: all 407 tests PASS after those exclusions. `git diff --check`: PASS.

## Subsequent home handoff (not executed here)

1. Human reviews and merges this guard PR. No automatic merge is authorized. Record actual merged SHA and verify live remote reachability.
2. Under separately authorized local guard adoption, fast-forward the canonical `/home/linux/Developer/skipi-guard` checkout to that merged commit, after checking no active writer and preserving its existing untracked `.worktrees/` tree. This PR does not touch that tree. The installed Seafarer pre-push hook points to `/home/linux/Developer/skipi-guard/bin/skipi-guard`; the config is read there. Template bytes are unchanged, so an identical existing hook needs verification, not rewrite. Check canonical render parity after adoption; an actual mismatch needs separately authorized installation.
3. Seafarer canonical Git home is `/home/linux/Developer/skipi-public`; the observed candidate worktree is `/home/linux/Developer/worktrees/seafarer-193-account-path-20260914`. In a separate home pin PR using the existing `guard-pin-bump` route, change ONLY `.github/workflows/skipi-guard.yml` guard checkout `ref` from `6fb407234c64a11019dda6f001d117fe0c7a8f4e` to the actual merged guard SHA. Do not bundle this fifth protected file into the consent source diff. Keep existing workflow/bootstrap behavior intact.
4. After that pin is integrated, replay the exact four-file consent source on the current home baseline and verify consent193 routing plus actual twelve home harnesses on the pushed bytes. Preserve the product source SHA relation in its home handoff. Build, release, deploy and runtime acceptance remain separate.

No product files, live hooks, local canonical guard branch, home pin, or deployment were mutated by this PREP.
