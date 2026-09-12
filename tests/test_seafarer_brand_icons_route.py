"""Seafarer routes `brand-icons` (52 files) and `guard-pin-bump` (1 file).

Wave Seafarer 0.4.192, the owner-accepted app icon (owner word on the emulator
frame: «нравится. мержим»). Draft of the exact composition:
skipi-ops/handoffs/route-icons-draft.json. Route-PR merge = owner/manager, not
the executor.

Why the two routes have the shape asserted below:

  brand-icons
    * 35 of the 52 paths live under `src-tauri/gen/**`, which is a
      release_sensitive_paths pattern -> verify() refuses the diff for any
      NON-release task ("release-sensitive path touch is blocked for this
      task"). So the task must be in release_tasks.
    * A release task WITHOUT an exact_task_file_sets entry glues every
      release_sensitive_path onto its allowed patterns (finding Н-1, RISKS
      №224b) — Cargo.lock, tauri.conf.json, android/**, the whole gen/**.
      So the task must also carry an exact set, and it is exactly the 52
      files. `test_exact_set_blocks_release_sensitive_glue` proves both halves.
    * The exact set is also what makes 51 files FAIL: the routing rule uses
      require_any_of, so a subset of the 52 still matches the rule; it is
      exact_file_set_check() that reports the missing file.
    * Two of the 52 are ADDITIONS in the home (`mipmap-anydpi-v26/ic_launcher.xml`
      and `values/ic_launcher_background.xml` are untracked at Seafarer main /
      dd271a80), the other 50 are modifications. The guard cannot tell the two
      apart: changed_files_between() runs `git diff --name-only
      --diff-filter=ACDMRTUXB` and keeps the path strings only — no status
      letter reaches resolve_task / exact_file_set_check / scope_check_for_task.
      `test_additions_and_modifications_are_indistinguishable` proves it on a
      fixture where the 50 are modified and the 2 are added.

  guard-pin-bump
    * `.github/workflows/skipi-guard.yml` matches NO release_sensitive_paths
      pattern (`.github/workflows/*release*` / `*deploy*` do not match
      `skipi-guard.yml`) and no protected pattern -> the task must NOT be a
      release task; adding it to release_tasks would only glue the sensitive
      paths on (Н-1 again).
    * It needs no exact_task_file_sets entry either: with a single literal
      allowed pattern, any extra file is already a scope violation, and the
      routing rule's require_all_of keeps the route closed for it.
      `test_pin_bump_needs_no_exact_file_set` states that mechanically.
    * Why the route exists at all — the honest version, after both reviewers
      caught the first one being false. A lone pin bump passes the gate
      TODAY, without any new route: the home's own workflow
      (`.github/workflows/skipi-guard.yml` on Seafarer dd271a80, the step
      "Run skipi-guard") adds `--override-protected
      skipi-guard-workflow-bootstrap` when the diff is exactly that one file,
      and pre_push_ref() passes auto_bootstrap_override=True for the same
      diff. So the route is NOT what makes the pin bump land. It is added so
      that this diff goes through a regular task with the seven harnesses
      instead of a named override — the price being that a pin bump stops
      looking like an override in an audit. Without the route the diff falls
      to default_task plugin-host (whose allowed patterns do not list the
      workflow file) and is carried by the bootstrap override instead; the
      only existing task that lists the path is publication-infra, whose
      require_any_of demands `scripts/publish-rf-mirror.sh`.

Both tasks run all seven harnesses of the home (the stack-metadata tier); an
exact-set release task inherits nothing (configured_harnesses), so the list is
literal for brand-icons, and guard-pin-bump lists the same seven explicitly.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

GUARD_LOADER = SourceFileLoader("skipi_guard_cli_brand_icons", str(GUARD))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
if GUARD_SPEC is None:
    raise RuntimeError(f"cannot load guard module from {GUARD}")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_LOADER.exec_module(GUARD_MODULE)

BRAND_TASK = "brand-icons"
BRAND_RULE = "seafarer brand icons routing (0.4.192)"
PIN_TASK = "guard-pin-bump"
PIN_RULE = "seafarer guard pin bump routing"
WORKFLOW_FILE = ".github/workflows/skipi-guard.yml"
PIN_FILES = [WORKFLOW_FILE]

# The 52 paths of the owner-accepted icon, in config order (C-sorted).
BRAND_FILES = [
    "src-tauri/gen/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
    "src-tauri/gen/android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-hdpi/ic_launcher_foreground.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-hdpi/ic_launcher_round.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-mdpi/ic_launcher.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-mdpi/ic_launcher_foreground.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-mdpi/ic_launcher_round.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xhdpi/ic_launcher_foreground.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xhdpi/ic_launcher_round.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxhdpi/ic_launcher_foreground.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxhdpi/ic_launcher_round.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png",
    "src-tauri/gen/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_round.png",
    "src-tauri/gen/android/app/src/main/res/values/ic_launcher_background.xml",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-20x20@1x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-20x20@2x-1.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-20x20@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-20x20@3x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-29x29@1x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-29x29@2x-1.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-29x29@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-29x29@3x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-40x40@1x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-40x40@2x-1.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-40x40@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-40x40@3x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-60x60@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-60x60@3x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-76x76@1x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-76x76@2x.png",
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-83.5x83.5@2x.png",
    "src-tauri/icons/128x128.png",
    "src-tauri/icons/128x128@2x.png",
    "src-tauri/icons/32x32.png",
    "src-tauri/icons/Square107x107Logo.png",
    "src-tauri/icons/Square142x142Logo.png",
    "src-tauri/icons/Square150x150Logo.png",
    "src-tauri/icons/Square284x284Logo.png",
    "src-tauri/icons/Square30x30Logo.png",
    "src-tauri/icons/Square310x310Logo.png",
    "src-tauri/icons/Square44x44Logo.png",
    "src-tauri/icons/Square71x71Logo.png",
    "src-tauri/icons/Square89x89Logo.png",
    "src-tauri/icons/StoreLogo.png",
    "src-tauri/icons/icon.icns",
    "src-tauri/icons/icon.ico",
    "src-tauri/icons/icon.png",
    "src-tauri/icons/source.png",]
# Additions in the home at Seafarer main / dd271a80 (`git ls-tree` FACT); the
# other 50 are modifications. The guard sees no difference — see the docstring.
BRAND_ADDED_IN_HOME = [
    "src-tauri/gen/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
    "src-tauri/gen/android/app/src/main/res/values/ic_launcher_background.xml",
]
# require_any_of of the routing rule: the two files that make the diff a real
# icon change rather than a stray touch of one asset.
BRAND_REQUIRE_ANY = [
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png",
    "src-tauri/icons/source.png",
]
# The seven harnesses of the home (identical to stack-metadata's tier).
BRAND_HARNESSES = [
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},]
PIN_HARNESSES = list(BRAND_HARNESSES)
# Never on the icon route: the code, the Android manifest, the version trio,
# the front end, the presence manifest, the guard workflow, ignored build
# output, and icon files that are NOT part of the accepted set.
BRAND_FORBIDDEN_EXTRAS = [
    "src-tauri/src/lib.rs",
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "dist/index.html",
    "presence-manifest.json",
    WORKFLOW_FILE,
    "src-tauri/gen/android/app/build/outputs/apk/release/app-release.apk",
    "src-tauri/gen/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml",
    "src-tauri/icons/64x64.png",
]


class SeafarerBrandIconsRouteTests(unittest.TestCase):
    # ---- fixture machinery (disposable git repos, never a product repo) ----

    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop(OVERRIDE_ENV, None)
        return env

    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
            env=self.child_env(),
        )

    def commit_files(self, repo: Path, message: str, updates: dict[str, str]) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def init_repo(self, repo: Path, seed: dict[str, str] | None = None) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        self.commit_files(repo, "seed fixture", {"fixture.txt": "seed\n", **(seed or {})})

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        task: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            "seafarer",
            "--repo",
            str(repo),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
            "--json",
            str(result_json),
        ]
        command.extend(["--task", task] if task else ["--auto-task"])
        proc = subprocess.run(command, text=True, capture_output=True, env=self.child_env())
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def verify_updates(
        self,
        updates: dict[str, str],
        *,
        prefix: str,
        task: str | None = None,
        seed: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo, seed)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json", task=task)

    def candidate(self, files: list[str]) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in files}

    def load_config(self) -> dict[str, Any]:
        with CONFIG.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_brand_pass(
        self,
        payload: dict[str, Any],
        proc: subprocess.CompletedProcess[str],
        *,
        task_source: str,
    ) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["changed_files"], sorted(BRAND_FILES))
        self.assertEqual(payload["task"], BRAND_TASK)
        self.assertEqual(payload["task_source"], task_source)
        self.assertEqual(payload["task_rule"], BRAND_RULE if task_source == "auto" else None)
        self.assertEqual(payload["effective_tasks"], [BRAND_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(payload["auto_bootstrap_override"], False)
        # The release-task stop-line is the only one that opens: the 35 gen/**
        # files are release-sensitive, nothing here is protected.
        self.assertEqual(payload["release_changes"], True)
        self.assertEqual(
            sorted(touch["path"] for touch in payload["release_paths_touched"]),
            sorted(path for path in BRAND_FILES if path.startswith("src-tauri/gen/")),
        )
        self.assertTrue(all(touch["pattern"] == "src-tauri/gen/**" for touch in payload["release_paths_touched"]))
        self.assertEqual([t for t in payload["protected_paths_touched"] if t["kind"] == "protected"], [])
        # Н-1: the exact set keeps the allowlist at exactly the 52 files.
        self.assertEqual(payload["allowed_file_patterns"], BRAND_FILES)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            BRAND_HARNESSES,
        )

    # ---- (а) the exact 52 pass, auto and explicit ----

    def test_exact_52_files_route_to_brand_icons_and_pass(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(BRAND_FILES),
            prefix="skipi-guard-seafarer-brand-full-",
        )
        self.assert_brand_pass(payload, proc, task_source="auto")

    def test_explicit_task_with_exact_52_files_passes(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(BRAND_FILES),
            prefix="skipi-guard-seafarer-brand-explicit-",
            task=BRAND_TASK,
        )
        self.assert_brand_pass(payload, proc, task_source="explicit")

    def test_additions_and_modifications_are_indistinguishable(self) -> None:
        # 50 files already tracked (modified by the candidate) + the 2 Android
        # adaptive-icon files that do not exist in the home yet (added).
        seeded = [path for path in BRAND_FILES if path not in BRAND_ADDED_IN_HOME]
        self.assertEqual(len(seeded), 50)
        seed = {path: f"old bytes for {path}\n" for path in seeded}
        proc, payload = self.verify_updates(
            self.candidate(BRAND_FILES),
            prefix="skipi-guard-seafarer-brand-mixed-",
            seed=seed,
        )
        self.assert_brand_pass(payload, proc, task_source="auto")
        # The guard's whole view of the diff is the path list: same verdict as
        # the all-additions fixture above, no status letter anywhere.
        self.assertIn("--diff-filter=ACDMRTUXB", GUARD.read_text(encoding="utf-8"))

    # ---- (б) the exact set is what disarms Н-1 / RISKS №224b ----

    def test_exact_set_blocks_release_sensitive_glue(self) -> None:
        config = self.load_config()
        self.assertTrue(GUARD_MODULE.is_release_task(config, BRAND_TASK))
        self.assertEqual(GUARD_MODULE.effective_allowed_patterns(config, BRAND_TASK, []), BRAND_FILES)
        sensitive = GUARD_MODULE.rule_patterns(config["release_sensitive_paths"])
        self.assertTrue(sensitive)
        for pattern in sensitive:
            self.assertNotIn(pattern, GUARD_MODULE.effective_allowed_patterns(config, BRAND_TASK, []))
        # Contrast: a release task WITHOUT an exact set does glue them on.
        glued = GUARD_MODULE.effective_allowed_patterns(config, "release", [])
        self.assertTrue(set(sensitive) <= set(glued))
        # Exact-set release tasks inherit no harnesses.
        harnesses = GUARD_MODULE.configured_harnesses(config, BRAND_TASK)
        self.assertEqual([{"name": h["name"], "command": h["command"]} for h in harnesses], BRAND_HARNESSES)

    def test_route_files_are_release_sensitive_but_never_protected(self) -> None:
        config = self.load_config()
        pattern_matches = GUARD_MODULE.pattern_matches
        protected = GUARD_MODULE.rule_patterns(config["protected_paths"])
        for must in ("**/*secret*", "**/*token*", "**/*.p12", "**/*.pem", "**/*camera*", "**/*qr*"):
            self.assertIn(must, protected)
        for path in BRAND_FILES:
            for pattern in protected:
                self.assertFalse(pattern_matches(path, pattern), f"{path} matches protected {pattern}")
        gen_files = [path for path in BRAND_FILES if path.startswith("src-tauri/gen/")]
        self.assertEqual(len(gen_files), 35)
        self.assertEqual(len([p for p in BRAND_FILES if p.startswith("src-tauri/icons/")]), 17)
        for path in gen_files:
            self.assertTrue(pattern_matches(path, "src-tauri/gen/**"), path)
        # …the mechanical reason brand-icons has to be a release task at all.
        self.assertIn(BRAND_TASK, config["release_tasks"])

    # ---- (в) negatives: 51, 53, and the named forbidden extras ----

    def test_51_files_fail(self) -> None:
        for dropped in BRAND_ADDED_IN_HOME + [
            "src-tauri/icons/source.png",
            "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png",
            "src-tauri/gen/android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
        ]:
            files = [path for path in BRAND_FILES if path != dropped]
            self.assertEqual(len(files), 51)
            for mode, task in (("auto", None), ("explicit", BRAND_TASK)):
                with self.subTest(dropped=dropped, mode=mode):
                    proc, payload = self.verify_updates(
                        self.candidate(files),
                        prefix=f"skipi-guard-seafarer-brand-51-{mode}-",
                        task=task,
                    )
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertEqual(payload["status"], "fail")
                    # require_any_of still matches a subset, so the route opens
                    # and the exact set is what closes it.
                    self.assertEqual(payload["task"], BRAND_TASK)
                    self.assertEqual(payload["exact_file_set_missing"], [dropped])
                    self.assertEqual(payload["exact_file_set_unexpected"], [])
                    self.assertIn(f"exact file set required for task '{BRAND_TASK}'", payload["errors"])

    def test_50_files_without_both_require_any_files_fall_out_of_the_route(self) -> None:
        files = [path for path in BRAND_FILES if path not in BRAND_REQUIRE_ANY]
        self.assertEqual(len(files), 50)
        proc, payload = self.verify_updates(
            self.candidate(files),
            prefix="skipi-guard-seafarer-brand-noany-",
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIsNone(payload["task_rule"])
        self.assertTrue(
            any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_53_files_fail(self) -> None:
        for extra in BRAND_FORBIDDEN_EXTRAS:
            updates = self.candidate(BRAND_FILES)
            updates[extra] = "forbidden extra file\n"
            self.assertEqual(len(updates), 53)
            with self.subTest(extra=extra, mode="auto"):
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-brand-53-auto-",
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], BRAND_TASK)
                self.assertTrue(payload["errors"], payload)
            with self.subTest(extra=extra, mode="explicit"):
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-brand-53-explicit-",
                    task=BRAND_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], BRAND_TASK)
                self.assertEqual(payload["exact_file_set_missing"], [])
                self.assertEqual(payload["exact_file_set_unexpected"], [extra])
                self.assertIn(extra, payload["scope_violations"])
                self.assertIn(f"exact file set required for task '{BRAND_TASK}'", payload["errors"])

    # ---- guard-pin-bump ----

    def test_lone_workflow_routes_to_guard_pin_bump_and_passes(self) -> None:
        # No --auto-bootstrap-override here on purpose: this asserts that the
        # ROUTE carries the diff by itself, as a regular task with seven
        # harnesses. It is not the only way the diff can pass — the home's
        # live workflow hands the gate the named bootstrap override for
        # exactly this one-file diff, and pre_push_ref() sets
        # auto_bootstrap_override=True — which is why the route buys
        # auditability (no override in the record), not feasibility.
        proc, payload = self.verify_updates(
            self.candidate(PIN_FILES),
            prefix="skipi-guard-seafarer-pin-alone-",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["changed_files"], PIN_FILES)
        self.assertEqual(payload["task"], PIN_TASK)
        self.assertEqual(payload["task_rule"], PIN_RULE)
        self.assertEqual(payload["effective_tasks"], [PIN_TASK])
        self.assertEqual(payload["allowed_file_patterns"], PIN_FILES)
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(payload["auto_bootstrap_override"], False)
        self.assertEqual(payload["release_changes"], False)
        self.assertEqual(payload["protected_paths_touched"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            PIN_HARNESSES,
        )

    def test_workflow_plus_any_other_file_fails(self) -> None:
        for extra in (
            "src-tauri/src/lib.rs",
            "dist/index.html",
            "src-tauri/icons/icon.png",
            "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
            "src-tauri/gen/android/app/src/main/res/values/ic_launcher_background.xml",
        ):
            files = [WORKFLOW_FILE, extra]
            for mode, task in (("auto", None), ("explicit", PIN_TASK)):
                with self.subTest(extra=extra, mode=mode):
                    proc, payload = self.verify_updates(
                        self.candidate(files),
                        prefix=f"skipi-guard-seafarer-pin-plus-{mode}-",
                        task=task,
                    )
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertEqual(payload["status"], "fail")
                    self.assertNotEqual(payload["task_rule"], PIN_RULE)
                    self.assertTrue(payload["errors"], payload)

    def test_pin_bump_needs_no_exact_file_set(self) -> None:
        config = self.load_config()
        pattern_matches = GUARD_MODULE.pattern_matches
        sensitive = GUARD_MODULE.rule_patterns(config["release_sensitive_paths"])
        protected = GUARD_MODULE.rule_patterns(config["protected_paths"])
        self.assertTrue(sensitive and protected)
        # The workflow file is neither release-sensitive nor protected: the
        # `.github/workflows/*release*` / `*deploy*` patterns do not match it.
        for pattern in sensitive + protected:
            self.assertFalse(pattern_matches(WORKFLOW_FILE, pattern), f"{WORKFLOW_FILE} matches {pattern}")
        self.assertIn(".github/workflows/*release*", sensitive)
        self.assertIn(".github/workflows/*deploy*", sensitive)
        self.assertNotIn(PIN_TASK, config["release_tasks"])
        self.assertFalse(GUARD_MODULE.is_release_task(config, PIN_TASK))
        self.assertNotIn(PIN_TASK, config["exact_task_file_sets"])
        # Standing invariant (Н-1 / RISKS №224b): promoted to a release task,
        # this route MUST get an exact set.
        if PIN_TASK in config["release_tasks"]:
            self.assertIn(PIN_TASK, config["exact_task_file_sets"])
        # No glue and no inheritance: one literal path, seven harnesses.
        self.assertEqual(GUARD_MODULE.effective_allowed_patterns(config, PIN_TASK, []), PIN_FILES)
        harnesses = GUARD_MODULE.configured_harnesses(config, PIN_TASK)
        self.assertEqual([{"name": h["name"], "command": h["command"]} for h in harnesses], PIN_HARNESSES)

    def test_pin_bump_does_not_reopen_publication_infra(self) -> None:
        config = self.load_config()
        publication = [rule for rule in config["task_routing"] if rule["task"] == "publication-infra"]
        self.assertEqual(len(publication), 1)
        self.assertEqual(publication[0]["require_any_of"], ["scripts/publish-rf-mirror.sh"])
        # publication-infra still wins its own diff (it sits earlier in the list).
        files = [WORKFLOW_FILE, "scripts/publish-rf-mirror.sh"]
        proc, payload = self.verify_updates(
            self.candidate(files),
            prefix="skipi-guard-seafarer-pin-publication-",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["task"], "publication-infra")
        self.assertEqual(payload["task_rule"], "publication-infra routing")

    # ---- config shape / first-match order / neighbours ----

    def test_route_config_shape(self) -> None:
        config = self.load_config()

        self.assertEqual(config["release_tasks"].count(BRAND_TASK), 1)
        self.assertEqual(config["release_tasks"][-1], BRAND_TASK)
        self.assertEqual(config["exact_task_file_sets"][BRAND_TASK], BRAND_FILES)
        self.assertEqual(len(config["exact_task_file_sets"][BRAND_TASK]), 52)
        self.assertEqual(set(config["exact_task_file_sets"]), {"stack-metadata", "ios-apple-project-265b", BRAND_TASK, "cv-order-282", "career-pattern-302"})
        self.assertEqual(config["allowed_file_patterns"][BRAND_TASK], BRAND_FILES)
        self.assertEqual(config["allowed_file_patterns"][PIN_TASK], PIN_FILES)
        self.assertEqual(config["harness_commands"][BRAND_TASK], BRAND_HARNESSES)
        self.assertEqual(config["harness_commands"][PIN_TASK], PIN_HARNESSES)
        self.assertEqual(config["harness_commands"][BRAND_TASK], config["harness_commands"]["stack-metadata"])
        self.assertEqual(len(config["harness_commands"][BRAND_TASK]), 7)
        self.assertEqual(len(config["harness_commands"][PIN_TASK]), 7)

        brand = [rule for rule in config["task_routing"] if rule.get("task") == BRAND_TASK]
        pin = [rule for rule in config["task_routing"] if rule.get("task") == PIN_TASK]
        self.assertEqual(len(brand), 1)
        self.assertEqual(len(pin), 1)
        self.assertEqual(brand[0]["name"], BRAND_RULE)
        self.assertEqual(brand[0]["when_all_files_in"], BRAND_FILES)
        self.assertEqual(brand[0]["require_any_of"], BRAND_REQUIRE_ANY)
        self.assertNotIn("require_all_of", brand[0])
        self.assertEqual(pin[0]["name"], PIN_RULE)
        self.assertEqual(pin[0]["when_all_files_in"], PIN_FILES)
        self.assertEqual(pin[0]["require_all_of"], PIN_FILES)
        self.assertNotIn("require_any_of", pin[0])

        # Literal paths only, no duplicates, no globs anywhere in the delta.
        self.assertEqual(len(set(BRAND_FILES)), 52)
        self.assertEqual(BRAND_FILES, sorted(BRAND_FILES))
        for pattern in BRAND_FILES + PIN_FILES:
            for glob_char in ("*", "?", "["):
                self.assertNotIn(glob_char, pattern)
        for forbidden in BRAND_FORBIDDEN_EXTRAS:
            self.assertNotIn(forbidden, BRAND_FILES)
            self.assertNotIn(forbidden, config["allowed_file_patterns"][BRAND_TASK])

    def test_new_rules_are_appended_last(self) -> None:
        config = self.load_config()
        routing_tasks = [rule["task"] for rule in config["task_routing"]]
        self.assertEqual(len(routing_tasks), 20)
        self.assertEqual(routing_tasks[16:], [BRAND_TASK, PIN_TASK, "cv-order-282", "career-pattern-302"])
        self.assertEqual(routing_tasks.count(BRAND_TASK), 1)
        self.assertEqual(routing_tasks.count(PIN_TASK), 1)

    def test_route_does_not_shadow_neighbours(self) -> None:
        config = self.load_config()
        # The iOS project route (34 files, all under gen/apple) still wins.
        ios_files = config["exact_task_file_sets"]["ios-apple-project-265b"]
        proc, payload = self.verify_updates(
            self.candidate(ios_files),
            prefix="skipi-guard-seafarer-brand-neighbour-ios-",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["task"], "ios-apple-project-265b")
        # The stack-metadata exact set still wins.
        proc, payload = self.verify_updates(
            self.candidate(config["exact_task_file_sets"]["stack-metadata"]),
            prefix="skipi-guard-seafarer-brand-neighbour-stack-",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["task"], "stack-metadata")
        # And the default stays the default.
        proc, payload = self.verify_updates(
            self.candidate(["dist/index.html"]),
            prefix="skipi-guard-seafarer-brand-neighbour-default-",
        )
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIsNone(payload["task_rule"])
        self.assertEqual(payload["status"], "pass")

    def test_route_does_not_weaken_protected_paths_or_stop_lines(self) -> None:
        config = self.load_config()
        self.assertEqual(config["default_task"], "plugin-host")
        self.assertEqual(
            [rule["name"] for rule in config["protected_paths"]],
            ["backend/server/prod data", "secrets/signing keys", "pairing/QR/camera bridge", "presence contracts"],
        )
        self.assertEqual(
            [rule["name"] for rule in config["release_sensitive_paths"]],
            [
                "catalog/latest/release manifests",
                "versions/tags",
                "Tauri/Cargo/mobile generated files",
                "Play/TestFlight/upload/deploy",
            ],
        )
        self.assertIn("src-tauri/gen/**", GUARD_MODULE.rule_patterns(config["release_sensitive_paths"]))


if __name__ == "__main__":
    unittest.main()
