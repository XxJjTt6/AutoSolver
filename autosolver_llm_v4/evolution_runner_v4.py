"""evolution_runner_v4 —— 时钟 A：多轮离线 LLM 自进化入口（产真实 lineage）。

每轮：build context → harness.run_round（Fool 用 DeepSeek 写/改 propose）→
经 EvolutionManager 权威裁决（安全门+沙箱+打分+registry+evolution_memory，桥接现有 evolution_state，
拆掉 accepted=0 的雷）→ 分类 → 写三层 memory → 事件落 llm_runs 供前端回放 → 停滞触发 Teacher 复盘。

CLI:
  python3 -m autosolver_llm_v4.evolution_runner_v4 --fake-model --rounds 3 --case large_seed301
  python3 -m autosolver_llm_v4.evolution_runner_v4 --provider deepseek --rounds 6 --case large_seed301
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_agent.evolution import EvolutionManager, GeneratedStrategy  # noqa: E402
from autosolver_llm_v4 import genius_v4, harness_v4, llm_client_v4, prompts_v4, tools_v4  # noqa: E402
from autosolver_llm_v4.memory_v4 import MemoryV4  # noqa: E402
from autosolver_llm_v4.teacher_v4 import Teacher  # noqa: E402
from tools.agent_trace_demo import infer_regime, parse_candidates, summarize_solution  # noqa: E402

DATA = _ROOT / "data" / "official_cases"


def _dataset_fp(case_text: str, name: str) -> str:
    return f"{name}_{hashlib.sha1(case_text.encode('utf-8')).hexdigest()[:8]}"


def _case_profile(candidates, all_tasks, regime) -> dict:
    return {
        "regime": regime,
        "tasks": len(all_tasks),
        "couriers": len({r[2] for r in candidates}),
        "rows": len(candidates),
        "avg_willingness": (sum(r[4] for r in candidates) / len(candidates)) if candidates else 0.0,
        "has_bundles": any(len(r[1]) > 1 for r in candidates),
    }


def _bridge_trial(mgr, code, regime, candidates, all_tasks, baseline_cost, case_profile, deadline_s=6.0):
    """把候选代码写入 evolution_state 并经现有 EvolutionManager 权威裁决。"""
    sid = mgr._next_strategy_id(f"llm_{regime}")
    path = mgr.generated_dir / f"{sid}.py"
    path.write_text(code, encoding="utf-8")
    mgr._update_registry(sid, {
        "status": "draft", "target_regime": regime, "source": "deepseek_llm_v4",
        "file": str(path), "attempts": 0, "accepted": 0, "rejected": 0,
    })
    mgr._append_memory({"event": "strategy_generated", "strategy_id": sid,
                        "target_regime": regime, "source": "deepseek_llm_v4", "file": str(path)})
    strat = GeneratedStrategy(sid, path, regime, "deepseek_llm_v4")
    helpers = {"time_left": lambda d: d - time.monotonic(), "now": time.monotonic}
    score_fn = lambda sol: genius_v4.score(sol, candidates, all_tasks)
    summarize_fn = lambda sol, cost: summarize_solution(sol, candidates, all_tasks, cost)
    outcome = mgr.run_generated_strategy(
        strat, candidates, all_tasks, deadline_s, helpers, baseline_cost, score_fn, summarize_fn, case_profile,
    )
    return sid, outcome


# ---------- FakeModelClient 默认脚本（离线/CI 用，驱动完整协议） ----------
_BAD = """def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    if time_left and time_left(deadline) <= 0:
        return []
    rows = sorted(candidates, key=lambda r: r[3])
    if not rows:
        return []
    r = rows[0]
    return [(r[0], [r[2]])]"""

_GOOD = """def propose(candidates, all_tasks, deadline, helpers):
    from collections import defaultdict
    time_left = helpers.get("time_left")
    rows = sorted(candidates, key=lambda r: (len(r[1]), r[3] / max(r[4], 0.001), r[3]))
    by_task = defaultdict(list)
    for r in rows:
        by_task[r[0]].append(r)
    used, covered, result = set(), set(), []
    for task_key, task_ids, courier_id, score, willingness, _ in rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if courier_id in used:
            continue
        if any(t in covered for t in task_ids):
            continue
        team = [courier_id]
        used.add(courier_id)
        if willingness < 0.6:
            for r2 in by_task[task_key]:
                if r2[2] not in used:
                    team.append(r2[2])
                    used.add(r2[2])
                    break
        covered.update(task_ids)
        result.append((task_key, team))
        if covered >= set(all_tasks):
            break
    return result"""


def _round_script(code, hyp, summary):
    return [
        f"<intent>写/改一版策略草稿：{hyp}</intent>\n<tool name=\"draft_strategy\"><code>\n{code}\n</code></tool>",
        "<intent>本地烟测当前草稿，看是否优于基线</intent>\n<tool name=\"smoke_test_strategy\"></tool>",
        f"<intent>烟测完成，提交本轮</intent>\n<final><hypothesis>{hyp}</hypothesis><summary>{summary}</summary></final>",
    ]


def default_fake_scripts(rounds: int):
    scripts = []
    scripts += _round_script(_BAD, "只派第一单试探（预期会因覆盖过低被拒）", "覆盖太低，下一轮改成覆盖优先的贪心")
    scripts += _round_script(_GOOD, "覆盖优先贪心 + 对低意愿任务追加备份骑手", "覆盖全、对低意愿多派，预期优于基线")
    for _ in range(max(0, rounds - 2)):
        scripts += _round_script(_GOOD, "沿用最优策略微调（多为重复/中性）", "与最优接近")
    return scripts


def run(provider="deepseek", rounds=6, case="large_seed301", run_id=None, model=None,
        fake_scripts=None, with_production=True, mgr_root=None, runs_root=None, mem_root=None,
        case_text=None):
    if case_text is not None:
        case_stem = case
    else:
        case_path = DATA / (case if case.endswith(".txt") else f"{case}.txt")
        case_text = case_path.read_text(encoding="utf-8")
        case_stem = case_path.stem
    candidates, all_tasks = parse_candidates(case_text)
    regime = infer_regime(candidates, all_tasks)
    baseline = genius_v4.baseline_greedy(case_text)
    baseline_cost = baseline["cost"]

    run_id = run_id or f"{provider}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fp = _dataset_fp(case_text, case_stem)
    mem = MemoryV4(run_id, fp, runs_root=runs_root, mem_root=mem_root)
    teacher = Teacher(memory=mem)

    if provider == "fake":
        client = llm_client_v4.FakeModelClient(fake_scripts or default_fake_scripts(rounds))
    else:
        client = llm_client_v4.LLMClient(provider=provider, model=model)

    mgr = EvolutionManager(Path(mgr_root) if mgr_root else (_ROOT / "autosolver_agent" / "evolution_state"))
    case_profile = _case_profile(candidates, all_tasks, regime)
    sys_prompt = prompts_v4.build_system_prompt(teacher)
    registry = tools_v4.ToolRegistry()

    best_code = None
    best_cost = None
    history: list[dict] = []
    lineage: list[dict] = []

    mem.log_event({"type": "run_start", "provider": provider, "model": getattr(client, "model", None),
                   "case": case_stem, "regime": regime, "baseline_cost": round(baseline_cost, 2)})

    for r in range(1, rounds + 1):
        review = None
        if provider != "fake" and teacher.should_review(history):
            review = teacher.review(client, history, regime)
            mem.log_event({"type": "teacher_review", "round": r, "text": review[:600]})

        checklist = teacher.checklist(regime)
        hits = mem.search(regime, k=4)
        prior = history[-1]["summary"] if history else None
        header = prompts_v4.build_round_header(r, regime, baseline_cost, best_cost, checklist, hits, prior, review)
        ctx = tools_v4.RoundContext(case_text, baseline_cost, memory=mem, best_code=best_code)

        try:
            result = harness_v4.run_round(client, ctx, sys_prompt, header, registry, mem, r, emit=mem.log_event)
        except Exception as exc:
            mem.log_event({"type": "round_end", "round": r, "outcome": "harness_error", "error": str(exc)})
            history.append({"round": r, "outcome": "harness_error", "summary": str(exc), "hypothesis": "", "candidate_cost": None})
            continue

        if not result.ok or not result.code:
            mem.log_event({"type": "round_end", "round": r, "outcome": "harness_failed", "best_so_far": best_cost})
            mem.write_episode({"round": r, "outcome": "harness_failed", "hypothesis": result.hypothesis})
            history.append({"round": r, "outcome": "harness_failed", "summary": result.summary,
                            "hypothesis": result.hypothesis, "candidate_cost": None})
            continue

        sid, outcome = _bridge_trial(mgr, result.code, regime, candidates, all_tasks, baseline_cost, case_profile)
        accepted = outcome.accepted
        cost = outcome.local_cost
        label = "accepted" if accepted else "rejected"
        improved = False
        if accepted and (best_cost is None or (cost is not None and cost < best_cost)):
            best_cost, best_code, improved = cost, result.code, True
            mgr._update_registry(sid, {"status": "promoted"})

        lineage.append({"round": r, "strategy_id": sid, "accepted": accepted,
                        "cost": (round(cost, 2) if cost is not None else None), "reason": outcome.reason})
        mem.log_event({"type": "judge", "round": r, "strategy_id": sid, "accepted": accepted,
                       "baseline": round(baseline_cost, 2),
                       "candidate": (round(cost, 2) if cost is not None else None), "reason": outcome.reason})
        mem.write_episode({"round": r, "strategy_id": sid, "regime": regime, "outcome": label,
                           "accepted": accepted, "hypothesis": result.hypothesis,
                           "candidate_cost": cost, "baseline_cost": baseline_cost,
                           "reason": outcome.reason, "elapsed_ms": outcome.elapsed_ms})
        mem.update_index(sid, {"regime": regime, "accepted": accepted,
                               "cost": cost, "status": "promoted" if improved else outcome.status})
        if accepted:
            gain = baseline_cost - (cost or baseline_cost)
            mem.write_note("lesson", f"{regime}: {(result.hypothesis or sid)[:48]} 有效(-{gain:.1f})",
                           f"假设：{result.hypothesis}\n结果：cost {cost:.2f} < baseline {baseline_cost:.2f}（-{gain:.1f}）。\n策略：{sid}",
                           tags=[regime, "accepted"])
        else:
            mem.write_note("try_error", f"{regime}: {(result.hypothesis or sid)[:48]} 失败",
                           f"假设：{result.hypothesis}\n失败原因：{outcome.reason}\ncost={cost}",
                           tags=[regime, "fail"])
        mem.log_event({"type": "round_end", "round": r, "outcome": label, "improved": improved, "best_so_far": best_cost})
        history.append({"round": r, "outcome": label, "summary": result.summary,
                        "hypothesis": result.hypothesis, "candidate_cost": cost})

    production_cost = None
    if with_production and provider != "fake":
        try:
            production_cost = round(genius_v4.production_solve(case_text)["cost"], 2)
        except Exception:
            production_cost = None

    result_obj = {
        "run_id": run_id, "provider": provider, "model": getattr(client, "model", None),
        "case": case_stem, "regime": regime,
        "baseline_greedy_cost": round(baseline_cost, 2),
        "production_solver_cost": production_cost,
        "best_llm_cost": (round(best_cost, 2) if best_cost is not None else None),
        "rounds": rounds, "accepted_count": sum(1 for x in lineage if x["accepted"]),
        "lineage": lineage, "usage": client.usage_summary(),
    }
    (mem.run_dir / "result.json").write_text(json.dumps(result_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    mem.log_event({"type": "run_end", "best_llm_cost": result_obj["best_llm_cost"],
                   "accepted_count": result_obj["accepted_count"]})
    mem.rebuild_index()
    return result_obj


def main(argv=None):
    p = argparse.ArgumentParser(description="时钟A：离线 LLM 自进化（DeepSeek）")
    p.add_argument("--provider", default="deepseek")
    p.add_argument("--rounds", type=int, default=6)
    p.add_argument("--case", default="large_seed301")
    p.add_argument("--model", default=None)
    p.add_argument("--run-id", default=None)
    p.add_argument("--fake-model", action="store_true")
    a = p.parse_args(argv)
    provider = "fake" if a.fake_model else a.provider
    res = run(provider=provider, rounds=a.rounds, case=a.case, run_id=a.run_id, model=a.model)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
