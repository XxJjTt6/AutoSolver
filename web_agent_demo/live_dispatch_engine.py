"""实时派单引擎：给 live 页「中途加临时订单 / 加骑手」用。

评委当场在地图上点一个位置加单、或加一个骑手，前端把「当前时刻真实骑手态（位置/负载/可用，
来自后端帧）+ 点击的订单位置 + 当前时段拥堵/天气」POST 过来，本模块**复用 day_simulation 的
真实打分公式**（`_assignment_profile` / `_effective_speed_mps` / `_timeout_risk` /
`_expected_cost_yuan` / autosolver_score），对每个候选骑手真实打分、按算法真实择优，返回逐候选
打分 + 选中骑手 + 路线。前后端同一套数据、同一套算法——后端真算、不造假。

不修改 day_simulation.py（只 import 复用其函数与数据类）。
"""
from __future__ import annotations

from typing import Any

from web_agent_demo.simulation_engine import Position
from web_agent_demo import day_simulation as ds
from web_agent_demo import road_routing as rr
from web_agent_demo import road_routing_patch


def _pos(d: dict[str, Any]) -> Position:
    return Position(
        lat=float(d["lat"]),
        lng=float(d["lng"]),
        screen_x=d.get("screen_x"),
        screen_y=d.get("screen_y"),
    )


def _profile_of(slice_: "ds.TimeSlice", order: "ds.DayOrder", plan: "ds._CourierPlan", algorithm_id: str) -> dict:
    return ds._assignment_profile(slice_, order, plan, algorithm_id)


def live_dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    """临时单派单：**候选打分用快速估算（不联网、秒级）**择优选骑手，**只对选中骑手联网取一次真实路网**
    （2 条腿、缓存后即时）并据此重算展示值+画折线。这样既快（原来对每个候选都联网→10s，现在 1~2s），
    又保证「前端画的路 = 后端展示的距离」（选中骑手那条是真实路网）。"""
    return _live_dispatch_impl(payload)


def _live_dispatch_impl(payload: dict[str, Any]) -> dict[str, Any]:
    """核心：对新订单在候选骑手里真实打分、择优派单。返回可直接被前端渲染的 JSON。"""
    time_s = int(payload.get("time_s", ds.DAY_START_S))
    ctx = payload.get("context") or {}
    order_in = payload.get("order") or {}
    riders_in = payload.get("riders") or []
    if not riders_in:
        return {"status": "error", "error": "没有可用骑手（riders 为空）"}
    if "destination" not in order_in:
        return {"status": "error", "error": "订单缺少客户位置 destination"}

    weather = str(ctx.get("weather", "clear"))
    congestion = float(ctx.get("congestion_level", 0.3))
    supply = int(ctx.get("courier_supply", max(1, len(riders_in))))
    active_orders = max(1, int(ctx.get("active_order_count", 1)))
    demand_phase = str(ctx.get("demand_phase", "lunch_peak"))

    # 真实 TimeSlice：拥堵/天气/供给决定速度、路由系数、未来压力（与全天仿真同源公式）。
    slice_ = ds.TimeSlice(
        id="live-slice",
        index=0,
        start_s=time_s,
        end_s=time_s + ds.DEFAULT_TIME_SLICE_S,
        label="live",
        demand_phase=demand_phase,
        weather=weather,
        congestion_level=congestion,
        courier_supply=supply,
        order_ids=tuple(f"live-{i}" for i in range(active_orders)),
        shock_ids=(),
        compare_due=False,
    )

    dest_pos = _pos(order_in["destination"])
    merchant_pos = _pos(order_in["merchant"]) if "merchant" in order_in else dest_pos
    default_tags: list[str] = []
    if weather in ("rain", "storm"):
        default_tags.append("weather_slowdown")
    if congestion >= 0.6:
        default_tags.append("road_congestion")
    risk_tags = tuple(order_in.get("risk_tags") or default_tags)

    order = ds.DayOrder(
        id=str(order_in.get("id", "O-LIVE")),
        merchant_id=str(order_in.get("merchant_id", "M-LIVE")),
        created_at_s=time_s,
        deadline_s=int(order_in.get("deadline_s", time_s + 32 * 60)),
        demand_phase=demand_phase,
        merchant_position=merchant_pos,
        destination=dest_pos,
        prep_time_s=float(order_in.get("prep_time_s", 360.0)),
        priority=float(order_in.get("priority", 0.5)),
        basket_value_yuan=float(order_in.get("basket_value_yuan", 35.0)),
        penalty_yuan=float(order_in.get("penalty_yuan", 8.0)),
        risk_tags=risk_tags,
    )

    # 候选骑手：位置/负载/可用时刻均来自前端（前端从后端帧读到），保证前后端一致。
    plans: list[ds._CourierPlan] = []
    for r in riders_in:
        courier = ds.DayCourier(
            id=str(r["id"]),
            label=str(r.get("label", r["id"])),
            home_zone_id="live",
            shift_start_s=0,
            shift_end_s=ds.DAY_END_S,
            capacity=int(r.get("capacity", 3)),
            base_speed_mps=float(r.get("base_speed_mps", 4.2)),
            willingness=float(r.get("willingness", 0.7)),
            start_position=_pos(r),
        )
        plan = ds._CourierPlan(
            courier=courier,
            position=_pos(r),
            available_at_s=float(r.get("available_at_s", time_s)),
            busy_time_s=0.0,
            assigned_count=int(r.get("assigned_count", 0)),
        )
        plans.append(plan)

    # 对每个候选骑手，用真实公式算 autosolver 综合分与基线（最近距离）视角。
    our = [(p, _profile_of(slice_, order, p, "autosolver_agent")) for p in plans]
    base = [(p, _profile_of(slice_, order, p, "nearest_greedy")) for p in plans]
    our_pick = min(our, key=lambda it: (it[1]["autosolver_score"], it[1]["timeout_risk"], it[1]["finish_at_s"], str(it[1]["courier_id"])))
    base_pick = min(base, key=lambda it: (it[1]["pickup_distance_m"], it[1]["courier_available_at_s"], str(it[1]["courier_id"])))
    picked_id = str(our_pick[1]["courier_id"])
    base_id = str(base_pick[1]["courier_id"])

    candidates = []
    for p, prof in sorted(our, key=lambda it: it[1]["autosolver_score"]):
        cid = str(prof["courier_id"])
        candidates.append(
            {
                "courier_id": cid,
                "distance_m": round(float(prof["pickup_distance_m"]), 1),
                "eta_min": round(float(prof["total_eta_s"]) / 60.0, 1),
                "cost_yuan": round(float(prof["expected_cost_yuan"]), 2),
                "timeout_risk": round(float(prof["timeout_risk"]), 3),
                "score": round(float(prof["autosolver_score"]), 1),
                "selected": cid == picked_id,
                "baseline_pick": cid == base_id,
            }
        )

    # 只对选中骑手联网取真实路网：重算它的 profile（真实距离→展示的 eta/成本）+ 取几何折线（取餐段+配送段）。
    # 仅 2 次网络请求、缓存后即时——这是把响应从 ~10s（原来对每个候选都联网）降到 1~2s 的关键。
    picked_pos = our_pick[0].position
    prev_net = road_routing_patch.ALLOW_NETWORK
    road_routing_patch.ALLOW_NETWORK = True
    try:
        picked_prof = _profile_of(slice_, order, our_pick[0], "autosolver_agent")  # 真实路网距离重算展示值
        pickup_leg = rr.lookup_leg(picked_pos.lat, picked_pos.lng, merchant_pos.lat, merchant_pos.lng, allow_network=True)
        delivery_leg = rr.lookup_leg(merchant_pos.lat, merchant_pos.lng, dest_pos.lat, dest_pos.lng, allow_network=True)
    finally:
        road_routing_patch.ALLOW_NETWORK = prev_net
    return {
        "status": "ok",
        "selected_courier_id": picked_id,
        "baseline_courier_id": base_id,
        "differs_from_baseline": picked_id != base_id,
        "eta_min": round(float(picked_prof["total_eta_s"]) / 60.0, 1),
        # 动画用：取餐段/总时长（秒），让临时单能像真实订单一样按时间推进「取餐中→配送中→已送达」。
        "pickup_eta_s": round(float(picked_prof["pickup_eta_s"]), 1),
        "total_eta_s": round(float(picked_prof["total_eta_s"]), 1),
        "cost_yuan": round(float(picked_prof["expected_cost_yuan"]), 2),
        "timeout_risk": round(float(picked_prof["timeout_risk"]), 3),
        "score": round(float(picked_prof["autosolver_score"]), 1),
        "route": {
            "courier": {"lat": our_pick[0].position.lat, "lng": our_pick[0].position.lng},
            "merchant": {"lat": merchant_pos.lat, "lng": merchant_pos.lng},
            "destination": {"lat": dest_pos.lat, "lng": dest_pos.lng},
            # 真实路网折线：前端注入单据此沿路跑（点含 lat/lng/screen_x/screen_y）。
            "pickup_polyline": pickup_leg["points"],
            "delivery_polyline": delivery_leg["points"],
        },
        "candidates": candidates,
        "candidate_count": len(candidates),
        "order_id": order.id,
    }
