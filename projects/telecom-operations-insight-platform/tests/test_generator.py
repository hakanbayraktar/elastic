#!/usr/bin/env python3
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator"))
from generate_capstone import KINDS, SCENARIOS, build_events, iter_bulk


class CapstoneGeneratorTests(unittest.TestCase):
    def test_each_request_has_five_correlated_application_sources(self):
        run_id, docs = build_events("normal", 20, "unit-run", datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(run_id, "unit-run")
        self.assertEqual(len(docs), 20 * 5 + 2 * 4)
        for n in (1, 10, 20):
            trace = f"capstone-trace-{run_id}-{n:06d}"
            group = [doc for doc in docs if doc["trace"]["id"] == trace]
            kinds = {doc["labels"]["source_kind"] for doc in group}
            self.assertTrue(set(KINDS) <= kinds)
            self.assertEqual(len({doc["labels"]["request_id"] for doc in group if doc["labels"]["source_kind"] in KINDS}), 1)

    def test_incident_scenarios_exceed_error_threshold(self):
        for scenario in ("high-5xx", "surge"):
            _, docs = build_events(scenario, 100, "incident")
            proxy = [d for d in docs if d["labels"]["source_kind"] == "proxy"]
            failures = sum(d["temp"]["status"] in ("500", "503") for d in proxy)
            self.assertGreater(failures / len(proxy), 0.05)

    def test_all_scenarios_and_bulk_metadata(self):
        for scenario in SCENARIOS:
            _, docs = build_events(scenario, 10, "bulk")
            lines = list(iter_bulk(docs, "logs-telecom.capstone-prod"))
            self.assertEqual(len(lines), 2 * len(docs))
            self.assertEqual(lines[0], '{"create":{"_index":"logs-telecom.capstone-prod"}}')
            self.assertIn('"training_profile":"capstone"', lines[1])
            self.assertIn("@example.test", lines[1])

    def test_request_bounds_and_invalid_scenario(self):
        with self.assertRaises(ValueError):
            build_events("unknown", 10)
        for count in (9, 10001):
            with self.assertRaises(ValueError):
                build_events("normal", count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
