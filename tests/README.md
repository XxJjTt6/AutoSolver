# 测试说明

`tests/` 覆盖比赛求解器、Agent 能力、全天仿真、双屏对比、记忆闭环和工作台页面契约。

## 测试分组

| 范围 | 代表测试 |
|---|---|
| 求解与约束 | `test_competition.py`、`test_validator.py`、`test_end_to_end.py` |
| 搜索与评估 | `test_candidate_gen.py`、`test_controller_lns.py`、`test_evaluator_consistency.py` |
| Agent 与演化 | `test_agent_evolution.py`、`test_llm_codegen.py`、`agent_capabilities/` |
| 全天仿真 | `test_day_simulation_contract.py`、`test_day_simulation_comparison.py` |
| 工作台数据 | `test_dispatch_workbench_data.py`、`test_simulation_api_contract.py` |
| 页面契约 | `test_web_agent_demo.py`、`test_web_agent_demo_v9.py` |

运行当前最终版本的核心回归测试：

```bash
python3 -m unittest \
  tests.test_main \
  tests.test_submission \
  tests.test_dispatch_workbench_data \
  tests.test_web_agent_demo_v9
```

测试以确定性输入和契约断言为主，避免把演示指标误当成官方评测结果。历史页面测试保留用于回看早期版本，不作为 v9 发布门。
