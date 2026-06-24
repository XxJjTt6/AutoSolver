"""Fool 工具集 v4 —— LLM 只能在这些工具里活动（= 安全边界）。"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_llm_v4 import genius_v4, sandbox_v4  # noqa: E402
from tools.agent_trace_demo import infer_regime, parse_candidates, summarize_solution  # noqa: E402

_MIN_EXAMPLE = """def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    used, covered, result = set(), set(), []
    rows = sorted(candidates, key=lambda r: (len(r[1]), r[3] / max(r[4], 0.001), r[3]))
    for task_key, task_ids, courier_id, score, willingness, _ in rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if courier_id in used:
            continue
        if any(t in covered for t in task_ids):
            continue
        used.add(courier_id); covered.update(task_ids)
        result.append((task_key, [courier_id]))
        if covered >= set(all_tasks):
            break
    return result"""


class RoundContext:
    def __init__(self, case_text: str, baseline_cost: float, memory=None,
                 best_code: str | None = None, smoke_budget_s: float = 2.5) -> None:
        self.case_text = case_text
        self.candidates, self.all_tasks = parse_candidates(case_text)
        self.regime = infer_regime(self.candidates, self.all_tasks)
        self.baseline_cost = baseline_cost
        self.memory = memory
        self.best_code = best_code
        self.draft_code = best_code
        self.smoke_budget_s = smoke_budget_s
        self.smoke_result: dict | None = None

    def profile(self) -> dict:
        couriers = len({r[2] for r in self.candidates})
        avg_w = sum(r[4] for r in self.candidates) / len(self.candidates) if self.candidates else 0.0
        return {
            "tasks": len(self.all_tasks), "couriers": couriers, "rows": len(self.candidates),
            "avg_willingness": round(avg_w, 4),
            "has_bundles": any(len(r[1]) > 1 for r in self.candidates),
            "regime": self.regime,
        }


def _t_profile_case(ctx: RoundContext, args: dict) -> dict:
    p = ctx.profile()
    return {"ok": True, "content": (
        f"tasks={p['tasks']} couriers={p['couriers']} rows={p['rows']} "
        f"avg_willingness={p['avg_willingness']} has_bundles={p['has_bundles']} regime={p['regime']}\n"
        f"baseline(greedy) cost = {ctx.baseline_cost:.2f}（要打败它）"
    )}


def _t_memory_search(ctx: RoundContext, args: dict) -> dict:
    if ctx.memory is None:
        return {"ok": True, "content": "(no memory configured)"}
    hits = ctx.memory.search(args.get("query", ctx.regime), k=5)
    if not hits:
        return {"ok": True, "content": "(no relevant memory)"}
    lines = [f"- [{h['meta'].get('section')}] {h['meta'].get('title')} :: {h['body'][:160]}" for h in hits]
    return {"ok": True, "content": "\n".join(lines)}


def _t_list_templates(ctx: RoundContext, args: dict) -> dict:
    return {"ok": True, "content": (
        "可参考方向：greedy（覆盖优先）/ multidispatch（对低意愿任务追加备份骑手）/ "
        "bundle（骑手稀缺时一人带多任务）/ low_w_rerank（按 willingness 重排尾段）。\n"
        "最小可行模板：\n```python\n" + _MIN_EXAMPLE + "\n```"
    )}


def _t_read_best(ctx: RoundContext, args: dict) -> dict:
    if not ctx.best_code:
        return {"ok": True, "content": "(还没有最优策略，用 draft_strategy 写第一版；可参考 list_strategy_templates)"}
    return {"ok": True, "content": "当前最优 propose():\n```python\n" + ctx.best_code + "\n```"}


def _t_draft_strategy(ctx: RoundContext, args: dict) -> dict:
    code = (args.get("code") or "").strip()
    if not code:
        return {"ok": False, "content": "draft_strategy 需要 <code>…</code> 里的完整 propose 代码"}
    ok, reason = sandbox_v4.safety_check_code(code)
    ctx.draft_code = code
    ctx.smoke_result = None
    status = "PASS" if ok else f"FAIL(safety): {reason} —— 请修正后重新 draft"
    return {"ok": True, "patch": code, "content": (
        f"draft 已写入（{len(code)} bytes）。安全门预检：{status}。\n现在必须 smoke_test_strategy 一次再 final。"
    )}


def _t_smoke(ctx: RoundContext, args: dict) -> dict:
    if not ctx.draft_code:
        return {"ok": False, "content": "还没有 draft，先 draft_strategy"}
    run = sandbox_v4.run_propose(ctx.draft_code, ctx.candidates, ctx.all_tasks, time_budget_s=ctx.smoke_budget_s)
    if not run["ok"]:
        ctx.smoke_result = {"legal": False, "reason": run["reason"]}
        return {"ok": True, "content": f"SMOKE FAIL: {run['reason']}（修正后重新 draft + smoke）"}
    sol = run["solution"]
    cost = genius_v4.score(sol, ctx.candidates, ctx.all_tasks)
    summ = summarize_solution(sol, ctx.candidates, ctx.all_tasks, cost)
    delta = cost - ctx.baseline_cost
    ctx.smoke_result = {
        "legal": bool(summ["valid"]), "cost": round(cost, 2),
        "coverage": f"{summ['covered_tasks']}/{summ['total_tasks']}", "elapsed_ms": run["elapsed_ms"],
    }
    return {"ok": True, "content": (
        f"SMOKE: legal={summ['valid']} cost={cost:.2f} (baseline {ctx.baseline_cost:.2f}, Δ{delta:+.2f}) "
        f"coverage={summ['covered_tasks']}/{summ['total_tasks']} elapsed={run['elapsed_ms']}ms\n"
        "（smoke 是预览，最终以 Genius 全量裁决为准；若 Δ<0 说明可能优于基线，可以 final）"
    )}


class ToolRegistry:
    HANDLERS = {
        "profile_case": _t_profile_case,
        "memory_search": _t_memory_search,
        "list_strategy_templates": _t_list_templates,
        "read_current_best_strategy": _t_read_best,
        "draft_strategy": _t_draft_strategy,
        "smoke_test_strategy": _t_smoke,
    }

    def run(self, name: str, ctx: RoundContext, args: dict) -> dict:
        handler = self.HANDLERS.get(name)
        if handler is None:
            return {"ok": False, "content": f"unknown tool: {name}. 可用: {', '.join(self.HANDLERS)}"}
        try:
            return handler(ctx, args or {})
        except Exception as exc:  # 工具不该让整轮崩
            return {"ok": False, "content": f"tool error in {name}: {exc}"}
