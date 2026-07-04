# Skipi Smoke Tools

Small verification tools used by release and target-verification smoke runs.

Rules for this directory:

- Tools must be deterministic and runnable locally.
- Tools must have tests under `tests/`.
- Scripts must return non-zero when they find a real failure signal.
- Do not hide command failures behind shell pipes; wrappers must use `set -euo pipefail`.
- Reports should include explicit exit codes and evidence paths.
- Never print secret values.

Current tools:

- `logcat_scanner.py` — classifies Android logcat files/directories and ignores known Pixel test-tool noise while still failing on real Skipi app crashes/ANRs.
