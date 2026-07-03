from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CrewingPresenceConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "configs" / "homes" / "crewing.json").open("r", encoding="utf-8") as handle:
            cls.config = json.load(handle)

    def test_presence_manifest_is_protected(self) -> None:
        protected = self.config["protected_paths"]
        self.assertTrue(
            any(
                rule.get("name") == "presence contracts" and "presence-manifest.json" in rule.get("patterns", [])
                for rule in protected
            )
        )

    def test_plugin_host_runs_presence_harness(self) -> None:
        harnesses = {
            entry["name"]: entry["command"]
            for entry in self.config["harness_commands"]["plugin-host"]
        }
        self.assertEqual(harnesses["crewing_plugin_isolation"], "node tests/crewing_plugin_isolation_harness.mjs")
        self.assertEqual(
            harnesses["shared_host_runtime_isolation"],
            "node /home/linux/Developer/skipi-plugins/_host-runtime/harness/isolation-contract.mjs",
        )
        self.assertEqual(harnesses["crewing_presence_contract"], "node tests/crewing_presence_contract_harness.mjs")

    def test_plugin_host_allows_presence_contract_files_but_not_workflow(self) -> None:
        allowed = set(self.config["allowed_file_patterns"]["plugin-host"])
        self.assertIn("presence-manifest.json", allowed)
        self.assertIn("tests/crewing_presence_contract_harness.mjs", allowed)
        self.assertNotIn(".github/workflows/skipi-guard.yml", allowed)


if __name__ == "__main__":
    unittest.main()
