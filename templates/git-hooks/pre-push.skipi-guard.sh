#!/usr/bin/env bash
set -euo pipefail

# Template only. Install into an app repo only under a separate explicit GO.
SKIPI_GUARD_BIN="${SKIPI_GUARD_BIN:-/home/linux/Developer/skipi-guard/bin/skipi-guard}"
SKIPI_GUARD_HOME="${SKIPI_GUARD_HOME:?set SKIPI_GUARD_HOME to broker, crewing, seafarer, onboard, management, server, or landing}"
SKIPI_GUARD_TASK="${SKIPI_GUARD_TASK:-plugin-host}"
SKIPI_GUARD_BASE="${SKIPI_GUARD_BASE:-origin/main}"
SKIPI_GUARD_HEAD="${SKIPI_GUARD_HEAD:-HEAD}"
SKIPI_GUARD_JSON="${SKIPI_GUARD_JSON:-/tmp/skipi-guard-pre-push.json}"

exec "$SKIPI_GUARD_BIN" verify \
  --home "$SKIPI_GUARD_HOME" \
  --task "$SKIPI_GUARD_TASK" \
  --base "$SKIPI_GUARD_BASE" \
  --head "$SKIPI_GUARD_HEAD" \
  --json "$SKIPI_GUARD_JSON"
