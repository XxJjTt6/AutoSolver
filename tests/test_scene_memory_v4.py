import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_dynamic_v4.scene_memory_v4 import SceneMemory

STRAT = """def propose(candidates, all_tasks, deadline, helpers):
    _ = deadline
    return []"""


class TestSceneMemory(unittest.TestCase):
    def test_disabled_recall_empty(self):
        sm = SceneMemory(enabled=False)
        self.assertEqual(sm.recall("large"), [])

    def test_recall_from_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gen = root / "generated_strategies"
            gen.mkdir(parents=True)
            sp = gen / "gen_llm_large_v001.py"
            sp.write_text(STRAT, encoding="utf-8")
            reg = {"gen_llm_large_v001": {
                "status": "promoted", "target_regime": "large", "accepted": 1,
                "last_cost": 1048.77, "file": str(sp),
            }, "rejected_one": {"status": "rejected", "target_regime": "large", "accepted": 0, "file": str(sp)}}
            (root / "strategy_registry.json").write_text(json.dumps(reg), encoding="utf-8")
            sm = SceneMemory(state_root=root, pack_root=root, enabled=True)  # root 无 manifest → 只读 registry
            hits = sm.recall("large")
            self.assertEqual(len(hits), 1)  # 只召回 accepted>0 的
            self.assertEqual(hits[0][0], "gen_llm_large_v001")
            self.assertIn("def propose", hits[0][1])
            self.assertEqual(sm.recall("scarce"), [])  # 该 regime 无记忆


if __name__ == "__main__":
    unittest.main()
