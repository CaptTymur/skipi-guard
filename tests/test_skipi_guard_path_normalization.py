from __future__ import annotations

import importlib.machinery
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "bin" / "skipi-guard"
skipi_guard = importlib.machinery.SourceFileLoader("skipi_guard_bin", str(GUARD)).load_module()


class SkipiGuardPathNormalizationTests(unittest.TestCase):
    def test_clean_path_preserves_dot_paths(self) -> None:
        cases = {
            ".github/workflows/skipi-guard.yml": ".github/workflows/skipi-guard.yml",
            ".env": ".env",
            ".env.local": ".env.local",
            "../outside": "../outside",
            "github/workflows/skipi-guard.yml": "github/workflows/skipi-guard.yml",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(skipi_guard.clean_path(raw), expected)

    def test_clean_path_strips_only_leading_dot_slash_prefix(self) -> None:
        cases = {
            "./dist/index.html": "dist/index.html",
            "./.github/workflows/skipi-guard.yml": ".github/workflows/skipi-guard.yml",
            "./.env": ".env",
            r".github\workflows\skipi-guard.yml": ".github/workflows/skipi-guard.yml",
            r".\github\workflows\skipi-guard.yml": "github/workflows/skipi-guard.yml",
            r".\dist\index.html": "dist/index.html",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(skipi_guard.clean_path(raw), expected)

    def test_dot_and_non_dot_paths_remain_distinct(self) -> None:
        self.assertNotEqual(
            skipi_guard.clean_path(".github/workflows/skipi-guard.yml"),
            skipi_guard.clean_path("github/workflows/skipi-guard.yml"),
        )
        self.assertNotEqual(skipi_guard.clean_path(".env"), skipi_guard.clean_path("env"))


if __name__ == "__main__":
    unittest.main()
