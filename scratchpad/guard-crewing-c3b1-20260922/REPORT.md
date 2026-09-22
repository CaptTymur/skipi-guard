# Crewing C3b1 guard route — owner612

Base: live `main` = `ff7d534bac1468230d9ab7632eb7271f2eefe159`, verified before worktree creation and again before publication. Implementation is limited to Crewing config, a new route regression, and the historical test's existing additive-route filter. Guard executable, deployed hooks, product code, protected/release paths, override tokens and all old route definitions/checks are unchanged. Human merge remains required.

## Allowed surface and routing

| Exact path | Reason |
|---|---|
| `dist/index.html` | Desktop pilot UI and RU/EN text |
| `src-tauri/src/crewing_intake.rs` | Fixed typed intake operations |
| `src-tauri/src/lib.rs` | Registration of those operations |
| `tests/crewing_c3b1_pilot_harness.mjs` | Pilot regression |
| `docs/crewing-pilot-c3b1/WORKLOG.md` | Required resumable product journal |
| `.github/workflows/skipi-guard.yml` | Future exact reviewed guard pin |

These six paths are a ceiling. Auto-routing requires the intake module and pilot harness, and at least one of index/lib; journal and workflow may be absent. Explicit task mode has the same path ceiling but does not enforce the auto-router's required-file predicates, consistent with the existing guard architecture. This is not an exact-six-file gate. The security-escaping route remains first; C3b1 follows it and has no overlap with its required files. No wildcard was added.

The new task retains all four plugin-host commands and adds pilot+CSP. SHA256 of the full parsed old config (after removing only this task) remains `4f53d45cf2bfc8e08b6d172f55e97be57daa736531d2c6d9444bdfc3a47938cc`. The historical security test excludes only the new task from its pre-security baseline, retaining all old assertions and its original baseline.

## Evidence sequence

All unit runs use `TMPDIR=$PWD/scratchpad/guard-crewing-c3b1-20260922/tmp python3 -m unittest discover -s tests -v`; the route-only runs additionally use `-p test_crewing_c3b1_route.py`.

- `baseline.log`: original main, 407 tests PASS.
- `red.log`: new regression before config fix; 7 tests with 30 failed subtests/assertions. The real five-file candidate resolves to plugin-host, reproducing the publication blocker.
- `green-route.log`: intermediate run with one assertion failure. Legacy plugin-host includes presence-manifest in its path scope; its independent protected gate blocks it. The new regression now asserts that actual protected failure rather than incorrectly claiming a legacy scope failure.
- `full-green.log`: intermediate run, 414 tests with 2 failures. Proposed first-position insertion conflicted with security-first assertions. C3b1 was moved after security, and the historical additive filter extended by exactly one Crewing task.
- `full-green-final.log`: completed final full-suite result is authoritative. See its final summary, not filenames of intermediate logs.
- `product-a2ab17e.json` / `.log`: exploratory CLI route/run evidence. The diff used a2ab17e while a parallel executor advanced the checkout, so this is NOT evidence of exact a2ab17e harness bytes. Superseded by the immutable snapshot result below.
- `product-e23e235.json`: all six real configured commands PASS on `git archive e23e235e05f28babe00d602f262fbaec405d2361`. Archive SHA256 `f52f2ee5be55771af259940ff1ab3c8bab8f7a110aa8b25d088c6db2321f4281`. Actual product changed-path set remains the first five paths above. Shared runtime read-only dependency was clean at `14a3d0657dde92e724ec4a16c943db93082671ac`; CI pins an older runtime, so hosted CI remains a separate check. Snapshot/archive and the scratch dependency symlink were removed only after a second `git archive` proved identical reconstruction hash. No product sources are published in this guard PR.

New regression covers all 64 subsets; each required-file omission and missing index/lib; native/server/release/protected/unrelated additions under auto and explicit task; legacy route outcomes; real CLI `--auto-task` and canonical rendered hook stdin at the same five/six-file candidate SHAs; all six commands invoked and each individual failure propagated by both paths. Hook fixtures are checked out at main while stdin points at candidate, proving the pushed revision controls execution. Only fixture node side effects are stubbed and recorded; no deployed hook is installed. Product snapshot checks are real commands, not fixture stubs.

## Remaining gates and stop

This PR prepares a bounded route; it does not install it, merge main, publish the product, approve native behavior, or prove hosted CI. Once a human merges the reviewed guard, product workflow review must prove a ref-only change and run ordinary old pin `fdbf3d8cc29435e5da64afd105e5850c571245fa` to the exact merged guard SHA `assert-config-superset`. The existing mixed product+workflow path does not automatically perform that workflow-only comparison. Allowlisting the workflow does not enforce its contents. Product SESSION-DURABILITY stays BLOCKED until its normal publication and CI succeed.

Cargo/Gradle, server security/mutation audit, deployment, environment overrides, force/no-verify, main merge, hook installation and product edits were not performed. Canonical guard's existing `.worktrees/` state was preserved. Disposable test fixtures clean themselves up; raw evidence remains here for remote durability with the feature branch.
