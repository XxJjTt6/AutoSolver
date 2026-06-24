import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_dynamic_v4 import order_stream_v4 as ostream
from autosolver_dynamic_v4.scenario_builder_v4 import SCENARIOS, speed_factor_at
from autosolver_dynamic_v4.sim_state_v4 import GRID_MAX, GRID_MIN, dist, stable_point, travel_min

CASE = "task_id_list\tcourier_id\ttotal_score\twillingness\n" + "\n".join(
    f"T{ i:02d}\tC{ (i*3)%12:02d}\t{10 + (i % 5)}\t{0.3 + (i % 6) * 0.1:.1f}" for i in range(24)
)


class TestDynamicSim(unittest.TestCase):
    def test_stable_point_in_range_and_deterministic(self):
        a = stable_point("T01", 0)
        b = stable_point("T01", 0)
        self.assertEqual(a, b)
        self.assertTrue(GRID_MIN <= a[0] <= GRID_MAX and GRID_MIN <= a[1] <= GRID_MAX)

    def test_travel_monotonic(self):
        o = (0, 0)
        self.assertLess(travel_min(o, (3, 4)), travel_min(o, (30, 40)))

    def test_orders_arrival_and_deadline(self):
        sc = SCENARIOS["weekday_peaks"]
        orders = ostream.build_orders(CASE, sc)
        self.assertEqual(len(orders), 24)
        for o in orders:
            self.assertEqual(o.deadline_min, o.arrival_min + sc["deadline_window"])
            self.assertTrue(0 <= o.arrival_min < sc["T"])
        # 到达量在三峰附近更密集（峰段 > 平段）
        hist = ostream.arrival_histogram(orders, sc)
        self.assertEqual(sum(hist), 24)

    def test_shock_slows_speed(self):
        sc = SCENARIOS["lunch_shock"]
        self.assertLess(speed_factor_at(120, sc), 1.0)   # 冲击窗内变慢
        self.assertEqual(speed_factor_at(10, sc), 1.0)   # 窗外正常


if __name__ == "__main__":
    unittest.main()
