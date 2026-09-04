# 调度工作台

`web_agent_demo/` 将求解算法、全天订单流、骑手状态、路线数据和长期记忆组织为可交互的五页工作台。

## 启动

```bash
python3 web_agent_demo/server_v9.py --host 127.0.0.1 --port 8799
```

浏览器访问 `http://127.0.0.1:8799`。核心演示仅依赖 Python 标准库；路线优先读取本地缓存，外部地图资源不可用时仍可展示回退视图。

## 当前入口

| 文件 | 职责 |
|---|---|
| `server_v9.py` | 当前启动器；复用基础服务并加载 v9 工作台。 |
| `day_replay_frontend_v9.py` | 渲染双屏对比、决策、记忆、订单池和骑手运力页面。 |
| `day_simulation.py` | 在相同输入和时间轴上运行基线与 AutoSolver。 |
| `dispatch_workbench_data.py` | 将仿真合同转换为页面实体、决策和记忆数据。 |
| `compare_engine.py` | 运行候选策略比较和评分。 |
| `memory_engine.py` | 管理经验召回、反馈和置信度更新。 |
| `road_routing.py` | 提供路线缓存、路径与距离数据。 |
| `runtime_roster.py` | 管理演示中临时加入的订单和骑手。 |

`server.py` 至 `server_v8.py` 以及对应前端文件用于保留迭代过程；新演示应使用 v9 入口。
