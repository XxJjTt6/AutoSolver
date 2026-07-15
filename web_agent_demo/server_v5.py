"""v5 启动器：基于 v4，对比页第 4 项指标由「P95 送达时长」换成「慢单率(>25min)」（P95 与均时曲线语义重复）。
复用原 server.py 的全部后端逻辑，仅把首页渲染替换为 day_replay_frontend_v5.render_day_replay_index。
不改动 server.py / server_v4.py / day_replay_frontend_v4.py 任何原文件。

用法与原 server 一致：
    python3 web_agent_demo/server_v5.py --host 127.0.0.1 --port 8799
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许以脚本方式直接运行（python3 web_agent_demo/server_v5.py）。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_agent_demo import server  # noqa: E402

# 道路路由补丁：把「直线距离 + 按算法暗改的乘子」换成真实路网单一事实源（前后端一致、铲除造假）。
# 必须在首次渲染/首次跑仿真之前 apply（day_replay_frontend_v5 的 _bootstrap_payload 惰性缓存首个请求时才跑仿真）。
# 生产态 allow_network=False：只读 route_cache.json（离线、快）；未命中才回退直线×绕路系数。
from web_agent_demo import road_routing_patch  # noqa: E402

road_routing_patch.apply(allow_network=False)

from web_agent_demo.day_replay_frontend_v5 import render_day_replay_index  # noqa: E402


def _render_index_v3() -> str:
    return render_day_replay_index()


# AgentRequestHandler.do_GET 内部直接调用模块级 render_index()，
# 在此处替换 server 模块命名空间里的引用即可让 v3 生效。
server.render_index = _render_index_v3


# 追加实时派单接口 POST /api/live-dispatch（问题二：中途加临时订单/骑手→后端真算派单），
# 包装原 do_POST：命中新路由则本地处理，否则委托原逻辑。不改 server.py 原文件。
import traceback  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

_orig_do_POST = server.AgentRequestHandler.do_POST


def _do_POST_v3(self) -> None:
    parsed = urlparse(self.path)
    if parsed.path == "/api/live-dispatch":
        try:
            from web_agent_demo.live_dispatch_engine import live_dispatch
            payload = self._read_json()
            self._send_json(live_dispatch(payload))
        except Exception as exc:  # noqa: BLE001
            self._send_json(
                {"status": "error", "error": str(exc), "traceback": traceback.format_exc()},
                status=500,
            )
        return
    # 可选：千问(LLM) 生成本轮派单策略（默认前端关闭；仅勾选并请求时命中）。key 只从环境变量读。
    if parsed.path == "/api/llm-strategy":
        try:
            from web_agent_demo.llm_strategy import generate_strategy
            self._send_json(generate_strategy(self._read_json()))
        except Exception as exc:  # noqa: BLE001
            self._send_json({"status": "error", "message": str(exc)}, status=500)
        return
    # 后台管理：订单池/骑手运力页新增订单/骑手。**添加秒回**（只记花名册），
    # 全天推演重算放后台线程跑（含联网取新增实体的真实路网腿），前端轮询 /api/roster-status，
    # done 后自动刷新——用户不必守着弹窗等（真实重算逻辑不变，只是不再阻塞交互）。
    if parsed.path == "/api/roster-status":
        from web_agent_demo import runtime_roster
        with _roster_recalc_lock:
            state = dict(_roster_recalc_state)
        self._send_json({"status": "ok", "recalc": state["status"], "error": state["error"], "roster": runtime_roster.counts()})
        return
    if parsed.path in ("/api/roster-add", "/api/roster-clear"):
        try:
            from web_agent_demo import runtime_roster
            payload = self._read_json() if parsed.path == "/api/roster-add" else {}
            added = None
            if parsed.path == "/api/roster-add":
                # 因果约束：中途加的订单/骑手只能影响「当前推演时刻之后」——下单时间、骑手上线时间
                # 一律 clamp 到 ≥ 前端传来的当前推演时刻（sim_time_s）。配合确定性派单，
                # 之前已发生的派单结果保持逐字节不变，只有之后的决策把新实体纳入。
                sim_now = int(payload.get("sim_time_s", 7 * 3600))
                if payload.get("type") == "order":
                    created = max(int(payload.get("created_at_s", 12 * 3600)), sim_now)
                    added = runtime_roster.add_order(str(payload.get("merchant_id", "")), created, str(payload.get("note", "")))
                elif payload.get("type") == "rider":
                    start = max(int(payload.get("shift_start_s", 7 * 3600)), sim_now)
                    end = max(int(payload.get("shift_end_s", 23 * 3600)), start + 1800)
                    added = runtime_roster.add_rider(str(payload.get("zone_id", "office_core")), start, end, int(payload.get("capacity", 3)))
                else:
                    self._send_json({"status": "error", "message": "type 必须是 order 或 rider"}, status=400)
                    return
            else:
                runtime_roster.clear()
            _start_roster_recalc()
            self._send_json({"status": "ok", "added": added, "roster": runtime_roster.counts(), "recalc": "background"})
        except Exception as exc:  # noqa: BLE001
            self._send_json({"status": "error", "message": str(exc), "traceback": traceback.format_exc()}, status=500)
        return
    return _orig_do_POST(self)


# ---- roster 后台重算：单线程串行；状态供前端轮询 ----
import threading  # noqa: E402

_roster_recalc_state = {"status": "idle", "error": "", "generation": 0}
_roster_recalc_lock = threading.Lock()


def _start_roster_recalc() -> None:
    def _worker(gen: int) -> None:
        from web_agent_demo import runtime_roster, road_routing_patch, road_routing
        from web_agent_demo import day_replay_frontend_v5 as fe
        try:
            fe._bootstrap_payload.cache_clear()
            prev_geo = road_routing_patch.GEOMETRY_NETWORK
            # 打分候选比较走缓存/快速估算；只有 realized 真实路线联网（展示的每条线/数字仍是真实路网）。
            road_routing_patch.GEOMETRY_NETWORK = bool(runtime_roster.counts()["orders"] or runtime_roster.counts()["riders"])
            try:
                fe._bootstrap_payload()  # 重算并填充缓存（完成后前端刷新即拿新世界）
            finally:
                road_routing_patch.GEOMETRY_NETWORK = prev_geo
                road_routing.save_cache()
            with _roster_recalc_lock:
                if _roster_recalc_state["generation"] == gen:
                    _roster_recalc_state["status"] = "done"
        except Exception as exc:  # noqa: BLE001
            with _roster_recalc_lock:
                if _roster_recalc_state["generation"] == gen:
                    _roster_recalc_state["status"] = "error"
                    _roster_recalc_state["error"] = str(exc)

    with _roster_recalc_lock:
        _roster_recalc_state["generation"] += 1
        _roster_recalc_state["status"] = "running"
        _roster_recalc_state["error"] = ""
        gen = _roster_recalc_state["generation"]
    threading.Thread(target=_worker, args=(gen,), daemon=True).start()


server.AgentRequestHandler.do_POST = _do_POST_v3


if __name__ == "__main__":
    raise SystemExit(server.main())
