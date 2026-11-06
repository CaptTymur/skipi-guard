# WORKLOG — guard No.975 / crewing `crewing-records`

The guard repo tracks no WORKLOG; this file exists because one act in this task leaves **no trace
in any diff**: moving the live guard checkout that every deployed pre-push hook executes.

## 2026-11-06 — live checkout fast-forwarded `4a10333` → `32b19c9d`

Manager decision (skipi-ops-04, 06.11): do it now, in my own home, after a live `ls-remote`;
zero writes to other repos. Done. No push to `main` — this was `git pull --ff-only`.

| | value |
| --- | --- |
| live `origin/main` at the time (re-checked) | `32b19c9d30086cf30cebe418deb762298c3ebc59` |
| `/home/linux/Developer/skipi-guard` HEAD **before** | `4a1033338ed55bda0cffe5717bec6b14956aafc6` |
| HEAD **after** | `32b19c9d30086cf30cebe418deb762298c3ebc59` (= live main) |
| fast-forward legitimate | `merge-base --is-ancestor 4a10333 32b19c9d` → true |
| working tree | clean apart from untracked `.worktrees/` |

**Radius, measured before moving.** The move carries `configs/homes/crewing.json` (+20 lines) and
nothing else that enforces: `bin/` **unchanged**, `templates/` **unchanged**. So no other home's
gate behaviour changed and the hook canon did not move — no hook reinstall was needed anywhere.

**Why it matters / what it changes.** The deployed hook
`/home/linux/Developer/skipi-crewing/.git/hooks/pre-push` runs
`SKIPI_GUARD_BIN=/home/linux/Developer/skipi-guard/bin/skipi-guard` — the live checkout, **not**
the SHA pinned in the home's CI workflow. Until this move, that checkout had **0** occurrences of
`crewing-records`; it now has 2.

**Proof the hook now reads the new config** (same probe, same code path, before and after, driven
through the on-disk `bin/skipi-guard` and its own `load_home_config('crewing')`):

| probe | before (`4a10333`) | after (`32b19c9d`) |
| --- | --- | --- |
| the 3 `reports/*.md` contract reports | `plugin-host`, **3 scope violations** → refused | `crewing-records`, **0 violations** |
| the 2-file pin bump | `crewing-c3b2`, 0 violations | `crewing-c3b2`, 0 violations (unchanged) |

Also verified after the move:

- `hooks check --home crewing` → `MATCH`, sha256 `a8677af2e79a9920a6c8a7b50674f1e076b9b173134710cd5c816a228bab75b0` (no drift introduced).
- `bin/skipi-guard` on disk is byte-identical to the blob at `32b19c9d` (`cmp` clean) — the hook executes the merged binary, not a stale working copy.
- CI on the merge commit: run `42243583474`, workflow `guard`, **completed / success**, 4m2s,
  2026-11-06T15:29:56Z. Worth stating explicitly because PR #78 went in on owner word with review
  bypassed — the bypass was of review, not of the suite, so the config now serving every crewing
  hook is test-green.

The guard's own suite was **not** re-run locally: main's CI is green above, and a local suite run
writes home-looking reports to a fixed `/tmp` path where it can overwrite a real incident report.

## Still open (manager: BACKLOG, not now)

- Harness prose in `skipi-crewing` still names `e8000d75` as the accepted pin
  (`tests/crewing_c3b2_candidate_harness.mjs:63-68`, `:2904-2909`); no assertion reads it.
- `crewing-records` has no `harness_commands` entry — a records push is checked for scope and
  nothing else.

Per manager decision, the pin bump itself plus the 930 split and its pushes are ONE stage of the
Crewing writer `skipi-crewing-e7` at FINALIZE, not a separate session; the merge of that PR is the
owner's button. Nothing in `skipi-crewing` was written from here.
