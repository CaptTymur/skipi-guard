from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"


class SkipiGuardRegressionTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)

    def init_repo(self, repo: Path) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-guard@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Guard Fixture")

    def run_guard(
        self, repo: Path, result_json: Path
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        proc = subprocess.run(
            [
                str(GUARD),
                "verify",
                "--home",
                "broker",
                "--task",
                "plugin-host",
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
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def run_home_guard(
        self,
        repo: Path,
        result_json: Path,
        *,
        home: str,
        task: str,
        override: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        command = [
            str(GUARD),
            "verify",
            "--home",
            home,
            "--task",
            task,
            "--repo",
            str(repo),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
            "--json",
            str(result_json),
        ]
        if override:
            command.extend(["--override-protected", override])
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
        )
        with result_json.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def seed_crewing_repo(self, repo: Path) -> None:
        (repo / "dist").mkdir()
        (repo / "tests").mkdir()
        (repo / "dist" / "index.html").write_text("<main>seed</main>\n", encoding="utf-8")
        (repo / "package.json").write_text('{"version":"0.0.0"}\n', encoding="utf-8")
        (repo / "tests" / "build_provenance_harness.mjs").write_text("console.log('seed');\n", encoding="utf-8")
        self.run_git(repo, "add", "dist/index.html", "package.json", "tests/build_provenance_harness.mjs")
        self.run_git(repo, "commit", "-q", "-m", "seed crewing files")

    def commit_files(self, repo: Path, message: str, updates: dict[str, str]) -> None:
        for relative, contents in updates.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", message)

    def test_deleted_protected_and_release_sensitive_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-delete-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "backend").mkdir()
            (repo / "backend" / "prod-data.json").write_text('{"prod": true}\n', encoding="utf-8")
            (repo / "latest.json").write_text('{"latest": "1.0.0"}\n', encoding="utf-8")
            self.run_git(repo, "add", "backend/prod-data.json", "latest.json")
            self.run_git(repo, "commit", "-q", "-m", "seed protected files")

            (repo / "backend" / "prod-data.json").unlink()
            (repo / "latest.json").unlink()
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "delete protected files")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["changed_files"], ["backend/prod-data.json", "latest.json"])
        self.assertTrue(payload["release_changes"])
        touched = payload["protected_paths_touched"]
        self.assertTrue(
            any(entry["path"] == "backend/prod-data.json" and entry["kind"] == "protected" for entry in touched)
        )
        self.assertTrue(
            any(entry["path"] == "latest.json" and entry["kind"] == "release-sensitive" for entry in touched)
        )

    def test_added_protected_and_release_sensitive_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-add-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
            self.run_git(repo, "add", "README.md")
            self.run_git(repo, "commit", "-q", "-m", "seed repo")

            (repo / "backend").mkdir()
            (repo / "backend" / "prod-data.json").write_text('{"prod": true}\n', encoding="utf-8")
            (repo / "latest.json").write_text('{"latest": "1.0.0"}\n', encoding="utf-8")
            self.run_git(repo, "add", "backend/prod-data.json", "latest.json")
            self.run_git(repo, "commit", "-q", "-m", "add protected files")

            proc, payload = self.run_guard(repo, root / "result.json")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["changed_files"], ["backend/prod-data.json", "latest.json"])
        self.assertTrue(payload["protected_paths_touched"])
        self.assertTrue(payload["release_changes"])

    def test_crewing_release_with_plugin_host_files_adds_plugin_host_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-release-plugin-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_crewing_repo(repo)
            self.commit_files(
                repo,
                "release and plugin host",
                {
                    "dist/index.html": "<main>crew flow</main>\n",
                    "package.json": '{"version":"0.0.1"}\n',
                },
            )

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="release")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["effective_tasks"], ["release", "plugin-host"])
        self.assertEqual(payload["scope_violations"], [])
        self.assertEqual(payload["additive_task_checks"][0]["matched_files"], ["dist/index.html"])
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertIn("crewing_crew_flow_demo", harnesses)
        self.assertIn("crewing_plugin_isolation", harnesses)
        self.assertIn("crewing_presence_contract", harnesses)
        self.assertIn("crewing_build_provenance", harnesses)

    def test_crewing_provenance_with_plugin_host_files_adds_plugin_host_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-provenance-plugin-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_crewing_repo(repo)
            self.commit_files(
                repo,
                "provenance and plugin host",
                {
                    "dist/index.html": "<main>provenance plus crew flow</main>\n",
                    "tests/build_provenance_harness.mjs": "console.log('updated');\n",
                },
            )

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="provenance")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["effective_tasks"], ["provenance", "plugin-host"])
        self.assertEqual(payload["scope_violations"], [])
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertIn("crewing_crew_flow_demo", harnesses)
        self.assertIn("crewing_plugin_isolation", harnesses)
        self.assertIn("crewing_presence_contract", harnesses)
        self.assertIn("crewing_build_provenance", harnesses)

    def test_crewing_release_only_diff_does_not_add_plugin_host_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-release-only-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_crewing_repo(repo)
            self.commit_files(repo, "release only", {"package.json": '{"version":"0.0.2"}\n'})

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="release")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["effective_tasks"], ["release"])
        self.assertEqual(payload["additive_task_checks"], [])
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertIn("crewing_crew_flow_demo", harnesses)
        self.assertIn("crewing_plugin_isolation", harnesses)
        self.assertIn("crewing_presence_contract", harnesses)

    def test_crewing_plugin_host_task_keeps_plugin_host_harnesses(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-plugin-only-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_crewing_repo(repo)
            self.commit_files(repo, "plugin host only", {"dist/index.html": "<main>plugin only</main>\n"})

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="plugin-host")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["effective_tasks"], ["plugin-host"])
        harnesses = {entry["name"] for entry in payload["tests"]}
        self.assertEqual(
            harnesses,
            {
                "crewing_plugin_isolation",
                "shared_host_runtime_isolation",
                "crewing_presence_contract",
                "crewing_crew_flow_demo",
            },
        )

    def test_crewing_release_with_disallowed_dist_file_fails_plugin_host_scope(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-crewing-release-bad-dist-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)
            self.seed_crewing_repo(repo)
            self.commit_files(
                repo,
                "release and bad dist",
                {
                    "dist/unreviewed.js": "console.log('bad');\n",
                    "package.json": '{"version":"0.0.3"}\n',
                },
            )

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="release")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["effective_tasks"], ["release", "plugin-host"])
        self.assertEqual(payload["scope_violations"], ["dist/unreviewed.js"])
        self.assertIn("changes outside allowed patterns for task 'plugin-host'", payload["errors"])

    def test_presence_modification_override_rejects_non_presence_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-presence-smuggle-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "dist").mkdir()
            (repo / "presence-manifest.json").write_text('{"contracts":[]}\n', encoding="utf-8")
            (repo / "dist" / "index.html").write_text("<main>seed</main>\n", encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "seed presence")

            (repo / "presence-manifest.json").write_text('{"contracts":["changed"]}\n', encoding="utf-8")
            (repo / "dist" / "index.html").write_text("<main>smuggled</main>\n", encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "presence plus dist")

            proc, payload = self.run_home_guard(
                repo,
                root / "result.json",
                home="crewing",
                task="release",
                override="crewing-presence-modification-approved",
            )

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("presence override requires presence-only changes", payload["errors"])
        self.assertTrue(any("dist/index.html" in error for error in payload["errors"]))

    def test_presence_modification_override_allows_presence_only_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-presence-only-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "presence-manifest.json").write_text('{"contracts":[]}\n', encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "seed presence")

            (repo / "presence-manifest.json").write_text('{"contracts":["changed"]}\n', encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "presence only")

            proc, payload = self.run_home_guard(
                repo,
                root / "result.json",
                home="crewing",
                task="release",
                override="crewing-presence-modification-approved",
            )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["scope_violations"], [])

    def test_release_task_rejects_non_release_non_additive_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-release-src-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "package.json").write_text('{"version":"0.0.0"}\n', encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "seed release")

            (repo / "src").mkdir()
            (repo / "package.json").write_text('{"version":"0.0.1"}\n', encoding="utf-8")
            (repo / "src" / "side.js").write_text("console.log('smuggled');\n", encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "release plus src")

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="release")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("src/side.js", payload["scope_violations"])
        self.assertIn("changes outside allowed patterns for task 'release'", payload["errors"])

    def test_unknown_task_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-guard-unknown-task-") as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.init_repo(repo)

            (repo / "dist").mkdir()
            (repo / "dist" / "index.html").write_text("<main>seed</main>\n", encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "seed dist")

            (repo / "dist" / "index.html").write_text("<main>changed</main>\n", encoding="utf-8")
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-q", "-m", "dist change")

            proc, payload = self.run_home_guard(repo, root / "result.json", home="crewing", task="typo-task")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("unknown or unconfigured task 'typo-task'", payload["errors"])


if __name__ == "__main__":
    unittest.main()
