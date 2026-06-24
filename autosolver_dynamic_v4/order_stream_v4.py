"""把静态算例动态化：合成订单到达时间 / 截止 / 坐标，并给出骑手初始位置。"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_dynamic_v4 import scenario_builder_v4 as sb  # noqa: E402
from autosolver_dynamic_v4.sim_state_v4 import SimOrder, stable_point  # noqa: E402
from tools.agent_trace_demo import parse_candidates  # noqa: E402


def build_orders(case_text: str, scenario: dict) -> list[SimOrder]:
    """每个 task 合成一条订单（单任务派单视角）。bundle 候选行在求解时仍可用。"""
    _, all_tasks = parse_candidates(case_text)
    orders = []
    for task_id in sorted(all_tasks):
        arrival = sb.sample_arrival(task_id, scenario)
        deadline = arrival + scenario["deadline_window"]
        orders.append(SimOrder(
            order_id=task_id,
            task_ids=(task_id,),
            arrival_min=arrival,
            deadline_min=deadline,
            pickup_xy=stable_point(task_id, 0),
            dropoff_xy=stable_point(task_id + "_d", 1),
        ))
    return sorted(orders, key=lambda o: o.arrival_min)


def courier_ids(case_text: str) -> list[str]:
    candidates, _ = parse_candidates(case_text)
    return sorted({row[2] for row in candidates})


def init_courier_positions(case_text: str) -> dict:
    return {c: stable_point(c, 2) for c in courier_ids(case_text)}


def arrival_histogram(orders: list[SimOrder], scenario: dict) -> list[int]:
    """每个 tick 的到达量（给前端画订单到达曲线）。"""
    T, step = scenario["T"], scenario["tick_min"]
    bins = [0] * ((T + step - 1) // step + 1)
    for o in orders:
        bins[min(len(bins) - 1, o.arrival_min // step)] += 1
    return bins
