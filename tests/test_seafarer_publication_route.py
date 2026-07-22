from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
CONFIG = ROOT / "configs" / "homes" / "seafarer.json"
OVERRIDE_ENV = "SKIPI_GUARD_OVERRIDE_TOKEN"

PUBLICATION_TASK = "publication-infra"
PUBLICATION_RULE = "publication-infra routing"
PUBLICATION_HARNESS = {
    "name": "seafarer_rf_mirror_publish_contract",
    "command": "node tests/rf_mirror_publish_contract_harness.mjs",
}
FUTURE_PRODUCT_FILES = [
    ".github/workflows/skipi-guard.yml",
    "scripts/publish-rf-mirror.sh",
    "scripts/prepare-rf-mirror.sh",
    "scripts/RF_MIRROR_PUBLISH.md",
    "tests/rf_mirror_publish_contract_harness.mjs",
]


class SeafarerPublicationRouteTests(unittest.TestCase):
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
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "seafarer",
                "--auto-task",
                "--repo",
                str(repo),
                "--base",
                "HEAD~1",
                "--head",
                "HEAD",
                "--json",
                str(result_json),
            ],
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
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.commit_files(repo, "candidate change", updates)
            return self.run_guard(repo, root / "result.json")

    def publication_candidate(self) -> dict[str, str]:
        return {path: f"fixture for {path}\n" for path in FUTURE_PRODUCT_FILES}

    def test_exact_candidate_routes_to_publication_infra(self) -> None:
        proc, payload = self.verify_updates(
            self.publication_candidate(),
            prefix="skipi-guard-seafarer-publication-route-",
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["changed_files"], sorted(FUTURE_PRODUCT_FILES))
        self.assertEqual(payload["task"], PUBLICATION_TASK)
        self.assertEqual(payload["task_source"], "auto")
        self.assertEqual(payload["task_rule"], PUBLICATION_RULE)
        self.assertEqual(payload["scope_violations"], [])
        self.assertFalse(payload["release_changes"])
        self.assertEqual(
            [{"name": entry["name"], "command": entry["command"]} for entry in payload["tests"]],
            [PUBLICATION_HARNESS],
        )

    def test_publication_route_is_literal_exact_and_non_release(self) -> None:
        with CONFIG.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        routes = [rule for rule in config["task_routing"] if rule.get("task") == PUBLICATION_TASK]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], PUBLICATION_RULE)
        self.assertEqual(routes[0]["when_all_files_in"], FUTURE_PRODUCT_FILES)
        self.assertEqual(routes[0]["require_any_of"], ["scripts/publish-rf-mirror.sh"])
        self.assertEqual(config["allowed_file_patterns"][PUBLICATION_TASK], FUTURE_PRODUCT_FILES)
        self.assertEqual(config["harness_commands"][PUBLICATION_TASK], [PUBLICATION_HARNESS])
        self.assertNotIn(PUBLICATION_TASK, config["release_tasks"])
        for pattern in routes[0]["when_all_files_in"] + config["allowed_file_patterns"][PUBLICATION_TASK]:
            if pattern.startswith("scripts/"):
                self.assertNotIn("*", pattern)
                self.assertNotIn("?", pattern)
                self.assertNotIn("[", pattern)

    def test_candidate_plus_forbidden_classes_stays_red(self) -> None:
        forbidden = {
            "unrelated script": ("scripts/not-approved.sh", "changes outside allowed patterns"),
            "protected": ("presence-manifest.json", "protected path touch requires --override-protected"),
            "release manifest": ("latest.json", "release-sensitive path touch is blocked for this task"),
            "version tag": ("VERSION", "release-sensitive path touch is blocked for this task"),
            "deploy": ("scripts/deploy-production.sh", "release-sensitive path touch is blocked for this task"),
        }
        for label, (path, expected_error) in forbidden.items():
            with self.subTest(label=label, path=path):
                updates = self.publication_candidate()
                updates[path] = f"forbidden {label}\n"
                proc, payload = self.verify_updates(
                    updates,
                    prefix=f"skipi-guard-seafarer-publication-{label.replace(' ', '-')}-",
                )

                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "fail")
                self.assertTrue(
                    any(expected_error in error for error in payload["errors"]),
                    payload["errors"],
                )
                self.assertNotEqual(payload["task"], PUBLICATION_TASK)

    def test_existing_routes_keep_their_classification_and_acceptance(self) -> None:
        existing_routes = {
            "repo-meta": (
                "repo-meta routing",
                {"AGENTS.md": "fixture agents\n", "CLAUDE.md": "fixture claude\n"},
            ),
            "release": (
                "canonical version-bump routing",
                {
                    "dist/index.html": '<meta name="app-version" content="0.4.179">\n',
                    "src-tauri/Cargo.toml": 'version = "0.4.179"\n',
                    "src-tauri/Cargo.lock": 'version = "0.4.179"\n',
                    "src-tauri/tauri.conf.json": '{"version":"0.4.179"}\n',
                },
            ),
            "settings-adopt": (
                "settings-adopt routing",
                {
                    "dist/index.html": "<main>settings</main>\n",
                    "dist/skipi-settings.js": "export const settings = {};\n",
                    "dist/SETTINGS_VERSION": "1\n",
                    "tests/unified_settings_fallback_harness.mjs": "console.log('ok');\n",
                },
            ),
        }
        for expected_task, (expected_rule, updates) in existing_routes.items():
            with self.subTest(task=expected_task):
                proc, payload = self.verify_updates(
                    updates,
                    prefix=f"skipi-guard-seafarer-existing-{expected_task}-",
                )

                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(payload["status"], "pass")
                self.assertEqual(payload["task"], expected_task)
                self.assertEqual(payload["task_rule"], expected_rule)
                self.assertEqual(payload["scope_violations"], [])


if __name__ == "__main__":
    unittest.main()
