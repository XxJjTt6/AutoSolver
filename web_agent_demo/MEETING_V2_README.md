# 会议方案 v4 演示（学习轨道控制台 + 动态双屏）· 使用说明

> 对应方案：`/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/docs/会议明确有用点_详细执行方案_v4_20260625.md`
> 本演示正面解决导师/用户两条反馈：①整场 demo「看得懂」；②前端「自主学习」有具体可跑的落地。
> 全部新建于 `web_agent_demo/`，**不改** `solver.py` / `server.py` / `autosolver_agent/`。

---

## 1. 启动

```bash
cd /Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改
python3 web_agent_demo/server_meeting_v2.py --host 127.0.0.1 --port 8766
# 浏览器打开 http://127.0.0.1:8766
```

数据自检（不起服务）：

```bash
python3 web_agent_demo/server_meeting_v2.py --selfcheck
# 期望: stats={generated:7,validated:14,trial:7,accepted:0,...} strategies=5 → PASS
```

单测：

```bash
python3 web_agent_demo/tests/test_learning_feed_v2.py     # 9/9 绿
```

---

## 2. 三幕怎么看（给零运筹背景的评委）

进页面先看 5 秒 onboarding（可关、可重看：右上「＝ 怎么看」）。顶部**常驻图例条**全程不消失：
`🟩 我们的方案 / 🟧 普通方案 / 🔵 我们的(不带记忆) / ✨ 流动线=当前采纳路线 / 🏷 演示数据 / 🎬 离线真实记录·回放`。

| 幕 | 一句话 | 看什么 |
|---|---|---|
| **第1幕 结果先行** | 同订单同时钟同指标，右边更省更准时 | 判决卡：每单成本 657↓（省 68.7%）/ 覆盖 100%↑ / 官方权威 654.29 |
| **第2幕 动态·机制>算法** | 单子一波波来就重排，按状况挑打法 | 左=普通贪心(暗橙线) vs 右=AutoSolver(**流动粒子线**)；底部「平均送达时间」橙/青两线；▶ 仿真这一天 |
| **第3幕 自主学习** | 进化的是"对状况的识别"，不是求解器 | 因果条①看场景→②挑打法→③结果更好；六阶段 Stage Rail；28 条真实事件逐条回放；折叠「学到了什么」(best-so-far 真阶梯 2097→683→657) + 「成绩单」(5 策略全被拒=质量门有判别力) + 「评委可能会问」Q&A |

导航：顶部三幕按钮，或「下一步 ▶」依次推进。

---

## 3. 诚实口径（守住，别被对抗式评委击穿）

- **现场零 LLM**：本服务只读两个固化数据文件、不跑求解、不调 LLM、不写盘。第3幕常驻 `🎬 真实记录·放慢回放，非动画`。
- **657 不冒充官方**：主屏权威分用**官方 654.29（large_seed301 同名隐藏算例）/ 706.197（整体 10/10）**；657.104 是本地复跑近似，标「本地实时估算·非官方分」，与官方 654.29 互相印证。
- **5 策略全被拒 = 质量门有判别力**：1 个超时 + 4 个成绩不如现有方案，自动淘汰、未进 `solver.py`。不讲成"进化提分"。registry 默认折叠，点开才看，防自爆。
- **best-so-far 真阶梯**：来自离线跑 `run_case_agent(large_seed301)` 捕获的真实 `best_update`，是确定性 portfolio 求解器的 anytime 改进，**非 LLM、不改 solver**。
- **进化的是场景识别**：`regime` 真值是规模/特征桶（大单量场景/小单量平峰/骑手不愿接/运力紧张），**不译成早午晚高峰/雨天**。
- **成本与送达时间两条独立路径**：成本走 `_solution_expected_cost`，送达时间走路径几何，互不喂，避免优化一个把另一个拆了。

---

## 4. 数据边界（什么是真、什么是演示层）

| 内容 | 真/演示 | 来源 |
|---|---|---|
| 28 条进化事件 / 5 个策略 / 全被拒 | **真实** | `web_agent_demo/fixtures/{evolution_memory.jsonl,strategy_registry.json}`（离线真实记录固化） |
| best-so-far 阶梯 2097→683→657 | **真实** | 离线 `run_case_agent` 捕获的 `best_update` |
| 官方 654.29 / 706.197、本地 657 / 贪心 2097 | **真实** | 评测/本地复跑 |
| 第2幕地图坐标、路线、平均送达时间曲线 | **演示层**（🏷） | `dynamic_dashboard_v2.js` 确定性合成（seed 固定，可复现） |

> 为什么读 fixture 而不是 `autosolver_agent/evolution_state/`：后者被 gitignore 且每次跑 agent 都会追加/覆盖，直接读会不可复现、单测随机崩。fixture 是"首次真跑固化"快照，随仓库提交。

---

## 5. 7 分钟 Demo 流（建议讲法）

1. **(0:00) 第1幕**：先抛结论——同一份 large_seed301，右边每单成本从 2097 降到 657，省 68.7%。强调"同台对比、可复现"。
2. **(1:00) 第2幕**：点「▶ 仿真这一天」，单子一波波来；看右屏流动粒子线=当前采纳路线，左屏普通贪心只会一直贪；底部两线在订单最密时段拉开差距。一句话："不缺算法，缺的是按状况挑打法这套机制。"
3. **(3:30) 第3幕**：因果条讲"认对状况→挑对打法→结果更好"；逐条回放它离线试过的每一步；展开"学到了什么"看 best-so-far 真阶梯；展开"成绩单"讲"5 个新打法自测都不如现有方案→一个没上线=质量门有判别力"。强调"进化的是识别，正式 solver 现场不改"。
4. **(6:30) 收尾**：右屏流动粒子线特写——亮头=履约方向、拖尾=执行过程；这套机制横向能切别的调度、纵向已从静态走到动态。

断网兜底：所有静态资源本地、学习数据读 fixture、动态为客户端确定性合成——**全程可离线演示**。

---

## 6. 截图 / 深链 URL 参数（调试与做 PPT 配图）

- `?act=N`：直达第 N 幕（1/2/3）。
- `?noob=1`：跳过 onboarding。
- `?open=1`：展开第3幕所有折叠区（学到了什么 / 成绩单 / Q&A）。

例：`http://127.0.0.1:8766/?act=3&noob=1&open=1`

无头 Chrome 命令行截图：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --screenshot=out.png --window-size=1280,1600 --force-device-scale-factor=1.5 \
  "http://127.0.0.1:8766/?act=3&noob=1&open=1" --virtual-time-budget=4000
```

---

## 7. 文件清单（全绝对路径）

后端 / 数据：
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/server_meeting_v2.py` — 只读服务（/ + /assets + learning-trace API + --selfcheck）
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/learning_feed_v2.py` — 只读解析器（读 fixture → 前端 schema + best-so-far）
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/fixtures/evolution_memory.jsonl` — 28 条真实进化事件（固化）
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/fixtures/strategy_registry.json` — 5 个策略（全 rejected，固化）
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/docs/prebuilt/learning-trace.json` — 归一化快照（断网兜底）

前端：
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/static/meeting_v2.html`
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/static/learning_track_v2.{css,js}`
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/static/flow_route_v2.js` — 流动粒子线（红框四层）
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/static/dynamic_dashboard_v2.js` — 第2幕动态双屏

测试：
- `/Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_logg_在这版上面改/web_agent_demo/tests/test_learning_feed_v2.py`
