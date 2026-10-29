"""Class check: a route's harness command must name a script some push can provide.

`bin/skipi-guard` runs EVERY harness of the resolved task (`configured_harnesses`
plus the release-task inheritance) regardless of which files the push touches.
So if a harness command names a script that does not exist in the home and that
no push on that route may create, the route is fail-closed for ANY content: the
diff is irrelevant, the hook always reports `harness failed: <name>` with
`Cannot find module`. That is the class this file pins.

Invariant, per route R and per harness command H resolved for R -- the script H
runs must satisfy at least one of:

  (a) it exists in the home checkout, or
  (b) it is listed in R's OWN `allowed_file_patterns`, so a push on R can add it
      in the same diff that runs it.

(b) is why a harness may legitimately precede its file: `security-escaping-191`
was created as owner-authorized debt (`66f063a`, 2026-09-04) whose
`require_all_of` DEMANDS the negatives harness in the diff, and every later
route inherits it by the cumulative-superset rule that
`test_crewing_635_single_user_route.py` enforces. Such a forward reference is
sound and is NOT flagged here. What is flagged is a harness enrolled in a route
that cannot deliver it.

Measured on main d8f57ccf (configs/homes/crewing.json blob 2e6b605c), 2026-10-29,
over all eight home configs with the real `configured_harnesses` resolution:
4 undeliverable (below), 12 sound forward references, 8 commands with no script
token. `KNOWN_DEBT` may only SHRINK -- `test_known_debt_has_no_stale_entry`
fails if an entry is delivered and left behind, so the list cannot rot into a
blanket waiver.

CI checks out only skipi-guard, so the two fleet-state tests skip where a home
checkout is absent. The detector itself is exercised unconditionally against
synthetic configs, each negative paired with a positive control in the same
window.
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"

LOADER = SourceFileLoader("guard_harness_targets", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

SCRIPT_SUFFIXES = (".mjs", ".js", ".py", ".sh")

# (home, task, harness name, script) that no push on `task` can satisfy.
# Each entry is a blocked route, not a tolerated one. Origin of both groups is
# the same: a harness was enrolled into a route's suite while the file was still
# undelivered, and the route's allowlist does not let that route create it.
KNOWN_DEBT = frozenset(
    {
        # skipi-broker: three harnesses inherited into the escaping route whose
        # own delivery routes are `stack-metadata` / `broker-map-demo-422`.
        ("broker", "security-escaping-191", "broker_map_msi_module_pin",
         "tests/map_msi_module_pin_harness.mjs"),
        ("broker", "security-escaping-191", "broker_stack_build_metadata",
         "tests/stack_build_metadata_harness.mjs"),
        ("broker", "security-escaping-191", "broker_stack_verification_negative_control",
         "tests/stack_verification_negative_control_harness.mjs"),
        # skipi-crewing: BACKLOG No179 negatives harness, owner-authorized
        # 2026-09-04 and never written; route 635 inherits it (cumulative
        # superset) but its allowlist cannot deliver it. Discharged by the home
        # authoring the file on `security-escaping-191`, not by dropping it.
        ("crewing", "crewing-635-single-user", "crewing_escaping_negative",
         "tests/crewing_escaping_negative_harness.mjs"),
    }
)

# Commands that run a suite runner rather than a file; nothing to resolve.
NO_SCRIPT_TOKEN = frozenset({"npm test", "pytest"})


def script_of(command: str) -> str | None:
    """The script a harness command runs, or None for a bare suite runner."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    return next((t for t in tokens if t.endswith(SCRIPT_SUFFIXES)), None)


def undeliverable_harnesses(config: dict[str, Any], repo: Path) -> set[tuple[str, str, str, str]]:
    """Harness commands whose script neither exists nor can be added on that route."""
    home = str(config.get("home", ""))
    allowed = {
        str(task): set(str(p) for p in patterns)
        for task, patterns in (config.get("allowed_file_patterns") or {}).items()
    }
    found: set[tuple[str, str, str, str]] = set()
    for task in sorted(MODULE.configured_tasks(config)):
        resolved = MODULE.unique_harnesses(MODULE.configured_harnesses(config, task))
        for harness in resolved:
            command = str(harness.get("command", ""))
            script = script_of(command)
            if script is None:
                continue
            path = Path(script)
            target = path if path.is_absolute() else repo / path
            if target.exists():
                continue
            if not path.is_absolute() and script in allowed.get(task, set()):
                continue  # sound forward reference: this route may deliver it
            found.add((home, task, str(harness.get("name", "")), script))
    return found


def home_configs() -> list[tuple[Path, dict[str, Any]]]:
    out = []
    for path in sorted((ROOT / "configs" / "homes").glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            out.append((path, json.load(handle)))
    return out


def fixture_home(tmp: Path, scripts: tuple[str, ...] = ()) -> Path:
    """A minimal home checkout: a .git marker plus the named scripts."""
    (tmp / ".git").mkdir(parents=True, exist_ok=True)
    for script in scripts:
        target = tmp / script
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// fixture\n", encoding="utf-8")
    return tmp


def fixture_config(command: str, allowed: list[str], task: str = "a-route") -> dict[str, Any]:
    return {
        "home": "fixture",
        "harness_commands": {task: [{"name": "probe", "command": command}]},
        "allowed_file_patterns": {task: allowed},
    }


class HarnessCommandTargets(unittest.TestCase):
    """The detector itself; runs everywhere, homes or no homes."""

    def test_detector_flags_a_script_the_route_cannot_deliver(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            config = fixture_config("node tests/ghost_harness.mjs", ["dist/index.html"])
            self.assertEqual(
                undeliverable_harnesses(config, repo),
                {("fixture", "a-route", "probe", "tests/ghost_harness.mjs")},
            )

    def test_detector_passes_a_script_the_route_may_deliver(self):
        """Negative control for the test above: same missing file, now allowlisted."""
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            config = fixture_config(
                "node tests/ghost_harness.mjs", ["dist/index.html", "tests/ghost_harness.mjs"]
            )
            self.assertEqual(undeliverable_harnesses(config, repo), set())

    def test_detector_passes_a_script_that_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw), ("tests/real_harness.mjs",))
            config = fixture_config("node tests/real_harness.mjs", ["dist/index.html"])
            self.assertEqual(undeliverable_harnesses(config, repo), set())

    def test_detector_ignores_a_bare_suite_runner(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            for command in sorted(NO_SCRIPT_TOKEN):
                self.assertIsNone(script_of(command), command)
                self.assertEqual(
                    undeliverable_harnesses(fixture_config(command, []), repo), set(), command
                )

    def test_detector_sees_harnesses_gained_by_release_inheritance(self):
        """The hook resolves inherited harnesses, so the check must too."""
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            config = {
                "home": "fixture",
                "release_tasks": ["release"],
                "harness_commands": {
                    "plugin-host": [{"name": "probe", "command": "node tests/ghost_harness.mjs"}],
                    "release": [],
                },
                "allowed_file_patterns": {},
            }
            found = undeliverable_harnesses(config, repo)
            self.assertIn(
                ("fixture", "release", "probe", "tests/ghost_harness.mjs"),
                found,
                "a harness inherited into a release task must be resolved like the hook does",
            )

    def test_absolute_script_paths_are_resolved_as_written(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            present = repo / "abs_harness.mjs"
            present.write_text("// fixture\n", encoding="utf-8")
            self.assertEqual(
                undeliverable_harnesses(fixture_config(f"node {present}", []), repo), set()
            )
            missing = repo / "gone_harness.mjs"
            self.assertEqual(
                undeliverable_harnesses(fixture_config(f"node {missing}", []), repo),
                {("fixture", "a-route", "probe", str(missing))},
            )


class FleetHarnessTargets(unittest.TestCase):
    """State of the eight home configs; needs the home checkouts on disk."""

    def measured(self) -> tuple[set[tuple[str, str, str, str]], list[str]]:
        found: set[tuple[str, str, str, str]] = set()
        skipped: list[str] = []
        for path, config in home_configs():
            repo = Path(str(config.get("repo", ""))).expanduser()
            if not (repo / ".git").exists():
                skipped.append(f"{path.stem} ({repo})")
                continue
            found |= undeliverable_harnesses(config, repo)
        return found, skipped

    def test_no_route_gains_an_undeliverable_harness_command(self):
        found, skipped = self.measured()
        if skipped and not found:
            self.skipTest(f"home checkouts absent: {', '.join(skipped)}")
        new = found - KNOWN_DEBT
        self.assertEqual(
            set(),
            new,
            "a harness command names a script this route can neither find nor create, "
            "so the route is fail-closed for any content: "
            + "; ".join(f"{h}/{t} {n} -> {s}" for h, t, n, s in sorted(new)),
        )

    def test_known_debt_has_no_stale_entry(self):
        """Delivering a harness must shrink KNOWN_DEBT, so it cannot become a blanket waiver."""
        found, skipped = self.measured()
        if skipped:
            self.skipTest(f"home checkouts absent: {', '.join(skipped)}")
        stale = KNOWN_DEBT - found
        self.assertEqual(
            set(),
            stale,
            "KNOWN_DEBT lists a harness that now resolves; delete the entry: "
            + "; ".join(f"{h}/{t} {n} -> {s}" for h, t, n, s in sorted(stale)),
        )

    def test_every_non_file_command_is_a_declared_suite_runner(self):
        for path, config in home_configs():
            for task in sorted(MODULE.configured_tasks(config)):
                for harness in MODULE.unique_harnesses(MODULE.configured_harnesses(config, task)):
                    command = str(harness.get("command", ""))
                    if script_of(command) is None:
                        self.assertIn(command, NO_SCRIPT_TOKEN, f"{path.stem}/{task}: {command}")


if __name__ == "__main__":
    unittest.main()
