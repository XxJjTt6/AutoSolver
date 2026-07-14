"""道路路由：为 day-replay 提供真实上海路网折线 + 道路距离，作为**前后端唯一事实源**。

设计要点（回应「路线不能穿楼」+「前后端必须一致」+「不能造假」）：
- 预计算阶段（precompute_routes.py）调 OSRM 公共服务，把每条 O-D 的道路折线 + 道路距离写盘缓存。
- 仿真 / 服务阶段**只读盘缓存**（离线、快）；命中不了才回退「直线×绕路系数 + 少量插值点」，并计数用于自检。
- 两个算法对同一条 O-D 拿到的是**同一条道路距离**——从根上铲除原 `_routing_factor` 按算法打折的暗改。

折线上的点用 dict 表示：{lat, lng, screen_x, screen_y}，与 day_simulation.simulation_to_dict(Position) 完全同构，
可直接放进 route 的 polyline，前端 Leaflet 用 lat/lng、SVG 用 screen_x/screen_y。screen 投影严格复刻
simulation_engine._screen_project，保证道路点与既有点落在同一屏幕坐标系里。
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# 与 day_simulation.DayScenario.map_bounds 完全一致（上海人民广场一带的真实经纬度框）。
_SW_LAT, _SW_LNG = 31.2148, 121.4520
_NE_LAT, _NE_LNG = 31.2460, 121.4954

_CACHE_PATH = Path(__file__).resolve().parent / "route_cache.json"
# 用「步行/非机动车」路网而非开车：外卖电动车骑手走人行道/小区/胡同小路，路径更直、更真实，
# 不像开车路网只肯走大路、爱绕大圈。FOSSGIS 公共 OSRM foot 实例（无需 key）。
_OSRM_BASE = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/"

# 回退（缓存未命中且不允许联网时）：城市道路相对直线的典型绕路系数（实测样本≈1.48，取 1.45 稍保守）。
_FALLBACK_DETOUR = 1.45

_EARTH_MPERDEG = 111_000.0

# 运行期自检：统计有多少条腿走了回退（预计算完整时应为 0）。
fallback_hits = 0
network_calls = 0          # 预计算时真实命中 OSRM 的次数
verbose = False            # 预计算把它设 True → 每 50 次联网打印一次进度
_cache: dict[str, Any] | None = None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _screen_project(lat: float, lng: float) -> tuple[float, float]:
    """严格复刻 simulation_engine._screen_project：经度→x(0..100)、纬度→y(0..100，北在上=y小)。"""
    screen_x = (lng - _SW_LNG) / max(1e-9, _NE_LNG - _SW_LNG) * 100.0
    screen_y = 100.0 - (lat - _SW_LAT) / max(1e-9, _NE_LAT - _SW_LAT) * 100.0
    return round(_clamp(screen_x, 0.0, 100.0), 3), round(_clamp(screen_y, 0.0, 100.0), 3)


def _point(lat: float, lng: float) -> dict[str, float]:
    sx, sy = _screen_project(lat, lng)
    return {"lat": round(lat, 7), "lng": round(lng, 7), "screen_x": sx, "screen_y": sy}


def _straight_distance_m(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    """与 day_simulation._distance_m 同口径的直线距离（等距圆柱近似 × 111000）。"""
    lat_m = (a_lat - b_lat) * _EARTH_MPERDEG
    lng_m = (a_lng - b_lng) * _EARTH_MPERDEG * math.cos(math.radians((a_lat + b_lat) / 2.0))
    return math.hypot(lat_m, lng_m)


def _key(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> str:
    # 5 位小数≈1m，足以把「骑手停在同一送达点」这类重复 O-D 合并命中。
    return f"{a_lat:.5f},{a_lng:.5f};{b_lat:.5f},{b_lng:.5f}"


def _load_cache() -> dict[str, Any]:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - 无缓存时从空开始
            _cache = {}
    return _cache


def save_cache() -> None:
    if _cache is not None:
        _CACHE_PATH.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")


def _fallback_leg(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> dict[str, Any]:
    global fallback_hits
    fallback_hits += 1
    # 直线加一个中点，距离按绕路系数放大（明确是回退近似，不冒充真实路网）。
    mid = _point((a_lat + b_lat) / 2.0, (a_lng + b_lng) / 2.0)
    pts = [_point(a_lat, a_lng), mid, _point(b_lat, b_lng)]
    dist = _straight_distance_m(a_lat, a_lng, b_lat, b_lng) * _FALLBACK_DETOUR
    return {"points": pts, "distance_m": round(dist, 3), "fallback": True}


def _osrm_leg(a_lat: float, a_lng: float, b_lat: float, b_lng: float, timeout: float = 15.0, retries: int = 3) -> dict[str, Any] | None:
    """调 OSRM 拿真实路网折线 + 道路距离；失败返回 None（交由回退处理）。仅预计算/运行时联网路径调用。

    预计算时任何一条腿走回退都会让生产端也回退，故这里带重试+退避，尽量把每条腿真实缓存下来。
    """
    coords = f"{a_lng},{a_lat};{b_lng},{b_lat}"
    url = _OSRM_BASE + urllib.parse.quote(coords) + "?overview=full&geometries=geojson&continue_straight=true"
    for attempt in range(max(1, retries)):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") != "Ok" or not data.get("routes"):
                return None
            route = data["routes"][0]
            coords_lnglat = route["geometry"]["coordinates"]
            if len(coords_lnglat) < 2:
                return None
            points = [_point(float(lat), float(lng)) for lng, lat in coords_lnglat]
            return {"points": points, "distance_m": round(float(route["distance"]), 3), "fallback": False}
        except Exception:  # noqa: BLE001 - 网络/解析异常：重试，最终失败交回退
            if attempt < retries - 1:
                time.sleep(0.6 * (attempt + 1))
    return None


def lookup_leg(
    a_lat: float,
    a_lng: float,
    b_lat: float,
    b_lng: float,
    *,
    allow_network: bool = False,
    pace_s: float = 0.0,
) -> dict[str, Any]:
    """取一条腿的道路折线 + 距离。

    allow_network=False（仿真/服务态）：只读缓存，未命中即回退（并计数）。
    allow_network=True（预计算/临时单）：未命中时联网请求 OSRM，成功则写回缓存。
    返回 {"points": [ {lat,lng,screen_x,screen_y}... ], "distance_m": float, "fallback": bool}
    """
    cache = _load_cache()
    key = _key(a_lat, a_lng, b_lat, b_lng)
    hit = cache.get(key)
    if hit:
        return hit
    if allow_network:
        if pace_s:
            time.sleep(pace_s)
        leg = _osrm_leg(a_lat, a_lng, b_lat, b_lng)
        if leg is not None:
            global network_calls
            network_calls += 1
            cache[key] = leg
            if network_calls % 100 == 0:
                save_cache()  # 增量落盘：预计算被中断也能续跑（已取的不重复请求）
            if verbose and network_calls % 50 == 0:
                print(f"[road_routing] OSRM 已取 {network_calls} 条腿，缓存 {len(cache)}，回退 {fallback_hits}", flush=True)
            return leg
    return _fallback_leg(a_lat, a_lng, b_lat, b_lng)


def route_two_legs(
    courier_lat: float,
    courier_lng: float,
    merchant_lat: float,
    merchant_lng: float,
    dest_lat: float,
    dest_lng: float,
    *,
    allow_network: bool = False,
    pace_s: float = 0.0,
) -> dict[str, Any]:
    """骑手→商家（取餐段）+ 商家→客户（配送段）拼成一条道路折线。

    返回 {"polyline":[...], "merchant_index":int, "pickup_distance_m":float,
          "delivery_distance_m":float, "total_distance_m":float, "fallback":bool}
    merchant_index = 取餐段最后一点（=商家）在整条 polyline 里的下标，供前端按商家顶点拆「取餐/配送」两段。
    """
    pickup = lookup_leg(courier_lat, courier_lng, merchant_lat, merchant_lng, allow_network=allow_network, pace_s=pace_s)
    delivery = lookup_leg(merchant_lat, merchant_lng, dest_lat, dest_lng, allow_network=allow_network, pace_s=pace_s)
    pickup_pts = pickup["points"]
    delivery_pts = delivery["points"]
    # 商家顶点是取餐段末点 = 配送段首点，去掉重复的那一个。
    merchant_index = len(pickup_pts) - 1
    polyline = list(pickup_pts) + list(delivery_pts[1:])
    return {
        "polyline": polyline,
        "merchant_index": merchant_index,
        "pickup_distance_m": pickup["distance_m"],
        "delivery_distance_m": delivery["distance_m"],
        "total_distance_m": round(pickup["distance_m"] + delivery["distance_m"], 3),
        "fallback": bool(pickup.get("fallback") or delivery.get("fallback")),
    }


def cache_stats() -> dict[str, Any]:
    cache = _load_cache()
    return {"cached_legs": len(cache), "fallback_hits": fallback_hits, "cache_path": str(_CACHE_PATH)}
