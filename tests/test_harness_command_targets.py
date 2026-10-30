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

Presence is resolved against each home's DEFAULT REF (`origin/HEAD`, else main,
else master) with `git cat-file -e`, never against the working tree: a home
checkout sits on whatever branch its last task left it on. Measured 2026-10-29,
4 of the 8 checkouts were NOT on their default branch (broker on
feat/map-msi-layer-revendor, seafarer on a fix branch, landing and server on
master while `main` does not resolve), and reading their trees reports files as
missing that are present on main. Absolute script paths stay a filesystem check
-- they point outside the home.

Presence is resolved on the default ref ALONE -- a script on some other branch is
not delivered (manager's decision 2026-10-30: a lagging local checkout is machine
hygiene, not a property of the home, and is cured by `git fetch` in that
checkout). So the two fleet tests below require the home checkouts to be FETCHED;
on a stale checkout they report a harness as missing that the remote's default
branch already carries.

Measured 2026-10-30 over all eight home configs with the real
`configured_harnesses` resolution: **0 undeliverable**, so `KNOWN_DEBT` is empty.
Its one entry (`crewing/crewing-635-single-user` -> `crewing_escaping_negative`)
was discharged by the crewing home authoring the harness, merged to crewing main
`64b016a0` (PR skipi-crewing #77, 2026-10-30T06:04:03Z) -- the fix this file
predicted, in the home rather than in the guard. `KNOWN_DEBT` may only SHRINK --
`test_known_debt_has_no_stale_entry` fails if an entry is delivered and left
behind, so the list cannot rot into a blanket waiver.

CI checks out only skipi-guard, so the two fleet-state tests skip where a home
checkout is absent. The detector itself is exercised unconditionally against
synthetic configs, each negative paired with a positive control in the same
window.
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
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
KNOWN_DEBT: frozenset[tuple[str, str, str, str]] = frozenset()

# Commands that run a suite runner rather than a file; nothing to resolve.
NO_SCRIPT_TOKEN = frozenset({"npm test", "pytest"})


def script_of(command: str) -> str | None:
    """The script a harness command runs, or None for a bare suite runner."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    return next((t for t in tokens if t.endswith(SCRIPT_SUFFIXES)), None)


def default_ref(repo: Path) -> str | None:
    """The home's default branch, or None when it cannot be determined offline.

    `origin/HEAD` is the authoritative answer. Without it, exactly one of
    `origin/main`/`origin/master` is unambiguous. When BOTH resolve there is no
    offline way to tell which is trunk, so this returns None rather than guessing:
    skipi-server carries both (`origin/master` 2667039 is its trunk, `origin/main`
    1f3c61d diverges) and guessing `origin/main` reported four of its harnesses as
    missing when they sit on `origin/master`. A local branch is never used -- it is
    whatever the last task left checked out, and routinely behind.
    """
    head = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True,
    )
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip().split("refs/remotes/", 1)[-1]
    resolving = [
        candidate
        for candidate in ("origin/main", "origin/master")
        if subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", candidate],
            capture_output=True, text=True,
        ).returncode == 0
    ]
    return resolving[0] if len(resolving) == 1 else None


def tracked_in_ref(repo: Path, ref: str, path: str) -> bool:
    """Is `path` in the tree of `ref`? Never consults the working tree."""
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{ref}:{path}"],
        capture_output=True, text=True,
    ).returncode == 0


def undeliverable_harnesses(
    config: dict[str, Any], repo: Path, ref: str | None = None
) -> set[tuple[str, str, str, str]]:
    """Harness commands whose script neither exists nor can be added on that route.

    Repo-relative scripts are resolved in `ref`'s tree (the home's default branch
    when not given), because a checkout's working tree reflects whatever branch
    the last task left behind. Absolute paths point outside the home and stay a
    filesystem check.
    """
    if ref is None:
        ref = default_ref(repo)
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
            if path.is_absolute():
                if path.exists():
                    continue
            elif ref is not None and tracked_in_ref(repo, ref, script):
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


def fixture_home(tmp: Path, scripts: tuple[str, ...] = (), published: bool = True) -> Path:
    """A minimal home checkout: a real git repo whose default branch holds `scripts`.

    `published` mirrors a clone by giving the repo an `origin/main` remote-tracking
    ref, which is what `default_ref` reads. Pass False for the case of a checkout
    with no remote-tracking refs at all.
    """
    run = lambda *a: subprocess.run(
        ["git", "-C", str(tmp), *a], capture_output=True, text=True, check=True
    )
    run("init", "-q", "-b", "main", ".")
    run("config", "user.email", "fixture@local")
    run("config", "user.name", "fixture")
    for script in scripts:
        target = tmp / script
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// fixture\n", encoding="utf-8")
    run("add", "-A")
    run("commit", "-q", "--allow-empty", "-m", "fixture")
    if published:
        run("update-ref", "refs/remotes/origin/main", run("rev-parse", "HEAD").stdout.strip())
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

    def test_presence_follows_the_ref_not_the_working_tree(self):
        """Regression: the first cut of this check read the working tree.

        A home checkout sits on whatever branch its last task left it on, so a
        script committed on the default branch but absent from the current
        worktree is present, and a script sitting only in the worktree is not.
        Measured 2026-10-29, 4 of 8 home checkouts were off their default
        branch, which mis-reported broker and seafarer harnesses as missing.
        """
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw), ("tests/committed_harness.mjs",))
            config = fixture_config("node tests/committed_harness.mjs", [])
            self.assertEqual("origin/main", default_ref(repo))

            # on the default ref, then removed from the worktree -> still present
            (repo / "tests/committed_harness.mjs").unlink()
            self.assertEqual(undeliverable_harnesses(config, repo), set())

            # present ONLY in the worktree, never committed -> not deliverable
            stray = repo / "tests/stray_harness.mjs"
            stray.write_text("// fixture\n", encoding="utf-8")
            self.assertEqual(
                undeliverable_harnesses(fixture_config("node tests/stray_harness.mjs", []), repo),
                {("fixture", "a-route", "probe", "tests/stray_harness.mjs")},
            )

    def test_default_ref_refuses_to_guess_between_main_and_master(self):
        """Regression: preferring origin/main blindly mis-read skipi-server.

        That home carries both `origin/master` (trunk, with the file) and a
        divergent `origin/main` (without it), and no `origin/HEAD`. Guessing
        `origin/main` reported four of its harnesses as undeliverable. With both
        present and no `origin/HEAD` the honest answer is "cannot tell offline".
        """
        run = lambda repo, *a: subprocess.run(
            ["git", "-C", str(repo), *a], capture_output=True, text=True, check=True
        )
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw), published=False)
            sha = run(repo, "rev-parse", "HEAD").stdout.strip()

            # exactly one remote-tracking candidate -> unambiguous
            run(repo, "update-ref", "refs/remotes/origin/master", sha)
            self.assertEqual("origin/master", default_ref(repo))

            # both candidates, no origin/HEAD -> refuse to guess
            run(repo, "update-ref", "refs/remotes/origin/main", sha)
            self.assertIsNone(default_ref(repo))

            # origin/HEAD is authoritative and settles it
            run(repo, "symbolic-ref", "refs/remotes/origin/HEAD",
                "refs/remotes/origin/master")
            self.assertEqual("origin/master", default_ref(repo))

    def test_a_local_branch_is_never_used_as_the_default_ref(self):
        """A checkout's own branch is not evidence about the home."""
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw), published=False)
            self.assertIsNone(default_ref(repo), "a local branch is not evidence")

    def test_a_script_on_no_ref_at_all_is_still_a_violation(self):
        """The shape the original finding had, documented so it stays caught.

        `crewing_escaping_negative` was absent from EVERY crewing ref when it was
        found (2026-10-29: `git log --all --diff-filter=A` empty, no path matching
        `escap` ever added). The assertion below first establishes that no ref of
        the fixture carries the script, so the case is the real one and not merely
        "missing from the default branch".
        """
        with tempfile.TemporaryDirectory() as raw:
            repo = fixture_home(Path(raw))
            refs = subprocess.run(
                ["git", "-C", str(repo), "for-each-ref", "--format=%(refname)"],
                capture_output=True, text=True,
            ).stdout.split()
            self.assertTrue(refs, "the fixture must have at least one ref")
            for ref in refs:
                self.assertFalse(
                    tracked_in_ref(repo, ref, "tests/ghost_harness.mjs"),
                    f"{ref} unexpectedly carries the script",
                )
            self.assertEqual(
                undeliverable_harnesses(
                    fixture_config("node tests/ghost_harness.mjs", []), repo
                ),
                {("fixture", "a-route", "probe", "tests/ghost_harness.mjs")},
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

    def measured(self) -> tuple[set[tuple[str, str, str, str]], list[str], set[str]]:
        """Findings, the homes that could not be measured, and the homes that could."""
        found: set[tuple[str, str, str, str]] = set()
        skipped: list[str] = []
        covered: set[str] = set()
        for path, config in home_configs():
            repo = Path(str(config.get("repo", ""))).expanduser()
            if not (repo / ".git").exists():
                skipped.append(f"{path.stem}: no checkout at {repo}")
                continue
            ref = default_ref(repo)
            if ref is None:
                skipped.append(
                    f"{path.stem}: cannot determine the default branch offline; "
                    "set it with `git remote set-head origin -a`"
                )
                continue
            covered.add(str(config.get("home", path.stem)))
            found |= undeliverable_harnesses(config, repo, ref)
        return found, skipped, covered

    def test_no_route_gains_an_undeliverable_harness_command(self):
        found, skipped, covered = self.measured()
        if not covered:
            self.skipTest("no home could be measured: " + "; ".join(skipped))
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
        found, skipped, covered = self.measured()
        if not covered:
            self.skipTest("no home could be measured: " + "; ".join(skipped))
        # Judge only entries whose home was actually measured: an unmeasurable home
        # must not retire the ratchet for the others.
        stale = {entry for entry in KNOWN_DEBT if entry[0] in covered} - found
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
