"""learning_feed_v2 解析器单测 (会议方案 v4 · B1 验收)。

断言真实数据的统计与诚实口径, 防止后续改动悄悄改坏真值绑定。
独立可跑: python3 web_agent_demo/tests/test_learning_feed_v2.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 让本文件无论从哪运行都能 import 到 web_agent_demo.learning_feed_v2
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from web_agent_demo import learning_feed_v2 as feed  # noqa: E402


class TestLearningFeedV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = feed.build_payload()

    def test_event_counts(self) -> None:
        s = self.payload["stats"]
        self.assertEqual(s["generated"], 7)
        self.assertEqual(s["validated"], 14)
        self.assertEqual(s["trial"], 7)

    def test_all_rejected_is_the_honest_story(self) -> None:
        s = self.payload["stats"]
        self.assertEqual(s["accepted"], 0, "诚实红线: 5 策略全被拒, accepted 必须为 0")
        self.assertEqual(s["reject_quality"], 6)
        self.assertEqual(s["reject_timeout"], 1)

    def test_safety_gate_all_passed(self) -> None:
        # 安全门 14 次校验全过 = 安全门是真的; 拒是质量门拒, 不是安全门拒。
        self.assertTrue(self.payload["stats"]["safety_all_passed"])

    def test_registry_five_strategies_all_rejected(self) -> None:
        strats = self.payload["strategies"]
        self.assertEqual(len(strats), 5)
        self.assertTrue(all(s["accepted"] == 0 for s in strats))
        self.assertTrue(all(s["status"] == "rejected" for s in strats))

    def test_degenerate_trial_flagged(self) -> None:
        # 06-21 的 gen_large_v002 是 1×1 退化算例 (cost=1.0), 必须打 degenerate 标, 不冒充正式对比。
        trials = [e for e in self.payload["events"] if e["event"] == "strategy_trial"]
        degen = [t for t in trials if t.get("degenerate")]
        self.assertEqual(len(degen), 1)
        self.assertEqual(degen[0]["local_cost"], 1.0)
        self.assertIn("冒烟", degen[0].get("cost_note", ""))

    def test_timeout_trial_has_no_cost(self) -> None:
        trials = [e for e in self.payload["events"] if e["event"] == "strategy_trial"]
        timeouts = [t for t in trials if t.get("reason") == "timeout"]
        self.assertEqual(len(timeouts), 1)
        self.assertIsNone(timeouts[0]["local_cost"])

    def test_baselines_official_vs_local_labeled(self) -> None:
        b = self.payload["baselines"]
        self.assertTrue(b["official_case"]["authoritative"])
        self.assertTrue(b["official_total"]["authoritative"])
        self.assertFalse(b["local_realtime"]["authoritative"], "657.104 必须标为非官方")

    def test_regime_not_translated_as_time_peak(self) -> None:
        # regime 真值是规模/特征桶, 严禁翻成早/午/晚高峰、雨天。
        cn_values = "".join(self.payload["regime_cn"].values())
        for forbidden in ("高峰", "雨天", "早餐", "午餐"):
            self.assertNotIn(forbidden, cn_values)
        self.assertEqual(feed.regime_cn("large"), "大单量场景")


if __name__ == "__main__":
    unittest.main(verbosity=2)
