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

## Templates

Templates are provided only as artifacts:

- `templates/git-hooks/pre-push.skipi-guard.sh`
- `templates/github-actions/skipi-guard.yml`

Do not install them into app repos without a separate explicit GO.

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
