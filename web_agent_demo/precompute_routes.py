"""离线预计算道路路由缓存（一次性，联网跑一遍）。

思路：给 day_simulation 打上道路补丁（ALLOW_NETWORK=True），用**与前端完全相同的 seed/controls**跑一遍
全天对比仿真。仿真需要哪条腿（打分的取餐/配送腿 + realized 路线折线）就现取现缓存 OSRM 真实路网。
由于同 seed/controls 决定论，生产端回放会命中**完全相同**的腿 → 100% 命中、零回退。

用法：
    python3 web_agent_demo/precompute_routes.py
产物：web_agent_demo/route_cache.json
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_agent_demo import road_routing as rr
from web_agent_demo import road_routing_patch


def main() -> int:
    rr.verbose = True
    # 与 day_replay_frontend_v3._bootstrap_payload 完全一致的参数（否则触及的 O-D 腿会不同）。
    road_routing_patch.apply(allow_network=True, pace_s=0.18)
    from web_agent_demo.day_simulation import DaySimulationControls, run_full_day_comparison

    # 必须与 day_replay_frontend_v3._bootstrap_payload 完全一致（高峰+适度紧缺 ~378单/11骑手，含合单多点路线）。
    controls = DaySimulationControls(courier_count=11, order_scale=0.68, weather="mixed", congestion_profile="weekday")
    started = time.time()
    print("[precompute] 开始跑全天对比仿真（联网取真实路网）……", flush=True)
    run_full_day_comparison(seed="frontend-shell", controls=controls)
    rr.save_cache()
    stats = rr.cache_stats()
    took = time.time() - started
    print(
        f"[precompute] 完成：缓存腿数={stats['cached_legs']}  联网次数={rr.network_calls}  "
        f"回退次数={rr.fallback_hits}  用时={took:.0f}s\n  缓存文件={stats['cache_path']}",
        flush=True,
    )
    if rr.fallback_hits > 0:
        print(
            f"[precompute] 警告：有 {rr.fallback_hits} 条腿走了回退（OSRM 未成功）。"
            f"再跑一次本脚本可续取（缓存持久化、命中的不会重复请求）。",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
