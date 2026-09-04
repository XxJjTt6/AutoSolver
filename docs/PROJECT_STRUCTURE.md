# 项目目录结构

本文说明当前 v9 版本的主要文件。正式求解器、网页演示和历史版本彼此独立，评委可以按下表快速定位。

## 核心目录

| 路径 | 当前定位 | 说明 |
|---|---|---|
| `solver.py` | 正式比赛求解入口 | 保留比赛要求的求解接口，与网页演示解耦。 |
| `solution.py` | 兼容入口 | 兼容其他导入或评测方式。 |
| `autosolver/` | 求解算法 | 包含候选生成、评估、组合搜索、回退和输出校验。 |
| `autosolver_agent/` | Agent 能力 | 包含控制、策略评估、记忆和实验能力。 |
| `web_agent_demo/` | 网页演示 | 包含全天仿真、算法对照、页面数据和本地服务。 |
| `tests/` | 自动化测试 | 覆盖求解器、仿真、双屏对比、长期记忆和页面契约。 |
| `tools/` | 辅助工具 | 包含打包、追踪和演示辅助脚本。 |
| `docs/` | 对外文档 | 包含文档中心、作品简介、产品说明和项目文档。 |

## 当前演示入口

| 路径 | 作用 |
|---|---|
| `web_agent_demo/server_v9.py` | 当前本地启动入口；复用基础服务并加载 v9 工作台。 |
| `web_agent_demo/day_replay_frontend_v9.py` | 生成双屏对比、已发生决策、长期记忆、订单池和骑手运力五个页面。 |
| `web_agent_demo/day_simulation.py` | 生成同一订单流下的基线与 AutoSolver 全天对照结果。 |
| `web_agent_demo/dispatch_workbench_data.py` | 把仿真结果整理为页面需要的订单、骑手、决策和记忆数据。 |
| `web_agent_demo/compare_engine.py` | 运行候选算法比较和评分。 |
| `web_agent_demo/memory_engine.py` | 管理调度经验、召回和结果反馈。 |
| `web_agent_demo/road_routing.py` | 读取路网缓存并提供路线数据。 |
| `web_agent_demo/runtime_roster.py` | 管理演示中临时新增的订单和骑手。 |

启动方式：

```bash
python3 web_agent_demo/server_v9.py --host 127.0.0.1 --port 8799
```

## 版本边界

| 文件 | 状态 |
|---|---|
| `server_v9.py`、`day_replay_frontend_v9.py` | 当前正式演示版本。 |
| `server.py`、`server_v2.py` 至 `server_v8.py` | 历史服务入口，保留用于回看迭代。 |
| `day_replay_frontend.py`、`day_replay_frontend_v2.py` 至 `day_replay_frontend_v8.py` | 历史页面版本，不作为当前启动入口。 |

历史文件不会影响 `server_v9.py` 的运行，也不需要在演示前删除。

## 数据与运行态文件

| 路径 | 说明 |
|---|---|
| `data/official_cases/` | 官方或脱敏样例数据。 |
| `web_agent_demo/generated_cases/` | 演示用构造样例。 |
| `web_agent_demo/route_cache.json` | 离线路线路径缓存。 |
| `web_agent_demo/.simulation_memory/` | 页面运行后按需生成的仿真记忆。 |
| `autosolver_agent/evolution_state/` | Agent 运行时状态。 |

`__pycache__/`、`*.pyc`、`.DS_Store` 和本地运行态缓存不属于正式源码或对外文档。

## 页面数据链路

```text
server_v9.py
  -> day_replay_frontend_v9.py
  -> run_full_day_comparison()
  -> build_dispatch_workbench_payload()
  -> 浏览器五页工作台
```

双屏对比的两侧使用同一订单流和同一推演时钟；决策过程、长期记忆、订单池和骑手运力也读取同一份工作台数据。
