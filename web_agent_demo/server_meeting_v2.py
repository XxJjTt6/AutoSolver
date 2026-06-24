"""会议方案 v4 · 演示服务入口 (server_meeting_v2)。

只读后端: 不跑求解、不调 LLM、不写盘。复用 learning_feed_v2 把真实离线进化记录喂前端。
原 web_agent_demo/server.py 与正式 solver.py / autosolver_agent/ 全部零改动。

启动:
  python3 web_agent_demo/server_meeting_v2.py --host 127.0.0.1 --port 8766
路由:
  GET  /                              → static/meeting_v2.html  (三幕单线引导页)
  GET  /assets/<file>                 → static/ 下静态资源 (js/css/...)
  GET  /api/meeting-v2/learning-trace → 真实学习轨道数据 (失败回退预生成快照)
  GET  /healthz                       → {"ok": true}
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web_agent_demo import learning_feed_v2 as feed  # noqa: E402

STATIC_DIR = ROOT / "web_agent_demo" / "static"
SNAPSHOT = ROOT / "docs" / "prebuilt" / "learning-trace.json"

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


def _learning_trace() -> dict:
    """优先真实解析; 任何异常回退预生成快照, 保证断网/坏数据也能出页面。"""
    try:
        return feed.build_payload()
    except Exception as exc:  # noqa: BLE001 - 演示服务: 任何异常都降级到快照
        if SNAPSHOT.exists():
            payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            payload["_fallback"] = f"live parse failed, served snapshot: {exc}"
            return payload
        raise


class MeetingHandler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        self._send(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8", status)

    def _send_static(self, rel: str) -> bool:
        # 防目录穿越: 解析后必须仍在 STATIC_DIR 内。
        target = (STATIC_DIR / rel).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return False
        if not target.is_file():
            return False
        ctype = _CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send(target.read_bytes(), ctype)
        return True

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        try:
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                if not self._send_static("meeting_v2.html"):
                    self._send(b"meeting_v2.html missing", "text/plain; charset=utf-8", 404)
                return
            if path == "/healthz":
                self._send_json({"ok": True})
                return
            if path == "/api/meeting-v2/learning-trace":
                self._send_json(_learning_trace())
                return
            if path.startswith("/assets/"):
                if self._send_static(path[len("/assets/"):]):
                    return
                self._send(b"asset not found", "text/plain; charset=utf-8", 404)
                return
            self._send(b"not found", "text/plain; charset=utf-8", 404)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, status=500)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[meeting-v2] {self.address_string()} - {fmt % args}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="会议方案 v4 演示服务 (学习轨道控制台)。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--selfcheck", action="store_true", help="只跑数据自检后退出, 不起服务")
    args = parser.parse_args(argv)

    if args.selfcheck:
        p = _learning_trace()
        s = p["stats"]
        ok = (s["generated"] == 7 and s["validated"] == 14 and s["trial"] == 7
              and s["accepted"] == 0 and len(p["strategies"]) == 5)
        print(f"[selfcheck] stats={s} strategies={len(p['strategies'])} → {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    server = ThreadingHTTPServer((args.host, args.port), MeetingHandler)
    print(f"会议方案 v4 演示服务: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
