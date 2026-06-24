"""system prompt / round header 构建。

输出协议（文本协议，不依赖原生 function-calling，DeepSeek-chat 跑得稳）：
每一步先 <intent>…</intent>（≤200字：做什么/为什么/期望信号），紧跟 恰好一个：
  <tool name="profile_case"></tool>
  <tool name="memory_search"><query>关键词</query></tool>
  <tool name="list_strategy_templates"></tool>
  <tool name="read_current_best_strategy"></tool>
  <tool name="draft_strategy"><code>...完整 propose() 代码...</code></tool>
  <tool name="smoke_test_strategy"></tool>
或收尾：
  <final><hypothesis>本轮假设一句话</hypothesis><summary>结果与下一步</summary></final>
硬性：draft_strategy 之后必须先 smoke_test_strategy 才能 <final>。
"""
from __future__ import annotations

_IDENTITY = """你是 AutoSolver 的 Fool 角色：一个通过"读经验→改策略→本地烟测→交确定性 Critic 打分→写记忆"的迭代式 AI Agent，目标是为即时配送派单问题写出更好的 propose() 策略。
你不是一次写完，而是站在当前最优基础上提出**一个**小改进假设、验证、再迭代。Critic（Genius）是确定性评测器，是绝对真理；不要自己宣称分数。"""

_PROTOCOL = """## 输出协议（严格遵守，否则被拒绝重来）
每一步：先一行 <intent>…</intent>（≤200字，说清 做什么/为什么/期望什么信号），紧跟**恰好一个**动作：
- <tool name="profile_case"></tool>                      读当前算例画像
- <tool name="memory_search"><query>词</query></tool>    检索历史经验（提新假设前建议先搜）
- <tool name="list_strategy_templates"></tool>          看可参考的策略模板
- <tool name="read_current_best_strategy"></tool>       读当前最优 propose() 全文
- <tool name="draft_strategy"><code>...完整 propose 代码...</code></tool>  写/改策略到草稿
- <tool name="smoke_test_strategy"></tool>              本地烟测当前草稿（预览，非最终分）
收尾：<final><hypothesis>一句话假设</hypothesis><summary>结果与下一步</summary></final>
铁律：① 每步必须有 <intent>；② draft 之后必须 smoke 一次才能 final；③ 一步只做一个动作。"""

_CANDIDATE_FMT = """## 数据与函数契约（逐字记住）
candidate 行 = (task_key:str, task_ids:tuple, courier_id:str, score:float, willingness:float, row_index:int)
即 row[0]=task_key, row[1]=task_ids元组, row[2]=courier_id, row[3]=score(罚分,越低越好), row[4]=willingness(0~1), row[5]=行号。
你只能写：def propose(candidates, all_tasks, deadline, helpers) -> list[tuple[str, list[str]]]
- task_key 必须来自候选行原文；不得重复用 courier；不得重复覆盖 task；尽量覆盖 all_tasks（未覆盖重罚）。
- 只能 import：collections/heapq/itertools/math/random/time；禁 while；用 helpers['time_left'](deadline)<=0.02 截断。"""


def build_system_prompt(teacher) -> str:
    parts = [
        _IDENTITY,
        _CANDIDATE_FMT,
        _PROTOCOL,
        "## 策略 Playbook（Teacher 知识库）\n" + teacher.playbook(),
    ]
    return "\n\n".join(p.strip() for p in parts)


def build_round_header(
    round_idx: int,
    regime: str,
    baseline_cost: float,
    best_cost: float | None,
    teacher_checklist: str,
    memory_hits: list[dict] | None = None,
    prior_summary: str | None = None,
    teacher_review: str | None = None,
) -> str:
    lines = [
        f"# 第 {round_idx} 轮",
        f"- 场景 regime = {regime}",
        f"- 贪心基线成本（要打败它）= {baseline_cost:.2f}",
        f"- 当前最优成本 best-so-far = {('%.2f' % best_cost) if best_cost is not None else '（还没有，先做一个能通过的可行解）'}",
        "- 目标：提出并验证**一个**小改进假设，让 Genius 全量裁决的成本 ≤ 基线。",
    ]
    if prior_summary:
        lines.append(f"\n上一轮小结：{prior_summary}")
    if teacher_review:
        lines.append(f"\nTeacher 复盘（停滞触发）：\n{teacher_review}")
    if memory_hits:
        lines.append("\n相关记忆（来自历史轮次，可用 memory_get 细看）：")
        for h in memory_hits[:4]:
            lines.append(f"- [{h['meta'].get('section')}] {h['meta'].get('title')} (score={h.get('score')})")
    lines.append("\n" + teacher_checklist)
    lines.append("\n现在开始：先 <intent>，再调用第一个工具（建议 profile_case 或 read_current_best_strategy）。")
    return "\n".join(lines)
