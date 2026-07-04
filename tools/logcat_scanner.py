#!/usr/bin/env python3
"""Skipi Android logcat classifier for smoke evidence.

The scanner intentionally does not treat generic AndroidRuntime/tool lines as
warnings. Only real crash/ANR patterns survive after known Pixel test-tool
noise is filtered out.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Iterable


NOISE_PATTERNS = [
    re.compile(r"\b(?:monkey|uiautomator)\b", re.IGNORECASE),
    re.compile(r"com\.android\.commands\.(?:monkey|uiautomator)", re.IGNORECASE),
    re.compile(r"com\.android\.crashrecovery", re.IGNORECASE),
    re.compile(r"com\.google\.android\.crashrecovery", re.IGNORECASE),
    re.compile(r"AconfigPackage: .*crashrecovery", re.IGNORECASE),
]

CRASH_PATTERNS = [
    re.compile(r"\bFATAL EXCEPTION\b", re.IGNORECASE),
    re.compile(r"\bANR in\b", re.IGNORECASE),
    re.compile(r"\bProcess:\s+app\.skipi\.", re.IGNORECASE),
    re.compile(r"\bAndroidRuntime\b.*\bapp\.skipi\.", re.IGNORECASE),
]


def is_noise(line: str) -> bool:
    return any(pattern.search(line) for pattern in NOISE_PATTERNS)


def is_crash_signal(line: str) -> bool:
    if is_noise(line):
        return False
    return any(pattern.search(line) for pattern in CRASH_PATTERNS)


def iter_files(paths: Iterable[str]) -> Iterable[pathlib.Path]:
    for item in paths:
        path = pathlib.Path(item)
        if path.is_dir():
            yield from sorted(p for p in path.rglob("*.txt") if p.is_file())
        elif path.is_file():
            yield path


def scan_file(path: pathlib.Path) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for number, line in enumerate(fh, 1):
            text = line.rstrip("\n")
            if is_crash_signal(text):
                matches.append({"file": str(path), "line": number, "text": text})
    return matches


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Classify Skipi Android logcat files.")
    parser.add_argument("paths", nargs="+", help="Logcat file or directory")
    parser.add_argument("--json", dest="json_path", default=None, help="Write JSON summary")
    args = parser.parse_args(argv)

    files = list(iter_files(args.paths))
    matches: list[dict[str, object]] = []
    for path in files:
        matches.extend(scan_file(path))

    payload = {
        "files_scanned": len(files),
        "crash_signals": len(matches),
        "matches": matches,
    }
    if args.json_path:
        pathlib.Path(args.json_path).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"files_scanned={payload['files_scanned']} crash_signals={payload['crash_signals']}")
    for match in matches[:20]:
        print(f"{match['file']}:{match['line']}: {match['text']}")
    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
