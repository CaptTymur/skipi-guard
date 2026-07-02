from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SeafarerThemeConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "configs" / "homes" / "seafarer.json").open("r", encoding="utf-8") as handle:
            cls.config = json.load(handle)

    def test_plugin_host_runs_theme_default_harness(self) -> None:
        harnesses = {
            entry["name"]: entry["command"]
            for entry in self.config["harness_commands"]["plugin-host"]
        }
        self.assertEqual(harnesses["seafarer_theme_default"], "node tests/seafarer_theme_default_harness.mjs")

    def test_plugin_host_allows_theme_harness_but_not_workflow(self) -> None:
        allowed = set(self.config["allowed_file_patterns"]["plugin-host"])
        self.assertIn("tests/seafarer_theme_default_harness.mjs", allowed)
        self.assertNotIn(".github/workflows/skipi-guard.yml", allowed)


if __name__ == "__main__":
    unittest.main()
