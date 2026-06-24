# AutoSolver v4 —— DeepSeek 自主学习 + 动态调度（总览）

> 本版按会议四点大改版：真接 LLM(DeepSeek) + 动态求解 + 对比可视化 + 前端自主学习。
> 正式 `solver.py` 热路径**零改动**；全部为新建 `*_v4` 模块。
> 远端分支：`https://github.com/XxJjTt6/AI-Hackahton_meituan`（`llm-dynamic-iter-01..06`，逐版累积）。

## 一图看懂（两个时钟）
- **时钟 A · 离线学习（真 DeepSeek）**：LLM 读记忆→改 `propose()` 策略→安全门→确定性 Critic 打分→写三层 memory，产真实"失败→修复→接受"lineage。
- **时钟 B · 在线调度（零 LLM 热路径）**：动态仿真按场景从已 accepted 策略库安全召回，滚动求解，双屏对比。
- 一句话：**学习在离线发生，现场只做安全召回**（现场不联网、不改 solver）。

## 会议四点 → 落点
| 会议点 | 落点 | 实测 |
|---|---|---|
| #4 接 LLM(港队思路) | `autosolver_llm_v4/`（Fool/Genius/Teacher 四角色闭环, DeepSeek） | large_seed301 离线 6/6 accepted, **2097.66→1048.77(-50%)** |
| #1 动态仿真+对比可视化 | `autosolver_dynamic_v4/`（滚动时域三泳道） | 一天25tick, **greedy 2111.88→AutoSolver 1091.08(-48%)**, 全程40/40 |
| #2 自主策略设计(agent/memory/交互) | 四角色 + 三层 memory A/B/C + 安全门/沙箱/registry | 见 `docs/llm_agent_architecture_v4.md` |
| #3 前端自主学习(Hermes式) | `web_agent_demo/server_v4.py` + `static/*_v4` | 双屏+流动粒子线+学习轨道+DeepSeek解说 |

## 跑起来
```bash
cd /Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改
# 前端（默认演示回放，断网/无 key 可用）→ http://127.0.0.1:8770
python3 web_agent_demo/server_v4.py --port 8770
# 全部 v4 测试（30 个）
python3 -m unittest discover -s tests -p "test_*_v4.py"
# 时钟A 离线自进化（需 DeepSeek key, 已放 .secrets/deepseek_key）
python3 -m autosolver_llm_v4.evolution_runner_v4 --provider deepseek --rounds 6 --case large_seed301
# 离线无 key 也能跑（FakeModelClient 回放）
python3 -m autosolver_llm_v4.evolution_runner_v4 --fake-model --rounds 3 --case large_seed301
# 时钟B 动态仿真
python3 -m autosolver_dynamic_v4.rolling_solver_v4 --case large_seed301 --scenario weekday_peaks
```

## 目录
- `autosolver_llm_v4/` — 时钟A：llm_client(DeepSeek+Fake)/sandbox/genius/memory/teacher/prompts/tools/harness/evolution_runner/dispatch_commentator + teacher_playbook + **strategy_pack_v4(真实学到策略,committed)** + demo_runs(真实lineage回放)
- `autosolver_dynamic_v4/` — 时钟B：sim_state/order_stream/scenario_builder/scene_memory/business_metrics/rolling_solver + demo(动态trace+解说+预览图)
- `web_agent_demo/server_v4.py` + `static/*_v4.{js,css}` — 前端（不改原 server.py）
- `tests/test_*_v4.py` — 30 个单测
- `docs/demo_runbook_v4.md`（答辩 runbook）/ `docs/llm_agent_architecture_v4.md`（架构）/ `docs/会议明确有用点_详细执行方案_v4_LLM大改版_20260625.md`（方案）

## 诚实红线
现场零 LLM、`solver.py` 零改动、学习全离线；657/1048/1091 为本地/演示口径不冒充官方 706.197；成本走 `_solution_expected_cost`、ETA 走几何两条独立路径；lineage 区分真模型/回放；Agent=四逻辑角色统一编排不虚构多进程；tick 解说只解说不决策；API key 经 `.secrets/`(gitignore) 隔离不进 git。
