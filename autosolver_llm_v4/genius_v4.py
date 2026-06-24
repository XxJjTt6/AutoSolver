"""Genius v4 —— 确定性 Critic（绝对真理）。

封装正式 solver.py 的确定性打分与贪心基线，不让 LLM 自评：
- score()        : solver._solution_expected_cost(solution, candidates, sorted(all_tasks))
- baseline_*()   : solver._fallback_official_greedy(candidates) 的成本
- judge()        : 对 LLM 生成的 propose() 代码做 安全门→执行→打分→合法性→accept/reject

口径红线：成本只走 _solution_expected_cost；ETA 不在这里算（在动态层走几何，见 v4 §6.5）。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_llm_v4 import sandbox_v4  # noqa: E402
from tools.agent_trace_demo import (  # noqa: E402
    infer_regime,
    parse_candidates,
    summarize_solution,
)

_SOLVER = None


def solver():
    global _SOLVER
    if _SOLVER is None:
        spec = importlib.util.spec_from_file_location("solver_v4_host", str(_ROOT / "solver.py"))
        if spec is None or spec.loader is None:
            raise ImportError("cannot load solver.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SOLVER = module
    return _SOLVER


def score(solution, candidates, all_tasks) -> float:
    return float(solver()._solution_expected_cost(solution, candidates, sorted(all_tasks)))


def baseline_greedy(case_text: str) -> dict:
    """官方贪心基线：返回 {solution, cost, coverage, regime}。"""
    candidates, all_tasks = parse_candidates(case_text)
    solution = solver()._fallback_official_greedy(candidates)
    cost = score(solution, candidates, all_tasks)
    summ = summarize_solution(solution, candidates, all_tasks, cost)
    return {
        "solution": solution,
        "cost": cost,
        "coverage": f"{summ['covered_tasks']}/{summ['total_tasks']}",
        "regime": infer_regime(candidates, all_tasks),
        "valid": summ["valid"],
    }


def production_solve(case_text: str) -> dict:
    """正式求解器结果（只读，用于参考/对照，不改 solver.py）。"""
    candidates, all_tasks = parse_candidates(case_text)
    solution = solver().solve(case_text)
    cost = score(solution, candidates, all_tasks)
    summ = summarize_solution(solution, candidates, all_tasks, cost)
    return {
        "solution": solution,
        "cost": cost,
        "coverage": f"{summ['covered_tasks']}/{summ['total_tasks']}",
        "valid": summ["valid"],
    }


def judge(code: str, case_text: str, baseline_cost: float, time_budget_s: float = 5.0) -> dict:
    """对一段 propose() 代码做完整裁决。accepted = 合法 且 成本 ≤ baseline−ε。"""
    candidates, all_tasks = parse_candidates(case_text)
    regime = infer_regime(candidates, all_tasks)
    run = sandbox_v4.run_propose(code, candidates, all_tasks, time_budget_s=time_budget_s)
    if not run["ok"]:
        return {
            "valid": False, "accepted": False, "reason": run["reason"],
            "baseline_cost": round(baseline_cost, 4), "candidate_cost": None,
            "coverage": None, "elapsed_ms": run.get("elapsed_ms"), "regime": regime,
        }
    solution = run["solution"]
    cost = score(solution, candidates, all_tasks)
    summ = summarize_solution(solution, candidates, all_tasks, cost)
    valid = bool(summ["valid"])
    accepted = bool(valid and cost <= baseline_cost - 1e-9)
    if not valid:
        reason = "invalid: " + "; ".join(summ["invalid_reasons"][:3])
    elif accepted:
        improve = (baseline_cost - cost) / baseline_cost * 100 if baseline_cost else 0.0
        reason = f"improved expected cost ({improve:.1f}% better than greedy baseline)"
    else:
        reason = "quality regression (not better than greedy baseline)"
    return {
        "valid": valid, "accepted": accepted, "reason": reason,
        "baseline_cost": round(baseline_cost, 4), "candidate_cost": round(cost, 4),
        "coverage": f"{summ['covered_tasks']}/{summ['total_tasks']}",
        "elapsed_ms": run.get("elapsed_ms"), "regime": regime,
        "solution": solution,
    }
