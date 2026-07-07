"""v3 启动器：合并版前端 —— v1 的双屏对比（原样保留）+ v2 的长期记忆（自主学习可视化）。
复用原 server.py 的全部后端逻辑，仅把首页渲染替换为 day_replay_frontend_v3.render_day_replay_index。
不改动 server.py / day_replay_frontend.py / day_replay_frontend_v2.py 任何原文件。

用法与原 server 一致：
    python3 web_agent_demo/server_v3.py --host 127.0.0.1 --port 8799
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许以脚本方式直接运行（python3 web_agent_demo/server_v3.py）。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_agent_demo import server  # noqa: E402
from web_agent_demo.day_replay_frontend_v3 import render_day_replay_index  # noqa: E402


def _render_index_v3() -> str:
    return render_day_replay_index()


# AgentRequestHandler.do_GET 内部直接调用模块级 render_index()，
# 在此处替换 server 模块命名空间里的引用即可让 v3 生效。
server.render_index = _render_index_v3


if __name__ == "__main__":
    raise SystemExit(server.main())
