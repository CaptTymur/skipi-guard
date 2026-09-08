"""Owner-authorized exact route `security-escaping-191` (skipi-broker + skipi-crewing).

Owner GO 2026-09-04: ONE route, TWO homes, strictly sequential implementation --
skipi-broker first (BACKLOG No191 + No197), skipi-crewing after (BACKLOG No179).
The GO authorizes the route only: no production deploy, no combined product
diff, no other backlog items.

What this file proves mechanically, by driving the real bin/skipi-guard:

  * the exact escaping-fix file set of each home routes to the route and passes
    scope -- today three of those paths are allowed by no task at all
    (broker: dist/map.js, src-tauri/src/lib.rs outside stack-metadata, and the
    new negatives harness; crewing: src-tauri/src/messaging.rs and its harness);
  * a diff WITHOUT the negatives harness does not open the route
    (`require_all_of`) and stays red on the default task;
  * ANY file outside the declared set drops the diff back to the default task
    and keeps it red -- in particular a version bump cannot ride this route;
  * every pre-route entry of both configs stays byte-identical (the route is
    purely additive: 98 insertions, 0 deletions).

The route deliberately has NO `exact_task_file_sets` entry: an executor commits
early and often, so an intermediate push of `dist/index.html` + the harness must
pass. The diff is bounded by `when_all_files_in` instead (same shape as the last
owner-authorized route, seafarer `login-gate-first-162b`, PR #49).

Baseline for the PRE_ROUTE literals below: skipi-guard main
c88ff1cc9531708769e0335bfc29a3689c8a2844 (PR #49). Verify or regenerate with
`git show c88ff1cc:configs/homes/<home>.json`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

ROUTE_TASK = "security-escaping-191"
DEFAULT_TASK = "plugin-host"


def _load_guard_module():
    """Import bin/skipi-guard as a module so its own matcher can be exercised.

    The module name is not __main__, so importing does not run the CLI.
    """
    spec = importlib.util.spec_from_loader(
        "skipi_guard_under_test", SourceFileLoader("skipi_guard_under_test", str(GUARD))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD_MODULE = _load_guard_module()

# --- broker (BACKLOG No191 escaping debt + No197 trial gate) -----------------
BROKER_RULE_NAME = (
    "broker dist escaping security routing "
    "(BACKLOG №191/№197, owner-authorized 2026-09-04)"
)
BROKER_ROUTE_FILES = [
    "dist/index.html",
    "dist/map.js",
    "src-tauri/src/lib.rs",
    "tests/broker_escaping_negative_harness.mjs",
]
BROKER_CORE_FILES = [
    "dist/index.html",
    "tests/broker_escaping_negative_harness.mjs",
]
BROKER_HARNESSES = [
    {"name": "broker_plugin_isolation", "command": "node tests/broker_plugin_isolation_harness.mjs"},
    {"name": "broker_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "broker_presence_contract", "command": "node tests/broker_presence_contract_harness.mjs"},
    {"name": "broker_map_contract", "command": "node tests/map_contract_harness.mjs"},
    {"name": "broker_trial_gate_wired", "command": "node tests/trial_gate_wired_harness.mjs"},
    {"name": "broker_csp_inline_handlers", "command": "node tests/csp_inline_handlers_harness.mjs"},
    {"name": "broker_escaping_negative", "command": "node tests/broker_escaping_negative_harness.mjs"},
    {"name": "broker_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {
        "name": "broker_stack_verification_negative_control",
        "command": "node tests/stack_verification_negative_control_harness.mjs",
    },
    {"name": "broker_map_msi_module_pin", "command": "node tests/map_msi_module_pin_harness.mjs"},
]
# Pre-existing routes of the home, with the classification they had before this
# route. `proguard` is expected to FAIL: .github/workflows/skipi-guard.yml is
# outside the release allowlist on main already. It is listed exactly so that a
# shift in that pre-existing behaviour would also be caught.
BROKER_EXISTING_ROUTES = [
    {
        "task": "repo-meta",
        "rule": "repo-meta routing",
        "status": "pass",
        "files": ["AGENTS.md", "CLAUDE.md"],
    },
    {
        "task": "stack-metadata",
        "rule": "broker Stage 4 stack-metadata routing",
        "status": "pass",
        "files": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs",
        ],
    },
    {
        "task": "release",
        "rule": "canonical version-bump routing",
        "status": "pass",
        "files": [
            "dist/index.html",
            "src-tauri/Cargo.toml",
            "src-tauri/Cargo.lock",
            "src-tauri/tauri.conf.json",
        ],
    },
    {
        "task": "settings-adopt",
        "rule": "settings-adopt routing",
        "status": "pass",
        "files": ["dist/index.html", "dist/skipi-settings.js"],
    },
    {
        "task": "release",
        "rule": "broker android proguard JNI-keep release routing",
        "status": "fail",
        "files": [
            "src-tauri/gen/android/app/proguard-rules.pro",
            ".github/workflows/skipi-guard.yml",
        ],
    },
]

# --- crewing (BACKLOG No179 escaping debt) ----------------------------------
CREWING_RULE_NAME = (
    "crewing dist escaping security routing "
    "(BACKLOG №179, owner-authorized 2026-09-04)"
)
CREWING_ROUTE_FILES = [
    "dist/index.html",
    "src-tauri/src/messaging.rs",
    "tests/crewing_escaping_negative_harness.mjs",
]
CREWING_CORE_FILES = [
    "dist/index.html",
    "tests/crewing_escaping_negative_harness.mjs",
]
CREWING_HARNESSES = [
    {"name": "crewing_plugin_isolation", "command": "node tests/crewing_plugin_isolation_harness.mjs"},
    {
        "name": "shared_host_runtime_isolation",
        "command": "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs",
    },
    {"name": "crewing_presence_contract", "command": "node tests/crewing_presence_contract_harness.mjs"},
    {"name": "crewing_crew_flow_demo", "command": "node tests/crewing_crew_flow_demo_harness.mjs"},
    {"name": "crewing_csp_inline_handlers", "command": "node tests/csp_inline_handlers_harness.mjs"},
    {"name": "crewing_mailbox_contract", "command": "node tests/crewing_mailbox_contract_harness.mjs"},
    {"name": "crewing_escaping_negative", "command": "node tests/crewing_escaping_negative_harness.mjs"},
    {"name": "crewing_build_provenance", "command": "node tests/build_provenance_harness.mjs"},
    {"name": "crewing_theme_default", "command": "node tests/crewing_theme_default_harness.mjs"},
    {
        "name": "crewing_compliance_manual_flow",
        "command": "node tests/crewing_compliance_manual_flow_harness.mjs",
    },
    {"name": "crewing_mail_cv_intake_demo", "command": "node tests/crewing_mail_cv_intake_demo_harness.mjs"},
    {"name": "crewing_settings5_preview_gated", "command": "node tests/settings5_preview_gated_harness.mjs"},
    {"name": "crewing_trial_gate_wired", "command": "node tests/trial_gate_wired_harness.mjs"},
    {
        "name": "crewing_trial_activate_unconnected",
        "command": "node tests/trial_activate_unconnected_harness.mjs",
    },
    {"name": "crewing_stack_build_metadata", "command": "node tests/stack_build_metadata_harness.mjs"},
    {
        "name": "crewing_stack_verification_negative_control",
        "command": "node tests/stack_verification_negative_control_harness.mjs",
    },
]
CREWING_EXISTING_ROUTES = [
    {
        "task": "repo-meta",
        "rule": "repo-meta routing",
        "status": "pass",
        "files": ["AGENTS.md", "CLAUDE.md"],
    },
    {
        "task": "stack-metadata",
        "rule": "crewing Stage 4 stack-metadata routing",
        "status": "pass",
        "files": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs",
        ],
    },
    {
        "task": "release",
        "rule": "canonical version-bump routing",
        "status": "pass",
        "files": [
            "dist/index.html",
            "src-tauri/Cargo.toml",
            "src-tauri/Cargo.lock",
            "src-tauri/tauri.conf.json",
        ],
    },
    {
        "task": "settings-adopt",
        "rule": "settings-adopt routing",
        "status": "pass",
        "files": [
            "dist/SETTINGS_VERSION",
            "dist/index.html",
            "dist/skipi-settings.css",
            "dist/skipi-settings.js",
            "tests/crewing_theme_default_harness.mjs",
        ],
    },
    {
        "task": "theme-default",
        "rule": "theme-default routing",
        "status": "pass",
        "files": ["dist/index.html", "tests/crewing_theme_default_harness.mjs"],
    },
    {
        "task": "provenance",
        "rule": "provenance routing",
        "status": "pass",
        "files": [
            "tests/build_provenance_harness.mjs",
            "src-tauri/build.rs",
            "src-tauri/src/lib.rs",
        ],
    },
]


BROKER_PRE_ROUTE = {
    "release_tasks": ["release", "release-infra", "build-release", "stack-metadata"],
    "default_task": "plugin-host",
    "exact_task_file_sets": {
        "stack-metadata": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs"
        ]
    },
    "task_routing": [
        {
            "name": "repo-meta routing",
            "task": "repo-meta",
            "when_all_files_in": ["AGENTS.md", "CLAUDE.md"]
        },
        {
            "name": "broker android proguard JNI-keep release routing",
            "task": "release",
            "when_all_files_in": [
                "src-tauri/gen/android/app/proguard-rules.pro",
                ".github/workflows/skipi-guard.yml"
            ],
            "require_any_of": ["src-tauri/gen/android/app/proguard-rules.pro"]
        },
        {
            "name": "broker Stage 4 stack-metadata routing",
            "task": "stack-metadata",
            "when_all_files_in": [
                "dist/index.html",
                "src-tauri/Cargo.lock",
                "src-tauri/Cargo.toml",
                "src-tauri/src/lib.rs",
                "src-tauri/tauri.conf.json",
                "tests/stack_build_metadata_harness.mjs",
                "tests/stack_verification_negative_control_harness.mjs"
            ],
            "require_all_of": [
                "dist/index.html",
                "src-tauri/Cargo.lock",
                "src-tauri/Cargo.toml",
                "src-tauri/src/lib.rs",
                "src-tauri/tauri.conf.json",
                "tests/stack_build_metadata_harness.mjs",
                "tests/stack_verification_negative_control_harness.mjs"
            ]
        },
        {
            "name": "canonical version-bump routing",
            "task": "release",
            "when_all_files_in": [
                "dist/index.html",
                "src-tauri/Cargo.toml",
                "src-tauri/Cargo.lock",
                "src-tauri/tauri.conf.json"
            ],
            "require_any_of": ["src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"]
        },
        {
            "name": "settings-adopt routing",
            "task": "settings-adopt",
            "when_all_files_in": ["dist/index.html", "dist/skipi-settings*"],
            "require_any_of": ["dist/skipi-settings*"]
        }
    ],
    "allowed_file_patterns": {
        "repo-meta": ["AGENTS.md", "CLAUDE.md"],
        "plugin-host": [
            "dist/index.html",
            "dist/plugin-host-bridge.js",
            "dist/map-module/map.js",
            "dist/map-module/map.css",
            "dist/map-module/VENDOR-PIN.json",
            "dist/leaflet/world-land.geojson",
            "dist/leaflet/world-coastline.geojson",
            "dist/msi/warnings.geojson",
            "presence-manifest.json",
            "tests/broker_plugin_isolation_harness.mjs",
            "tests/broker_presence_contract_harness.mjs",
            "tests/map_msi_module_pin_harness.mjs"
        ],
        "settings-adopt": ["dist/index.html", "dist/skipi-settings*"],
        "release": ["dist/index.html"],
        "stack-metadata": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs"
        ]
    },
    "harness_commands": {
        "plugin-host": [
            ["broker_plugin_isolation", "node tests/broker_plugin_isolation_harness.mjs"],
            ["broker_build_provenance", "node tests/build_provenance_harness.mjs"],
            ["broker_presence_contract", "node tests/broker_presence_contract_harness.mjs"]
        ],
        "provenance": [["broker_build_provenance", "node tests/build_provenance_harness.mjs"]],
        "settings-adopt": [
            ["broker_plugin_isolation", "node tests/broker_plugin_isolation_harness.mjs"],
            ["broker_build_provenance", "node tests/build_provenance_harness.mjs"],
            ["broker_presence_contract", "node tests/broker_presence_contract_harness.mjs"]
        ],
        "release": [
            ["broker_plugin_isolation", "node tests/broker_plugin_isolation_harness.mjs"],
            ["broker_build_provenance", "node tests/build_provenance_harness.mjs"],
            ["broker_presence_contract", "node tests/broker_presence_contract_harness.mjs"]
        ],
        "stack-metadata": [
            ["broker_stack_build_metadata", "node tests/stack_build_metadata_harness.mjs"],
            [
                "broker_stack_verification_negative_control",
                "node tests/stack_verification_negative_control_harness.mjs"
            ],
            ["broker_plugin_isolation", "node tests/broker_plugin_isolation_harness.mjs"],
            ["broker_build_provenance", "node tests/build_provenance_harness.mjs"],
            ["broker_presence_contract", "node tests/broker_presence_contract_harness.mjs"]
        ]
    },
    "protected_paths": {
        "backend/server/prod data": [
            "backend/**",
            "server/**",
            "api/**",
            "data/prod/**",
            "prod/**",
            "production/**",
            "media/**",
            "uploads/**"
        ],
        "secrets/signing keys": [
            ".env",
            ".env.*",
            "**/.env",
            "**/.env.*",
            "keys/**",
            "signing/**",
            "**/*.pem",
            "**/*.p12",
            "**/*.keystore",
            "**/*secret*",
            "**/*token*"
        ],
        "pairing/QR/camera bridge": [
            "**/*pair*",
            "**/*Pair*",
            "**/*qr*",
            "**/*QR*",
            "**/*camera*",
            "**/*Camera*",
            "**/*barcode*",
            "**/*Barcode*"
        ],
        "presence contracts": ["presence-manifest.json"]
    },
    "release_sensitive_paths": {
        "catalog/latest/release manifests": [
            "latest.json",
            "**/latest.json",
            "catalog/**",
            "**/catalog/**",
            "release/**",
            "releases/**",
            "downloads/**",
            "manifest*.json",
            "**/manifest*.json"
        ],
        "versions/tags": [
            "VERSION",
            "version.txt",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "src-tauri/tauri.conf.json",
            "Cargo.toml",
            "Cargo.lock"
        ],
        "Tauri/Cargo/mobile generated files": [
            "src-tauri/gen/**",
            "src-tauri/target/**",
            "src-tauri/Cargo.lock",
            "android/**",
            "ios/**",
            "build/**",
            "*.apk",
            "*.aab",
            "*.ipa",
            "dist/**/*.apk"
        ],
        "Play/TestFlight/upload/deploy": [
            "fastlane/**",
            "play/**",
            "testflight/**",
            "scripts/deploy*",
            "scripts/upload*",
            "scripts/*testflight*",
            "scripts/*play*",
            ".github/workflows/*release*",
            ".github/workflows/*deploy*"
        ]
    }
}

CREWING_PRE_ROUTE = {
    "release_tasks": ["release", "release-infra", "build-release", "stack-metadata"],
    "default_task": "plugin-host",
    "exact_task_file_sets": {
        "stack-metadata": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs"
        ]
    },
    "task_routing": [
        {
            "name": "repo-meta routing",
            "task": "repo-meta",
            "when_all_files_in": ["AGENTS.md", "CLAUDE.md"]
        },
        {
            "name": "crewing android proguard JNI-keep release routing",
            "task": "release",
            "when_all_files_in": [
                "src-tauri/gen/android/app/proguard-rules.pro",
                ".github/workflows/skipi-guard.yml"
            ],
            "require_any_of": ["src-tauri/gen/android/app/proguard-rules.pro"]
        },
        {
            "name": "crewing Stage 4 stack-metadata routing",
            "task": "stack-metadata",
            "when_all_files_in": [
                "dist/index.html",
                "src-tauri/Cargo.lock",
                "src-tauri/Cargo.toml",
                "src-tauri/src/lib.rs",
                "src-tauri/tauri.conf.json",
                "tests/stack_build_metadata_harness.mjs",
                "tests/stack_verification_negative_control_harness.mjs"
            ],
            "require_all_of": [
                "dist/index.html",
                "src-tauri/Cargo.lock",
                "src-tauri/Cargo.toml",
                "src-tauri/src/lib.rs",
                "src-tauri/tauri.conf.json",
                "tests/stack_build_metadata_harness.mjs",
                "tests/stack_verification_negative_control_harness.mjs"
            ]
        },
        {
            "name": "provenance routing",
            "task": "provenance",
            "when_all_files_in": ["tests/build_provenance_harness.mjs", "src-tauri/build.rs", "src-tauri/src/lib.rs"]
        },
        {
            "name": "canonical version-bump routing",
            "task": "release",
            "when_all_files_in": [
                "dist/index.html",
                "src-tauri/Cargo.toml",
                "src-tauri/Cargo.lock",
                "src-tauri/tauri.conf.json"
            ],
            "require_any_of": ["src-tauri/Cargo.toml", "src-tauri/Cargo.lock", "src-tauri/tauri.conf.json"]
        },
        {
            "name": "settings-adopt routing",
            "task": "settings-adopt",
            "when_all_files_in": [
                "dist/SETTINGS_VERSION",
                "dist/index.html",
                "dist/skipi-settings.css",
                "dist/skipi-settings.js",
                "tests/crewing_theme_default_harness.mjs"
            ],
            "require_any_of": ["dist/SETTINGS_VERSION", "dist/skipi-settings.css", "dist/skipi-settings.js"]
        },
        {
            "name": "theme-default routing",
            "task": "theme-default",
            "when_all_files_in": ["dist/index.html", "tests/crewing_theme_default_harness.mjs"],
            "require_any_of": ["tests/crewing_theme_default_harness.mjs"]
        }
    ],
    "allowed_file_patterns": {
        "repo-meta": ["AGENTS.md", "CLAUDE.md"],
        "plugin-host": [
            "dist/index.html",
            "dist/plugin-host-bridge.js",
            "tests/crewing_plugin_isolation_harness.mjs",
            "presence-manifest.json",
            "tests/crewing_presence_contract_harness.mjs",
            "tests/crewing_crew_flow_demo_harness.mjs",
            "tests/crewing_theme_default_harness.mjs"
        ],
        "settings-adopt": [
            "dist/SETTINGS_VERSION",
            "dist/index.html",
            "dist/skipi-settings.css",
            "dist/skipi-settings.js",
            "tests/crewing_theme_default_harness.mjs"
        ],
        "theme-default": ["dist/index.html", "tests/crewing_theme_default_harness.mjs"],
        "release": ["dist/index.html"],
        "stack-metadata": [
            "dist/index.html",
            "src-tauri/Cargo.lock",
            "src-tauri/Cargo.toml",
            "src-tauri/src/lib.rs",
            "src-tauri/tauri.conf.json",
            "tests/stack_build_metadata_harness.mjs",
            "tests/stack_verification_negative_control_harness.mjs"
        ]
    },
    "harness_commands": {
        "plugin-host": [
            ["crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"],
            [
                "shared_host_runtime_isolation",
                "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"
            ],
            ["crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"],
            ["crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"]
        ],
        "release": [
            ["crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"],
            [
                "shared_host_runtime_isolation",
                "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"
            ],
            ["crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"],
            ["crewing_build_provenance", "node tests/build_provenance_harness.mjs"]
        ],
        "provenance": [["crewing_build_provenance", "node tests/build_provenance_harness.mjs"]],
        "settings-adopt": [
            ["crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"],
            [
                "shared_host_runtime_isolation",
                "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"
            ],
            ["crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"],
            ["crewing_theme_default", "node tests/crewing_theme_default_harness.mjs"],
            ["crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"]
        ],
        "theme-default": [
            ["crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"],
            [
                "shared_host_runtime_isolation",
                "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs"
            ],
            ["crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"],
            ["crewing_theme_default", "node tests/crewing_theme_default_harness.mjs"],
            ["crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"]
        ],
        "stack-metadata": [
            ["crewing_stack_build_metadata", "node tests/stack_build_metadata_harness.mjs"],
            [
                "crewing_stack_verification_negative_control",
                "node tests/stack_verification_negative_control_harness.mjs"
            ],
            ["crewing_plugin_isolation", "node tests/crewing_plugin_isolation_harness.mjs"],
            ["crewing_presence_contract", "node tests/crewing_presence_contract_harness.mjs"],
            ["crewing_crew_flow_demo", "node tests/crewing_crew_flow_demo_harness.mjs"],
            ["crewing_build_provenance", "node tests/build_provenance_harness.mjs"]
        ]
    },
    "protected_paths": {
        "backend/server/prod data": [
            "backend/**",
            "server/**",
            "api/**",
            "data/prod/**",
            "prod/**",
            "production/**",
            "media/**",
            "uploads/**"
        ],
        "secrets/signing keys": [
            ".env",
            ".env.*",
            "**/.env",
            "**/.env.*",
            "keys/**",
            "signing/**",
            "**/*.pem",
            "**/*.p12",
            "**/*.keystore",
            "**/*secret*",
            "**/*token*"
        ],
        "pairing/QR/camera bridge": [
            "**/*pair*",
            "**/*Pair*",
            "**/*qr*",
            "**/*QR*",
            "**/*camera*",
            "**/*Camera*",
            "**/*barcode*",
            "**/*Barcode*"
        ],
        "presence contracts": ["presence-manifest.json"]
    },
    "release_sensitive_paths": {
        "catalog/latest/release manifests": [
            "latest.json",
            "**/latest.json",
            "catalog/**",
            "**/catalog/**",
            "release/**",
            "releases/**",
            "downloads/**",
            "manifest*.json",
            "**/manifest*.json"
        ],
        "versions/tags": [
            "VERSION",
            "version.txt",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "src-tauri/tauri.conf.json",
            "Cargo.toml",
            "Cargo.lock"
        ],
        "Tauri/Cargo/mobile generated files": [
            "src-tauri/gen/**",
            "src-tauri/target/**",
            "src-tauri/Cargo.lock",
            "android/**",
            "ios/**",
            "build/**",
            "*.apk",
            "*.aab",
            "*.ipa",
            "dist/**/*.apk"
        ],
        "Play/TestFlight/upload/deploy": [
            "fastlane/**",
            "play/**",
            "testflight/**",
            "scripts/deploy*",
            "scripts/upload*",
            "scripts/*testflight*",
            "scripts/*play*",
            ".github/workflows/*release*",
            ".github/workflows/*deploy*"
        ]
    },
    "additive_task_checks": [
        {
            "name": "plugin-host protections follow release/provenance routing",
            "task": "plugin-host",
            "when_tasks": ["release", "provenance"],
            "patterns": ["dist/**", "presence-manifest.json", "tests/crewing_*_harness.mjs"]
        }
    ]
}


class SecurityEscapingRouteContract:
    """Contract both homes of the route must satisfy.

    Mixed into a real TestCase per home; it is deliberately not a TestCase
    itself so unittest discovery does not run it standalone.
    """

    HOME = ""
    RULE_NAME = ""
    ROUTE_FILES: list[str] = []
    CORE_FILES: list[str] = []
    HARNESSES: list[dict[str, str]] = []
    EXISTING_ROUTES: list[dict[str, Any]] = []
    PRE_ROUTE: dict[str, Any] = {}

    # A version bump and the guard CI pin are the two things this route must
    # never be able to carry (they are what an exact route is usually abused
    # for). Neither is in the declared set.
    RELEASE_BUMP_FILE = "src-tauri/Cargo.toml"
    CI_PIN_FILE = ".github/workflows/skipi-guard.yml"
    EXPECTED_HARNESS_COUNT = 0
    # Every green harness of the home that reads a file this route opens must
    # run on the route: opening a file while dropping the only checks that read
    # it is the defect this list exists to prevent (merge-gate audit F-1/F-2).
    GUARDED_READERS: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
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
        guard_bin: Path | None = None,
        run_harness: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(guard_bin or GUARD),
            "verify",
            "--home",
            self.HOME,
            "--auto-task",
            "--repo",
            str(repo),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
            "--json",
            str(result_json),
        ]
        if run_harness:
            command.append("--run-harness")
        proc = subprocess.run(command, text=True, capture_output=True, env=self.child_env())
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def guard_root_with_config(self, root: Path, mutate) -> Path:
        """Materialise a throwaway guard root whose config has been mutated.

        skipi-guard resolves its config dir from its own location
        (ROOT = Path(__file__).resolve().parents[1]), so copying the single
        script next to a patched configs/homes/<home>.json runs the real gate
        against a hypothetical config. Nothing in the checkout is touched.
        """
        guard_root = root / "guard"
        (guard_root / "bin").mkdir(parents=True)
        (guard_root / "configs" / "homes").mkdir(parents=True)
        guard_bin = guard_root / "bin" / "skipi-guard"
        shutil.copy2(GUARD, guard_bin)
        guard_bin.chmod(0o755)
        config = self.load_config()
        mutate(config)
        (guard_root / "configs" / "homes" / f"{self.HOME}.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return guard_bin

    def verify_files(
        self,
        files: list[str],
        *,
        prefix: str,
        mutate_config=None,
        run_harness: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        updates = {path: f"fixture for {path}\n" for path in files}
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            guard_bin = None if mutate_config is None else self.guard_root_with_config(root, mutate_config)
            return self.run_guard(repo, root / "result.json", guard_bin=guard_bin, run_harness=run_harness)

    def load_config(self) -> dict[str, Any]:
        with (ROOT / "configs" / "homes" / f"{self.HOME}.json").open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_opens_route(self, files: list[str], *, prefix: str) -> None:
        proc, payload = self.verify_files(files, prefix=prefix)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(files))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], self.RULE_NAME)
        self.assertEqual(payload["effective_tasks"], [ROUTE_TASK])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["exact_file_set_missing"], [])
        self.assertEqual(payload["exact_file_set_unexpected"], [])
        self.assertEqual(payload["errors"], [])
        # Nothing in the declared set is release-sensitive: the security fix
        # never touches a version file.
        self.assertFalse(payload["release_changes"])
        self.assertEqual(payload["release_paths_touched"], [])
        self.assertEqual(payload["protected_paths_touched"], [])
        # The route is not a release task, so no plugin-host/provenance
        # inheritance happens: the effective harness list is exactly the
        # declared one, in order.
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            self.HARNESSES,
        )

    def assert_stays_red_on_default_task(self, files: list[str], *, prefix: str) -> dict[str, Any]:
        proc, payload = self.verify_files(files, prefix=prefix)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["task"], DEFAULT_TASK)
        self.assertIsNone(payload["task_rule"])
        self.assertTrue(
            any("changes outside allowed patterns" in error for error in payload["errors"]),
            payload["errors"],
        )
        return payload

    # ------------------------------------------------------------------
    # the route opens for exactly the authorized work
    # ------------------------------------------------------------------
    def test_route_file_set_routes_and_passes_scope(self) -> None:
        self.assert_opens_route(self.ROUTE_FILES, prefix=f"skipi-guard-{self.HOME}-escaping-set-")

    def test_partial_push_of_core_files_still_passes(self) -> None:
        # No exact_task_file_sets entry, on purpose: an executor commits early
        # and often, so every subset that still carries both core files must
        # pass. Anything wider is bounded by when_all_files_in.
        candidates = [self.CORE_FILES] + [
            [path for path in self.ROUTE_FILES if path != extra]
            for extra in self.ROUTE_FILES
            if extra not in self.CORE_FILES
        ]
        subsets: list[list[str]] = []
        for subset in candidates:
            if subset not in subsets:
                subsets.append(subset)
        for subset in subsets:
            with self.subTest(files=subset):
                self.assert_opens_route(subset, prefix=f"skipi-guard-{self.HOME}-escaping-partial-")

    # ------------------------------------------------------------------
    # the route stays shut for everything else
    # ------------------------------------------------------------------
    def test_diff_without_a_core_file_does_not_open_route(self) -> None:
        # require_all_of: the negatives harness and dist/index.html must both
        # be in every push of the branch, or the diff falls back to the default
        # task and stays red.
        for core in self.CORE_FILES:
            with self.subTest(missing=core):
                files = [path for path in self.ROUTE_FILES if path != core]
                self.assert_stays_red_on_default_task(
                    files, prefix=f"skipi-guard-{self.HOME}-escaping-no-core-"
                )

    def test_any_file_outside_the_declared_set_stays_red(self) -> None:
        for extra in (self.CI_PIN_FILE, "src/unrelated.txt", "dist/plugin-host-bridge.js"):
            with self.subTest(extra=extra):
                self.assert_stays_red_on_default_task(
                    self.ROUTE_FILES + [extra],
                    prefix=f"skipi-guard-{self.HOME}-escaping-extra-",
                )

    def test_version_bump_cannot_ride_the_route(self) -> None:
        # The whole point of bounding the route: a release-sensitive file added
        # to the escaping diff must not be silently authorized. It falls back to
        # the default task, which is not a release task, so the touch is blocked
        # on top of the scope violation.
        payload = self.assert_stays_red_on_default_task(
            self.ROUTE_FILES + [self.RELEASE_BUMP_FILE],
            prefix=f"skipi-guard-{self.HOME}-escaping-bump-",
        )

        self.assertTrue(payload["release_changes"])
        self.assertIn(
            self.RELEASE_BUMP_FILE,
            [touch["path"] for touch in payload["release_paths_touched"]],
        )
        self.assertTrue(
            any("release-sensitive path touch is blocked" in error for error in payload["errors"]),
            payload["errors"],
        )

    def test_dist_index_alone_does_not_route_to_security191(self) -> None:
        # security191 must not capture index-only. OWNER422 now requires six
        # checks for Broker index-only; Crewing keeps its prior default route.
        proc, payload = self.verify_files(
            ["dist/index.html"], prefix=f"skipi-guard-{self.HOME}-escaping-index-alone-"
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["task"], "broker-map-demo-422" if self.HOME == "broker" else DEFAULT_TASK)
        self.assertEqual(
            payload["task_rule"],
            "broker Map/shared Demo routing (OWNER422, 2026-09-08)" if self.HOME == "broker" else None,
        )
        self.assertNotEqual(payload["task"], ROUTE_TASK)
        expected_harnesses = [
            {"name": name, "command": command}
            for name, command in self.PRE_ROUTE["harness_commands"][DEFAULT_TASK]
        ]
        if self.HOME == "broker":
            expected_harnesses.extend([
                {"name": "broker_map_contract", "command": "node tests/map_contract_harness.mjs"},
                {"name": "broker_trial_gate_wired", "command": "node tests/trial_gate_wired_harness.mjs"},
                {"name": "broker_demo", "command": "node tests/broker_demo_harness.mjs"},
            ])
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            expected_harnesses,
        )

    # ------------------------------------------------------------------
    # the declaration itself
    # ------------------------------------------------------------------
    def test_route_declaration_is_literal_and_routed_first(self) -> None:
        config = self.load_config()

        rules = [rule for rule in config["task_routing"] if rule.get("task") == ROUTE_TASK]
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        # First in the array: routing is first-match-wins, so the position is
        # part of the contract.
        self.assertIs(rule, config["task_routing"][0])
        self.assertEqual(
            rule,
            {
                "name": self.RULE_NAME,
                "task": ROUTE_TASK,
                "when_all_files_in": self.ROUTE_FILES,
                "require_all_of": self.CORE_FILES,
            },
        )
        self.assertNotIn("require_any_of", rule)
        self.assertEqual(config["allowed_file_patterns"][ROUTE_TASK], self.ROUTE_FILES)
        self.assertEqual(config["harness_commands"][ROUTE_TASK], self.HARNESSES)

        # Literals only: a glob here would silently widen the route.
        for pattern in rule["when_all_files_in"] + rule["require_all_of"] + config["allowed_file_patterns"][ROUTE_TASK]:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("[", pattern)
        for core in self.CORE_FILES:
            self.assertIn(core, self.ROUTE_FILES)
        names = [entry["name"] for entry in self.HARNESSES]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), self.EXPECTED_HARNESS_COUNT)
        # The allowlist must exist and be non-empty: a task with no allowed
        # patterns is NOT scope-checked at all (see the fail-open test below),
        # so an empty or missing entry silently unbounds the route.
        self.assertTrue(config["allowed_file_patterns"].get(ROUTE_TASK))

    def test_route_is_not_a_release_task(self) -> None:
        config = self.load_config()

        # Not listed, and not named so that skipi-guard's is_release_task()
        # naming convention would classify it as one. This is what makes a
        # release-sensitive file fatal instead of authorized.
        self.assertNotIn(ROUTE_TASK, config["release_tasks"])
        lowered = ROUTE_TASK.lower()
        self.assertNotEqual(lowered, "release")
        self.assertFalse(lowered.startswith("release-"))
        self.assertFalse(lowered.endswith("-release"))
        # And no exact set: partial pushes must pass (see the partial-push test).
        self.assertNotIn(ROUTE_TASK, config["exact_task_file_sets"])

    # ------------------------------------------------------------------
    # the declaration cannot be hollowed out
    # ------------------------------------------------------------------
    def test_route_patterns_are_directory_qualified_single_file_paths(self) -> None:
        """Every route pattern must name exactly one file, by full path.

        skipi-guard's matcher treats a glob-free pattern with no "/" as a
        BASENAME match (`path.endswith("/" + pattern)`), so `map.js` would also
        match `dist/map-module/map.js` -- the vendored Leaflet module. A
        coordinated edit of the config and this file's constants would
        otherwise keep the suite green while the real gate let a vendor file
        ride the route.
        """
        config = self.load_config()
        rule = config["task_routing"][0]
        patterns = (
            rule["when_all_files_in"] + rule["require_all_of"] + config["allowed_file_patterns"][ROUTE_TASK]
        )
        self.assertTrue(patterns)
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                for glob_char in ("*", "?", "["):
                    self.assertNotIn(glob_char, pattern)
                # A directory component is what disables basename matching.
                self.assertIn("/", pattern, f"{pattern!r} would match by basename anywhere in the tree")
                self.assertFalse(pattern.startswith("/"))
                self.assertTrue(GUARD_MODULE.pattern_matches(pattern, pattern))
                # ... and it must match nothing but itself.
                directory, _, base = pattern.rpartition("/")
                for decoy in (
                    base,
                    f"vendor/{pattern}",
                    f"{directory}/vendored/{base}",
                    f"{directory}/map-module/{base}",
                    f"other/{base}",
                    f"{pattern}.bak",
                ):
                    if decoy == pattern:
                        continue
                    self.assertFalse(
                        GUARD_MODULE.pattern_matches(decoy, pattern),
                        f"{pattern!r} also matches {decoy!r}",
                    )

    def test_declared_harnesses_cover_every_file_the_route_opens(self) -> None:
        # Merge-gate audit F-1: the route opened src-tauri/src/lib.rs for the
        # broker while leaving behind the only two harnesses that read it,
        # because before the route lib.rs was reachable only through
        # stack-metadata, where they are mandatory.
        # Read the live config, not this file's constant: asserting a constant
        # against a constant would prove nothing.
        config = self.load_config()
        commands = {entry["command"] for entry in config["harness_commands"][ROUTE_TASK]}
        for opened_file, readers in self.GUARDED_READERS.items():
            for reader in readers:
                with self.subTest(opened=opened_file, harness=reader):
                    self.assertIn(f"node tests/{reader}", commands)

    def test_missing_harness_file_fails_the_run(self) -> None:
        """--run-harness must actually execute the commands.

        Without this the suite never runs a harness, so a command pointing at a
        file that does not exist would sit in the config looking green forever.
        The fixture repo has no real harness scripts, so every declared command
        must fail loudly.
        """
        proc, payload = self.verify_files(
            self.ROUTE_FILES,
            prefix=f"skipi-guard-{self.HOME}-escaping-harness-",
            run_harness=True,
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertTrue(payload["tests"])
        statuses = {entry["status"] for entry in payload["tests"]}
        self.assertIn("fail", statuses)
        self.assertTrue(
            any("harness" in error.lower() or "failed" in error.lower() for error in payload["errors"]),
            payload["errors"],
        )

    def test_gate_fails_open_without_a_route_allowlist(self) -> None:
        """KNOWN GATE LIMITATION, pinned deliberately.

        scope_check_for_task() returns None when a task has no allowed
        patterns, so deleting allowed_file_patterns[route] does not turn the
        route red -- it silently switches scope checking OFF for it. The gate
        fails OPEN here, which is why the presence and exact content of the
        allowlist is asserted structurally rather than behaviourally.

        Fixing it means changing bin/skipi-guard, which is out of scope for a
        route PR. If the gate is ever made to fail closed on a missing
        allowlist, this test should start failing -- update it then.
        """
        def drop_allowlist(config: dict[str, Any]) -> None:
            del config["allowed_file_patterns"][ROUTE_TASK]

        proc, payload = self.verify_files(
            self.ROUTE_FILES,
            prefix=f"skipi-guard-{self.HOME}-escaping-noallowlist-",
            mutate_config=drop_allowlist,
        )

        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["scope_checks"], [])
        self.assertEqual(proc.returncode, 0, "gate now fails closed on a missing allowlist -- update this test")
        self.assertEqual(payload["status"], "pass")

    def test_route_allowlist_is_load_bearing_when_present(self) -> None:
        # The counterpart to the fail-open test: as long as the allowlist is
        # there, narrowing it does bite. Drop one path from it and that path
        # becomes a scope violation while the routing rule still matches.
        removed = self.ROUTE_FILES[1]

        def narrow_allowlist(config: dict[str, Any]) -> None:
            config["allowed_file_patterns"][ROUTE_TASK] = [
                pattern for pattern in config["allowed_file_patterns"][ROUTE_TASK] if pattern != removed
            ]

        proc, payload = self.verify_files(
            self.ROUTE_FILES,
            prefix=f"skipi-guard-{self.HOME}-escaping-narrowed-",
            mutate_config=narrow_allowlist,
        )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(payload["scope_violations"], [removed])

    def test_deleting_route_files_is_accepted_known_gate_limitation(self) -> None:
        """KNOWN GATE LIMITATION, pinned deliberately.

        The gate reads `git diff --name-only`, so it sees WHICH paths changed
        but not HOW: a commit that deletes dist/map.js and src-tauri/src/lib.rs
        outright routes and passes exactly like one that edits them. Blocking
        deletions needs a change-kind check inside bin/skipi-guard, which a
        route PR may not make. The boundary is held by the task card and
        manager acceptance instead.
        """
        deletable = [path for path in self.ROUTE_FILES if path not in self.CORE_FILES]
        self.assertTrue(deletable)
        with tempfile.TemporaryDirectory(prefix=f"skipi-guard-{self.HOME}-escaping-delete-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.run_git(repo, "init", "-q")
            self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
            self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")
            self.commit_files(repo, "base", {path: "original\n" for path in self.ROUTE_FILES})
            for path in deletable:
                (repo / path).unlink()
            self.commit_files(repo, "delete route files", {path: "edited\n" for path in self.CORE_FILES})
            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(payload["changed_files"], sorted(self.ROUTE_FILES))
        self.assertEqual(payload["task"], ROUTE_TASK)
        self.assertEqual(
            proc.returncode, 0, "gate now distinguishes deletions from edits -- update this test"
        )
        self.assertEqual(payload["status"], "pass")

    # ------------------------------------------------------------------
    # additivity: nothing that existed before the route moved
    # ------------------------------------------------------------------
    def test_pre_route_config_surface_is_unchanged(self) -> None:
        config = self.load_config()
        pre = self.PRE_ROUTE

        self.assertEqual(config["release_tasks"], pre["release_tasks"])
        self.assertEqual(config["default_task"], pre["default_task"])
        self.assertEqual(config["exact_task_file_sets"], pre["exact_task_file_sets"])

        # OWNER422 adds one independently tested Broker route. Exclude only
        # that task from this historical snapshot; its exact shape and the
        # entire pre-422 config are pinned in test_broker_map_demo_route.py.
        later_tasks = {"broker-map-demo-422"} if self.HOME == "broker" else set()
        # The security route stays first; every historical rule stays in order.
        self.assertEqual(config["task_routing"][0]["task"], ROUTE_TASK)
        self.assertEqual(
            [rule for rule in config["task_routing"][1:] if rule["task"] not in later_tasks],
            pre["task_routing"],
        )

        self.assertEqual(
            {task: patterns for task, patterns in config["allowed_file_patterns"].items()
             if task != ROUTE_TASK and task not in later_tasks},
            pre["allowed_file_patterns"],
        )
        self.assertEqual(
            {
                task: [[entry["name"], entry["command"]] for entry in entries]
                for task, entries in config["harness_commands"].items()
                if task != ROUTE_TASK and task not in later_tasks
            },
            pre["harness_commands"],
        )
        # AGENTS.md invariant: narrowing protected_paths needs its own PR with a
        # justification per path. A route PR must not touch them at all.
        self.assertEqual(
            {rule["name"]: rule["patterns"] for rule in config["protected_paths"]},
            pre["protected_paths"],
        )
        self.assertEqual(
            {rule["name"]: rule["patterns"] for rule in config["release_sensitive_paths"]},
            pre["release_sensitive_paths"],
        )
        self.assertEqual(
            config.get("additive_task_checks", []),
            pre.get("additive_task_checks", []),
        )

    def test_existing_routes_keep_their_classification(self) -> None:
        for case in self.EXISTING_ROUTES:
            with self.subTest(rule=case["rule"]):
                proc, payload = self.verify_files(
                    case["files"], prefix=f"skipi-guard-{self.HOME}-existing-"
                )

                self.assertEqual(payload["task"], case["task"])
                self.assertEqual(payload["task_rule"], case["rule"])
                self.assertEqual(payload["status"], case["status"])
                self.assertEqual(proc.returncode, 0 if case["status"] == "pass" else 1)
                if case["status"] == "pass":
                    self.assertEqual(payload["scope_violations"], [])


class BrokerSecurityEscapingRouteTests(SecurityEscapingRouteContract, unittest.TestCase):
    HOME = "broker"
    RULE_NAME = BROKER_RULE_NAME
    ROUTE_FILES = BROKER_ROUTE_FILES
    CORE_FILES = BROKER_CORE_FILES
    HARNESSES = BROKER_HARNESSES
    EXISTING_ROUTES = BROKER_EXISTING_ROUTES
    PRE_ROUTE = BROKER_PRE_ROUTE
    EXPECTED_HARNESS_COUNT = 10
    # Green on the home's live main 7f163cb0. Every one of these reads a file
    # the route opens, so every one of them has to run on the route.
    GUARDED_READERS = {
        "src-tauri/src/lib.rs": [
            "stack_build_metadata_harness.mjs",
            "stack_verification_negative_control_harness.mjs",
            "build_provenance_harness.mjs",
            "broker_plugin_isolation_harness.mjs",
        ],
        "dist/map.js": ["map_contract_harness.mjs"],
        "dist/index.html": [
            "broker_presence_contract_harness.mjs",
            "build_provenance_harness.mjs",
            "csp_inline_handlers_harness.mjs",
            "map_contract_harness.mjs",
            "map_msi_module_pin_harness.mjs",
            "stack_build_metadata_harness.mjs",
            "stack_verification_negative_control_harness.mjs",
            "trial_gate_wired_harness.mjs",
            "broker_plugin_isolation_harness.mjs",
        ],
    }

    def test_route_opens_the_three_paths_no_task_allowed_before(self) -> None:
        # The reason the route needed an owner GO at all: dist/map.js is not the
        # allowlisted dist/map-module/map.js, src-tauri/src/lib.rs was reachable
        # only inside stack-metadata (which demands all seven files including the
        # version bump), and the negatives harness is a brand new file.
        pre_allowed = {
            pattern
            for patterns in BROKER_PRE_ROUTE["allowed_file_patterns"].values()
            for pattern in patterns
        }
        for path in ("dist/map.js", "tests/broker_escaping_negative_harness.mjs"):
            self.assertNotIn(path, pre_allowed)
        self.assertNotIn("dist/map.js", BROKER_PRE_ROUTE["allowed_file_patterns"][DEFAULT_TASK])
        self.assertIn("dist/map-module/map.js", BROKER_PRE_ROUTE["allowed_file_patterns"][DEFAULT_TASK])
        self.assertEqual(
            [task for task, patterns in BROKER_PRE_ROUTE["allowed_file_patterns"].items()
             if "src-tauri/src/lib.rs" in patterns],
            ["stack-metadata"],
        )


class CrewingSecurityEscapingRouteTests(SecurityEscapingRouteContract, unittest.TestCase):
    HOME = "crewing"
    RULE_NAME = CREWING_RULE_NAME
    ROUTE_FILES = CREWING_ROUTE_FILES
    CORE_FILES = CREWING_CORE_FILES
    HARNESSES = CREWING_HARNESSES
    EXISTING_ROUTES = CREWING_EXISTING_ROUTES
    PRE_ROUTE = CREWING_PRE_ROUTE
    EXPECTED_HARNESS_COUNT = 16
    # Green on the home's live main 12a7ce4c.
    GUARDED_READERS = {
        "src-tauri/src/messaging.rs": ["crewing_crew_flow_demo_harness.mjs"],
        "dist/index.html": [
            "build_provenance_harness.mjs",
            "crewing_compliance_manual_flow_harness.mjs",
            "crewing_crew_flow_demo_harness.mjs",
            "crewing_mail_cv_intake_demo_harness.mjs",
            "crewing_mailbox_contract_harness.mjs",
            "crewing_plugin_isolation_harness.mjs",
            "crewing_presence_contract_harness.mjs",
            "crewing_theme_default_harness.mjs",
            "csp_inline_handlers_harness.mjs",
            "settings5_preview_gated_harness.mjs",
            "stack_build_metadata_harness.mjs",
            "stack_verification_negative_control_harness.mjs",
            "trial_activate_unconnected_harness.mjs",
            "trial_gate_wired_harness.mjs",
        ],
    }

    def test_route_opens_the_two_paths_no_task_allowed_before(self) -> None:
        # src-tauri/src/messaging.rs is allowed by none of the seven pre-route
        # tasks, and the negatives harness is new.
        pre_allowed = {
            pattern
            for patterns in CREWING_PRE_ROUTE["allowed_file_patterns"].values()
            for pattern in patterns
        }
        for path in ("src-tauri/src/messaging.rs", "tests/crewing_escaping_negative_harness.mjs"):
            self.assertNotIn(path, pre_allowed)

    def test_route_does_not_widen_the_plugin_host_allowlist(self) -> None:
        # dist/index.html is the one route path plugin-host already allowed.
        # The route must add nothing to plugin-host itself.
        config = self.load_config()
        self.assertEqual(
            config["allowed_file_patterns"][DEFAULT_TASK],
            CREWING_PRE_ROUTE["allowed_file_patterns"][DEFAULT_TASK],
        )
        self.assertIn("dist/index.html", config["allowed_file_patterns"][DEFAULT_TASK])
        for path in CREWING_ROUTE_FILES:
            if path != "dist/index.html":
                self.assertNotIn(path, config["allowed_file_patterns"][DEFAULT_TASK])


if __name__ == "__main__":
    unittest.main()
