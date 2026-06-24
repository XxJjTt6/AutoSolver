"""业务指标：成本/覆盖/ETA/准时率/命中率（被追问不翻车）。

- total_cost: 已派单选中候选行 score 之和（越低越好，分配质量；不冒充官方分）。
- avg_cost_per_order: total_cost / 已派单数（核心对比量）。
- coverage: 已派单 / 已到达订单。
- avg_eta_min: 平均配送时长（几何 ETA，独立于成本函数）。
- on_time_rate: eta ≤ deadline 占比。
- regime_hit_rate: warm 泳道召回到学到策略并胜出的 tick 占比（"自主学习"量化）。
"""
from __future__ import annotations


def compute(lane_state, arrived_total: int) -> dict:
    assigned = lane_state.assigned
    n = len(assigned)
    on_time = sum(1 for a in assigned.values() if a["eta"] <= a["deadline"])
    durations = [a["eta"] - a["assign_min"] for a in assigned.values()]
    avg_eta = sum(durations) / n if n else 0.0
    return {
        "total_cost": round(lane_state.total_cost, 2),
        "assigned": n,
        "arrived": arrived_total,
        "coverage": round(n / arrived_total, 3) if arrived_total else 0.0,
        "coverage_str": f"{n}/{arrived_total}",
        "avg_cost_per_order": round(lane_state.total_cost / n, 2) if n else 0.0,
        "avg_eta_min": round(avg_eta, 1),
        "on_time_rate": round(on_time / n, 3) if n else 0.0,
        "regime_hit_rate": round(lane_state.hit_count / lane_state.decision_count, 3) if lane_state.decision_count else 0.0,
    }
