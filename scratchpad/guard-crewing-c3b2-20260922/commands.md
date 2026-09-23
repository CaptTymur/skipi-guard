# Reproduction commands

Working directory: `/home/linux/Developer/worktrees/guard-crewing-c3b2-20260922`.
Base: `b2f187b72fc4beed4a8ad5600f02e31de92e5257` (live SSH main matched before worktree creation).

Every suite run uses the same output-isolation adapter:

```bash
TMPDIR="$PWD/scratchpad/guard-crewing-c3b2-20260922/tmp" \
PYTHONPATH="$PWD/scratchpad/guard-crewing-c3b2-20260922/adapter" \
python3 -m unittest discover -s tests -v
```

Baseline ran before creating the new test: 420 tests. Red used the new test against unchanged base config:

```bash
TMPDIR="$PWD/scratchpad/guard-crewing-c3b2-20260922/tmp" \
PYTHONPATH="$PWD/scratchpad/guard-crewing-c3b2-20260922/adapter" \
python3 -m unittest discover -s tests -p test_crewing_c3b2_route.py -v
```

Targeted after config addition:

```bash
TMPDIR="$PWD/scratchpad/guard-crewing-c3b2-20260922/tmp" \
PYTHONPATH="$PWD/scratchpad/guard-crewing-c3b2-20260922/adapter" \
python3 -m unittest discover -s tests -p 'test_crewing_c3b*_route.py' -v
```

`adapter/sitecustomize.py` only supplies the CLI's existing `--json` option when a legacy hook test would use the fixed `/tmp/skipi-guard-pre-push-<home>.json`, and redirects that old pathname's test read to the same scratch destination. TMPDIR isolates legacy temporary fixtures. No assertions, task/base/head, checks, override, canonical hook, or engine code are replaced. New C3b2 tests already use an explicit output-only CLI adapter inside each fixture and record node invocations instead of invoking external product checks. No product hook is installed.

`targeted-first.log` records a corrected test expectation: pre-existing hook-only pure-pin auto-bootstrap succeeds, whereas plain verify rejects it. The final test preserves both behaviors. No guard implementation changed to make that test pass.

`full-first.log` retains the initial full candidate run: 428 tests, one old security baseline snapshot needed the same additive-task normalization already used for later routes. The final run keeps every old security assertion and baseline value.
