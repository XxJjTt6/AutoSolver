import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_llm_v4 import evolution_runner_v4 as runner

CASE = "\n".join([
    "task_id_list\tcourier_id\ttotal_score\twillingness",
    "T0\tC0\t10\t0.9",
    "T0\tC1\t12\t0.5",
    "T1\tC1\t11\t0.8",
    "T1\tC2\t9\t0.4",
    "T2\tC2\t13\t0.7",
    "T2\tC3\t8\t0.6",
    "T3\tC3\t7\t0.5",
    "T3\tC0\t14\t0.3",
])


class TestRunnerFake(unittest.TestCase):
    def test_fake_run_produces_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            res = runner.run(
                provider="fake", rounds=3, case="tiny_test", case_text=CASE,
                run_id="t1", with_production=False,
                mgr_root=td / "state", runs_root=td / "runs", mem_root=td / "mem",
            )
            self.assertEqual(res["provider"], "fake")
            self.assertEqual(len(res["lineage"]), 3)
            # events 落盘可供前端回放
            events = (td / "runs" / "t1" / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("round_start", events)
            self.assertIn("judge", events)
            # registry 桥接：strategy_registry.json 真实生成
            reg = json.loads((td / "state" / "strategy_registry.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(reg), 3)
            # 至少有一轮被裁决（accepted 或 rejected 都行，关键是 pipeline 通）
            outcomes = {x["accepted"] for x in res["lineage"]}
            self.assertTrue(outcomes)
            # episodes B 层
            eps = (td / "mem" / "runs").glob("**/episodes.jsonl")
            self.assertTrue(any(eps))


if __name__ == "__main__":
    unittest.main()
