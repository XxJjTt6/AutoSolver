"""autosolver_llm_v4 — 时钟 A：离线 LLM 自进化闭环（DeepSeek）。

四角色 Genius/Fool/Teacher/Frontend 的离线学习轨道实现：
- llm_client_v4 : DeepSeek（OpenAI 兼容）+ FakeModelClient（无 key/断网可跑）
- sandbox_v4    : AST 安全门 + 受限执行 propose()
- genius_v4     : 确定性 Critic（封装 solver.py 的 _solution_expected_cost）
- memory_v4     : 三层记忆 A/B/C + 轻量 BM25
- teacher_v4    : 策略护栏 + 停滞复盘
- prompts_v4    : system prompt / round header
- tools_v4      : Fool 工具集（= 安全边界）
- harness_v4    : 单轮 run_round 工具循环（intent/smoke gate/final）
- evolution_runner_v4 : 多轮离线进化入口，产真实 lineage

正式 solver.py 热路径零改动；本包只在离线轨道运行。
"""

__all__ = [
    "llm_client_v4",
    "sandbox_v4",
    "genius_v4",
    "memory_v4",
    "teacher_v4",
    "prompts_v4",
    "tools_v4",
    "harness_v4",
    "evolution_runner_v4",
]
