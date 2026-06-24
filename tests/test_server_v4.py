import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web_agent_demo import server_v4


class TestServerV4(unittest.TestCase):
    def test_scenarios(self):
        r = server_v4.get_scenarios()
        self.assertEqual(r["status"], "ok")
        self.assertTrue(any(s["id"] == "weekday_peaks" for s in r["scenarios"]))

    def test_dynamic_demo_cache(self):
        r = server_v4.get_dynamic("large_seed301", "weekday_peaks", live=False)
        self.assertIn("steps", r)
        self.assertGreater(len(r["steps"]), 5)
        self.assertIn("greedy", r["steps"][0]["lanes"])

    def test_lineage_and_events(self):
        lin = server_v4.get_lineage()
        self.assertIn("lineage", lin)
        self.assertGreaterEqual(lin["accepted_count"], 1)
        ev = server_v4.get_events()
        self.assertEqual(ev["status"], "ok")
        self.assertTrue(any(e["type"] == "judge" for e in ev["events"]))

    def test_commentary(self):
        r = server_v4.get_commentary("weekday_peaks")
        self.assertIn("by_tick", r)
        if r["by_tick"]:
            any_c = next(iter(r["by_tick"].values()))
            self.assertIn("text", any_c)
            self.assertIn("phase", any_c)

    def test_index_has_mounts(self):
        html = server_v4.render_index()
        for token in ("mapL", "mapR", "costChart", "ribbon", "flow_route_v4.js", "dashboard_v4.js"):
            self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
