"""一天订单到达场景 + Peak Shock。

确定性合成（按 order_id 哈希），保证可复现、断网可回放、左右双屏天然同源。
"""
from __future__ import annotations

import hashlib

# 每个 peak = (中心占比, 扩散占比, 权重)；shock = (起始分, 结束分, 速度因子)
SCENARIOS = {
    "weekday_peaks": {
        "label": "工作日三高峰（早/午/晚）",
        "T": 240,
        "tick_min": 10,
        "horizon_min": 30,
        "peaks": [(0.20, 0.06, 0.40), (0.50, 0.05, 0.38), (0.80, 0.06, 0.22)],
        "deadline_window": 32,
        "shock": None,
    },
    "lunch_shock": {
        "label": "午高峰突发拥堵（雨天/活动）",
        "T": 240,
        "tick_min": 10,
        "horizon_min": 30,
        "peaks": [(0.22, 0.05, 0.30), (0.50, 0.04, 0.50), (0.80, 0.06, 0.20)],
        "deadline_window": 28,
        "shock": (110, 150, 0.5),  # 110~150 分钟速度减半 → ETA 上升，演示"扰动—恢复"
    },
}


def _h(*parts) -> float:
    raw = "::".join(str(p) for p in parts).encode("utf-8")
    return int(hashlib.sha1(raw).hexdigest()[:8], 16) / 0xFFFFFFFF


def sample_arrival(order_id: str, scenario: dict) -> int:
    T = scenario["T"]
    peaks = scenario["peaks"]
    # 按权重选 peak
    r = _h(order_id, "peak")
    acc, chosen = 0.0, peaks[-1]
    total_w = sum(p[2] for p in peaks)
    for p in peaks:
        acc += p[2] / total_w
        if r <= acc:
            chosen = p
            break
    center, spread, _ = chosen
    offset = (_h(order_id, "offset") - 0.5) * 2 * spread  # [-spread, +spread]
    minute = (center + offset) * T
    return int(max(0, min(T - 1, minute)))


def speed_factor_at(clock_min: int, scenario: dict) -> float:
    shock = scenario.get("shock")
    if shock and shock[0] <= clock_min <= shock[1]:
        return float(shock[2])
    return 1.0


def list_scenarios() -> list[dict]:
    return [{"id": k, "label": v["label"], "T": v["T"], "tick_min": v["tick_min"],
             "has_shock": v.get("shock") is not None} for k, v in SCENARIOS.items()]
