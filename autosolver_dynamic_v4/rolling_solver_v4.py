"""滚动时域核心：逐 tick 揭示订单、移动骑手、冻结决策、窗口重算；三泳道同源对比。

泳道：
- greedy : 官方贪心基线 _fallback_official_greedy
- cold   : 组合策略 default（多派贪心），无记忆
- warm   : 同 default + 召回离线学到的策略，取更优（带记忆）

CLI: python3 -m autosolver_dynamic_v4.rolling_solver_v4 --case large_seed301 --scenario weekday_peaks
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_dynamic_v4 import business_metrics_v4 as metrics  # noqa: E402
from autosolver_dynamic_v4 import order_stream_v4 as ostream  # noqa: E402
from autosolver_dynamic_v4.scenario_builder_v4 import SCENARIOS, speed_factor_at  # noqa: E402
from autosolver_dynamic_v4.scene_memory_v4 import SceneMemory  # noqa: E402
from autosolver_dynamic_v4.sim_state_v4 import (  # noqa: E402
    SPEED, DynamicSolveStep, LaneState, StepLane, travel_min,
)
from autosolver_llm_v4 import genius_v4, sandbox_v4  # noqa: E402
from tools.agent_trace_demo import infer_regime, parse_candidates  # noqa: E402

DATA = _ROOT / "data" / "official_cases"

# cold 泳道：基础单派贪心（AutoSolver 机制，但无记忆/无学到的精细化）
COLD_PROPOSE = """def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    used, covered, result = set(), set(), []
    rows = sorted(candidates, key=lambda r: (len(r[1]), r[3] / max(r[4], 0.001), r[3]))
    for task_key, task_ids, courier_id, score, willingness, _ in rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if courier_id in used or any(t in covered for t in task_ids):
            continue
        used.add(courier_id); covered.update(task_ids)
        result.append((task_key, [courier_id]))
        if covered >= set(all_tasks):
            break
    return result"""


def _run_code(code, candidates, all_tasks_set, budget_s):
    out = sandbox_v4.run_propose(code, candidates, all_tasks_set, time_budget_s=budget_s)
    return out["solution"] if out["ok"] else None


def _solve_lane(lane, lane_sub, pend_tasks, warm_mem, headline_regime, budget):
    if not lane_sub:
        return [], "idle", False
    if lane == "greedy":
        return genius_v4.solver()._fallback_official_greedy(lane_sub), "greedy", False
    default_sol = _run_code(COLD_PROPOSE, lane_sub, set(pend_tasks), budget) or []
    best, label, hit = default_sol, "cold_basic", False
    best_cost = genius_v4.score(default_sol, lane_sub, pend_tasks) if default_sol else float("inf")
    if lane == "warm" and warm_mem is not None:
        for sid, code in warm_mem.recall(headline_regime):
            sol = _run_code(code, lane_sub, set(pend_tasks), budget)
            if not sol:
                continue
            c = genius_v4.score(sol, lane_sub, pend_tasks)
            if c < best_cost - 1e-9:
                best, best_cost, label, hit = sol, c, sid, True
    return best, label, hit


def _commit(ls, sol, order_by_id, clock, speed):
    """提交本 tick 派单。返回 (viz 列表, 本tick已提交的 (task_key,[couriers]) 列表)。"""
    new, committed = [], []
    busy_this_tick = set()
    for task_key, couriers in sol:
        if not couriers:
            continue
        team = [c for c in couriers if c not in busy_this_tick and ls.courier_free_at.get(c, 0) <= clock]
        if not team:
            continue
        ids = task_key.split(",")
        order0 = order_by_id.get(ids[0])
        if order0 is None or any(tid in ls.assigned for tid in ids):
            continue
        courier = team[0]
        cpos = ls.courier_xy.get(courier)
        if cpos is None:
            continue
        eta = int(clock + travel_min(cpos, order0.pickup_xy, speed) + travel_min(order0.pickup_xy, order0.dropoff_xy, speed))
        for tid in ids:
            o = order_by_id.get(tid)
            if o is None:
                continue
            ls.assigned[tid] = {"courier": courier, "eta": eta, "deadline": o.deadline_min, "assign_min": clock}
        for c in team:
            busy_this_tick.add(c)
            ls.courier_free_at[c] = eta
            ls.courier_xy[c] = order0.dropoff_xy
        ls.solution.append((task_key, team))
        committed.append((task_key, team))
        new.append({"order": task_key, "courier": courier, "team": team, "pickup": order0.pickup_xy,
                    "dropoff": order0.dropoff_xy, "courier_from": cpos, "eta": eta,
                    "deadline": order0.deadline_min})
    return new, committed


def simulate(case_text, scenario_id="weekday_peaks", state_root=None, pack_root=None,
             lanes=("greedy", "cold", "warm"), tick_budget_s=0.8):
    scenario = SCENARIOS[scenario_id]
    candidates, all_tasks_full = parse_candidates(case_text)
    headline_regime = infer_regime(candidates, all_tasks_full)
    orders = ostream.build_orders(case_text, scenario)
    order_by_id = {o.order_id: o for o in orders}
    courier_pos = ostream.init_courier_positions(case_text)

    warm_mem = SceneMemory(state_root, pack_root=pack_root, enabled=True)
    lane_state = {
        ln: LaneState(ln, courier_xy=dict(courier_pos), courier_free_at={c: 0 for c in courier_pos})
        for ln in lanes
    }
    T, step, H = scenario["T"], scenario["tick_min"], scenario["horizon_min"]
    steps = []
    for clock in range(0, T + 1, step):
        speed = speed_factor_at(clock, scenario) * SPEED
        arrived_set = {o.order_id for o in orders if o.arrival_min <= clock}
        arrived = len(arrived_set)
        window_orders = [o for o in orders if o.arrival_min <= clock and o.deadline_min >= clock]
        win_ids = {o.order_id for o in window_orders}
        sub_candidates = [r for r in candidates if set(r[1]) <= win_ids]
        regime = infer_regime(sub_candidates, win_ids) if sub_candidates else headline_regime
        step_lanes = {}
        for ln, ls in lane_state.items():
            pend = {o.order_id for o in window_orders if not ls.is_frozen(o.order_id)}
            avail = set(ls.available_couriers(clock))
            lane_sub = [r for r in sub_candidates if set(r[1]) <= pend and r[2] in avail]
            sol, label, hit = _solve_lane(
                ln, lane_sub, pend, warm_mem if ln == "warm" else None, headline_regime, tick_budget_s)
            new_assigns, committed = _commit(ls, sol, order_by_id, clock, speed)
            if committed:  # 累计真实期望成本（仅本tick已派任务，tick内唯一有效，多派降无接单风险）
                tick_tasks = {t for tk, _ in committed for t in tk.split(",")}
                ls.total_cost += genius_v4.score(committed, candidates, tick_tasks)
            ls.decision_count += 1
            if hit:
                ls.hit_count += 1
            step_lanes[ln] = StepLane(metrics.compute(ls, arrived), new_assigns, label, hit)
        steps.append(DynamicSolveStep(clock // step, clock, regime, sorted(win_ids), arrived, speed / SPEED, step_lanes))

    summary = {
        "case_regime": headline_regime,
        "scenario": scenario_id,
        "scenario_label": scenario["label"],
        "total_orders": len(orders),
        "couriers": len(courier_pos),
        "warm_known_regimes": warm_mem.known_regimes(),
        "final": {ln: metrics.compute(ls, len(orders)) for ln, ls in lane_state.items()},
    }
    # 学习收益（warm vs cold vs greedy）
    fin = summary["final"]
    if "cold" in fin and "warm" in fin and fin["cold"]["avg_cost_per_order"]:
        summary["warm_vs_cold_cost_pct"] = round(
            (fin["cold"]["avg_cost_per_order"] - fin["warm"]["avg_cost_per_order"])
            / fin["cold"]["avg_cost_per_order"] * 100, 1)
    return {
        "meta": {"scenario": scenario_id, "T": T, "tick_min": step, "horizon_min": H,
                 "arrival_hist": ostream.arrival_histogram(orders, scenario)},
        "summary": summary,
        "steps": [s.to_dict() for s in steps],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="时钟B：动态滚动时域仿真（三泳道）")
    p.add_argument("--case", default="large_seed301")
    p.add_argument("--scenario", default="weekday_peaks")
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    case_path = DATA / (a.case if a.case.endswith(".txt") else f"{a.case}.txt")
    res = simulate(case_path.read_text(encoding="utf-8"), a.scenario)
    fin = res["summary"]["final"]
    print(json.dumps({"summary": res["summary"], "ticks": len(res["steps"]),
                      "greedy": fin.get("greedy"), "cold": fin.get("cold"), "warm": fin.get("warm")},
                     ensure_ascii=False, indent=2))
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
