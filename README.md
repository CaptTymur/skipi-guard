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

Protected-path overrides must be explicit. The token is not written to JSON.

```bash
SKIPI_GUARD_OVERRIDE_TOKEN=ack-stop-line \
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
