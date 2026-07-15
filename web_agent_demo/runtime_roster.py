"""运行时花名册：「订单池 / 骑手运力」页新增的订单与骑手（后台管理语义）。

- 新增实体存在本模块的内存列表里（会话级；重启服务即清空）。
- `inject_world(world)` 在 `generate_full_day_world` 之后把它们注入 DaySimulationWorld：
  订单挂到对应时段的 order_ids、骑手并入 couriers、时段 courier_supply 同步 +N —— 之后整条
  仿真管线（基线/我方派单、合单、路线、指标、决策、记忆）**真实重算**，新增实体和原生数据完全同权。
- 后端真算、不造假：新增单的路网腿由 /api/roster-add 里的联网预热现取现缓存（真实 OSRM foot 路网）。
"""
from __future__ import annotations

import dataclasses
import hashlib
from typing import Any

from web_agent_demo.simulation_engine import Position
from web_agent_demo import road_routing as rr

_orders: list[dict[str, Any]] = []
_riders: list[dict[str, Any]] = []


def counts() -> dict[str, int]:
    return {"orders": len(_orders), "riders": len(_riders)}


def clear() -> None:
    _orders.clear()
    _riders.clear()


def _h01(key: str, salt: str) -> float:
    """确定性伪随机 [0,1)：同一 id 每次注入位置一致（可复现，不用真随机）。"""
    digest = hashlib.sha256(f"{key}|{salt}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def _pos(lat: float, lng: float) -> Position:
    sx, sy = rr._screen_project(lat, lng)
    return Position(round(lat, 7), round(lng, 7), sx, sy)


def _zone_point(world: Any, zone_id: str, key: str) -> Position:
    """商圈内取一个确定性的客户/骑手落点：该商圈某商家位置 + ~200-600m 偏移。"""
    merchants = [m for m in world.merchants if m.zone_id == zone_id] or list(world.merchants)
    base = merchants[int(_h01(key, "pick") * len(merchants))].position
    dlat = (_h01(key, "lat") - 0.5) * 0.010   # ~±550m
    dlng = (_h01(key, "lng") - 0.5) * 0.012
    return _pos(base.lat + dlat, base.lng + dlng)


def add_order(merchant_id: str, created_at_s: int, note: str = "") -> dict[str, Any]:
    idx = len(_orders) + 1
    entry = {"id": f"O-CUSTOM-{idx:02d}", "merchant_id": merchant_id, "created_at_s": int(created_at_s), "note": note}
    _orders.append(entry)
    return entry


def add_rider(zone_id: str, shift_start_s: int, shift_end_s: int, capacity: int = 3) -> dict[str, Any]:
    idx = len(_riders) + 1
    entry = {"id": f"R-CUSTOM-{idx:02d}", "zone_id": zone_id, "shift_start_s": int(shift_start_s), "shift_end_s": int(shift_end_s), "capacity": int(capacity)}
    _riders.append(entry)
    return entry


def inject_world(world: Any) -> Any:
    """把新增订单/骑手注入 world（无新增时原样返回）。"""
    if not _orders and not _riders:
        return world
    from web_agent_demo import day_simulation as ds

    merchants_by_id = {m.id: m for m in world.merchants}
    new_couriers = []
    for r in _riders:
        start = _zone_point(world, r["zone_id"], r["id"])
        new_couriers.append(ds.DayCourier(
            id=r["id"], label=f"R{len(world.couriers) + len(new_couriers) + 1:03d}",
            home_zone_id=r["zone_id"], shift_start_s=r["shift_start_s"], shift_end_s=r["shift_end_s"],
            capacity=r["capacity"], base_speed_mps=4.2, willingness=0.72, start_position=start,
        ))
    new_orders = []
    for o in _orders:
        merchant = merchants_by_id.get(o["merchant_id"]) or world.merchants[0]
        dest = _zone_point(world, merchant.zone_id, o["id"])
        # 时段 phase 必须归入下单时刻真实所属的时段（早餐/午高峰/晚高峰…）：
        # 所有按时段分组/筛选的视图（订单池释放节奏、时间段筛选）才能看到这单。自造 "custom" 会被全部漏掉。
        slice_for = next((ts for ts in world.time_slices if ts.start_s <= o["created_at_s"] < ts.end_s), None)
        phase = slice_for.demand_phase if slice_for else "lunch_peak"
        new_orders.append(ds.DayOrder(
            id=o["id"], merchant_id=merchant.id, created_at_s=o["created_at_s"],
            deadline_s=o["created_at_s"] + 32 * 60, demand_phase=phase,
            merchant_position=merchant.position, destination=dest,
            prep_time_s=360.0, priority=0.5, basket_value_yuan=35.0, penalty_yuan=8.0, risk_tags=(),
        ))
    slices = list(world.time_slices)
    for no in new_orders:
        for i, ts in enumerate(slices):
            if ts.start_s <= no.created_at_s < ts.end_s:
                slices[i] = dataclasses.replace(ts, order_ids=ts.order_ids + (no.id,))
                break
    if new_couriers:
        # 时段运力供给数只加给「该骑手上线之后」的时段——因果一致的关键之一：
        # 若给过去时段也 +N，过去时段的打分压力(future_pressure)会变 → 已发生的派单被改写。
        slices = [
            dataclasses.replace(ts, courier_supply=ts.courier_supply + sum(1 for c in new_couriers if c.shift_start_s <= ts.start_s))
            for ts in slices
        ]
    return dataclasses.replace(
        world,
        couriers=world.couriers + tuple(new_couriers),
        orders=world.orders + tuple(new_orders),
        time_slices=tuple(slices),
    )
