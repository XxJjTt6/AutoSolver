"""道路路由补丁：把 day_simulation 的「直线距离 + 按算法暗改的乘子」换成**真实路网单一事实源**。

沿用本项目既有的 monkeypatch 模式（server_v3 已这样包装 render_index / do_POST），**不修改 day_simulation.py /
dispatch_workbench_data.py 原文件**，只在 import 期替换其模块命名空间里的函数。

铲除的四处「按算法暗改」（回应「两算法同一套物理、真实可解释、不能造假」）：
  1. _routing_factor        我方距离 ×0.82~1.02  → 统一用真实道路距离，两算法同一条
  2. _effective_speed_mps   我方速度 ×1.06、拥堵阻力 0.32(基线0.42) → 统一 0.42、去掉 ×1.06
  3. _expected_cost_yuan    我方成本 ×0.94 → 去掉
  4. _timeout_risk          我方风险 ×0.78 → 去掉
铲除后，我方相对基线的优势只来自**更聪明的派单选择**（autosolver_score 的多因子目标 vs 基线最近贪心），
而非物理层面的暗改。距离/几何全部来自 road_routing 的道路缓存 → 前端画的线 = 后端算的距离，物理上不可能不一致。
"""
from __future__ import annotations

from typing import Any

from web_agent_demo import day_simulation as ds
from web_agent_demo import dispatch_workbench_data as wb
from web_agent_demo import road_routing as rr

# 预计算脚本把它设 True：仿真按需联网取真实路网并写缓存。生产/服务态保持 False：只读缓存、离线。
ALLOW_NETWORK = False
# 仅「realized 路线几何/距离」联网（打分候选比较仍走缓存/快速估算）——roster 增量重算用：
# 展示的每条线与每个数字仍来自真实路网，但不为落选候选付几百次网络请求（与临时单派单同一原则）。
GEOMETRY_NETWORK = False

_applied = False


# ---- 铲除暗改：四个「两算法同一套物理」的替身 ----
def _routing_factor_neutral(algorithm_id: str, time_slice: Any, order: Any) -> float:
    return 1.0  # 不再按算法打折；真实道路距离已由 road_routing 提供


def _effective_speed_mps_neutral(courier: Any, time_slice: Any, algorithm_id: str) -> float:
    congestion_drag = time_slice.congestion_level * 0.42  # 两算法同系数（原基线值），铲除我方 0.32 暗改
    weather_drag = {"rain": 0.10, "storm": 0.18, "event": 0.08}.get(time_slice.weather, 0.0)
    load_factor = 0.92 + courier.willingness * 0.14
    speed = courier.base_speed_mps * max(0.42, 1.0 - congestion_drag - weather_drag) * load_factor
    # 铲除 if autosolver_agent: speed *= 1.06
    return max(1.25, speed)


def _timeout_risk_neutral(order: Any, time_slice: Any, finish_at_s: float, algorithm_id: str) -> float:
    slack_s = order.deadline_s - finish_at_s
    if slack_s >= 0:
        pressure = 1.0 / (1.0 + min(3600.0, slack_s) / 900.0)
    else:
        pressure = 0.82 + min(0.16, abs(slack_s) / 3600.0)
    risk = 0.08 + time_slice.congestion_level * 0.18 + order.priority * 0.12 + pressure * 0.34
    # 铲除 if autosolver_agent: risk *= 0.78
    return round(ds._clamp(risk, 0.02, 0.98), 4)


def _expected_cost_yuan_neutral(distance_m: float, wait_for_courier_s: float, timeout_risk: float, order: Any, algorithm_id: str) -> float:
    distance_cost = distance_m / 1000.0 * 2.35
    wait_cost = wait_for_courier_s / 60.0 * 0.18
    risk_cost = timeout_risk * order.penalty_yuan
    # 铲除 efficiency = 0.94 if autosolver_agent else 1.0
    return round(distance_cost + wait_cost + risk_cost + 2.8, 4)


# ---- 用真实道路距离打分（其余公式与原版逐字一致，只换距离来源、去掉 routing_factor）----
def _assignment_profile_road(time_slice: Any, order: Any, plan: Any, algorithm_id: str) -> dict[str, Any]:
    p, m, d = plan.position, order.merchant_position, order.destination
    pickup = rr.lookup_leg(p.lat, p.lng, m.lat, m.lng, allow_network=ALLOW_NETWORK, pace_s=_PACE_S)
    delivery = rr.lookup_leg(m.lat, m.lng, d.lat, d.lng, allow_network=ALLOW_NETWORK, pace_s=_PACE_S)
    pickup_distance = pickup["distance_m"]
    delivery_distance = delivery["distance_m"]
    total_distance = pickup_distance + delivery_distance
    speed = ds._effective_speed_mps(plan.courier, time_slice, algorithm_id)
    pickup_eta = pickup_distance / speed
    delivery_eta = delivery_distance / speed
    start_at = max(float(order.created_at_s), plan.available_at_s)
    wait_for_courier = max(0.0, start_at - order.created_at_s)
    prep_wait = max(0.0, order.prep_time_s - pickup_eta)
    finish_at = start_at + pickup_eta + prep_wait + delivery_eta
    total_eta = finish_at - order.created_at_s
    timeout_risk = ds._timeout_risk(order, time_slice, finish_at, algorithm_id)
    expected_cost = ds._expected_cost_yuan(total_distance, wait_for_courier, timeout_risk, order, algorithm_id)
    load_penalty = plan.assigned_count * 38.0
    future_pressure = len(time_slice.order_ids) / max(1.0, time_slice.courier_supply)
    autosolver_score = finish_at + timeout_risk * 1800.0 + expected_cost * 35.0 + load_penalty + future_pressure * 160.0
    if algorithm_id == "nearest_greedy":
        autosolver_score = pickup_distance
    return {
        "courier_id": plan.courier.id,
        "courier_available_at_s": plan.available_at_s,
        "pickup_distance_m": pickup_distance,
        "total_distance_m": total_distance,
        "pickup_eta_s": pickup_eta + wait_for_courier,
        "delivery_eta_s": delivery_eta + prep_wait,
        "total_eta_s": total_eta,
        "finish_at_s": finish_at,
        "expected_cost_yuan": expected_cost,
        "timeout_risk": timeout_risk,
        "courier_busy_s": pickup_eta + prep_wait + delivery_eta,
        "late": finish_at > order.deadline_s,
        "autosolver_score": autosolver_score,
    }


# ---- 路线折线：换成真实路网（取餐段 + 配送段），带商家分割点 merchant_index ----
def _route_overlay_road(order: Any, courier: Any, lane: str) -> dict[str, Any]:
    cs, m, d = courier.start_position, order.merchant_position, order.destination
    legs = rr.route_two_legs(cs.lat, cs.lng, m.lat, m.lng, d.lat, d.lng, allow_network=ALLOW_NETWORK or GEOMETRY_NETWORK, pace_s=_PACE_S)
    return {
        "lane": lane,
        "order_id": order.id,
        "courier_id": courier.id,
        "polyline": legs["polyline"],
        "merchant_index": legs["merchant_index"],
    }


def _record_route_overlay_road(record: Any, order: Any, algorithm_id: str) -> dict[str, Any]:
    cs, m, d = record.courier_start_position, record.merchant_position, record.destination_position
    legs = rr.route_two_legs(cs.lat, cs.lng, m.lat, m.lng, d.lat, d.lng, allow_network=ALLOW_NETWORK or GEOMETRY_NETWORK, pace_s=_PACE_S)
    return {
        "lane": "challenger" if algorithm_id == "autosolver_agent" else "baseline",
        "order_id": order.id,
        "courier_id": record.assignment.courier_id,
        "polyline": legs["polyline"],
        "merchant_index": legs["merchant_index"],
        "eta_s": record.assignment.total_eta_s,
        "cost_yuan": record.assignment.expected_cost_yuan,
        "assign_at_s": round(record.finish_at_s - record.courier_busy_s, 3),
        "complete_at_s": round(record.finish_at_s, 3),
    }


# ---- 透传 merchant_index 到前端 route 载荷（原 _route_payloads 会丢弃未知字段）----
def _route_payloads_with_merchant_index(contract: Any, map_aliases: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for frame in contract.frames:
        for lane, algorithm_frame in (("baseline", frame.baseline), ("ours", frame.challenger)):
            for route in algorithm_frame.route_overlays:
                order_id = route.get("order_id", "")
                courier_id = route.get("courier_id", "")
                routes.append(
                    {
                        "id": f"ROUTE-{frame.id}-{lane}-{courier_id}-{order_id}",
                        "frame_id": frame.id,
                        "time_s": frame.sim_time_s,
                        "lane": lane,
                        "order_id": order_id,
                        "order_label": wb._display_alias(map_aliases, "orders", str(order_id)),
                        "courier_id": courier_id,
                        "courier_label": wb._display_alias(map_aliases, "riders", str(courier_id)),
                        "polyline": [wb._position_payload(point) for point in route.get("polyline", [])],
                        "merchant_index": route.get("merchant_index"),  # 商家分割点下标（取餐段/配送段边界）
                        "batch_size": route.get("batch_size"),          # 顺路合单：这趟骑手带几单（>1 即合单）
                        "batch_start_s": route.get("batch_start_s"),    # 批次真实出发时刻（批内相同；分组/运动锚点用）
                        "eta_s": route.get("eta_s", 0),
                        "cost_yuan": route.get("cost_yuan", 0),
                        "assign_at_s": route.get("assign_at_s"),
                        "complete_at_s": route.get("complete_at_s"),
                    }
                )
    return routes


# 预计算联网时给每条腿之间加点节流（对公共 OSRM 友好）；生产态 ALLOW_NETWORK=False 时此值不生效。
_PACE_S = 0.0


def apply(allow_network: bool = False, pace_s: float = 0.0) -> None:
    """替换 day_simulation / dispatch_workbench_data 命名空间里的相关函数。须在首次跑仿真之前调用。"""
    global _applied, ALLOW_NETWORK, _PACE_S
    ALLOW_NETWORK = allow_network
    _PACE_S = pace_s
    if _applied:
        return
    ds._routing_factor = _routing_factor_neutral
    ds._effective_speed_mps = _effective_speed_mps_neutral
    ds._timeout_risk = _timeout_risk_neutral
    ds._expected_cost_yuan = _expected_cost_yuan_neutral
    ds._assignment_profile = _assignment_profile_road
    ds._route_overlay = _route_overlay_road
    ds._record_route_overlay = _record_route_overlay_road
    wb._route_payloads = _route_payloads_with_merchant_index
    # 顺路合单：只给我方加「一骑手带多单」的真实批次派单（基线不变）。
    from web_agent_demo import batching_engine
    batching_engine.install()
    # 运行时花名册：订单池/骑手运力页新增的订单与骑手注入 world，整条仿真管线真实重算。
    from web_agent_demo import runtime_roster
    _orig_generate_world = ds.generate_full_day_world

    def _generate_world_with_roster(*args: Any, **kwargs: Any) -> Any:
        return runtime_roster.inject_world(_orig_generate_world(*args, **kwargs))

    ds.generate_full_day_world = _generate_world_with_roster
    _applied = True
