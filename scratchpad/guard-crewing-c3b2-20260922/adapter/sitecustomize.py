"""Legacy suite I/O isolation only; does not alter checks or their outcomes."""
import io
import os
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / 'tmp'
PREFIX = '/tmp/skipi-guard-pre-push-'
# The real CLI already accepts --json; provide it only for its default output.
if Path(sys.argv[0]).name == 'skipi-guard' and len(sys.argv) > 1 and sys.argv[1] == 'pre-push-ref' and '--json' not in sys.argv:
    home = sys.argv[sys.argv.index('--home') + 1]
    sys.argv.extend(['--json', str(DEST / f'skipi-guard-pre-push-{home}.json')])
# One legacy test reads the historical default pathname directly.
_original_open = io.open
def _isolated_open(file, *args, **kwargs):
    if isinstance(file, (str, os.PathLike)) and str(file).startswith(PREFIX):
        file = DEST / Path(file).name
    return _original_open(file, *args, **kwargs)
io.open = _isolated_open
