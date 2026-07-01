from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "bin" / "skipi-report-verify"


class SkipiReportVerifyTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)

    def init_repo(self, repo: Path, main_branch: bool = False) -> None:
        self.run_git(repo, "init", "-q")
        self.run_git(repo, "config", "user.email", "skipi-verifier@example.invalid")
        self.run_git(repo, "config", "user.name", "Skipi Verifier Fixture")
        if main_branch:
            self.run_git(repo, "checkout", "-q", "-b", "main")

    def write_fixture_files(self, root: Path, report: dict[str, Any], guard: dict[str, Any]) -> tuple[Path, Path, Path]:
        report_path = root / "report.json"
        guard_path = root / "guard.json"
        verify_path = root / "verify.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        guard_path.write_text(json.dumps(guard, indent=2) + "\n", encoding="utf-8")
        return report_path, guard_path, verify_path

    def run_verify(self, root: Path, report: dict[str, Any], guard: dict[str, Any]) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        report_path, guard_path, verify_path = self.write_fixture_files(root, report, guard)
        proc = subprocess.run(
            [
                str(VERIFY),
                "--report",
                str(report_path),
                "--guard-result",
                str(guard_path),
                "--json",
                str(verify_path),
            ],
            text=True,
            capture_output=True,
        )
        with verify_path.open("r", encoding="utf-8") as handle:
            return proc, json.load(handle)

    def make_repo_fixture(
        self,
        root: Path,
        changed_files: list[str] | None = None,
        release: bool = False,
        test_status: str = "pass",
        main_branch: bool = False,
    ) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        repo = root / "repo"
        repo.mkdir()
        self.init_repo(repo, main_branch=main_branch)

        (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
        self.run_git(repo, "add", "README.md")
        self.run_git(repo, "commit", "-q", "-m", "seed")

        files = changed_files or ["dist/index.html"]
        for file_path in files:
            path = repo / file_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{file_path}\n", encoding="utf-8")
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-q", "-m", "feature change")

        sha = self.run_git(repo, "rev-parse", "--short=12", "HEAD").stdout.strip()
        release_touches = []
        if release:
            release_touches = [
                {
                    "path": "package.json",
                    "kind": "release-sensitive",
                    "rule": "versions/tags",
                    "pattern": "package.json",
                }
            ]
        report = {
            "schema_version": "skipi-report.v1",
            "task": "plugin-host",
            "home": "broker",
            "claimed_rung": "local",
            "repo": str(repo),
            "branch": "feature/report-verifier-fixture",
            "sha": sha,
            "files": files,
            "tests": [{"name": "fixture_tests", "claimed": "pass"}],
            "scope_assertion": "no release/backend/catalog/latest/version/tag changes",
            "protected_paths_touched": release_touches,
        }
        guard = {
            "schema_version": "skipi-guard.v1",
            "home": "broker",
            "task": "plugin-host",
            "repo": str(repo),
            "base": "HEAD~1",
            "head": "HEAD",
            "sha": sha,
            "changed_files": files,
            "protected_paths_touched": release_touches,
            "release_paths_touched": release_touches,
            "release_changes": release,
            "tests": [
                {
                    "name": "fixture_tests",
                    "command": "pytest",
                    "status": test_status,
                    "summary": "synthetic fixture",
                }
            ],
            "status": "fail" if test_status == "fail" else "pass",
            "errors": ["synthetic test failure"] if test_status == "fail" else [],
        }
        return repo, report, guard

    def assert_failed_with(self, payload: dict[str, Any], code: str) -> None:
        self.assertEqual(payload["schema_version"], "skipi-verifier.v1")
        self.assertEqual(payload["status"], "fail")
        self.assertIn(code, self.mismatch_codes(payload))

    def mismatch_codes(self, payload: dict[str, Any]) -> set[str]:
        return {entry["code"] for entry in payload["mismatches"]}

    def test_positive_verification_demo_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-pass-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root)
            proc, payload = self.run_verify(root, report, guard)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["claimed_rung"], "local")
        self.assertEqual(payload["verified_rung"], "local")
        self.assertEqual(payload["mismatches"], [])

    def test_claimed_sha_differs_from_git_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-sha-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root)
            report["sha"] = "deadbee"
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "sha_mismatch")

    def test_report_and_guard_sha_stale_from_git_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-stale-sha-") as tmp:
            root = Path(tmp)
            repo, report, guard = self.make_repo_fixture(root)
            stale_sha = self.run_git(repo, "rev-parse", "--short=12", "HEAD~1").stdout.strip()
            report["sha"] = stale_sha
            guard["sha"] = stale_sha
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        codes = self.mismatch_codes(payload)
        self.assertIn("sha_mismatch", codes)
        self.assertIn("guard_sha_mismatch", codes)

    def test_report_sha_full_sha_with_trailing_text_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-report-sha-superstring-") as tmp:
            root = Path(tmp)
            repo, report, guard = self.make_repo_fixture(root)
            full_sha = self.run_git(repo, "rev-parse", "HEAD").stdout.strip()
            report["sha"] = f"{full_sha}notasha"
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "sha_mismatch")

    def test_guard_sha_full_sha_with_trailing_text_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-guard-sha-superstring-") as tmp:
            root = Path(tmp)
            repo, report, guard = self.make_repo_fixture(root)
            full_sha = self.run_git(repo, "rev-parse", "HEAD").stdout.strip()
            guard["sha"] = f"{full_sha}notasha"
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "guard_sha_mismatch")

    def test_non_hex_report_sha_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-non-hex-sha-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root)
            report["sha"] = "zzzzzzz"
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "sha_mismatch")

    def test_claimed_files_omit_changed_file_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-files-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root, changed_files=["dist/index.html", "tests/harness.js"])
            report["files"] = ["dist/index.html"]
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "files_mismatch")

    def test_report_and_guard_omit_git_changed_file_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-guard-files-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(
                root,
                changed_files=["dist/index.html", "tests/harness.js"],
            )
            report["files"] = ["dist/index.html"]
            guard["changed_files"] = ["dist/index.html"]
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        codes = self.mismatch_codes(payload)
        self.assertIn("files_mismatch", codes)
        self.assertIn("guard_files_mismatch", codes)

    def test_no_release_claim_with_version_file_change_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-release-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root, changed_files=["package.json"], release=True)
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "release_claim_mismatch")
        self.assert_failed_with(payload, "version_tag_claim_mismatch")

    def test_omitted_release_sensitive_git_file_still_fails_claims(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-omitted-release-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(
                root,
                changed_files=["dist/index.html", "package.json"],
            )
            report["files"] = ["dist/index.html"]
            report["protected_paths_touched"] = []
            guard["changed_files"] = ["dist/index.html"]
            guard["protected_paths_touched"] = []
            guard["release_paths_touched"] = []
            guard["release_changes"] = False
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        codes = self.mismatch_codes(payload)
        self.assertIn("files_mismatch", codes)
        self.assertIn("guard_files_mismatch", codes)
        self.assertIn("guard_protected_paths_mismatch", codes)
        self.assertIn("protected_paths_mismatch", codes)
        self.assertIn("release_claim_mismatch", codes)
        self.assertIn("version_tag_claim_mismatch", codes)

    def test_pr_ready_claim_without_pr_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-pr-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root)
            report["claimed_rung"] = "pr_ready"
            report.pop("pr", None)
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "pr_missing")

    def test_merged_claim_sha_not_in_main_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-merged-") as tmp:
            root = Path(tmp)
            repo, report, guard = self.make_repo_fixture(root, main_branch=True)
            self.run_git(repo, "branch", "feature/report-verifier-fixture")
            self.run_git(repo, "checkout", "-q", "main")
            self.run_git(repo, "reset", "--hard", "-q", "HEAD~1")
            self.run_git(repo, "checkout", "-q", "feature/report-verifier-fixture")
            report["claimed_rung"] = "merged"
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "merged_sha_not_in_main")

    def test_test_claim_pass_with_guard_fail_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="skipi-report-verify-test-") as tmp:
            root = Path(tmp)
            _repo, report, guard = self.make_repo_fixture(root, test_status="fail")
            proc, payload = self.run_verify(root, report, guard)

        self.assertNotEqual(proc.returncode, 0)
        self.assert_failed_with(payload, "test_claim_mismatch")


if __name__ == "__main__":
    unittest.main()
