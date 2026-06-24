"""server_v4 —— v4 演示服务（双屏动态对比 + 流动粒子线 + LLM 学习轨道）。

不改原 server.py。默认读 committed demo trace（断网/无 key 可演示）；?live=1 现场重算。
数据函数与 HTTP 分离，便于单测。

启动: python3 web_agent_demo/server_v4.py --host 127.0.0.1 --port 8770
"""
from __future__ import annotations

import argparse
import http.server
import json
import sys
import urllib.parse
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_dynamic_v4 import rolling_solver_v4 as rs  # noqa: E402
from autosolver_dynamic_v4.scenario_builder_v4 import SCENARIOS, list_scenarios  # noqa: E402

STATIC = _ROOT / "web_agent_demo" / "static"
DEMO_DYN = _ROOT / "autosolver_dynamic_v4" / "demo"
DEMO_LINEAGE = _ROOT / "autosolver_llm_v4" / "demo_runs" / "deepseek_iter02_lineage"
DATA = _ROOT / "data" / "official_cases"


# ---------------- 数据函数（可单测） ----------------
def get_scenarios() -> dict:
    return {"status": "ok", "scenarios": list_scenarios()}


def get_dynamic(case: str = "large_seed301", scenario: str = "weekday_peaks", live: bool = False) -> dict:
    if scenario not in SCENARIOS:
        scenario = "weekday_peaks"
    if not live:
        cached = DEMO_DYN / f"{case}_{scenario}.json"
        if cached.exists():
            data = json.loads(cached.read_text(encoding="utf-8"))
            data["source"] = "demo_cache"
            return data
    case_path = DATA / (case if case.endswith(".txt") else f"{case}.txt")
    if not case_path.exists():
        return {"error": f"case not found: {case}"}
    data = rs.simulate(case_path.read_text(encoding="utf-8"), scenario)
    data["source"] = "live"
    return data


def get_lineage() -> dict:
    f = DEMO_LINEAGE / "result.json"
    if not f.exists():
        return {"error": "no lineage demo"}
    return json.loads(f.read_text(encoding="utf-8"))


def get_commentary(scenario: str = "weekday_peaks") -> dict:
    f = DEMO_DYN / f"commentary_{scenario}.json"
    if not f.exists():
        return {"scenario": scenario, "by_tick": {}}
    return json.loads(f.read_text(encoding="utf-8"))


def get_events() -> dict:
    f = DEMO_LINEAGE / "events.jsonl"
    if not f.exists():
        return {"status": "ok", "events": []}
    events = [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"status": "ok", "events": events}


# ---------------- HTTP ----------------
class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, obj, ctype="application/json", code=200):
        if ctype == "application/json":
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        else:
            body = obj if isinstance(obj, bytes) else str(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if "json" in ctype or "text" in ctype or "javascript" in ctype else ""))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        q = urllib.parse.parse_qs(parsed.query)
        try:
            if path in ("/", "/index.html"):
                return self._send(render_index(), ctype="text/html")
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/"):])
            if path == "/api/v4/scenarios":
                return self._send(get_scenarios())
            if path == "/api/v4/dynamic":
                return self._send(get_dynamic(
                    q.get("case", ["large_seed301"])[0],
                    q.get("scenario", ["weekday_peaks"])[0],
                    q.get("live", ["0"])[0] in ("1", "true"),
                ))
            if path == "/api/v4/commentary":
                return self._send(get_commentary(q.get("scenario", ["weekday_peaks"])[0]))
            if path == "/api/v4/llm/lineage":
                return self._send(get_lineage())
            if path == "/api/v4/llm/events":
                return self._send(get_events())
            return self._send({"error": "not found"}, code=404)
        except Exception as exc:  # noqa: BLE001
            return self._send({"error": str(exc)}, code=500)

    def _serve_static(self, name):
        fp = (STATIC / name).resolve()
        if not str(fp).startswith(str(STATIC.resolve())) or not fp.exists():
            return self._send({"error": "not found"}, code=404)
        ctype = "text/css" if name.endswith(".css") else "application/javascript" if name.endswith(".js") else "text/plain"
        return self._send(fp.read_bytes(), ctype=ctype)


def render_index() -> str:
    return """<!doctype html><html lang=zh><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>AutoSolver · 动态调度 + LLM 自主学习</title>
<link rel=stylesheet href=/static/styles_v4.css></head><body>
<header class=topbar>
  <div class=brand>AutoSolver <span>· 即时配送动态调度 + LLM 自主学习</span></div>
  <div class=controls>
    <select id=scenario></select>
    <button id=play class=primary>▶ 播放动态仿真</button>
    <span id=clock class=clock>--:--</span>
    <span id=src class=tag></span>
  </div>
</header>
<section id=verdict class=verdict></section>
<section class=stage>
  <div class=panel><div class=panel-h>左屏 · Greedy 基线</div><svg id=mapL viewBox="0 0 100 100" preserveAspectRatio=xMidYMid></svg></div>
  <div class=panel right><div class=panel-h>右屏 · AutoSolver（暖启动·发光流动粒子线）</div><svg id=mapR viewBox="0 0 100 100" preserveAspectRatio=xMidYMid></svg></div>
</section>
<section id=commentary class=commentary><span class=cmt-ico>🧠 调度解说（DeepSeek·只解说不决策）</span><span id=cmtText class=cmt-text>—</span></section>
<section class=curves>
  <div class=chart-box><div class=chart-h>每单期望成本（越低越好）· greedy / cold / warm 三泳道</div><svg id=costChart viewBox="0 0 100 100" preserveAspectRatio=none></svg></div>
  <div class=chart-box><div class=chart-h>订单到达量（一天）</div><svg id=arrChart viewBox="0 0 100 100" preserveAspectRatio=none></svg></div>
</section>
<section class=learn>
  <div class=learn-h>LLM 自主学习轨道（时钟A · 离线 DeepSeek 真实回放）<span id=learnSub></span></div>
  <div id=ribbon class=ribbon></div>
  <div class=learn-body>
    <div id=roundStream class=stream></div>
    <div class=learn-right><div class=chart-h>best-so-far（学习结果）</div><svg id=bestChart viewBox="0 0 100 100" preserveAspectRatio=none></svg></div>
  </div>
</section>
<script src=/static/flow_route_v4.js></script>
<script src=/static/charts_v4.js></script>
<script src=/static/llm_trace_v4.js></script>
<script src=/static/dashboard_v4.js></script>
</body></html>"""


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8770)
    a = p.parse_args(argv)
    httpd = http.server.ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"server_v4 on http://{a.host}:{a.port}  (Ctrl-C 退出)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
