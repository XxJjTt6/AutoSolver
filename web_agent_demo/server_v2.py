"""v2 启动器：复用原 server.py 的全部后端逻辑，仅把首页渲染替换为
day_replay_frontend_v2.render_day_replay_index（自解释改造版），不改动任何原文件。

用法与原 server 一致：
    python3 web_agent_demo/server_v2.py --host 127.0.0.1 --port 8765
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许以脚本方式直接运行（python3 web_agent_demo/server_v2.py）。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_agent_demo import server  # noqa: E402
from web_agent_demo.day_replay_frontend_v2 import render_day_replay_index  # noqa: E402


def _render_index_v2() -> str:
    return render_day_replay_index()


# AgentRequestHandler.do_GET 内部直接调用模块级 render_index()，
# 在此处替换 server 模块命名空间里的引用即可让 v2 生效。
server.render_index = _render_index_v2


if __name__ == "__main__":
    raise SystemExit(server.main())
