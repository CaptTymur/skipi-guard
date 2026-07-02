from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerPresenceConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "configs" / "homes" / "broker.json").open("r", encoding="utf-8") as handle:
            cls.config = json.load(handle)

    def test_presence_manifest_is_protected(self) -> None:
        protected = self.config["protected_paths"]
        self.assertTrue(
            any(
                rule.get("name") == "presence contracts" and "presence-manifest.json" in rule.get("patterns", [])
                for rule in protected
            )
        )

    def test_plugin_host_runs_presence_and_provenance_harnesses(self) -> None:
        harnesses = {
            entry["name"]: entry["command"]
            for entry in self.config["harness_commands"]["plugin-host"]
        }
        self.assertEqual(harnesses["broker_plugin_isolation"], "node tests/broker_plugin_isolation_harness.mjs")
        self.assertEqual(harnesses["broker_build_provenance"], "node tests/build_provenance_harness.mjs")
        self.assertEqual(harnesses["broker_presence_contract"], "node tests/broker_presence_contract_harness.mjs")

    def test_plugin_host_allows_presence_contract_files_but_not_workflow(self) -> None:
        allowed = set(self.config["allowed_file_patterns"]["plugin-host"])
        self.assertIn("presence-manifest.json", allowed)
        self.assertIn("tests/broker_presence_contract_harness.mjs", allowed)
        self.assertNotIn(".github/workflows/skipi-guard.yml", allowed)


if __name__ == "__main__":
    unittest.main()
