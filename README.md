# skipi-guard

Stop-line guard skeleton for Skipi homes.

The CLI compares a configured home repo between `--base` and `--head`, classifies changed files against per-home protected and release-sensitive paths, lists configured harness commands, and emits stable JSON with `schema_version: skipi-guard.v1`.

## Usage

```bash
/home/linux/Developer/skipi-guard/bin/skipi-guard verify \
  --home broker \
  --task plugin-host \
  --base origin/main \
  --head HEAD \
  --json /tmp/out.json
```

Harness commands are not run by default:

```bash
/home/linux/Developer/skipi-guard/bin/skipi-guard verify \
  --home crewing \
  --task plugin-host \
  --base origin/main \
  --head HEAD \
  --run-harness \
  --json /tmp/out.json
```

Protected-path overrides must use a recognized token bound to the selected home
and its allowed file set. Unknown tokens fail closed. The token is not written
to JSON.

```bash
SKIPI_GUARD_OVERRIDE_TOKEN=broker-presence-contracts-bootstrap \
  /home/linux/Developer/skipi-guard/bin/skipi-guard verify \
  --home broker \
  --task plugin-host \
  --base origin/main \
  --head HEAD
```

## JSON Contract

The schema file is `schemas/skipi-guard.v1.schema.json`. Required top-level fields:

```json
{
  "schema_version": "skipi-guard.v1",
  "home": "broker",
  "task": "plugin-host",
  "repo": "/home/linux/Developer/skipi-broker",
  "base": "origin/main",
  "head": "HEAD",
  "sha": "shortsha",
  "changed_files": [],
  "protected_paths_touched": [],
  "release_changes": false,
  "tests": [],
  "status": "pass",
  "errors": []
}
```

## Pre-push hook canon

`templates/git-hooks/pre-push.skipi-guard.sh` is the git-tracked canonical
source of every deployed home pre-push hook. Enforcement logic living only in
`.git/hooks/` is forbidden (AGENTS.md); deployed hooks must be byte-identical
to the render of this canon.

The hook reads the pre-push stdin lines
(`<local ref> <local sha> <remote ref> <remote sha>`) and validates every
pushed ref on its pushed bytes (SKI-INC-2026-07-16): base is the remote sha
when known locally, otherwise the merge-base with `origin/main`; head is the
pushed local sha, never the checkout HEAD. Ref deletions are skipped, an empty
stdin exits 0, and any failing ref fails the whole push. Harnesses run in a
temporary detached worktree at the pushed sha. There are no
`SKIPI_GUARD_BASE`/`SKIPI_GUARD_HEAD`/`SKIPI_GUARD_TASK` env overrides: stdin
is authoritative and the task is resolved from the pushed diff via the
declarative `task_routing` rules in `configs/homes/<home>.json`
(all changed files inside a rule's file set; mixed diffs fall back to
`default_task`).

```bash
# print the rendered hook for a home
bin/skipi-guard hooks render --home broker

# install into the home checkout (only under a separate explicit GO)
bin/skipi-guard hooks install --home broker

# drift check: exit 1 unless deployed == render(canon), byte for byte
bin/skipi-guard hooks check --home broker
```

Per-ref validation used by the hook (one pre-push stdin line):

```bash
bin/skipi-guard pre-push-ref \
  --home broker \
  --repo /home/linux/Developer/skipi-broker \
  --local-ref refs/heads/feature-x --local-sha <sha> \
  --remote-ref refs/heads/feature-x --remote-sha <sha-or-zeros>
```

`verify` accepts `--auto-task` (exactly one of `--task`/`--auto-task`) to
resolve the task from the same declarative routing rules; the CI template
`templates/github-actions/skipi-guard.yml` uses it by default, with
`vars.SKIPI_GUARD_TASK` as an explicit per-repo override.

Do not install templates into app repos without a separate explicit GO.

## Report Reality Verifier

`skipi-report-verify` compares a worker report against the guard result, local git facts, and remote branch/PR facts when the claimed rung requires them.

```bash
/home/linux/Developer/skipi-guard/bin/skipi-report-verify \
  --report /tmp/report.json \
  --guard-result /tmp/guard.json \
  --json /tmp/verify.json
```

Verifier JSON uses `schema_version: skipi-verifier.v1`:

```json
{
  "schema_version": "skipi-verifier.v1",
  "task": "broker-plugin-host-skeleton",
  "status": "pass",
  "claimed_rung": "pr_ready",
  "verified_rung": "pr_ready",
  "mismatches": [],
  "evidence": []
}
```

The verifier exits non-zero when the report disagrees with guard/git/PR reality. It tolerates legacy reports without `schema_version` by emitting a warning. The schema file is `schemas/skipi-verifier.v1.schema.json`.
