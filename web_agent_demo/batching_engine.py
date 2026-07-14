"""顺路合单引擎：只给我方(autosolver_agent)加「一个骑手顺路带多单」的真实批次派单。

基线(nearest_greedy)保持原样逐单派——调度领域标准的「朴素贪心 vs 智能合单」对比，
合单差距真实来自智能（会顺路合 vs 不会），不是写死乘子。

后端真算：真实形成批次（同商家/近商家+目的地相近，受容量约束）、真实路网多点路线
（骑手→取餐序→送达序）、每单真实送达时刻与距离；前端只画后端产物、不自己编造。

不改 day_simulation.py 原文件：apply 时保存原 _simulate_day_algorithm，我方走本模块、基线走原逻辑。
"""
from __future__ import annotations

from typing import Any

from web_agent_demo import day_simulation as ds
from web_agent_demo import road_routing as rr

CAP = 3                  # 骑手同时最多带单数（用现实量级；也可读 courier.capacity）
NEAR_MERCHANT_M = 260.0  # 可并入同批的商家间距上限（同商家=0；收紧=只合真正同片餐厅）
NEAR_DEST_M = 650.0      # 可并入同批的目的地间距上限（收紧=只合真正顺路、绕路小，保证合单省距离）

_orig_simulate = None    # apply 时保存的原 _simulate_day_algorithm（基线用）


def _net() -> tuple[bool, float]:
    # 批次的 realized 行程几何：ALLOW_NETWORK(预计算) 或 GEOMETRY_NETWORK(roster 增量重算) 时联网取真实路网。
    from web_agent_demo import road_routing_patch as p
    return (p.ALLOW_NETWORK or p.GEOMETRY_NETWORK), p._PACE_S


def _straight(a: Any, b: Any) -> float:
    return rr._straight_distance_m(a.lat, a.lng, b.lat, b.lng)


def _leg(a: Any, b: Any) -> dict[str, Any]:
    net, pace = _net()
    return rr.lookup_leg(a.lat, a.lng, b.lat, b.lng, allow_network=net, pace_s=pace)


def _same_pos(a: Any, b: Any) -> bool:
    return abs(a.lat - b.lat) < 1e-6 and abs(a.lng - b.lng) < 1e-6


def _form_batches(orders: list[Any]) -> list[list[Any]]:
    """同时段订单按「商家近 + 目的地相近」贪心合成批次，最多 CAP 单。这一步就是我方合单的真实决策。"""
    batches: list[list[Any]] = []
    for o in sorted(orders, key=lambda x: x.created_at_s):
        placed = False
        for b in batches:
            if len(b) >= CAP:
                continue
            merchant_ok = any(_straight(o.merchant_position, x.merchant_position) <= NEAR_MERCHANT_M for x in b)
            dest_ok = any(_straight(o.destination, x.destination) <= NEAR_DEST_M for x in b)
            if merchant_ok and dest_ok:
                b.append(o)
                placed = True
                break
        if not placed:
            batches.append([o])
    return batches


def _choose_courier(batch: list[Any], plans: dict[str, Any], time_slice: Any) -> Any:
    """给整批选最优骑手：候选限定「已空闲/很快空出」，用我方综合分对锚点单打分择优。"""
    anchor = batch[0]
    candidates = [p for p in plans.values() if p.courier.shift_start_s <= anchor.created_at_s < p.courier.shift_end_s]
    if not candidates:
        candidates = list(plans.values())
    reasonable = 18 * 60
    avail = [p for p in candidates if p.available_at_s <= anchor.created_at_s + reasonable]
    if avail:
        candidates = avail
    else:
        earliest = min(p.available_at_s for p in candidates)
        candidates = [p for p in candidates if p.available_at_s <= earliest + reasonable]
    return min(candidates, key=lambda p: (ds._assignment_profile(time_slice, anchor, p, "autosolver_agent")["autosolver_score"], p.courier.id))


def _run_batch(plan: Any, batch: list[Any], time_slice: Any) -> tuple[list[Any], list[dict[str, Any]], float, Any, float]:
    """真实跑一趟合单：骑手→取餐序(去重最近)→送达序(最近)。返回每单 record、每单 overlay、批次结束时刻、末点、总忙时。"""
    algo = "autosolver_agent"
    courier = plan.courier
    speed = ds._effective_speed_mps(courier, time_slice, algo)
    start_pos = plan.position
    batch_start_t = max(float(plan.available_at_s), min(float(o.created_at_s) for o in batch))

    # 取餐序：唯一商家，从骑手当前位置最近序。
    merchants: list[Any] = []
    for o in batch:
        if not any(_same_pos(o.merchant_position, m) for m in merchants):
            merchants.append(o.merchant_position)
    pickup_seq: list[Any] = []
    cur = start_pos
    remaining_m = merchants[:]
    while remaining_m:
        nxt = min(remaining_m, key=lambda m: _straight(cur, m))
        remaining_m.remove(nxt)
        pickup_seq.append(nxt)
        cur = nxt

    # 走取餐序：累积时刻、路径点、取餐段距离；到店等餐（prep）。
    pickup_points: list[dict[str, Any]] = [rr._point(start_pos.lat, start_pos.lng)]
    pickup_dist = 0.0
    t = batch_start_t
    cur = start_pos
    for m in pickup_seq:
        leg = _leg(cur, m)
        pickup_dist += leg["distance_m"]
        t += leg["distance_m"] / speed
        pickup_points += leg["points"][1:]
        for o in batch:
            if _same_pos(o.merchant_position, m):
                t = max(t, float(o.created_at_s) + float(o.prep_time_s))  # 等这家的餐出锅
        cur = m
    pickup_done_t = t
    merchant_index = len(pickup_points) - 1  # overlay 里「取餐段/配送段」的分割点（最后一个取餐点）

    # 配送序：客户从当前位置最近序。每单到达时刻=其真实送达时刻。
    records: list[Any] = []
    overlays: list[dict[str, Any]] = []
    cur_points = list(pickup_points)
    prev_pos = cur
    prev_t = pickup_done_t
    remaining_o = list(batch)
    first = True
    while remaining_o:
        o = min(remaining_o, key=lambda x: _straight(prev_pos, x.destination))
        remaining_o.remove(o)
        leg = _leg(prev_pos, o.destination)
        seg_dist = leg["distance_m"]
        arrive_t = prev_t + seg_dist / speed
        cur_points = cur_points + leg["points"][1:]  # 起点→取餐序→…→该单客户 的完整点串
        # 该单距离=边际配送段；第一个送达的单额外背取餐段，使 sum(单距离)=骑手真实总里程（不重复计）。
        order_dist = seg_dist + (pickup_dist if first else 0.0)
        first = False

        timeout_risk = ds._timeout_risk(o, time_slice, arrive_t, algo)
        expected_cost = ds._expected_cost_yuan(order_dist, max(0.0, batch_start_t - float(o.created_at_s)), timeout_risk, o, algo)
        assignment = ds.DispatchAssignment(
            order_id=o.id, courier_id=courier.id, merchant_id=o.merchant_id,
            pickup_eta_s=round(pickup_done_t - float(o.created_at_s), 3),
            delivery_eta_s=round(arrive_t - pickup_done_t, 3),
            total_eta_s=round(arrive_t - float(o.created_at_s), 3),
            expected_cost_yuan=round(expected_cost, 3),
            timeout_risk=round(timeout_risk, 4),
            rationale=f"AutoSolver 顺路合单：{courier.id} 一趟带 {len(batch)} 单",
        )
        records.append(ds._AssignmentRecord(
            assignment=assignment, slice_id=time_slice.id, created_at_s=o.created_at_s,
            finish_at_s=round(arrive_t, 3), distance_m=round(order_dist, 3),
            courier_busy_s=round(seg_dist / speed, 3), basket_value_yuan=o.basket_value_yuan,
            late=arrive_t > o.deadline_s, courier_start_position=start_pos,
            merchant_position=o.merchant_position, destination_position=o.destination,
        ))
        overlays.append({
            "lane": "challenger", "order_id": o.id, "courier_id": courier.id,
            "polyline": list(cur_points), "merchant_index": merchant_index,
            "batch_size": len(batch),
            "eta_s": assignment.total_eta_s, "cost_yuan": assignment.expected_cost_yuan,
            "assign_at_s": round(batch_start_t, 3),  # 骑手开始这趟合单的时刻
            "complete_at_s": round(arrive_t, 3),     # 该单真实送达时刻
        })
        prev_pos = o.destination
        prev_t = arrive_t

    finish = prev_t
    busy = finish - batch_start_t
    return records, overlays, finish, prev_pos, busy


def simulate_day_batched(world: Any, algorithm_id: str) -> Any:
    """我方(autosolver_agent) 走合单；其它算法(基线)走原逻辑，完全不变。"""
    if algorithm_id != "autosolver_agent":
        return _orig_simulate(world, algorithm_id)

    label, family = ds._algorithm_label_family(algorithm_id)
    plans = {c.id: ds._CourierPlan(courier=c, position=c.start_position, available_at_s=c.shift_start_s) for c in world.couriers}
    order_by_id = {o.id: o for o in world.orders}
    records_by_slice: dict[str, list[Any]] = {ts.id: [] for ts in world.time_slices}
    metrics_by_slice: dict[str, Any] = {}
    completed_by_slice: dict[str, tuple[str, ...]] = {}
    courier_positions_by_slice: dict[str, tuple[dict[str, Any], ...]] = {}
    route_overlays_by_slice: dict[str, tuple[dict[str, Any], ...]] = {}
    summary_by_slice: dict[str, str] = {}
    cumulative: list[Any] = []
    all_records: list[Any] = []

    for time_slice in world.time_slices:
        orders = [order_by_id[oid] for oid in time_slice.order_ids]
        slice_records: list[Any] = []
        slice_overlays: list[dict[str, Any]] = []
        for batch in _form_batches(orders):
            plan = _choose_courier(batch, plans, time_slice)
            recs, ovls, finish, last_pos, busy = _run_batch(plan, batch, time_slice)
            plan.available_at_s = finish
            plan.position = last_pos
            plan.busy_time_s += busy
            plan.assigned_count += len(batch)
            slice_records.extend(recs)
            slice_overlays.extend(ovls)
            all_records.extend(recs)
        cumulative.extend(slice_records)
        records_by_slice[time_slice.id] = slice_records
        metrics_by_slice[time_slice.id] = ds._metrics_from_records(cumulative, world, plans)
        completed_by_slice[time_slice.id] = tuple(r.assignment.order_id for r in cumulative if r.finish_at_s <= time_slice.end_s)
        courier_positions_by_slice[time_slice.id] = ds._courier_position_snapshots(plans, time_slice.end_s)
        route_overlays_by_slice[time_slice.id] = tuple(slice_overlays)
        summary_by_slice[time_slice.id] = ds._slice_decision_summary(algorithm_id, slice_records)

    frame_ids = tuple(ds._frame_id(ts.id) for ts in world.time_slices if ds._should_emit_frame(ts, records_by_slice[ts.id]))
    return ds._AlgorithmSimulationResult(
        algorithm_id=algorithm_id, label=label, family=family,
        metrics=ds._metrics_from_records(all_records, world, plans),
        frame_ids=frame_ids,
        records_by_slice={k: tuple(v) for k, v in records_by_slice.items()},
        metrics_by_slice=metrics_by_slice, completed_by_slice=completed_by_slice,
        courier_positions_by_slice=courier_positions_by_slice,
        route_overlays_by_slice=route_overlays_by_slice, summary_by_slice=summary_by_slice,
    )


def install() -> None:
    """在 road_routing_patch.apply() 里调用：保存原 _simulate_day_algorithm，替换为合单版。"""
    global _orig_simulate
    if _orig_simulate is None:
        _orig_simulate = ds._simulate_day_algorithm
    ds._simulate_day_algorithm = simulate_day_batched
