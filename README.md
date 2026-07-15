# AutoSolver 外卖配送智能调度工作台

美团 AI Hackathon 命题四项目。系统在同一批订单、同一条时间轴上并行运行两套调度方案：左侧是最近距离贪心基线，右侧是 AutoSolver Agent，让调度差异、决策依据和长期记忆都能直接查看。

**在线演示：** [https://xxjjtt6.github.io/AI-Hackahton_meituan/](https://xxjjtt6.github.io/AI-Hackahton_meituan/)

## 核心页面

| 页面 | 主要内容 |
|---|---|
| 双屏对比 | 左右同步回放同一订单流，对照路线、等待时间、配送成本和超时情况。 |
| 决策过程 | 展示每轮触发原因、候选过滤、策略评分、最终派单及放弃原因。 |
| 长期记忆 | 展示经验召回、结果回写、场景复用和策略迁移。 |
| 订单池 | 按推演时钟查看已经下单的订单、风险和两套算法的处理结果。 |
| 骑手运力 | 查看骑手班次、位置、负载、任务链和预计空闲时间。 |

## 快速运行

环境要求：Python 3.10 或更高版本。核心演示使用 Python 标准库，不需要执行 `pip install`。

在终端进入解压后的项目根目录，然后运行：

```bash
python3 web_agent_demo/server_v7.py --host 127.0.0.1 --port 8765
```

浏览器打开：

```text
http://127.0.0.1:8765
```

如果 `8765` 端口已被占用，可以把命令中的端口改为 `8766`，并打开对应地址。

## 建议演示顺序

1. 在“双屏对比”点击“开始推理”，先看两套算法在同一时间轴上的结果分化。
2. 进入“决策过程”，选择一轮派单，查看采纳和放弃方案的原因。
3. 进入“长期记忆”，查看经验如何被召回、回写并用于后续场景。
4. 最后用“订单池”和“骑手运力”核对每轮决策的输入状态。

## 项目结构

| 路径 | 说明 |
|---|---|
| `solver.py` | 正式比赛求解入口。 |
| `autosolver/`、`autosolver_agent/` | 求解算法、Agent 控制、评估和记忆模块。 |
| `web_agent_demo/server_v7.py` | 当前本地演示入口。 |
| `web_agent_demo/day_replay_frontend_v7.py` | 当前五页调度工作台。 |
| `tests/` | 算法、仿真、对比、记忆和页面测试。 |
| `docs/` | 产品说明、技术文档和项目结构说明。 |

`server.py`、`server_v2.py` 至 `server_v6.py` 及对应前端文件仅保留为历史迭代记录，当前演示请使用 `server_v7.py`。

## 验证

```bash
python3 -m py_compile web_agent_demo/server_v7.py
python3 -m unittest tests.test_dispatch_workbench_data
```

页面中的对比数据用于演示和解释两套调度方案，不替代比赛官方评测结果。详细说明见 [文档中心](docs/README.md)。
