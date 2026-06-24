# v4 架构说明（四角色 · 三层 memory · 两个时钟）

> 实现分支：`https://github.com/XxJjTt6/AI-Hackahton_meituan`（llm-dynamic-iter-01..04）。
> 正式 `solver.py` 热路径零改动；本架构全部为新建 `*_v4` 模块。

## 1. 两个时钟（核心诚实框架）
- **时钟 A · 离线学习（真 DeepSeek）**：单位=轮。LLM 读记忆→改 `propose()` 策略代码→本地烟测→确定性 Critic 打分→写三层 memory，产真实"失败→修复→接受"lineage。
- **时钟 B · 在线调度（零 LLM 热路径）**：单位=仿真分钟。动态仿真按场景从已 accepted 的策略库安全召回，滚动求解，双屏对比。
> 一句话挡追问："学习在离线发生，现场只做安全召回。"

## 2. 四角色 → 真实模块
| 角色 | 职责 | 落点 |
|---|---|---|
| Genius | 确定性 Critic（绝对真理），打分/判合法/出裁决 | `autosolver_llm_v4/genius_v4.py`（封 `solver._solution_expected_cost` + 贪心基线 + summarize） |
| Fool | LLM 迭代主体，工具循环改策略 | `autosolver_llm_v4/harness_v4.py` + `tools_v4.py` + `prompts_v4.py` |
| Teacher | 策略护栏 + playbook + 停滞复盘 | `autosolver_llm_v4/teacher_v4.py` + `teacher_playbook_v4.md` |
| Frontend | 双屏 + 曲线 + 学习轨道 | `web_agent_demo/server_v4.py` + `static/*_v4.{js,css}` |
工程实情：一个统一控制器编排四个**逻辑角色**，不虚构多进程。

## 3. 三层 memory
- A 单轮：`llm_runs/<run>/round_NNN/dialog.jsonl` + `events.jsonl`（前端回放）
- B 数据集级：`llm_memory/runs/<fp>/episodes.jsonl` + `strategy_index.json`；桥接现有 `autosolver_agent/evolution_state/`（registry/memory）
- C 全局：`llm_memory/notes/{lesson,try_error,key_decision}_*.md` + `MEMORY.md`，轻量 BM25 检索
- **持久化提示**：evolution_state 被 git 跟踪+gitignore 易被重置 → 真实学到策略固化在 committed `autosolver_llm_v4/strategy_pack_v4/`（warm 召回主源）。

## 4. 数据流
```
时钟A: Teacher护栏/playbook → Fool(DeepSeek)改propose → sandbox安全门 → Genius打分 → 三层memory ↺ → accepted入strategy_pack
时钟B: 一天订单(确定性合成) → SimClock滚动窗口/冻结 → {greedy / cold无记忆 / warm召回pack} 同源求解 → 业务指标 → 双屏+三泳道曲线+彗星线
前端: /api/v4/dynamic(双屏trace) + /api/v4/llm/{lineage,events}(学习轨道回放)
```

## 5. 安全/学习信号
- 安全门：AST 白名单 import、禁 eval/exec/os/subprocess、禁 while、强制签名/返回类型/deadline。
- smoke gate：draft 后必须本地烟测才能 final。
- Critic：合法 + 覆盖不降 + 不超时 + 成本 ≤ 基线−ε 才 accepted。
- 记忆：accepted→lesson；失败→try_error（下轮降权）；停滞→Teacher 复盘。

## 6. 文件清单
- LLM 轨道：`autosolver_llm_v4/{llm_client,sandbox,genius,memory,teacher,prompts,tools,harness,evolution_runner}_v4.py` + `teacher_playbook_v4.md` + `strategy_pack_v4/` + `demo_runs/`
- 动态仿真：`autosolver_dynamic_v4/{sim_state,order_stream,scenario_builder,scene_memory,business_metrics,rolling_solver}_v4.py` + `demo/`
- 前端：`web_agent_demo/server_v4.py` + `static/{flow_route,charts,llm_trace,dashboard}_v4.js` + `styles_v4.css`
- 测试：`tests/test_*_v4.py`（29 个，全过）

## 7. 关键设计决策（key_decision）
1. LLM 改 `propose()` 受限模块，不改 `solver.py`（风险隔离，复用现有沙箱）。
2. 文本工具协议（intent/tool/final）+ 代码容错捕获，DeepSeek-chat 跑得稳，6/6 成功。
3. 动态成本按 tick 已派任务累计期望成本（骑手跨 tick 复用，不能对累计解算静态成本=会 inf）。
4. ETA 走几何独立于成本函数（防第二目标自圆其说）。
5. 真实学到策略固化为 committed pack（免受 evolution_state 重置）。
