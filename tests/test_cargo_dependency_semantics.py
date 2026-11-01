"""A Cargo dependency delta at an unchanged package identity is not a release class.

BACKLOG No877, owner GO 2026-11-01 (DECISIONS 1643; rule 1498 lifted for this case
by that word). Before this, `release_sensitive_paths` matched
`src-tauri/Cargo.toml` and `src-tauri/Cargo.lock` by PATH alone, so a non-release
task could not carry a new dependency: the unconditional check refused the push
with "release-sensitive path touch is blocked for this task" regardless of what
had actually changed inside the file. A version bump and a `serde_json` feature
flag were the same event to the gate.

The predicate now implemented, read out of the file content at the same two refs
the diff is taken from:

  * `Cargo.toml` -- release iff `[package].version` or `[package].name` moved;
  * `Cargo.lock` -- release iff the ROOT package's locked version moved, the root
    being the `[package].name` of the sibling manifest;
  * anything else -- untouched.

Fail-closed everywhere: a file added or removed, a manifest whose `[package]`
cannot be read, a lock with no entry for the root package, or an unreadable ref
all answer "release". A gate may not go quiet on an unknown.

`protected_paths` is deliberately NOT touched -- only the release-sensitive
classification moves -- and `tauri.conf.json`/`package.json` stay a release touch
whatever their content, pinned by
`test_tauri_conf_and_package_json_are_untouched_by_this_rule`.

Radius over the eight home configs: five treat the Cargo paths as
release-sensitive (broker, crewing, management, onboard, seafarer); landing,
plugin-delivery and server do not, so the predicate selects nothing there --
stated by `test_homes_without_cargo_release_rules_select_nothing`, not assumed.
Only crewing has a non-release task whose allowlist carries both Cargo paths
(`crewing-635-single-user`), so it is the one home where the whole push can be
asserted green end to end; for the other four the assertion is on the presence or
absence of the release-sensitive error itself, under their non-release
`plugin-host`.

Live control case (handoff): crewing `0cf73ef1` on
`feature/crewing-635-single-user-20261030` -- `+libc`, `serde_json` gains
`features = ["raw_value"]`, lock gains a `"libc"` dependency line, package
version unchanged at 0.4.139. Against the hook's own base,
`merge-base(0cf73ef1, origin/main)` = `64b016a0`, that push went from one error to
`errors=0`, and the three dropped touches are reported under
`cargo_dependency_touches` with their reason.
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

LOADER = SourceFileLoader("guard_cargo_semantics", str(GUARD))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

MANIFEST = "src-tauri/Cargo.toml"
LOCK = "src-tauri/Cargo.lock"
ROOT_CRATE = "skipi-crewing"
BASE_VERSION = "0.4.139"
RELEASE_ERROR = "release-sensitive path touch is blocked for this task"

# Homes whose release_sensitive_paths match the Cargo paths, and those that do not.
CARGO_HOMES = ("broker", "crewing", "management", "onboard", "seafarer")
NON_CARGO_HOMES = ("landing", "plugin-delivery", "server")


def home_config(home: str) -> dict[str, Any]:
    with (ROOT / "configs" / "homes" / f"{home}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def manifest_text(version: str, *, name: str = ROOT_CRATE, extra_deps: str = "") -> str:
    return (
        "[package]\n"
        f'name = "{name}"\n'
        f'version = "{version}"\n'
        'edition = "2021"\n'
        "\n"
        "[dependencies]\n"
        'serde_json = "1.0"\n'
        f"{extra_deps}"
    )


def lock_text(version: str, *, name: str = ROOT_CRATE, root_deps: str = "", extra_entry: str = "") -> str:
    return (
        "version = 3\n"
        "\n"
        "[[package]]\n"
        f'name = "{name}"\n'
        f'version = "{version}"\n'
        "dependencies = [\n"
        ' "serde_json",\n'
        f"{root_deps}"
        "]\n"
        "\n"
        "[[package]]\n"
        'name = "serde_json"\n'
        'version = "1.0.0"\n'
        f"{extra_entry}"
    )


class CargoFixture:
    """A home-shaped checkout whose Cargo files can be moved one axis at a time."""

    def __init__(self, tmp: Path) -> None:
        self.repo = tmp
        self._run("init", "-q", "-b", "main", ".")
        self._run("config", "user.email", "fixture@local")
        self._run("config", "user.name", "fixture")
        self.write(MANIFEST, manifest_text(BASE_VERSION))
        self.write(LOCK, lock_text(BASE_VERSION))
        self.write("dist/index.html", "<html></html>\n")
        self.write("src-tauri/tauri.conf.json", json.dumps({"version": BASE_VERSION}) + "\n")
        self.write("src-tauri/src/lib.rs", "// rs\n")
        self.commit("base")
        self._run("tag", "baseline")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], capture_output=True, text=True, check=True
        )

    def write(self, path: str, text: str) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> None:
        self._run("add", "-A")
        self._run("commit", "-q", "-m", message)

    def reset(self) -> None:
        self._run("reset", "-q", "--hard", "baseline")

    def is_release(self, path: str) -> tuple[bool, str]:
        return MODULE.cargo_touch_is_release(self.repo, "baseline", "HEAD", path)

    def verify(self, home: str, *task_args: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as out:
            report = Path(out) / "guard.json"
            subprocess.run(
                ["python3", str(GUARD), "verify", "--home", home, "--repo", str(self.repo),
                 "--base", "baseline", "--head", "HEAD", "--json", str(report), *task_args],
                capture_output=True, text=True,
            )
            with report.open("r", encoding="utf-8") as handle:
                return json.load(handle)


class CargoTomlParsing(unittest.TestCase):
    def test_package_identity_is_read_from_the_package_table_only(self):
        text = (
            "[package]\n"
            'name = "skipi-crewing"\n'
            'version = "0.4.139"\n'
            "\n"
            "[dependencies]\n"
            'serde_json = { version = "1.0", features = ["raw_value"] }\n'
            "\n"
            "[dev-dependencies]\n"
            'name = "decoy"\n'
            'version = "9.9.9"\n'
        )
        self.assertEqual(("skipi-crewing", "0.4.139"), MODULE.cargo_manifest_identity(text))

    def test_a_key_that_merely_starts_with_the_name_is_not_the_key(self):
        text = '[package]\nversion-notes = "x"\nname_suffix = "y"\n'
        self.assertEqual((None, None), MODULE.cargo_manifest_identity(text))

    def test_lock_version_is_read_for_the_named_package(self):
        text = lock_text("0.4.139")
        self.assertEqual("0.4.139", MODULE.cargo_lock_version_of(text, ROOT_CRATE))
        self.assertEqual("1.0.0", MODULE.cargo_lock_version_of(text, "serde_json"))
        self.assertIsNone(MODULE.cargo_lock_version_of(text, "absent-crate"))


class CargoPredicate(unittest.TestCase):
    """The four cases the handoff names, each with its opposite in the same window."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = CargoFixture(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def test_red_a_manifest_version_change_is_a_release_touch(self):
        self.fx.write(MANIFEST, manifest_text("0.4.140"))
        self.fx.commit("bump")
        is_release, reason = self.fx.is_release(MANIFEST)
        self.assertTrue(is_release)
        self.assertIn("0.4.139 -> 0.4.140", reason)

    def test_green_a_dependency_delta_is_not_a_release_touch(self):
        self.fx.write(
            MANIFEST,
            manifest_text(
                BASE_VERSION,
                extra_deps='libc = "0.2"\nserde_json = { version = "1.0", features = ["raw_value"] }\n',
            ),
        )
        self.fx.commit("deps")
        is_release, reason = self.fx.is_release(MANIFEST)
        self.assertFalse(is_release, reason)
        self.assertIn(BASE_VERSION, reason)

    def test_green_a_lock_with_only_a_dependency_delta_is_not_a_release_touch(self):
        self.fx.write(
            LOCK,
            lock_text(BASE_VERSION, root_deps=' "libc",\n',
                      extra_entry='\n[[package]]\nname = "libc"\nversion = "0.2.0"\n'),
        )
        self.fx.commit("lock deps")
        is_release, reason = self.fx.is_release(LOCK)
        self.assertFalse(is_release, reason)

    def test_red_a_lock_with_a_root_version_change_is_a_release_touch(self):
        self.fx.write(LOCK, lock_text("0.4.140"))
        self.fx.commit("lock bump")
        is_release, reason = self.fx.is_release(LOCK)
        self.assertTrue(is_release)
        self.assertIn("0.4.139 -> 0.4.140", reason)

    def test_red_a_manifest_name_change_is_a_release_touch(self):
        self.fx.write(MANIFEST, manifest_text(BASE_VERSION, name="skipi-renamed"))
        self.fx.commit("rename")
        is_release, reason = self.fx.is_release(MANIFEST)
        self.assertTrue(is_release)
        self.assertIn("[package].name", reason)

    def test_a_dependency_version_bump_in_the_lock_is_not_the_root_version(self):
        """A dependency's own version moving is still only a dependency delta."""
        self.fx.write(LOCK, lock_text(BASE_VERSION).replace('version = "1.0.0"', 'version = "1.0.1"'))
        self.fx.commit("dep bump")
        is_release, reason = self.fx.is_release(LOCK)
        self.assertFalse(is_release, reason)


class CargoPredicateFailsClosed(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = CargoFixture(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def test_an_added_manifest_is_a_release_touch(self):
        self.fx.write("extra/Cargo.toml", manifest_text(BASE_VERSION, name="extra"))
        self.fx.commit("add manifest")
        is_release, reason = self.fx.is_release("extra/Cargo.toml")
        self.assertTrue(is_release)
        self.assertIn("added or removed", reason)

    def test_a_removed_manifest_is_a_release_touch(self):
        (self.fx.repo / MANIFEST).unlink()
        self.fx.commit("drop manifest")
        self.assertTrue(self.fx.is_release(MANIFEST)[0])

    def test_an_unreadable_package_table_is_a_release_touch(self):
        self.fx.write(MANIFEST, "[dependencies]\nserde_json = \"1.0\"\n")
        self.fx.commit("no package table")
        is_release, reason = self.fx.is_release(MANIFEST)
        self.assertTrue(is_release)
        self.assertIn("cannot read", reason)

    def test_a_lock_missing_the_root_package_is_a_release_touch(self):
        self.fx.write(LOCK, 'version = 3\n\n[[package]]\nname = "serde_json"\nversion = "1.0.0"\n')
        self.fx.commit("lock without root")
        is_release, reason = self.fx.is_release(LOCK)
        self.assertTrue(is_release)
        self.assertIn("locked version", reason)

    def test_a_lock_whose_manifest_is_unreadable_is_a_release_touch(self):
        self.fx.write(MANIFEST, "garbage\n")
        self.fx.write(LOCK, lock_text(BASE_VERSION, root_deps=' "libc",\n'))
        self.fx.commit("manifest unreadable")
        is_release, reason = self.fx.is_release(LOCK)
        self.assertTrue(is_release)
        self.assertIn("root package name", reason)


class CargoSplitAcrossHomes(unittest.TestCase):
    """Radius: the same content judged against every home's own rules."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = CargoFixture(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def split(self, home: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        config = home_config(home)
        touches = MODULE.classify_paths(
            [MANIFEST, LOCK], config.get("release_sensitive_paths", []), "release-sensitive"
        )
        return MODULE.split_cargo_dependency_touches(self.fx.repo, "baseline", "HEAD", touches)

    def test_dependency_delta_is_dropped_in_every_cargo_home(self):
        self.fx.write(MANIFEST, manifest_text(BASE_VERSION, extra_deps='libc = "0.2"\n'))
        self.fx.write(LOCK, lock_text(BASE_VERSION, root_deps=' "libc",\n'))
        self.fx.commit("deps")
        for home in CARGO_HOMES:
            kept, dropped = self.split(home)
            self.assertEqual([], kept, f"{home}: nothing may stay release-sensitive")
            self.assertTrue(dropped, f"{home}: the touches must be reported as dependency-only")

    def test_version_change_is_kept_in_every_cargo_home(self):
        self.fx.write(MANIFEST, manifest_text("0.4.140"))
        self.fx.write(LOCK, lock_text("0.4.140"))
        self.fx.commit("bump")
        for home in CARGO_HOMES:
            kept, dropped = self.split(home)
            self.assertTrue(kept, f"{home}: a version bump stays release-sensitive")
            self.assertEqual([], dropped, f"{home}: nothing may be dropped")

    def test_homes_without_cargo_release_rules_select_nothing(self):
        """Zero radius stated: these homes never classify the Cargo paths at all."""
        self.fx.write(MANIFEST, manifest_text("0.4.140"))
        self.fx.commit("bump")
        for home in NON_CARGO_HOMES:
            config = home_config(home)
            self.assertEqual(
                [],
                MODULE.classify_paths(
                    [MANIFEST, LOCK], config.get("release_sensitive_paths", []), "release-sensitive"
                ),
                home,
            )

    def test_tauri_conf_and_package_json_are_untouched_by_this_rule(self):
        """A different class: these stay release-sensitive whatever their content."""
        self.fx.write("src-tauri/tauri.conf.json", json.dumps({"version": BASE_VERSION, "x": 1}) + "\n")
        self.fx.write("package.json", json.dumps({"version": BASE_VERSION}) + "\n")
        self.fx.commit("manifests with unchanged versions")
        for home in CARGO_HOMES:
            config = home_config(home)
            touches = MODULE.classify_paths(
                ["src-tauri/tauri.conf.json", "package.json"],
                config.get("release_sensitive_paths", []),
                "release-sensitive",
            )
            self.assertTrue(touches, home)
            kept, dropped = MODULE.split_cargo_dependency_touches(
                self.fx.repo, "baseline", "HEAD", touches
            )
            self.assertEqual(touches, kept, f"{home}: this rule must not reclassify them")
            self.assertEqual([], dropped, home)


class CargoCli(unittest.TestCase):
    """End to end through the real binary."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = CargoFixture(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def test_red_a_version_bump_is_blocked_under_a_non_release_task(self):
        self.fx.write(MANIFEST, manifest_text("0.4.140"))
        self.fx.write(LOCK, lock_text("0.4.140"))
        self.fx.commit("bump")
        for home in CARGO_HOMES:
            payload = self.fx.verify(home, "--task", "plugin-host")
            self.assertIn(RELEASE_ERROR, payload["errors"], home)
            self.assertTrue(payload["release_changes"], home)

    def test_green_a_dependency_delta_is_not_blocked_under_a_non_release_task(self):
        self.fx.write(MANIFEST, manifest_text(BASE_VERSION, extra_deps='libc = "0.2"\n'))
        self.fx.write(LOCK, lock_text(BASE_VERSION, root_deps=' "libc",\n'))
        self.fx.commit("deps")
        for home in CARGO_HOMES:
            payload = self.fx.verify(home, "--task", "plugin-host")
            self.assertNotIn(RELEASE_ERROR, payload["errors"], home)
            self.assertFalse(payload["release_changes"], home)
            self.assertTrue(payload["cargo_dependency_touches"], home)

    def test_the_whole_push_is_green_on_the_one_route_that_allows_both_paths(self):
        """crewing-635-single-user: the live control case 0cf73ef1, reproduced."""
        self.fx.write(
            MANIFEST,
            manifest_text(
                BASE_VERSION,
                extra_deps='libc = "0.2"\nserde_json = { version = "1.0", features = ["raw_value"] }\n',
            ),
        )
        self.fx.write(LOCK, lock_text(BASE_VERSION, root_deps=' "libc",\n'))
        self.fx.write("src-tauri/src/native_account.rs", "// account\n")
        self.fx.commit("635 shape with a dependency delta")
        payload = self.fx.verify("crewing", "--task", "crewing-635-single-user")
        self.assertEqual([], payload["errors"])
        self.assertEqual("pass", payload["status"])
        self.assertFalse(payload["release_changes"])
        self.assertEqual(
            {MANIFEST, LOCK},
            {touch["path"] for touch in payload["cargo_dependency_touches"]},
        )


if __name__ == "__main__":
    unittest.main()
