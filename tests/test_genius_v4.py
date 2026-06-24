import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_llm_v4 import genius_v4

CASE = "\n".join([
    "task_id_list\tcourier_id\ttotal_score\twillingness",
    "T0\tC0\t10\t0.9",
    "T0\tC1\t12\t0.5",
    "T1\tC1\t11\t0.8",
    "T1\tC2\t9\t0.4",
    "T2\tC2\t13\t0.7",
    "T2\tC3\t8\t0.6",
])

GOOD = """def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    used, covered, result = set(), set(), []
    for r in sorted(candidates, key=lambda r: r[3]):
        if time_left(deadline) <= 0.02:
            break
        if r[2] in used or any(t in covered for t in r[1]):
            continue
        used.add(r[2]); covered.update(r[1]); result.append((r[0], [r[2]]))
    return result"""

ONLY_ONE = """def propose(candidates, all_tasks, deadline, helpers):
    _ = deadline
    r = sorted(candidates, key=lambda r: r[3])[0]
    return [(r[0], [r[2]])]"""


class TestGenius(unittest.TestCase):
    def test_baseline_greedy(self):
        base = genius_v4.baseline_greedy(CASE)
        self.assertGreater(base["cost"], 0)
        self.assertTrue(base["valid"])

    def test_judge_full_cover_better_than_partial(self):
        base = genius_v4.baseline_greedy(CASE)
        good = genius_v4.judge(GOOD, CASE, base["cost"])
        partial = genius_v4.judge(ONLY_ONE, CASE, base["cost"])
        self.assertTrue(good["valid"])
        self.assertTrue(partial["valid"])  # legal but low coverage
        # full coverage should not be worse than partial (uncovered penalty)
        self.assertLessEqual(good["candidate_cost"], partial["candidate_cost"])
        self.assertEqual(good["coverage"], "3/3")

    def test_judge_rejects_invalid_code(self):
        verdict = genius_v4.judge("import os\n" + GOOD, CASE, 100.0)
        self.assertFalse(verdict["accepted"])
        self.assertFalse(verdict["valid"])


if __name__ == "__main__":
    unittest.main()
