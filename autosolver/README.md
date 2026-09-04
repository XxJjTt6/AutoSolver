# 核心求解模块

`autosolver/` 负责从输入适配到合法结果输出的完整求解链路。比赛字符串输入由 `competition.py` 处理，结构化输入由 `main.py` 统一编排。

## 模块职责

| 模块 | 职责 |
|---|---|
| `adapter.py`、`models.py` | 将外部输入转换为内部问题模型。 |
| `candidate_gen.py` | 根据订单、骑手和约束生成候选分配。 |
| `greedy.py`、`column_solver.py`、`lns.py` | 提供贪心、列搜索和局部邻域改进。 |
| `fast_evaluator.py`、`accurate_evaluator.py` | 分别承担快速筛选和更精细的可行性评估。 |
| `controller.py` | 在时间预算内组织搜索并保留当前最优解。 |
| `validator.py`、`formatter.py` | 校验约束并转换为提交格式。 |
| `fallback.py` | 在异常或质量门未通过时提供确定性回退。 |
| `competition.py` | 实现比赛候选表输入的高性能求解路径。 |

## 入口

```python
from autosolver.main import solve

result = solve(raw_input, time_budget=10.0)
```

根目录 `solver.py` 仍是比赛正式入口；本目录保留模块化实现，便于测试、演示和继续迭代。
