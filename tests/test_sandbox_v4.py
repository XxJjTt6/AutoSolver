import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_llm_v4 import sandbox_v4

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


class TestSandbox(unittest.TestCase):
    def test_good_passes(self):
        ok, reason = sandbox_v4.safety_check_code(GOOD)
        self.assertTrue(ok, reason)

    def test_allow_from_collections_import(self):
        code = "from collections import defaultdict\ndef propose(candidates, all_tasks, deadline, helpers):\n    _ = deadline\n    return list(defaultdict(list).items())"
        ok, reason = sandbox_v4.safety_check_code(code)
        self.assertTrue(ok, reason)

    def test_reject_import_os(self):
        ok, reason = sandbox_v4.safety_check_code("import os\n" + GOOD)
        self.assertFalse(ok)
        self.assertIn("unsafe import", reason)

    def test_reject_while(self):
        bad = GOOD.replace("    for r in", "    while True:\n        break\n    for r in")
        ok, reason = sandbox_v4.safety_check_code(bad)
        self.assertFalse(ok)
        self.assertIn("while", reason)

    def test_reject_eval(self):
        ok, reason = sandbox_v4.safety_check_code("def propose(candidates, all_tasks, deadline, helpers):\n    return eval('[]')")
        self.assertFalse(ok)

    def test_reject_bad_signature(self):
        ok, reason = sandbox_v4.safety_check_code("def propose(a, b):\n    deadline=0\n    return []")
        self.assertFalse(ok)
        self.assertIn("signature", reason)

    def test_reject_missing_propose(self):
        ok, reason = sandbox_v4.safety_check_code("def foo():\n    return []")
        self.assertFalse(ok)

    def test_run_propose_executes(self):
        candidates = [("T0", ("T0",), "C0", 10.0, 0.9, 0), ("T1", ("T1",), "C1", 9.0, 0.8, 1)]
        all_tasks = {"T0", "T1"}
        out = sandbox_v4.run_propose(GOOD, candidates, all_tasks, time_budget_s=1.0)
        self.assertTrue(out["ok"], out["reason"])
        self.assertEqual(len(out["solution"]), 2)


if __name__ == "__main__":
    unittest.main()
