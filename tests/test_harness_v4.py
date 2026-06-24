import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_llm_v4 import genius_v4, harness_v4, llm_client_v4, prompts_v4, tools_v4
from autosolver_llm_v4.teacher_v4 import Teacher

CASE = "\n".join([
    "task_id_list\tcourier_id\ttotal_score\twillingness",
    "T0\tC0\t10\t0.9",
    "T1\tC1\t9\t0.8",
    "T2\tC2\t8\t0.7",
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


class TestHarness(unittest.TestCase):
    def test_intent_required_then_full_loop(self):
        scripts = [
            "<tool name=\"profile_case\"></tool>",  # 缺 intent -> 被要求补
            "<intent>看画像</intent>\n<tool name=\"profile_case\"></tool>",
            f"<intent>写草稿</intent>\n<tool name=\"draft_strategy\"><code>\n{GOOD}\n</code></tool>",
            "<intent>提交（应被拦：必须先 smoke）</intent>\n<final><hypothesis>h</hypothesis><summary>s</summary></final>",
            "<intent>烟测</intent>\n<tool name=\"smoke_test_strategy\"></tool>",
            "<intent>提交</intent>\n<final><hypothesis>greedy</hypothesis><summary>done</summary></final>",
        ]
        client = llm_client_v4.FakeModelClient(scripts)
        base = genius_v4.baseline_greedy(CASE)
        ctx = tools_v4.RoundContext(CASE, base["cost"])
        teacher = Teacher()
        sys_prompt = prompts_v4.build_system_prompt(teacher)
        header = prompts_v4.build_round_header(1, ctx.regime, base["cost"], None, teacher.checklist(ctx.regime))
        events = []
        res = harness_v4.run_round(client, ctx, sys_prompt, header, tools_v4.ToolRegistry(),
                                   memory=None, round_idx=1, emit=events.append)
        self.assertTrue(res.ok)
        self.assertIn("propose", res.code)
        self.assertEqual(res.hypothesis, "greedy")
        types = [e["type"] for e in events]
        self.assertIn("smoke", types)
        self.assertIn("patch", types)

    def test_parse_output_variants(self):
        kind, payload = harness_v4.parse_output("<final><hypothesis>a</hypothesis><summary>b</summary></final>")
        self.assertEqual(kind, "final")
        self.assertEqual(payload["hypothesis"], "a")
        kind, payload = harness_v4.parse_output('<tool name="smoke_test_strategy"></tool>')
        self.assertEqual(kind, "tool")
        self.assertEqual(payload["name"], "smoke_test_strategy")
        kind, payload = harness_v4.parse_output('<tool name="memory_search"><query>scarce</query></tool>')
        self.assertEqual(payload["args"]["query"], "scarce")


if __name__ == "__main__":
    unittest.main()
