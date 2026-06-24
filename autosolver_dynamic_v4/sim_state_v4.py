"""动态仿真状态模型 + 几何（坐标/距离/ETA/骑手移动）。

坐标为演示合成（SHA1 哈希，复刻 web_agent_demo/server.py:82 _stable_point 的思路）。
ETA 走几何距离 / 速度，独立于 solver 的成本函数（诚实红线：第二目标不自圆其说）。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

SPEED = 4.0  # 归一化网格单位/分钟（演示参数）
GRID_MIN, GRID_MAX = 7.5, 92.5


def stable_point(entity_id: str, lane: int = 0) -> tuple[float, float]:
    d = hashlib.sha1(str(entity_id).encode("utf-8")).digest()
    x = 12 + d[0] / 255 * 74
    y = 16 + d[1] / 255 * 68
    if lane:
        gx, gy = lane % 3, (lane // 3) % 3
        x += (gx - 1) * 9
        y += (gy - 1) * 7
    return (round(min(GRID_MAX, max(GRID_MIN, x)), 2), round(min(GRID_MAX, max(GRID_MIN, y)), 2))


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def travel_min(a, b, speed: float = SPEED) -> float:
    return dist(a, b) / max(0.1, speed)


@dataclass(frozen=True)
class SimOrder:
    order_id: str            # = task_id（单任务）或 task_key（bundle）
    task_ids: tuple          # 覆盖的 task id
    arrival_min: int
    deadline_min: int
    pickup_xy: tuple
    dropoff_xy: tuple


@dataclass
class LaneState:
    """单泳道（greedy/cold/warm）独立运行态。"""
    lane: str
    courier_xy: dict = field(default_factory=dict)       # courier_id -> (x,y)
    courier_free_at: dict = field(default_factory=dict)  # courier_id -> 分钟（空闲时刻）
    assigned: dict = field(default_factory=dict)         # order_id -> {courier, eta, deadline}
    solution: list = field(default_factory=list)         # 累计派单 [(task_key, [courier,...]), ...]
    total_cost: float = 0.0                              # 真实期望成本(_solution_expected_cost over running solution)
    hit_count: int = 0
    decision_count: int = 0

    def available_couriers(self, clock: int) -> list[str]:
        return [c for c, free in self.courier_free_at.items() if free <= clock]

    def is_frozen(self, order_id: str) -> bool:
        return order_id in self.assigned


@dataclass
class StepLane:
    metrics: dict
    new_assignments: list
    strategy_label: str
    hit: bool


@dataclass
class DynamicSolveStep:
    tick: int
    clock_min: int
    regime: str
    window: list           # 本 tick 开放决策的 order_id
    arrived_total: int
    speed_factor: float    # <1 表示拥堵/扰动（Peak Shock）
    lanes: dict            # lane -> StepLane

    def to_dict(self) -> dict:
        return {
            "tick": self.tick, "clock_min": self.clock_min, "regime": self.regime,
            "window": self.window, "arrived_total": self.arrived_total,
            "speed_factor": round(self.speed_factor, 3),
            "lanes": {
                k: {"metrics": v.metrics, "new_assignments": v.new_assignments,
                    "strategy": v.strategy_label, "hit": v.hit}
                for k, v in self.lanes.items()
            },
        }
