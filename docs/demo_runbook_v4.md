# v4 演示 Runbook（答辩用）—— DeepSeek 自主学习 + 动态调度

> 一句话：**我们参考港队 MTASA 的四角色，用 DeepSeek 把项目做成"离线真自主学习 + 在线安全召回"的两时钟闭环，动态仿真双屏证明结果更好，前端把"学习过程+结果"画出来。**
> 本版全部为可运行真代码，分支推送在 `https://github.com/XxJjTt6/AI-Hackahton_meituan`（llm-dynamic-iter-01..04）。

---

## 0. 启动命令
```bash
cd /Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改
# 前端（默认读 committed demo trace，断网/无 key 也能演示）
python3 web_agent_demo/server_v4.py --host 127.0.0.1 --port 8770
# 浏览器打开 http://127.0.0.1:8770
```
现场要"真跑"时（需 DeepSeek key，已放 .secrets/deepseek_key）：
```bash
# 时钟A：离线自进化（产真实 accepted lineage）
python3 -m autosolver_llm_v4.evolution_runner_v4 --provider deepseek --rounds 6 --case large_seed301
# 时钟B：动态仿真现场重算（前端加 ?live=1）
python3 -m autosolver_dynamic_v4.rolling_solver_v4 --case large_seed301 --scenario weekday_peaks
```

---

## 1. 三分钟演示路径（点击顺序）
1. **开场（业务）**：这是即时配送高峰派单——订单陆续来、骑手有限且意愿不定、派错影响 ETA 和成本。
2. **看结果（双屏）**：页面已自动载入"工作日三高峰"。指着顶部判决卡：同一批订单、同一时钟，**AutoSolver 每单期望成本 1091 vs 贪心 2111，低约 48%**，覆盖 40/40，准时率更高。
3. **点"▶ 播放动态仿真"**：左屏贪心、右屏 AutoSolver 同步推进一天。**右屏那条发光流动的青绿粒子线 = 当前采纳的派单路径**（亮头是履约方向、拖尾粒子是执行过程）。底部三条曲线：橙=贪心、蓝=无记忆 AutoSolver、青绿=带记忆 AutoSolver。
4. **切"午高峰突发拥堵"场景**：高峰注入拥堵（降速），曲线出现"扰动—恢复"，说明动态鲁棒性。
5. **讲自主学习（下方轨道）**：这是**离线 DeepSeek 真跑**的学习记录——时间带 R1…R6 每轮按是否被接受上色；点一轮看它的**证据流**：假设(intent)→调工具→改策略代码→本地烟测→**Genius 确定性裁决 ACCEPTED/REJECTED**→写记忆。右边 best-so-far 曲线 **2097→1048 一路下降**，就是"学习的过程和结果"。
6. **收口（诚实）**："学习在离线发生，现场不联网、不改正式 solver；线上只做安全召回——这才是生产级边界。"

---

## 2. 指标口径表（被追问照这个答，别混用）
| 数字 | 含义 | 来源 | 能说什么 |
|---|---|---|---|
| `706.197` | 官方榜单成绩 | `archive/runs/official_submit_*.json` | 正式成绩只引用它 |
| `657.104` | large_seed301 本地求解成本 | `solver.py` production | 本地相对比较，**不冒充官方** |
| `2097.658` | large_seed301 贪心基线本地成本 | `_fallback_official_greedy` | 对比基准 |
| `2097→1048.77` | DeepSeek 离线学习 6/6 accepted | 真实 run（llm_runs / demo_runs） | **真自主学习曲线，-50%** |
| 动态 `2111.88→1091.08` | 一天动态仿真累计期望成本 | rolling_solver_v4 三泳道 | AutoSolver vs 贪心 **-48%** |
| ETA / 准时率 | 几何距离 / 速度（仿真合成） | sim_state_v4，**独立于成本函数** | 业务演示口径，需角标 |

---

## 3. 八个 Q&A（备问）
1. **是不是 LLM 现场改 solver？** 不是。两个时钟：学习在离线（DeepSeek 跑工具循环改 `propose()` 策略，过安全门+确定性 Critic），现场只做安全召回，正式 `solver.py` 零改动。
2. **accepted=0 不是假自进化吗？** 那是旧版。现在是真的：`autosolver_llm_v4/demo_runs/deepseek_iter02_lineage/result.json` 有 6/6 真实 accepted lineage（2097→1048.77），策略代码固化在 `autosolver_llm_v4/strategy_pack_v4/`。
3. **LLM 生成的代码安全吗？** AST 安全门：白名单 import、禁 eval/exec/os/subprocess、禁 while、强制 `propose` 签名与返回类型、强制 deadline 检查；不安全直接拒。
4. **动态求解具体怎么做？** 滚动时域控制：每 tick 揭示新到订单、骑手按几何移动、已派决策冻结不可撤销、只对滚动窗口重算；左右双屏用**同一订单流**（确定性合成）保证同源对比。
5. **cold/warm 区别？** cold=AutoSolver 机制但无记忆（基础单派）；warm=召回离线学到的多派策略（有记忆）。warm 用的就是 DeepSeek 学到并被 Critic 接受的策略。
6. **为什么 LLM 1048 还不如 production 657？** LLM 在 10 秒安全边界内自主探索到 -50%，已证明机制；production 是我们重度调优的专用求解器。机制可持续逼近，且可迁移到别的调度问题。
7. **地图点位是真的吗？** 真实地图语义 + 演示合成几何（已角标）；核心胜负由同一订单流下的成本/ETA/覆盖率曲线证明，不靠地图。
8. **断网/没网怎么办？** 前端默认放 committed demo trace + 真实 lineage 回放，完全不依赖网络；要真跑再加 `?live=1` / 配 key。

---

## 4. 诚实红线（守住）
1. 现场热路径零 LLM；`solver.py` 零改动；学习全在离线时钟 A。
2. 657/1048/1091 都是本地/演示口径，绝不冒充官方 706.197。
3. 成本走 `_solution_expected_cost`，ETA 走几何，两条独立路径。
4. lineage 区分"真 DeepSeek 跑出"与"FakeModelClient 回放"。
5. Agent = 四角色由统一控制器编排，不虚构多进程。

---

## 5. 兜底
- 服务起不来 → 回退原 `web_agent_demo/server.py`（未改动）。
- 动效卡顿 → `prefers-reduced-motion` 自动关粒子；地图只画最近 8 条在途线。
- DeepSeek 限流 → 客户端指数退避重试 → 回退 FakeModelClient 回放。
- 录屏兜底 → 用 `autosolver_dynamic_v4/demo/v4_dashboard_preview.png` 及录屏。
