"""The release door may not move a version without the harness that pins it.

Owner GO 2026-10-29 (DECISIONS 1614): tighten the `release` door so a version
bump cannot pass without the pinning `stack_build_metadata` harness -- keyed on
a PROPERTY, not on a task or harness name.

The remedy is to RUN that harness, not to refuse the diff. Refusing it was the
first cut and it reddened 18 tests in five homes: the four-file shape is the
deliberate "canonical version-bump routing" rule, and
`test_seafarer_version_bump_route.test_missing_stack_harness_keeps_the_pre_existing_release_route`
exists precisely to assert that a missing stack harness must NOT break it. So
classification and scope are left exactly as they were, the pinning harness is
added to the harnesses the push must run, and a stale pin is what fails it --
which is the defect itself, not a new structural rule.

The property, read entirely out of the config: an `exact_task_file_sets` entry
declares files that may only move together, and a harness script listed INSIDE
that set is the one that pins the other members -- it is bumped in the same diff
it validates. So a diff that moves the set's version-bearing members (the ones
matching `release_sensitive_paths`) must go through a task whose resolved
harnesses include that pinning harness. The exact door satisfies this by
construction; a non-exact release task does not, because
`effective_allowed_patterns` hands it every release-sensitive pattern WITHOUT
listing them and without adding the harness.

What that hole cost, measured 2026-10-29 in skipi-crewing: `620dbfa`
(0.4.136 -> 0.4.137, 15.10) and `2f383f4` (-> 0.4.138, 19.10) each carried the
same four files -- dist/index.html, src-tauri/Cargo.lock, src-tauri/Cargo.toml,
src-tauri/tauri.conf.json -- omitting src/lib.rs and both harnesses. That shape
routes to `release` and passed, so the pinning harness stayed at 0.4.136 while
the home moved to 0.4.138 and the harness was red on main for two weeks
(BACKLOG No879). The green shape is all seven files through the exact door:
`5a4fc75` (02.08, which introduced the pin at 0.4.136) and `a10ec7c4` (29.10,
the 0.4.139 bump, pin moved to 0.4.139).

Radius, measured over the eight home configs: five homes declare both a
`stack-metadata` exact set and a `*stack_build_metadata` harness -- broker,
crewing, management, onboard, seafarer -- and in them 16 tasks could move a
version-bearing member without running the pin (every non-exact release task,
plus seafarer's `mobile-external-url`, which is in that home's `release_tasks`).
landing, plugin-delivery and server declare no exact set, so the check selects
nothing there and says so in `test_homes_without_an_exact_set_are_untouched`.

Behavioural delta against the previous binary, same fixture: exactly two shapes
change, both the intended one (the 4-file bump on `release`, auto-routed and
forced). The 7-file form, a release push with no version-bearing file, and a
route-635 push all keep their previous verdict.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"

LOADER = SourceFileLoader("guard_release_door", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

PIN_COMMAND = "node tests/stack_build_metadata_harness.mjs"
NEGATIVE_CONTROL_COMMAND = "node tests/stack_verification_negative_control_harness.mjs"

# Homes that declare both a stack-metadata exact set and a pinning harness.
PINNED_HOMES = ("broker", "crewing", "management", "onboard", "seafarer")
# Homes with no exact set at all: the check must select nothing.
UNPINNED_HOMES = ("landing", "plugin-delivery", "server")

# The four files of 620dbfa / 2f383f4, and the seven of 5a4fc75 / a10ec7c4.
BUMP_FOUR = (
    "dist/index.html",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
)
EXACT_SEVEN = BUMP_FOUR + (
    "src-tauri/src/lib.rs",
    "tests/stack_build_metadata_harness.mjs",
    "tests/stack_verification_negative_control_harness.mjs",
)


def home_config(home: str) -> dict[str, Any]:
    with (ROOT / "configs" / "homes" / f"{home}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def harnesses_for(config: dict[str, Any], task: str) -> list[dict[str, Any]]:
    return MODULE.unique_harnesses(MODULE.configured_harnesses(config, task))


class VersionPinningProperty(unittest.TestCase):
    """The pin is derived from the declared coupling, not from a name."""

    def test_pin_is_the_harness_whose_script_sits_inside_the_exact_set(self):
        for home in PINNED_HOMES:
            config = home_config(home)
            pins = MODULE.version_pinning_harnesses(config, "stack-metadata")
            members = set(config["exact_task_file_sets"]["stack-metadata"])
            self.assertIn(PIN_COMMAND, pins, home)
            self.assertIn(NEGATIVE_CONTROL_COMMAND, pins, home)
            for pin in pins:
                script = pin.split()[-1]  # pins is keyed by command
                self.assertIn(script, members, f"{home}: {pin} is not a member of its own exact set")

    def test_a_harness_outside_the_exact_set_is_not_a_pin(self):
        """Negative control: only membership of the set makes a harness a pin."""
        config = {
            "exact_task_file_sets": {"e": ["v.json", "tests/pin.mjs"]},
            "harness_commands": {
                "e": [
                    {"name": "pin", "command": "node tests/pin.mjs"},
                    {"name": "outsider", "command": "node tests/outsider.mjs"},
                ]
            },
        }
        self.assertEqual(
            MODULE.version_pinning_harnesses(config, "e"), {"node tests/pin.mjs": "pin"},
            "pins map command -> declared harness name, so the injected entry keeps its name",
        )

    def test_homes_without_an_exact_set_are_untouched(self):
        """Zero radius must be stated, not assumed: no exact set, no finding ever."""
        for home in UNPINNED_HOMES:
            config = home_config(home)
            self.assertEqual({}, config.get("exact_task_file_sets", {}), home)
            self.assertEqual(
                [],
                MODULE.unpinned_version_moves(config, list(BUMP_FOUR), []),
                home,
            )


class UnpinnedVersionMoves(unittest.TestCase):
    """The detector, on the real home configs."""

    def version_members(self, config: dict[str, Any]) -> list[str]:
        return [
            member
            for member in config["exact_task_file_sets"]["stack-metadata"]
            if MODULE.classify_paths([member], config.get("release_sensitive_paths", []), "r")
        ]

    def test_the_exact_door_is_satisfied_by_construction(self):
        for home in PINNED_HOMES:
            config = home_config(home)
            found = MODULE.unpinned_version_moves(
                config, list(EXACT_SEVEN), harnesses_for(config, "stack-metadata")
            )
            self.assertEqual([], found, home)

    def test_every_door_that_could_move_a_version_now_runs_the_pin_or_is_reported(self):
        """The 16 open doors measured 2026-10-29 are all closed for version diffs."""
        closed = 0
        for home in PINNED_HOMES:
            config = home_config(home)
            members = self.version_members(config)
            self.assertTrue(members, home)
            for task in sorted(MODULE.configured_tasks(config)):
                effective = MODULE.effective_allowed_patterns(
                    config,
                    task,
                    [c for c in config.get("additive_task_checks", []) if c.get("task") == task],
                )
                carries = [
                    m for m in members if any(MODULE.pattern_matches(m, p) for p in effective)
                ]
                if not carries:
                    continue
                resolved = harnesses_for(config, task)
                commands = {str(h.get("command", "")) for h in resolved}
                found = MODULE.unpinned_version_moves(config, carries, resolved)
                if PIN_COMMAND in commands:
                    self.assertEqual([], found, f"{home}/{task} runs the pin, must not be flagged")
                else:
                    self.assertTrue(found, f"{home}/{task} can move {carries} without the pin")
                    closed += 1
        self.assertEqual(16, closed, "the measured radius of open doors changed")

    def test_a_diff_with_no_version_bearing_path_is_never_flagged(self):
        config = home_config("crewing")
        self.assertEqual(
            [],
            MODULE.unpinned_version_moves(config, ["dist/index.html"], []),
            "dist/index.html alone carries no version",
        )

    def test_listing_the_pin_on_the_door_silences_it(self):
        """Proves the check keys on the harness coupling, not on the task name."""
        config = home_config("crewing")
        members = self.version_members(config)
        self.assertTrue(MODULE.unpinned_version_moves(config, members, []))
        pinned = harnesses_for(config, "stack-metadata")
        self.assertEqual([], MODULE.unpinned_version_moves(config, members, pinned))


class ReleaseDoorCli(unittest.TestCase):
    """Drives the real binary against a fixture whose pin can be stale or current."""

    PIN_NAME = "crewing_stack_build_metadata"

    def fixture(self, tmp: Path, pin: str, version: str) -> Path:
        run = lambda *a: subprocess.run(
            ["git", "-C", str(tmp), *a], capture_output=True, text=True, check=True
        )
        run("init", "-q", "-b", "main", ".")
        run("config", "user.email", "fixture@local")
        run("config", "user.name", "fixture")
        (tmp / "dist").mkdir(parents=True, exist_ok=True)
        (tmp / "src-tauri/src").mkdir(parents=True, exist_ok=True)
        (tmp / "tests").mkdir(parents=True, exist_ok=True)
        (tmp / "dist/index.html").write_text("<html></html>\n", encoding="utf-8")
        (tmp / "src-tauri/Cargo.lock").write_text("lock\n", encoding="utf-8")
        (tmp / "src-tauri/Cargo.toml").write_text("toml\n", encoding="utf-8")
        (tmp / "src-tauri/src/lib.rs").write_text("rs\n", encoding="utf-8")
        (tmp / "src-tauri/tauri.conf.json").write_text(
            json.dumps({"version": version}) + "\n", encoding="utf-8"
        )
        # a real pinning harness: it asserts the manifest still carries its literal
        (tmp / "tests/stack_build_metadata_harness.mjs").write_text(
            "import fs from 'node:fs';\n"
            f"const PIN = '{pin}';\n"
            "const t = JSON.parse(fs.readFileSync('src-tauri/tauri.conf.json','utf8'));\n"
            "if (t.version !== PIN) { throw new Error(`pin ${PIN} != ${t.version}`); }\n",
            encoding="utf-8",
        )
        (tmp / "tests/stack_verification_negative_control_harness.mjs").write_text(
            "// negative control\n", encoding="utf-8"
        )
        run("add", "-A")
        run("commit", "-q", "-m", "base")
        run("tag", "baseline")
        return tmp

    def verify(self, repo: Path, *extra: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as out:
            report = Path(out) / "guard.json"
            subprocess.run(
                ["python3", str(GUARD), "verify", "--home", "crewing", "--repo", str(repo),
                 "--auto-task", "--base", "baseline", "--head", "HEAD",
                 "--json", str(report), *extra],
                capture_output=True, text=True,
            )
            with report.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    def commit(self, repo: Path, message: str) -> None:
        subprocess.run(["git", "-C", str(repo), "add", "-A"],
                       capture_output=True, text=True, check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qam", message],
                       capture_output=True, text=True, check=True)

    def bump_four(self, repo: Path, to_version: str) -> None:
        """The 620dbfa / 2f383f4 shape: four files, no harness."""
        (repo / "src-tauri/tauri.conf.json").write_text(
            json.dumps({"version": to_version}) + "\n", encoding="utf-8"
        )
        for name in ("dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml"):
            with (repo / name).open("a", encoding="utf-8") as handle:
                handle.write("bump\n")
        self.commit(repo, "canonical four-file bump")

    def pin_status(self, payload: dict[str, Any]) -> str | None:
        for entry in payload.get("tests", []):
            if entry.get("name") == self.PIN_NAME:
                return entry.get("status")
        return None

    def test_the_four_file_bump_keeps_its_classification(self):
        """The canonical route is NOT taken away -- only the harness is added."""
        with tempfile.TemporaryDirectory() as raw:
            repo = self.fixture(Path(raw), pin="0.4.138", version="0.4.138")
            self.bump_four(repo, "0.4.139")
            payload = self.verify(repo)
            self.assertEqual("release", payload["task"])
            self.assertEqual("canonical version-bump routing", payload["task_rule"])
            self.assertEqual([], payload["scope_violations"])

    def test_the_four_file_bump_now_runs_the_pinning_harness(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = self.fixture(Path(raw), pin="0.4.138", version="0.4.138")
            self.bump_four(repo, "0.4.139")
            payload = self.verify(repo)
            self.assertTrue(payload["unpinned_version_moves"], payload)
            finding = payload["unpinned_version_moves"][0]
            self.assertEqual("stack-metadata", finding["exact_task"])
            self.assertIn("src-tauri/tauri.conf.json", finding["moved_version_paths"])
            self.assertIsNotNone(
                self.pin_status(payload), "the pinning harness must be in the plan"
            )

    def test_a_stale_pin_fails_the_four_file_bump(self):
        """The 2f383f4 defect: version moves to 0.4.139, pin stays at 0.4.138."""
        with tempfile.TemporaryDirectory() as raw:
            repo = self.fixture(Path(raw), pin="0.4.138", version="0.4.138")
            self.bump_four(repo, "0.4.139")
            payload = self.verify(repo, "--run-harness")
            # Assert on the pin entry and its own error, not on the overall status:
            # the fixture does not carry the other release-door harnesses, so a
            # status assertion would pass for the wrong reason.
            self.assertEqual("fail", self.pin_status(payload))
            self.assertTrue(
                any(self.PIN_NAME in error for error in payload["errors"]), payload["errors"]
            )

    def test_the_seven_file_exact_bump_passes_with_the_pin_moved(self):
        """Positive control, 5a4fc75 / a10ec7c4 shape: pin bumped in the same diff."""
        with tempfile.TemporaryDirectory() as raw:
            repo = self.fixture(Path(raw), pin="0.4.138", version="0.4.138")
            (repo / "src-tauri/tauri.conf.json").write_text(
                json.dumps({"version": "0.4.139"}) + "\n", encoding="utf-8"
            )
            (repo / "tests/stack_build_metadata_harness.mjs").write_text(
                "import fs from 'node:fs';\n"
                "const PIN = '0.4.139';\n"
                "const t = JSON.parse(fs.readFileSync('src-tauri/tauri.conf.json','utf8'));\n"
                "if (t.version !== PIN) { throw new Error(`pin ${PIN} != ${t.version}`); }\n",
                encoding="utf-8",
            )
            for name in ("dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml",
                         "src-tauri/src/lib.rs",
                         "tests/stack_verification_negative_control_harness.mjs"):
                with (repo / name).open("a", encoding="utf-8") as handle:
                    handle.write("bump\n")
            self.commit(repo, "seven-file exact bump")
            payload = self.verify(repo, "--run-harness")
            self.assertEqual("stack-metadata", payload["task"])
            self.assertEqual([], payload["unpinned_version_moves"],
                             "the exact door already carries its pin")
            self.assertEqual("pass", self.pin_status(payload))

    def test_a_dependency_only_change_does_not_fail_the_pin(self):
        """BACKLOG No877: a Cargo delta with an unchanged version must not be blocked.

        The pin is injected (the path is version-bearing) and PASSES, because
        nothing about the version moved -- injection is not a refusal. Asserted on
        the pin entry alone: this fixture lacks the other release-door harnesses.
        """
        with tempfile.TemporaryDirectory() as raw:
            repo = self.fixture(Path(raw), pin="0.4.138", version="0.4.138")
            with (repo / "src-tauri/Cargo.toml").open("a", encoding="utf-8") as handle:
                handle.write("[dependencies]\nserde = \"1\"\n")
            self.commit(repo, "dependency delta only")
            payload = self.verify(repo, "--run-harness")
            self.assertEqual("pass", self.pin_status(payload))
            self.assertTrue(payload["unpinned_version_moves"])
            self.assertFalse(
                [error for error in payload["errors"] if self.PIN_NAME in error],
                "a dependency delta must raise no pin error",
            )


if __name__ == "__main__":
    unittest.main()
