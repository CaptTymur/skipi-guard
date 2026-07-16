#!/usr/bin/env bash
set -euo pipefail

# skipi-guard canonical pre-push hook (home: __SKIPI_GUARD_HOME__).
# Rendered from the git-tracked canon templates/git-hooks/pre-push.skipi-guard.sh
# in skipi-guard. Do not edit deployed copies by hand.
#   install:     skipi-guard hooks install --home __SKIPI_GUARD_HOME__
#   drift check: skipi-guard hooks check   --home __SKIPI_GUARD_HOME__
# Every pushed ref from the pre-push stdin is validated on its pushed bytes;
# base/head come from stdin, never from the checkout HEAD (SKI-INC-2026-07-16).
# No env overrides: stdin is authoritative (decision 2026-07-16).

SKIPI_GUARD_BIN="__SKIPI_GUARD_BIN__"
SKIPI_GUARD_HOME="__SKIPI_GUARD_HOME__"
SKIPI_GUARD_REPO="$(git rev-parse --show-toplevel)"

STATUS=0
while read -r LOCAL_REF LOCAL_SHA REMOTE_REF REMOTE_SHA; do
  if [[ -z "${LOCAL_SHA:-}" ]]; then
    continue
  fi
  if ! "$SKIPI_GUARD_BIN" pre-push-ref \
    --home "$SKIPI_GUARD_HOME" \
    --repo "$SKIPI_GUARD_REPO" \
    --local-ref "$LOCAL_REF" \
    --local-sha "$LOCAL_SHA" \
    --remote-ref "$REMOTE_REF" \
    --remote-sha "$REMOTE_SHA" </dev/null; then
    STATUS=1
  fi
done
exit "$STATUS"
