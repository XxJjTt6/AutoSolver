import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_dynamic_v4 import rolling_solver_v4 as rs

CASE = "task_id_list\tcourier_id\ttotal_score\twillingness\n" + "\n".join(
    f"T{i:02d}\tC{c:02d}\t{8 + ((i + c) % 7)}\t{0.3 + ((i + c) % 6) * 0.1:.1f}"
    for i in range(18) for c in range(i % 4, (i % 4) + 3)
)


class TestDynamicCompare(unittest.TestCase):
    def test_three_lanes_same_window_and_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            res = rs.simulate(CASE, "weekday_peaks", state_root=Path(td), pack_root=Path(td))  # 空记忆 → warm==cold
        self.assertIn("steps", res)
        self.assertTrue(len(res["steps"]) > 5)
        for step in res["steps"]:
            self.assertEqual(set(step["lanes"].keys()), {"greedy", "cold", "warm"})
            for lane in step["lanes"].values():
                for key in ("total_cost", "coverage", "avg_cost_per_order", "on_time_rate", "avg_eta_min"):
                    self.assertIn(key, lane["metrics"])
        # 冻结单调：每泳道 assigned 数随 tick 不减
        for lane in ("greedy", "cold", "warm"):
            seq = [s["lanes"][lane]["metrics"]["assigned"] for s in res["steps"]]
            self.assertEqual(seq, sorted(seq))
        fin = res["summary"]["final"]
        # warm 不差于 cold（warm = default ∪ recall 取更优）
        self.assertLessEqual(fin["warm"]["avg_cost_per_order"], fin["cold"]["avg_cost_per_order"] + 1e-6)

    def test_shock_scenario_runs(self):
        with tempfile.TemporaryDirectory() as td:
            res = rs.simulate(CASE, "lunch_shock", state_root=Path(td), pack_root=Path(td))
        self.assertTrue(any(s["speed_factor"] < 1.0 for s in res["steps"]))  # 有扰动窗


if __name__ == "__main__":
    unittest.main()
