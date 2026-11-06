# Pin-bump recipe: skipi-crewing → guard `32b19c9d` (route `crewing-records`)

Read-only advisory for the manager (skipi-ops-04), 2026-11-06.
**Nothing was written in `skipi-crewing`** — writer e7 is under the coordinator there.
Everything below is either *found in code* (named ref read) or *measured* (resolver driven over
a diff list). Owner decisions are marked *approved*. No layer is mixed.

## 0. Baseline, measured

| thing | value | how |
| --- | --- | --- |
| guard live `main` | `32b19c9d30086cf30cebe418deb762298c3ebc59` | `git ls-remote origin main` |
| what it is | merge of PR #78 `guard/crewing-records-975-20261106` over `57b84f5` "guard: give crewing a text-only route for its stage records" | `git log` |
| crewing live `main` | `f145c6017eaea3804a5429e5aa428b6fb0ece6d9` (merge PR #79) | `git ls-remote origin main` |
| guard pin on crewing `main` | `4a1033338ed55bda0cffe5717bec6b14956aafc6` (= guard main *before* #78) | read at ref |
| branch 930 tip | `f59e4aa3c29d8f8e33e662d4cbb59d4f82710fd4`, **not on origin** → gate base = merge-base = `f145c601` | `ls-remote` empty |

The manager's `f145c601` is confirmed. All file reads were done **against `origin/main`**, not the
working tree: the `skipi-crewing` checkout sits on `chore/crewing-898-record-20261105` (`6e5fc45`),
so a worktree read would have reported the wrong pin.

## 1. The two files that carry the pin — exact lines and literals now

Two files, **three** literal sites. A one-file bump is the recipe that caused SKI-INC-2026-11-01.

| # | file | line | literal at `origin/main` |
| --- | --- | --- | --- |
| 1 | `.github/workflows/skipi-guard.yml` | **23** | `          ref: 4a1033338ed55bda0cffe5717bec6b14956aafc6` |
| 2 | `tests/crewing_c3b2_candidate_harness.mjs` | **69** | `ok(/repository: CaptTymur\/skipi-guard\n\s+ref: 4a1033338ed55bda0cffe5717bec6b14956aafc6\n/.test(workflow), 'the workflow pins exactly the accepted guard SHA (K2 + K2.1 + No.664 routes)');` |
| 3 | `tests/crewing_c3b2_candidate_harness.mjs` | **2891** | `softOk(pins === '4a1033338ed55bda0cffe5717bec6b14956aafc6', 'S5: the workflow pins exactly the accepted guard SHA');` |

Three things that are easy to get wrong here:

- **`softOk` is enforcing, not advisory.** `tests/crewing_c3b2_candidate_harness.mjs:39-44` —
  `if (!condition) { failed += 1; … }`. It does not throw, so the run continues; it still reddens.
  Line 2891 is a real gate, not a note.
- **Do not touch workflow line 36**, `ref: d6238191c554bc370983366672c41b41116754ce`. That is
  `skipi-host-runtime`, and harness line **62** asserts it is unchanged.
- **The line-69 regex ends in `\n`.** It requires the pin line to be followed by a newline —
  supplied today by line 24 (`path: .skipi-guard`). Do not reflow or reorder the `with:` block.

### Fourth site — convention, not an assertion

`tests/crewing_c3b2_candidate_harness.mjs:2910` holds a `superseded` reject list of six guard SHAs,
each **assembled from two halves** so the probe cannot read its own source and pass
(`'93b1a51e' + 'b59d0dff…'`, …). Line 2912 asserts neither the harness nor the workflow still
contains any of them. Every one of the six prior bumps added its predecessor here.

Nothing *forces* adding `4a10333…`, so it is the home's call. If it is added:
split it into halves like the others, and add it **only in the same commit that bumps lines 69 and
2891** — while those lines still carry it, `!selfSrc.includes(sha)` makes the assertion defeat
itself.

A grep is not enough to find these sites: the reject needles are half-literals, and a test file
holds the values it rejects as well as the one it accepts. Read the assertion, not the file.

## 2. The new value, one commit

Three lines, both files, one commit (why one commit: §3).

```
# in skipi-crewing, on the pin-bump branch — NOT run by me
OLD=4a1033338ed55bda0cffe5717bec6b14956aafc6
NEW=32b19c9d30086cf30cebe418deb762298c3ebc59

sed -i "s/$OLD/$NEW/" .github/workflows/skipi-guard.yml
sed -i "s/$OLD/$NEW/g" tests/crewing_c3b2_candidate_harness.mjs

# expect exactly 3 changed lines, 2 files, and ZERO remaining hits:
git diff --numstat          # -> 1 1 .github/workflows/skipi-guard.yml ; 2 2 tests/…c3b2…mjs
git grep -n "$OLD"          # -> empty, unless the superseded entry below was added
git grep -n d6238191        # -> still workflow:36 and harness:62, untouched
```

Optional fourth line, the convention of §1 — append to the `superseded` array at line 2910
(`'4a103333' + '8ed55bda…'` concatenates to the old pin; the halves keep the probe from reading
its own source):

```
, '4a103333' + '8ed55bda0cffe5717bec6b14956aafc6'
```

**Dry-run, measured.** The two blobs were taken from `origin/main` into session scratch, the two
`sed` lines above applied, and the four pin assertions re-implemented verbatim from the harness and
run against the result:

```
ok   L62   runtime pin d6238191 unchanged
ok   L69   workflow pins exactly the new guard SHA (trailing \n present)
ok   L2891 extracted pin === 32b19c9d30086cf30cebe418deb762298c3ebc59
ok   L2912 no superseded pin accepted (7 entries, incl. the old one)
```

Diff shape: workflow `1 1`, harness `2 2` without the superseded entry, `3 3` with it. This was
run on copies in scratch — `skipi-crewing` was never written to.

Also stale after the bump, prose only, no assertion reads them: the comment at lines **63-68**
still calls `e8000d75` "the accepted configuration", and **2904-2909** narrates `e8000d75` as the
newest entry. Whoever writes the commit should refresh both to name `32b19c9d` / guard No.975,
or the next reader is misinformed by the file that is supposed to be the record.

## 3. Why both files must move in ONE commit

`.github/workflows/skipi-guard.yml:172` gates `assert-config-superset` on the diff being
**exactly one file** and that file being the workflow:

```
if [[ "${#GUARD_CHANGED_FILES[@]}" -eq 1 && "${GUARD_CHANGED_FILES[0]}" == ".github/workflows/skipi-guard.yml" ]]; then
```

So a two-file pin bump **skips config-superset by construction** (this is RISKS №497, written up
in the harness comment at 2901-2903). The compensating check is harness line 2891 — and that line
only runs if the resolved task's harness set contains the c3b2 harness.

Measured: it does.

| the 2-file diff | result |
| --- | --- |
| resolved task | `crewing-c3b2` (rule *"crewing C3b2 candidate facts and decisions routing (owner619, 2026-09-22)"*) |
| scope violations | **0** — both paths are in `allowed_file_patterns["crewing-c3b2"]` |
| protected / release-sensitive touches | 0 / 0 |
| harnesses | 7, including `node tests/crewing_c3b2_candidate_harness.mjs` |

So the two-file bump **is self-checking**: it loses config-superset and gains the harness that
reads the pin. Splitting it into two commits is the failure mode — a workflow-only commit takes
the superset path under `--override-protected skipi-guard-workflow-bootstrap` and leaves the
harness literal stale, which reddens the *next* diff that routes to `crewing-c3b2`.

## 4. Resolver over the combined diff — measured

**Method.** `bin/skipi-guard` and `configs/homes/crewing.json` read at guard `32b19c9d`, then
`resolve_task` → `additive_task_checks` → `effective_allowed_patterns` → `scope_check_for_task` →
`classify_paths` → `configured_harnesses` driven over `git diff --name-only` lists. Read-only: the
guard CLI was never invoked against `skipi-crewing`, so no `--json` report was written and no
existing report was overwritten.

Routing semantics, from `bin/skipi-guard:140-173`: a rule matches only if **ALL** changed files are
inside its file set; a mixed diff falls back to `default_task` (`plugin-host`); first matching rule
wins.

| case | files | task | scope viol. | harnesses | verdict |
| --- | --- | --- | --- | --- | --- |
| A pin bump only | 2 | `crewing-c3b2` | 0 | 7 (incl. pin harness) | **passes** |
| B branch 930 vs main | 163 | `plugin-host` (default) | **163** | 4 | **refused** |
| C `reports/CROSSCHECK-973-2026-11-06.md` only | 1 | `crewing-records` | 0 | **0** | passes |
| D all three `reports/*.md` | 3 | `crewing-records` | 0 | **0** | passes |
| E 930 + the 3 reports | 166 | `plugin-host` | **166** | 4 | **refused** |
| F 930 + reports + pin bump | 168 | `plugin-host` | **168** | 4 | **refused** |
| G 930 + pin bump | 165 | `plugin-host` | **165** | 4 | **refused** |

The contract reports are `reports/CROSSCHECK-973-2026-11-06.md` (on `docs/crewing-973-crosscheck-20261106`),
plus `reports/CONFIRM-973-v2-2026-11-06.md` and `reports/EDITS-973-client-20261106.md` (on
`chore/crewing-898-record-20261105`). Three files, all `reports/*.md`, all records-eligible.
`reports/` does not exist on `main` yet.

### The 930 set splits four ways — denominator 163

| slice | n | task | viol | harnesses |
| --- | --- | --- | --- | --- |
| records-eligible text evidence | **106** | `crewing-records` | 0 | **0** |
| `src-tauri/src/{lib,native_lifecycle,native_local_commit,native_local_joint_tests}.rs` | **4** | `crewing-635-single-user` | 0 | 19 |
| `AGENTS.md` | **1** | `repo-meta` | 0 | 0 |
| non-text evidence residue | **52** | `plugin-host` (default) | **52** | 4 |
| | 106+4+1+52 = **163** ✓ | | | |

The 106 + the 3 reports together still resolve to `crewing-records` with 0 violations (109 files).

**The 52-file residue has no route at all** — not one task's `allowed_file_patterns` covers even a
single one of them. By extension: `.sh` 13, `.py` 11, `.log` 8, `.rc` 6, `.rs` 9 (snippets and
copies under `scratchpad/`), `.jsonl` 1, `.bin` 1, `.tsv` 1, `.before` 1, no extension 1
(`scratchpad/crewing-930/evidence/s4-out/attempts`).

### One matcher divergence worth knowing

The route patterns are `scratchpad/*.md` etc., and the **guard** matches with
`fnmatch.fnmatchcase` (`bin/skipi-guard:57-72`), whose `*` **crosses `/`**. So
`scratchpad/*.md` does reach `scratchpad/crewing-930/evidence/LIVE-PROBE-ANALYSIS.md` — measured,
and that is why 106 of the nested files are eligible at all.

The workflow's own inline JS (`globToRegExp`, line 99) maps `*` → `[^/]*` and would **not** match
those paths. It does not decide the route — it only feeds the `release_sensitive` log line, and CI
passes `--auto-task` (line 266; line 263 says the bash-computed task is "manual path retained for
logs/bootstrap only"). But the two matchers do not agree, and anyone reading the workflow as the
spec will predict the opposite of what the gate does.

## 5. Order — pin-bump PR first; 930 does not pass either way

**Answer to (4): a branch-930 push with the pin bump inside does not pass.** Case G: 165 files,
165 scope violations. The pin bump cannot rescue 930, because routing is all-or-nothing and the
diff is mixed. The bump must go as its own PR (case A, clean).

Measured ordering facts, including gotcha №140:

- The deployed hook `/home/linux/Developer/skipi-crewing/.git/hooks/pre-push` is **not drifted**
  (`hooks check` → `MATCH`, sha256 `a8677af2…`) and runs
  `SKIPI_GUARD_BIN=/home/linux/Developer/skipi-guard/bin/skipi-guard` — the **live checkout**, not
  the pinned SHA.
- That checkout is at `4a10333` and contains **zero** occurrences of `crewing-records`.
- Under that on-disk config, measured: a reports-only push routes to `plugin-host` with
  **3 violations** → refused locally. The pin bump itself routes to `crewing-c3b2` with
  **0 violations** → accepted locally today, no guard pull needed first.
- Every `skipi-crewing` worktree shares that one hook (`git rev-parse --git-path hooks` from the
  930 worktree resolves to `/home/linux/Developer/skipi-crewing/.git/hooks`), so there is no
  worktree from which a records push passes until the checkout moves.

So:

1. **Pin-bump PR** off `main f145c601`, the three lines of §2, one commit. Passes the local hook
   now; its own PR run checks out guard `32b19c9d` (the pin is already bumped on that branch) and
   routes to `crewing-c3b2` with the pin harness running.
2. **Human merges** it. `main` now pins `32b19c9d`.
3. **Fast-forward `/home/linux/Developer/skipi-guard` to `32b19c9d`** — a separate step, and the
   one that actually makes `crewing-records` work for local pushes. Until then CI knows the route
   and the hook does not.
4. **Then** push records slices: `reports/*.md` and the 106 text files, separately from code.

Step 3 is not optional and is not part of the PR. It is also the step that is invisible in any
diff, which is exactly why it gets forgotten.

## 6. What does NOT pass — back to the manager

1. **930 is not pushable as one branch**, with or without the pin bump (163/165 violations). It has
   to be split along §4's four slices; the records route handles only one of them.
2. **The 52-file non-text evidence residue has no route in any task.** `.sh`, `.py`, `.log`, `.rc`,
   `scratchpad/**/*.rs`, `.jsonl`, `.bin`, `.tsv`, `attempts`. The route as merged is text-only
   (`.json`/`.md`/`.txt`) by its own name and config. Covering them is a **new guard route = a new
   guard PR with per-path justification**, not a pin bump, and not something I will widen on a peer
   request. Alternative without a guard change: the 52 files stay unpushed (evidence lives on disk
   and in the handoff), or they are re-expressed as `.txt`/`.md`/`.json` records.
3. **`crewing-records` has no `harness_commands` entry** — measured: 0 harnesses. A records push is
   checked for scope and nothing else. That is a deliberate zero-radius route, but it means the
   route is also unexercised in the home; its negative control lives only in guard
   `tests/test_crewing_records_route.py`. Flagging, not objecting.
4. **Stale prose in the harness** (lines 63-68, 2904-2909) still names `e8000d75` as accepted.
   No assertion reads it; a future reader will be misled. Fix it in the same commit.
5. `AGENTS.md` on 930 routes alone to `repo-meta` (0 violations) — it can ride with neither the
   code slice nor the records slice, so it is a third push or it is dropped from 930.

## Appendix — reproducing this

Driver scripts are session-scratch, not committed; the measurement is reproducible from the two
blobs plus a diff list:

```
git -C skipi-guard show 32b19c9d:bin/skipi-guard                 > guard.py
git -C skipi-guard show 32b19c9d:configs/homes/crewing.json      > crewing.json
git -C skipi-crewing diff --name-only f145c601...f59e4aa          > set930.txt
# then: resolve_task(cfg, files) / scope_check_for_task(cfg, task, files, effective_allowed_patterns(...))
```

`resolve_task` and `pattern_matches` are pure functions of (config, file list) — driving them
directly is why no guard report was written anywhere during this work.
