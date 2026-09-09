"""Seafarer route `ios-apple-project-265b` — one-shot exact route for the iOS project.

Task card: skipi-ops/handoffs/seafarer-0-4-191/TASKCARD-A0-guard-routes.md
(wave Seafarer 0.4.191, OWNER (430)/(431); route-PR merge = owner click only).

The iOS project `src-tauri/gen/apple/**` of the Seafarer home exists only on the
Mac (RISKS №265b). Every one of its 34 files matches the release-sensitive
pattern `src-tauri/gen/**`, so it can only land through a release task — and a
release task WITHOUT an exact_task_file_sets entry glues every
release_sensitive_path onto its allowed patterns (finding Н-1, RISKS №224b).
Hence the shape of this route, asserted below:

  * release task (release_tasks)               -> release-sensitive stop-line opens
  * exact_task_file_sets = exactly the 34 files -> effective_allowed_patterns adds
                                                  NOTHING from release_sensitive_paths
  * task_routing when_all_files_in = require_all_of = the 34 files, appended
    LAST (first-match: the 14 historical rules keep their order and priority)
  * harness_commands = the seven stack-metadata harnesses (exact-set release
    tasks inherit nothing, see configured_harnesses())

The route is deliberately one-shot: 33 files, 34 + anything, or a lone
Info.plist all FAIL (missing / unexpected) — see task card, known residue
RISKS №267b.

Baseline for the PRESERVE oracle: skipi-guard main
746bc882fbd9cf75517f64b8de944525ea05d89f. BASELINE_TEXT below is the byte-exact
content of `git show 746bc882:configs/homes/seafarer.json` (sha256 pinned);
when that commit is reachable locally the literal is cross-checked against the
live `git show` output as well (CI checkouts are shallow, so the literal is the
oracle there).
"""

from __future__ import annotations

import hashlib
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

GUARD_LOADER = SourceFileLoader("skipi_guard_cli_265b", str(GUARD))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
if GUARD_SPEC is None:
    raise RuntimeError(f"cannot load guard module from {GUARD}")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_LOADER.exec_module(GUARD_MODULE)

ROUTE_TASK = "ios-apple-project-265b"
ROUTE_RULE = "seafarer iOS Apple project save routing (265b)"
SIBLING_TASK = "ai-recognize-257"  # the other route of the same task card (R1)
BASELINE_SHA = "746bc882fbd9cf75517f64b8de944525ea05d89f"
BASELINE_SHA256 = "847fb6b8a07f34a27c0bd986a9ff76d22478c01a8ab9950316f16c2e1f82cb42"

# Exact set R2 — FACT `git status --porcelain --untracked-files=all` on the Mac
# (task card §"Exact set R2", HEAD Mac 5be395df), in card order.
ROUTE_FILES = [
    "src-tauri/gen/apple/.gitignore",
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
    "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/Contents.json",
    "src-tauri/gen/apple/Assets.xcassets/Contents.json",
    "src-tauri/gen/apple/ExportOptions-appstore.plist",
    "src-tauri/gen/apple/ExportOptions.plist",
    "src-tauri/gen/apple/LaunchScreen.storyboard",
    "src-tauri/gen/apple/Podfile",
    "src-tauri/gen/apple/Sources/skipi/bindings/bindings.h",
    "src-tauri/gen/apple/Sources/skipi/main.mm",
    "src-tauri/gen/apple/project.yml",
    "src-tauri/gen/apple/skipi.xcodeproj/project.pbxproj",
    "src-tauri/gen/apple/skipi.xcodeproj/project.xcworkspace/contents.xcworkspacedata",
    "src-tauri/gen/apple/skipi.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings",
    "src-tauri/gen/apple/skipi.xcodeproj/xcshareddata/xcschemes/skipi_iOS.xcscheme",
    "src-tauri/gen/apple/skipi_iOS/Info.plist",
    "src-tauri/gen/apple/skipi_iOS/skipi_iOS.entitlements",
]
# Exact-set release task: configured_harnesses() inherits nothing, this list
# is the whole set the route runs — the same seven as stack-metadata.
ROUTE_HARNESSES = [
    {"name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {"name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs"},
    {"name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs"},
    {"name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs"},
    {"name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs"},
    {"name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs"},
]
# Extras that must never ride this route: ignored build output and vendored
# static libs of the iOS project, a lock file that is not in the FACT set,
# secrets-looking names, the front-end, the version trio, the presence
# manifest, the guard workflow and an unrelated file.
ROUTE_FORBIDDEN_EXTRAS = [
    "src-tauri/gen/apple/build/x",
    "src-tauri/gen/apple/build/skipi.xcarchive/Info.plist",
    "src-tauri/gen/apple/Externals/arm64/release/libapp.a",
    "src-tauri/gen/apple/Podfile.lock",
    "src-tauri/gen/apple/AuthKey_token.p8",
    "src-tauri/gen/apple/skipi_iOS/secret.plist",
    "src-tauri/gen/apple/signing.p12",
    "src-tauri/gen/android/app/src/main/AndroidManifest.xml",
    "dist/index.html",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.toml",
    "src-tauri/Cargo.lock",
    "src-tauri/src/commands/ai.rs",
    "presence-manifest.json",
    ".github/workflows/skipi-guard.yml",
    "src/unrelated.txt",
]
WORKFLOW_FILE = ".github/workflows/skipi-guard.yml"

# `git show 746bc882:configs/homes/seafarer.json`, byte-exact (sha256 pinned
# in BASELINE_SHA256 and re-checked in test_baseline_literal_is_the_real_blob).
BASELINE_TEXT = r'''{
  "home": "seafarer",
  "repo": "/home/linux/Developer/skipi-public",
  "stop_lines": [
    "no backend/server/prod data",
    "no catalog/latest/release/signing keys",
    "no app version/tag bump",
    "no Tauri/Cargo/mobile generated changes",
    "no pairing/QR/camera bridge changes",
    "no Play/TestFlight/upload/deploy"
  ],
  "release_tasks": ["release", "release-infra", "build-release", "stack-metadata", "mobile-external-url", "login-gate-first-162b", "entry-fork-187", "mobile-ime-inset", "version-bump", "native-share"],
  "default_task": "plugin-host",
  "exact_task_file_sets": {
    "stack-metadata": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/vault.rs", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs", "tests/stack_verification_negative_control_harness.mjs"]
  },
  "task_routing": [
    {
      "name": "mobile external-url fix routing",
      "task": "mobile-external-url",
      "when_all_files_in": ["src-tauri/src/commands/vault.rs", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"],
      "require_all_of": ["src-tauri/src/commands/vault.rs", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"]
    },
    {
      "name": "assistant non-blocking fix routing (140)",
      "task": "assistant-nonblocking",
      "when_all_files_in": ["src-tauri/src/commands/assistant.rs", "tests/no_dead_tauri_invoke_harness.mjs"],
      "require_all_of": ["src-tauri/src/commands/assistant.rs", "tests/no_dead_tauri_invoke_harness.mjs"]
    },
    {
      "name": "login gate first screen + 0.4.186 bump routing (162b)",
      "task": "login-gate-first-162b",
      "when_all_files_in": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/app_login.rs", "src-tauri/src/lib.rs", "src-tauri/tauri.conf.json", "tests/login_gate_first_screen_harness.mjs", "tests/no_dead_tauri_invoke_harness.mjs", "tests/stack_build_metadata_harness.mjs"],
      "require_all_of": ["src-tauri/src/commands/app_login.rs", "dist/index.html", "tests/login_gate_first_screen_harness.mjs"]
    },
    {
      "name": "seafarer mobile entry fork + 0.4.187 bump routing (187)",
      "task": "entry-fork-187",
      "when_all_files_in": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", "tests/bundled_plugin_isolation_harness.mjs", "tests/login_gate_first_screen_harness.mjs", "tests/stack_build_metadata_harness.mjs"],
      "require_all_of": ["dist/index.html", "tests/login_gate_first_screen_harness.mjs"]
    },
    {
      "name": "seafarer mobile IME inset fix routing (308)",
      "task": "mobile-ime-inset",
      "when_all_files_in": ["dist/index.html", "src-tauri/gen/android/app/src/main/AndroidManifest.xml", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt", "tests/bundled_plugin_isolation_harness.mjs"],
      "require_any_of": ["src-tauri/gen/android/app/src/main/AndroidManifest.xml", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"]
    },
    {
      "name": "seafarer native share routing (332)",
      "task": "native-share",
      "when_all_files_in": ["dist/index.html", "presence-manifest.json", "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml", "src-tauri/src/commands/mail_intent.rs", "src-tauri/src/commands/packages.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"],
      "require_any_of": ["src-tauri/gen/android/app/src/main/res/xml/file_paths.xml", "src-tauri/src/commands/packages.rs", "src-tauri/src/commands/mail_intent.rs"]
    },
    {
      "name": "seafarer 0.4.189 mobile native routing",
      "task": "mobile-189-native",
      "when_all_files_in": ["dist/index.html", "dist/intelligence.js", "src-tauri/src/commands/account_delete.rs", "src-tauri/src/commands/vault.rs", "src-tauri/src/feedback.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"],
      "require_any_of": ["src-tauri/src/commands/vault.rs", "src-tauri/src/feedback.rs", "src-tauri/src/commands/account_delete.rs"]
    },
    {
      "name": "seafarer canonical version bump routing (204)",
      "task": "version-bump",
      "when_all_files_in": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs"],
      "require_all_of": ["src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs"]
    },
    {
      "name": "repo-meta routing",
      "task": "repo-meta",
      "when_all_files_in": ["AGENTS.md", "CLAUDE.md"]
    },
    {
      "name": "seafarer Stage 4 stack-metadata routing",
      "task": "stack-metadata",
      "when_all_files_in": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/vault.rs", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs", "tests/stack_verification_negative_control_harness.mjs"],
      "require_all_of": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/vault.rs", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs", "tests/stack_verification_negative_control_harness.mjs"]
    },
    {
      "name": "canonical version-bump routing",
      "task": "release",
      "when_all_files_in": ["dist/index.html", "src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"],
      "require_any_of": ["src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"]
    },
    {
      "name": "settings-adopt routing",
      "task": "settings-adopt",
      "when_all_files_in": ["dist/index.html", "dist/skipi-settings*", "dist/SETTINGS_VERSION", "tests/unified_settings_fallback_harness.mjs"],
      "require_any_of": ["dist/skipi-settings*", "tests/unified_settings_fallback_harness.mjs"]
    },
    {
      "name": "publication-infra routing",
      "task": "publication-infra",
      "when_all_files_in": [".github/workflows/skipi-guard.yml", "scripts/publish-rf-mirror.sh", "scripts/prepare-rf-mirror.sh", "scripts/RF_MIRROR_PUBLISH.md", "tests/rf_mirror_publish_contract_harness.mjs"],
      "require_any_of": ["scripts/publish-rf-mirror.sh"]
    },
    {
      "name": "assistant-module routing",
      "task": "assistant-module",
      "when_all_files_in": ["dist/index.html", "dist/skipi-assistant*", "dist/ASSISTANT_VERSION", "src-tauri/src/commands/app_login.rs", "src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs"],
      "require_any_of": ["dist/skipi-assistant*", "src-tauri/src/commands/app_login.rs"]
    }
  ],
  "protected_paths": [
    {
      "name": "backend/server/prod data",
      "patterns": ["backend/**", "server/**", "api/**", "data/prod/**", "prod/**", "production/**", "media/**", "uploads/**"]
    },
    {
      "name": "secrets/signing keys",
      "patterns": [".env", ".env.*", "**/.env", "**/.env.*", "keys/**", "signing/**", "**/*.pem", "**/*.p12", "**/*.keystore", "**/*secret*", "**/*token*"]
    },
    {
      "name": "pairing/QR/camera bridge",
      "patterns": ["**/*pair*", "**/*Pair*", "**/*qr*", "**/*QR*", "**/*camera*", "**/*Camera*", "**/*barcode*", "**/*Barcode*"]
    },
    {
      "name": "presence contracts",
      "patterns": ["presence-manifest.json"]
    }
  ],
  "release_sensitive_paths": [
    {
      "name": "catalog/latest/release manifests",
      "patterns": ["latest.json", "**/latest.json", "catalog/**", "**/catalog/**", "release/**", "releases/**", "downloads/**", "manifest*.json", "**/manifest*.json"]
    },
    {
      "name": "versions/tags",
      "patterns": ["VERSION", "version.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "src-tauri/tauri.conf.json", "Cargo.toml", "Cargo.lock"]
    },
    {
      "name": "Tauri/Cargo/mobile generated files",
      "patterns": ["src-tauri/gen/**", "src-tauri/target/**", "src-tauri/Cargo.lock", "android/**", "ios/**", "build/**", "*.apk", "*.aab", "*.ipa", "dist/**/*.apk"]
    },
    {
      "name": "Play/TestFlight/upload/deploy",
      "patterns": ["fastlane/**", "play/**", "testflight/**", "scripts/deploy*", "scripts/upload*", "scripts/*testflight*", "scripts/*play*", ".github/workflows/*release*", ".github/workflows/*deploy*"]
    }
  ],
  "harness_commands": {
    "mobile-external-url": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" }
    ],
    "assistant-nonblocking": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" }
    ],
    "login-gate-first-162b": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" },
      { "name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs" }
    ],
    "entry-fork-187": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" },
      { "name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs" },
      { "name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs" }
    ],
    "mobile-ime-inset": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" },
      { "name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs" },
      { "name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs" }
    ],
    "version-bump": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" }
    ],
    "native-share": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" },
      { "name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs" },
      { "name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs" }
    ],
    "mobile-189-native": [
      { "name": "seafarer_bundled_plugin_isolation", "command": "node tests/bundled_plugin_isolation_harness.mjs" },
      { "name": "seafarer_build_provenance", "command": "node tests/build_provenance_harness.mjs" },
      { "name": "seafarer_presence_contract", "command": "node tests/seafarer_presence_contract_harness.mjs" },
      { "name": "seafarer_theme_default", "command": "node tests/seafarer_theme_default_harness.mjs" },
      { "name": "seafarer_remote_prod_delivery_config", "command": "node tests/remote_prod_delivery_config_harness.mjs" },
      { "name": "seafarer_no_dead_tauri_invoke", "command": "node tests/no_dead_tauri_invoke_harness.mjs" },
      { "name": "seafarer_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs" },
      { "name": "seafarer_stack_verification_negative_control", "command": "node tests/stack_verification_negative_control_harness.mjs" },
      { "name": "seafarer_login_gate_first_screen", "command": "node tests/login_gate_first_screen_harness.mjs" },
      { "name": "seafarer_demo_vault_contract", "command": "node tests/demo_vault_contract_harness.mjs" }
    ],
    "plugin-host": [
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      }
    ],
    "assistant-module": [
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      }
    ],
    "demo-vault": [
      {
        "name": "seafarer_demo_vault_contract",
        "command": "node tests/demo_vault_contract_harness.mjs"
      }
    ],
    "contract-sync": [
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      },
      {
        "name": "seafarer_demo_vault_contract",
        "command": "node tests/demo_vault_contract_harness.mjs"
      },
      {
        "name": "seafarer_plugin_remote_over_bundled",
        "command": "node tests/plugin_remote_over_bundled_harness.mjs"
      }
    ],
    "release": [
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      }
    ],
    "provenance": [
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      }
    ],
    "publication-infra": [
      {
        "name": "seafarer_rf_mirror_publish_contract",
        "command": "node tests/rf_mirror_publish_contract_harness.mjs"
      }
    ],
    "settings-adopt": [
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      },
      {
        "name": "seafarer_unified_settings_fallback",
        "command": "node tests/unified_settings_fallback_harness.mjs"
      }
    ],
    "stack-metadata": [
      {
        "name": "seafarer_stack_build_metadata",
        "command": "node tests/stack_build_metadata_harness.mjs"
      },
      {
        "name": "seafarer_stack_verification_negative_control",
        "command": "node tests/stack_verification_negative_control_harness.mjs"
      },
      {
        "name": "seafarer_bundled_plugin_isolation",
        "command": "node tests/bundled_plugin_isolation_harness.mjs"
      },
      {
        "name": "seafarer_build_provenance",
        "command": "node tests/build_provenance_harness.mjs"
      },
      {
        "name": "seafarer_presence_contract",
        "command": "node tests/seafarer_presence_contract_harness.mjs"
      },
      {
        "name": "seafarer_theme_default",
        "command": "node tests/seafarer_theme_default_harness.mjs"
      },
      {
        "name": "seafarer_remote_prod_delivery_config",
        "command": "node tests/remote_prod_delivery_config_harness.mjs"
      }
    ]
  },
  "allowed_file_patterns": {
    "mobile-external-url": ["src-tauri/src/commands/vault.rs", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt"],
    "assistant-nonblocking": ["src-tauri/src/commands/assistant.rs", "tests/no_dead_tauri_invoke_harness.mjs"],
    "login-gate-first-162b": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/app_login.rs", "src-tauri/src/lib.rs", "src-tauri/tauri.conf.json", "tests/login_gate_first_screen_harness.mjs", "tests/no_dead_tauri_invoke_harness.mjs", "tests/stack_build_metadata_harness.mjs"],
    "entry-fork-187": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", "tests/bundled_plugin_isolation_harness.mjs", "tests/login_gate_first_screen_harness.mjs", "tests/stack_build_metadata_harness.mjs"],
    "mobile-ime-inset": ["dist/index.html", "src-tauri/gen/android/app/src/main/AndroidManifest.xml", "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt", "tests/bundled_plugin_isolation_harness.mjs"],
    "version-bump": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs"],
    "native-share": ["dist/index.html", "presence-manifest.json", "src-tauri/gen/android/app/src/main/res/xml/file_paths.xml", "src-tauri/src/commands/mail_intent.rs", "src-tauri/src/commands/packages.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"],
    "mobile-189-native": ["dist/index.html", "dist/intelligence.js", "src-tauri/src/commands/account_delete.rs", "src-tauri/src/commands/vault.rs", "src-tauri/src/feedback.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs"],
    "repo-meta": ["AGENTS.md", "CLAUDE.md"],
    "plugin-host": ["dist/index.html", "dist/plugin-host-ui.js", "dist/plugin-host-bridge.js", "dist/plugin-host-config.js", "dist/plugin-loader.js", "dist/plugin-remote-boot.js", "src-tauri/src/commands/account_sync.rs", "src-tauri/src/commands/mod.rs", "src-tauri/src/commands/profile.rs", "src-tauri/src/lib.rs", "tests/bundled_plugin_isolation_harness.mjs", "presence-manifest.json", "tests/seafarer_presence_contract_harness.mjs", "tests/seafarer_theme_default_harness.mjs", "tests/remote_prod_delivery_config_harness.mjs", "tests/plugin_remote_over_bundled_harness.mjs", "tests/account_profile_sync_harness.mjs"],
    "demo-vault": ["dist/index.html", "src-tauri/resources/demo-vault.zip", "src-tauri/src/db.rs", "tests/demo_vault_contract_harness.mjs"],
    "contract-sync": ["dist/index.html", "dist/plugin-host-ui.js", "src-tauri/resources/demo-vault.zip", "src-tauri/src/db.rs", "tests/demo_vault_contract_harness.mjs", "tests/plugin_remote_over_bundled_harness.mjs"],
    "publication-infra": [".github/workflows/skipi-guard.yml", "scripts/publish-rf-mirror.sh", "scripts/prepare-rf-mirror.sh", "scripts/RF_MIRROR_PUBLISH.md", "tests/rf_mirror_publish_contract_harness.mjs"],
    "settings-adopt": ["dist/index.html", "dist/skipi-settings*", "dist/SETTINGS_VERSION", "tests/unified_settings_fallback_harness.mjs"],
    "stack-metadata": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/src/commands/vault.rs", "src-tauri/tauri.conf.json", "tests/stack_build_metadata_harness.mjs", "tests/stack_verification_negative_control_harness.mjs"],
    "assistant-module": ["dist/index.html", "dist/skipi-assistant*", "dist/ASSISTANT_VERSION", "src-tauri/src/commands/app_login.rs", "src-tauri/src/commands/mod.rs", "src-tauri/src/lib.rs"],
    "release": ["dist/index.html"]
  }
}
'''


def baseline_config() -> dict[str, Any]:
    return json.loads(BASELINE_TEXT)


class SeafarerIosAppleRouteTests(unittest.TestCase):
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

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
        self.commit_files(repo, "seed fixture", {"fixture.txt": "seed\n"})

    def run_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        task: str | None = None,
        auto_bootstrap_override: bool = False,
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
        if task:
            command.extend(["--task", task])
        else:
            command.append("--auto-task")
        if auto_bootstrap_override:
            command.append("--auto-bootstrap-override")
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            env=self.child_env(),
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def verify_updates(
        self,
        updates: dict[str, str],
        *,
        prefix: str,
        task: str | None = None,
        auto_bootstrap_override: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(
                repo,
                root / "result.json",
                task=task,
                auto_bootstrap_override=auto_bootstrap_override,
            )

    def candidate(self, files: list[str]) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in files}

    def load_config(self) -> dict[str, Any]:
        with CONFIG.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_routed_pass(
        self,
        payload: dict[str, Any],
        proc: subprocess.CompletedProcess[str],
        files: list[str],
        *,
        task_source: str,
    ) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["changed_files"], sorted(files))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], task_source)
        self.assertEqual(payload["task_rule"], ROUTE_RULE if task_source == "auto" else None)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(payload["override_present"], False)
        self.assertEqual(payload["auto_bootstrap_override"], False)
        # Every file is under src-tauri/gen/** (release-sensitive), nothing is
        # protected: the release-task stop-line is what opens, nothing else.
        self.assertEqual(payload["release_changes"], True)
        self.assertEqual(sorted(t["path"] for t in payload["release_paths_touched"]), sorted(files))
        self.assertTrue(all(t["pattern"] == "src-tauri/gen/**" for t in payload["release_paths_touched"]))
        self.assertEqual([t for t in payload["protected_paths_touched"] if t["kind"] == "protected"], [])
        # (б) exact set => NOTHING from release_sensitive_paths is glued on.
        self.assertEqual(payload["allowed_file_patterns"], ROUTE_FILES)
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            ROUTE_HARNESSES,
        )

    # (а) push of exactly the 34 files -> task R2, PASS without override.
    def test_exact_34_files_route_to_ios_apple_project_and_pass(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-265b-full-",
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES, task_source="auto")

    def test_explicit_task_with_exact_34_files_passes(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate(ROUTE_FILES),
            prefix="skipi-guard-seafarer-265b-explicit-full-",
            task=ROUTE_TASK,
        )
        self.assert_routed_pass(payload, proc, ROUTE_FILES, task_source="explicit")

    # (б) the exact set blocks the release_sensitive_paths glue (Н-1 / №224b),
    # checked directly on the guard functions as well as via the payload above.
    def test_exact_set_blocks_release_sensitive_glue(self) -> None:
        config = self.load_config()
        self.assertTrue(GUARD_MODULE.is_release_task(config, ROUTE_TASK))
        self.assertEqual(GUARD_MODULE.effective_allowed_patterns(config, ROUTE_TASK, []), ROUTE_FILES)
        sensitive = GUARD_MODULE.rule_patterns(config["release_sensitive_paths"])
        for pattern in sensitive:
            self.assertNotIn(pattern, GUARD_MODULE.effective_allowed_patterns(config, ROUTE_TASK, []))
        # Contrast: the same function on a release task WITHOUT an exact set
        # does glue them on — that is the hole this route avoids, not fixes.
        glued = GUARD_MODULE.effective_allowed_patterns(config, "release", [])
        self.assertTrue(set(sensitive) <= set(glued))
        harnesses = GUARD_MODULE.configured_harnesses(config, ROUTE_TASK)
        self.assertEqual(
            [{"name": h["name"], "command": h["command"]} for h in harnesses],
            ROUTE_HARNESSES,
        )

    # (в) 33 files -> FAIL, both auto and explicit.
    def test_33_files_fail(self) -> None:
        for dropped in (
            "src-tauri/gen/apple/skipi_iOS/Info.plist",
            "src-tauri/gen/apple/.gitignore",
            "src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png",
            "src-tauri/gen/apple/skipi.xcodeproj/project.pbxproj",
            "src-tauri/gen/apple/skipi_iOS/skipi_iOS.entitlements",
        ):
            files = [path for path in ROUTE_FILES if path != dropped]
            self.assertEqual(len(files), 33)
            with self.subTest(dropped=dropped, mode="auto"):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-265b-33-auto-",
                )
                # require_all_of keeps the route closed -> default plugin-host
                # -> release-sensitive touch blocked + scope violations.
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task"], "plugin-host")
                self.assertIsNone(payload["task_rule"])
                self.assertTrue(
                    any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
                    payload["errors"],
                )
                self.assertEqual(payload["scope_violations"], sorted(files))
            with self.subTest(dropped=dropped, mode="explicit"):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-265b-33-explicit-",
                    task=ROUTE_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["task_source"], "explicit")
                self.assertEqual(payload["exact_file_set_missing"], [dropped])
                self.assertEqual(payload["exact_file_set_unexpected"], [])
                self.assertIn(f"exact file set required for task '{ROUTE_TASK}'", payload["errors"])

    # (в) 34 + any extra -> FAIL, both auto and explicit.
    def test_34_plus_extra_file_fails(self) -> None:
        for extra in ROUTE_FORBIDDEN_EXTRAS:
            updates = self.candidate(ROUTE_FILES)
            updates[extra] = "forbidden extra file\n"
            with self.subTest(extra=extra, mode="auto"):
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-265b-extra-auto-",
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertNotEqual(payload["task"], ROUTE_TASK)
                self.assertTrue(payload["errors"], payload)
            with self.subTest(extra=extra, mode="explicit"):
                proc, payload = self.verify_updates(
                    updates,
                    prefix="skipi-guard-seafarer-265b-extra-explicit-",
                    task=ROUTE_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], ROUTE_TASK)
                self.assertEqual(payload["exact_file_set_missing"], [])
                self.assertEqual(payload["exact_file_set_unexpected"], [extra])
                self.assertIn(extra, payload["scope_violations"])
                self.assertIn(f"exact file set required for task '{ROUTE_TASK}'", payload["errors"])
                self.assertTrue(
                    any("changes outside allowed patterns" in error for error in payload["errors"]),
                    payload["errors"],
                )

    # (в) gen/apple/build/x alone and a lone Info.plist -> FAIL.
    def test_build_output_alone_fails(self) -> None:
        for files in (
            ["src-tauri/gen/apple/build/x"],
            ["src-tauri/gen/apple/build/x", "src-tauri/gen/apple/skipi_iOS/Info.plist"],
        ):
            with self.subTest(files=files, mode="auto"):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-265b-build-auto-",
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["task"], "plugin-host")
                self.assertTrue(
                    any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
                    payload["errors"],
                )
            with self.subTest(files=files, mode="explicit"):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix="skipi-guard-seafarer-265b-build-explicit-",
                    task=ROUTE_TASK,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["exact_file_set_unexpected"], ["src-tauri/gen/apple/build/x"])
                self.assertIn("src-tauri/gen/apple/build/x", payload["scope_violations"])

    def test_lone_info_plist_fails(self) -> None:
        lone = ["src-tauri/gen/apple/skipi_iOS/Info.plist"]
        proc, payload = self.verify_updates(
            self.candidate(lone),
            prefix="skipi-guard-seafarer-265b-lone-auto-",
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], "plugin-host")

        proc, payload = self.verify_updates(
            self.candidate(lone),
            prefix="skipi-guard-seafarer-265b-lone-explicit-",
            task=ROUTE_TASK,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(len(payload["exact_file_set_missing"]), 33)
        self.assertEqual(
            payload["exact_file_set_missing"],
            [path for path in ROUTE_FILES if path not in lone],
        )
        self.assertEqual(payload["exact_file_set_unexpected"], [])

    # Config shape: release ∧ exact ∧ harness, literal, in both routing lists.
    def test_route_config_shape(self) -> None:
        config = self.load_config()

        self.assertIn(ROUTE_TASK, config["release_tasks"])
        self.assertEqual(config["release_tasks"].count(ROUTE_TASK), 1)
        self.assertIn(ROUTE_TASK, config["exact_task_file_sets"])
        self.assertEqual(config["exact_task_file_sets"][ROUTE_TASK], ROUTE_FILES)
        self.assertEqual(len(config["exact_task_file_sets"][ROUTE_TASK]), 34)
        self.assertEqual(set(config["exact_task_file_sets"]), {"stack-metadata", ROUTE_TASK})
        self.assertTrue(config["harness_commands"][ROUTE_TASK])
        self.assertEqual(config["harness_commands"][ROUTE_TASK], ROUTE_HARNESSES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], config["harness_commands"]["stack-metadata"])
        self.assertEqual(len(config["harness_commands"][ROUTE_TASK]), 7)
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], ROUTE_FILES)

        routes = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], ROUTE_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], ROUTE_FILES)
        self.assertEqual(routes[0]["require_all_of"], ROUTE_FILES)
        self.assertNotIn("require_any_of", routes[0])

        # Literal paths only, no duplicates, nothing ignored/vendored/secret.
        self.assertEqual(len(set(ROUTE_FILES)), 34)
        for pattern in ROUTE_FILES:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
            self.assertTrue(pattern.startswith("src-tauri/gen/apple/"), pattern)
            self.assertNotIn("/build/", pattern)
            self.assertNotIn("/Externals/", pattern)
            self.assertFalse(pattern.endswith(".a"), pattern)
            self.assertFalse(pattern.endswith(".lock"), pattern)
        # Deliberately outside: the Android side, the version trio, the front
        # end, the Rust commands (the R1 sibling has its own single file).
        for forbidden in ROUTE_FORBIDDEN_EXTRAS:
            self.assertNotIn(forbidden, ROUTE_FILES)

    def test_no_route_file_matches_a_protected_pattern(self) -> None:
        config = self.load_config()
        pattern_matches = GUARD_MODULE.pattern_matches
        protected = GUARD_MODULE.rule_patterns(config["protected_paths"])
        # The patterns the card names explicitly must still be in the config
        # (this test would be vacuous otherwise).
        for must in ("**/*secret*", "**/*token*", "**/*.p12", "**/*.pem", "**/*pair*", "**/*camera*", "**/*qr*"):
            self.assertIn(must, protected)
        for path in ROUTE_FILES:
            for pattern in protected:
                self.assertFalse(pattern_matches(path, pattern), f"{path} matches protected {pattern}")
        # ...and every one of them IS release-sensitive, via src-tauri/gen/**:
        # the mechanical reason the task must be a release task at all.
        for path in ROUTE_FILES:
            self.assertTrue(pattern_matches(path, "src-tauri/gen/**"), path)
        # Sanity of the oracle: the secrets patterns do bite on the names we
        # keep out.
        self.assertTrue(pattern_matches("src-tauri/gen/apple/AuthKey_token.p8", "**/*token*"))
        self.assertTrue(pattern_matches("src-tauri/gen/apple/signing.p12", "**/*.p12"))

    # first-match: the two new rules are appended LAST, the 14 old ones are
    # unchanged and keep their order.
    def test_new_routing_rules_are_appended_last(self) -> None:
        config = self.load_config()
        baseline = baseline_config()

        routing = config["task_routing"]
        self.assertEqual(len(baseline["task_routing"]), 14)
        self.assertEqual(len(routing), 16)
        self.assertEqual(routing[:14], baseline["task_routing"])
        self.assertEqual([rule["task"] for rule in routing[14:]], [SIBLING_TASK, ROUTE_TASK])

    # PRESERVE: everything that existed at 746bc882 is byte-identical.
    def test_pre_route_config_is_preserved_byte_for_byte(self) -> None:
        config = self.load_config()
        baseline = baseline_config()
        new_tasks = {SIBLING_TASK, ROUTE_TASK}

        self.assertEqual(config["home"], baseline["home"])
        self.assertEqual(config["repo"], baseline["repo"])
        self.assertEqual(config["stop_lines"], baseline["stop_lines"])
        self.assertEqual(config["default_task"], baseline["default_task"])
        self.assertEqual(config["default_task"], "plugin-host")
        self.assertEqual(config["protected_paths"], baseline["protected_paths"])
        self.assertEqual(config["release_sensitive_paths"], baseline["release_sensitive_paths"])
        self.assertEqual(config["release_tasks"], baseline["release_tasks"] + [ROUTE_TASK])
        self.assertEqual(
            config["exact_task_file_sets"],
            {**baseline["exact_task_file_sets"], ROUTE_TASK: ROUTE_FILES},
        )
        self.assertEqual(
            config["exact_task_file_sets"]["stack-metadata"],
            baseline["exact_task_file_sets"]["stack-metadata"],
        )
        for section in ("harness_commands", "allowed_file_patterns"):
            with self.subTest(section=section):
                self.assertEqual(set(config[section]), set(baseline[section]) | new_tasks)
                for task, entries in baseline[section].items():
                    self.assertEqual(config[section][task], entries, f"{section}[{task}] changed")
        self.assertEqual(set(config), set(baseline))
        # The literal baseline in this file is exactly the 746bc882 blob.
        self.assertEqual(hashlib.sha256(BASELINE_TEXT.encode("utf-8")).hexdigest(), BASELINE_SHA256)

    def test_baseline_literal_is_the_real_blob(self) -> None:
        # Live cross-check against git when the baseline commit is reachable
        # (developer checkouts). CI checkouts are shallow: there the sha256 pin
        # above is the oracle, and this test says so instead of passing silently.
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE_SHA}^{{commit}}"],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            self.skipTest(f"baseline commit {BASELINE_SHA[:8]} not reachable here (shallow clone); sha256 pin is the oracle")
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{BASELINE_SHA}:configs/homes/seafarer.json"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(shown.stdout, BASELINE_TEXT)

    # pin-bump gotcha (№140): the workflow file alone gets the bootstrap
    # override; the workflow plus anything else does not.
    def test_workflow_bootstrap_override_only_for_the_lone_workflow_file(self) -> None:
        proc, payload = self.verify_updates(
            self.candidate([WORKFLOW_FILE]),
            prefix="skipi-guard-seafarer-265b-pin-alone-",
            auto_bootstrap_override=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["auto_bootstrap_override"], True)
        self.assertEqual(payload["override_present"], True)

        for extra in ("src-tauri/gen/apple/skipi_iOS/Info.plist", "src-tauri/src/commands/ai.rs", "dist/index.html"):
            with self.subTest(extra=extra):
                proc, payload = self.verify_updates(
                    self.candidate([WORKFLOW_FILE, extra]),
                    prefix="skipi-guard-seafarer-265b-pin-plus-",
                    auto_bootstrap_override=True,
                )
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertEqual(payload["auto_bootstrap_override"], False)
                self.assertEqual(payload["override_present"], False)
                self.assertNotEqual(payload["task"], ROUTE_TASK)

    # Neighbour routes are not shadowed (the new rules sit last anyway).
    def test_route_does_not_shadow_neighbour_routes(self) -> None:
        baseline = baseline_config()
        existing_routes = {
            "mobile-external-url": [
                "src-tauri/src/commands/vault.rs",
                "src-tauri/gen/android/app/src/main/java/app/skipi/seafarer/MainActivity.kt",
            ],
            "assistant-nonblocking": ["src-tauri/src/commands/assistant.rs", "tests/no_dead_tauri_invoke_harness.mjs"],
            "entry-fork-187": baseline["allowed_file_patterns"]["entry-fork-187"],
            "mobile-ime-inset": baseline["allowed_file_patterns"]["mobile-ime-inset"],
            "native-share": [
                path for path in baseline["allowed_file_patterns"]["native-share"] if path != "presence-manifest.json"
            ],
            "mobile-189-native": baseline["allowed_file_patterns"]["mobile-189-native"],
            "version-bump": baseline["allowed_file_patterns"]["version-bump"],
            "stack-metadata": baseline["exact_task_file_sets"]["stack-metadata"],
            "release": ["dist/index.html", "src-tauri/Cargo.lock", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json"],
            "repo-meta": ["AGENTS.md", "CLAUDE.md"],
        }
        rule_names = {rule["task"]: rule["name"] for rule in baseline["task_routing"]}
        for expected_task, files in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    self.candidate(files),
                    prefix=f"skipi-guard-seafarer-265b-neighbour-{expected_task}-",
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], rule_names[expected_task])
                self.assertEqual(payload["scope_violations"], [])
        # The default stays the default.
        proc, payload = self.verify_updates(
            self.candidate(["dist/index.html"]),
            prefix="skipi-guard-seafarer-265b-neighbour-default-",
        )
        self.assertEqual(payload["task"], "plugin-host")
        self.assertIsNone(payload["task_rule"])
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
