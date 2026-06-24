"""autosolver_dynamic_v4 —— 时钟 B：动态调度仿真（滚动时域控制）。

把静态算例动态化：订单按一天分布陆续到达、骑手物理移动、已派决策冻结、每 tick 滚动重算。
三泳道同源对比：Greedy(基线) / AutoSolver冷启动(无记忆) / AutoSolver暖启动(召回离线学到的策略)。
正式 solver.py 零改动；本包只读复用其贪心与成本口径，ETA 走几何（独立于成本函数）。
"""

__all__ = [
    "sim_state_v4",
    "order_stream_v4",
    "scenario_builder_v4",
    "scene_memory_v4",
    "business_metrics_v4",
    "rolling_solver_v4",
]
