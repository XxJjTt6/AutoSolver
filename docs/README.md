# AutoSolver 文档中心

这里集中放置当前 v7 外卖配送智能调度工作台的对外说明。建议先看根目录 [README](../README.md)，再根据评审需要阅读产品或技术文档。

## 阅读顺序

| 文档 | 适合场景 |
|---|---|
| [根目录 README](../README.md) | 快速了解项目、在线地址和本地运行方式。 |
| [作品简介](deliverables/作品简介.md) | 报名页、展示页或答辩开场。 |
| [产品说明文档](deliverables/产品说明文档.md) | 了解双屏对比、五个页面和演示流程。 |
| [项目文档](deliverables/项目文档.md) | 了解数据流、算法对照、记忆机制和验证方式。 |
| [项目目录结构](PROJECT_STRUCTURE.md) | 查找正式入口、当前演示入口和历史版本。 |
| [官方记录索引](ARCHIVE_INDEX.md) | 查看官方结果的引用边界。 |

## 当前版本

| 部分 | 当前入口 | 定位 |
|---|---|---|
| 正式求解器 | `solver.py` | 比赛评测时执行的求解入口。 |
| v7 演示系统 | `web_agent_demo/server_v7.py` | 本地启动外卖配送智能调度工作台。 |
| v7 页面 | `web_agent_demo/day_replay_frontend_v7.py` | 双屏对比、决策过程、长期记忆、订单池、骑手运力。 |
| 历史版本 | `server.py`、`server_v2.py` 至 `server_v6.py` | 仅用于保留迭代过程，不是当前演示入口。 |

## 运行演示

```bash
python3 web_agent_demo/server_v7.py --host 127.0.0.1 --port 8799
```

打开 `http://127.0.0.1:8799`。也可以直接访问 [GitHub Pages 在线演示](https://xxjjtt6.github.io/AI-Hackahton_meituan/)。

## 统一说明

- 双屏对比使用同一批订单和同一条时间轴，左侧为最近距离贪心基线，右侧为 AutoSolver Agent。
- 决策过程解释触发、过滤、评分、派单、采纳和放弃原因。
- 长期记忆展示冷启动、经验召回、结果回写和跨场景复用。
- 订单池和骑手运力只展示当前推演时刻已经可见的输入状态。
- 页面指标用于演示和解释，不替代官方评测结果。

## 验证

```bash
python3 -m unittest tests.test_day_simulation_comparison tests.test_dispatch_workbench_data tests.test_web_agent_demo
```
