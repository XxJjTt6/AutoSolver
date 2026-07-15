from __future__ import annotations

import unittest


class WebAgentDemoV8Test(unittest.TestCase):
    def test_decision_advantage_headline_labels_cumulative_savings(self) -> None:
        from web_agent_demo.day_replay_frontend_v8 import render_day_replay_index

        html = render_day_replay_index()

        self.assertIn(
            "return `累计节省 ${fmtNumber(result.time_saved_min || 0, 1)} 分钟`;",
            html,
        )
        self.assertNotIn(
            "return `本轮节省 ${fmtNumber(result.time_saved_min || 0, 1)} 分钟`;",
            html,
        )


if __name__ == "__main__":
    unittest.main()
