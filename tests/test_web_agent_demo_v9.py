from __future__ import annotations

import unittest


class WebAgentDemoV9Test(unittest.TestCase):
    def test_decision_page_never_lists_future_rounds_or_schedule(self) -> None:
        from web_agent_demo.day_replay_frontend_v9 import render_day_replay_index

        html = render_day_replay_index()

        self.assertIn(
            "const visibleDecisions = workbench.decisions.filter(decisionUnlocked);",
            html,
        )
        self.assertIn("尚无已发生的决策轮", html)
        self.assertIn(
            "return `已发生 ${decisionRoundOrdinal(inferenceState.currentTimeS)} 轮`;",
            html,
        )
        self.assertIn(
            '["决策轮次", decisionRoundOrdinal(inferenceState.currentTimeS)]',
            html,
        )
        self.assertIn('let selectedDecisionId = "";', html)
        self.assertNotIn("将于 ${escapeHtml(item.trigger_time_label)} 触发", html)
        self.assertNotIn("把时间轴推进过 ${escapeHtml(firstLabel)}", html)


if __name__ == "__main__":
    unittest.main()
