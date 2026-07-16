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

    def test_settings_adopt_runs_the_full_plugin_host_harness_set(self) -> None:
        """BACKLOG п.47: settings-adopt is fail-closed with the same three
        harnesses as plugin-host — no weaker gate for the adopt path."""
        plugin_host = {
            entry["name"]: entry["command"]
            for entry in self.config["harness_commands"]["plugin-host"]
        }
        settings_adopt = {
            entry["name"]: entry["command"]
            for entry in self.config["harness_commands"]["settings-adopt"]
        }
        self.assertEqual(settings_adopt, plugin_host)

    def test_settings_adopt_allowlist_is_exactly_wiring_plus_vendored_module(self) -> None:
        """BACKLOG п.47: only the index.html wiring and the vendored
        dist/skipi-settings* module bytes; nothing else (no presence manifest,
        no harness files, no workflow)."""
        allowed = self.config["allowed_file_patterns"]["settings-adopt"]
        self.assertEqual(sorted(allowed), ["dist/index.html", "dist/skipi-settings*"])


if __name__ == "__main__":
    unittest.main()
