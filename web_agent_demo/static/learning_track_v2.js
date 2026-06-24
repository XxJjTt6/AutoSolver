/* 会议方案 v4 · 学习轨道控制台前端 (iter-01)
   只读 /api/meeting-v2/learning-trace 真实数据; 三幕导航 + 判决卡 + Stage Rail + 事件时间线 + 折叠证据。
   诚实红线: 主屏权威用官方 654.29/706.197; 657 标"本地实时估算"; 5 策略全被拒=质量门有判别力。 */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const fmt = (n, d = 1) => (n == null ? "—" : Number(n).toFixed(d));

  let DATA = null;
  let evIdx = 0;

  // ---------- 三幕导航 ----------
  const ACTS = ["act1", "act2", "act3"];
  let actI = 0;
  function showAct(i) {
    actI = Math.max(0, Math.min(ACTS.length - 1, i));
    ACTS.forEach((a, k) => $(a).classList.toggle("is-hidden", k !== actI));
    document.querySelectorAll(".act-btn").forEach((b) =>
      b.classList.toggle("is-active", b.dataset.act === ACTS[actI]));
    $("nextBtn").textContent = actI < ACTS.length - 1 ? "下一步 ▶" : "重头看 ⟲";
    if (window.DynamicDashboard && DynamicDashboard.setActive) DynamicDashboard.setActive(ACTS[actI] === "act2");
  }
  document.querySelectorAll(".act-btn").forEach((b) =>
    b.addEventListener("click", () => showAct(ACTS.indexOf(b.dataset.act))));
  $("nextBtn").addEventListener("click", () => showAct(actI < ACTS.length - 1 ? actI + 1 : 0));

  // ---------- 第1幕：判决卡 ----------
  function renderVerdict() {
    if (!DATA) return;
    const b = DATA.baselines;
    const greedy = b.greedy_local.value, official = b.official_case.value, ours = b.local_realtime.value;
    // 头条成本值用【官方权威 654.29】; 省幅用【同口径本地比】(贪心 2097.7→本地 657.1)=唯一有效同口径比，
    // 避免拿官方解÷本地贪心的混口径。657 仅作本地↔官方互证，不在头条冒充官方。
    const save = ((greedy - ours) / greedy) * 100;
    $("vSave").textContent = save.toFixed(1) + "%";
    const cov = DATA.coverage || { covered: 40, total: 40 };
    const kpis = [
      { k: "每单成本（官方）", v: fmt(official, 2), dir: "↓越低越好", sub: `比贪心省 ${save.toFixed(1)}%（同口径本地：${fmt(greedy, 0)}→${fmt(ours, 0)}）`, win: true },
      { k: "接单覆盖率", v: `${Math.round((cov.covered / cov.total) * 100)}%`, dir: "↑越高越好", sub: `${cov.covered}/${cov.total} 单全覆盖 · ${cov.note || "省成本不靠少接单"}`, win: false },
      { k: "整体官方总分", v: fmt(b.official_total.value, 2), dir: "↑越高越好", sub: "10/10 满分提交", win: false },
    ];
    $("kpiRow").innerHTML = kpis.map((x) => `
      <div class="kpi">
        <div class="k">${x.k}${x.dir ? `<span class="dir">${x.dir}</span>` : ""}</div>
        <div class="v ${x.win ? "win" : ""}">${x.v}</div>
        <div class="sub">${x.sub}</div>
      </div>`).join("");
    $("verdictFoot").innerHTML =
      `怎么读：<b style="color:#1cf4d2">右边每单成本远低于贪心（同口径本地 ${fmt(greedy, 0)}→${fmt(ours, 0)}，省 ${save.toFixed(1)}%），数越小越好。</b>` +
      ` <span style="color:#5b748b">官方权威同算例成本 ${fmt(official, 2)} ≈ 本地实时估算 ${fmt(ours, 1)}，互相印证（🏷本地估算·非官方分）。更多口径见第3幕「评委可能会问」。</span>`;
  }

  // ---------- 第3幕：Stage Rail ----------
  function stageState(stageKey) {
    // 根据真实统计给信号灯: 看场景/试造/安全检查=绿; 试跑=绿; 判决=黄(质检拦截); 记下来=黄(移出活跃池)
    const s = DATA.stats;
    if (stageKey === "judge") return "s-warn";       // 0 采纳, 质检拦截 → 黄(有判别力), 非红
    if (stageKey === "memory") return "s-warn";      // 全部移出活跃池
    if (stageKey === "sandbox") return s.reject_timeout > 0 ? "s-warn" : "s-ok";
    return "s-ok";
  }
  function renderStageRail() {
    const cur = currentEvent();
    const html = DATA.stages.map((st, i) => {
      const cls = stageState(st.key) + (cur && cur.stage === st.key ? " is-cur" : "");
      const arrow = i < DATA.stages.length - 1 ? '<span class="stage-arrow">›</span>' : "";
      return `<div class="stage-node ${cls}" title="${st.desc}"><i class="sig"></i>${st.cn}</div>${arrow}`;
    }).join("");
    $("stageRail").innerHTML = html;
    // 统一用"策略级"口径(5 个新打法)，与成绩单/Q&A 一致，避免同屏 7 vs 5 自相矛盾。
    const ss = DATA.strategies || [];
    const nQ = ss.filter((s) => s.last_reason === "quality regression").length;
    const nT = ss.filter((s) => s.last_reason === "timeout").length;
    $("stageStat").innerHTML =
      `${ss.length} 个新打法 · 安全检查全过 · <b>0 个上线</b>` +
      `（${nQ} 个成绩不达标 + ${nT} 个超时）` +
      ` —— 没采纳 = 机制帮你挡掉了打不过现有方案的新打法。`;
  }

  // ---------- 第3幕：事件时间线（一次只亮 1 条）----------
  const KIND = {
    strategy_generated: { cls: "k-gen", label: "🧪 试造打法" },
    strategy_validated: { cls: "k-val", label: "🛡 安全检查" },
  };
  function trialKind(ev) {
    return ev.reason === "timeout"
      ? { cls: "k-trial-t", label: "⏱ 试跑超时" }
      : { cls: "k-trial-q", label: "⚖ 质量门判决" };
  }
  function kindOf(ev) {
    return ev.event === "strategy_trial" ? trialKind(ev) : KIND[ev.event] || { cls: "", label: ev.event };
  }
  function currentEvent() { return DATA && DATA.events.length ? DATA.events[evIdx] : null; }

  function renderEventCard() {
    const ev = currentEvent();
    if (!ev) { $("eventCard").innerHTML = "<div class='ev-line'>暂无记录</div>"; return; }
    const kind = kindOf(ev);
    let body = "";
    if (ev.event === "strategy_generated") {
      const c = ev.case || {};
      body = `
        <div class="ev-title">${ev.strategy_id} → ${ev.regime_cn}</div>
        <div class="ev-line">针对「${ev.regime_cn}」试造了一个新打法，准备拿去检查、试跑。</div>
        <div class="ev-line">目标算例：<b>${c.tasks ?? "?"} 单 · ${c.couriers ?? "?"} 骑手</b>${ev.degenerate ? ' <span class="ev-degen">（只用 1 单 1 骑手跑通流程的探针，不计入正式成绩）</span>' : ""}</div>`;
    } else if (ev.event === "strategy_validated") {
      body = `
        <div class="ev-title">${ev.strategy_id}</div>
        <div class="ev-line">过安全门：检查代码安不安全、接口对不对。</div>
        <div class="ev-checks">
          <span class="ev-check">✓ 语法</span>
          <span class="ev-check">✓ 安全(AST)</span>
          <span class="ev-check">✓ 接口</span>
        </div>
        <div class="ev-line">结论：<b>${ev.reason === "passed" ? "通过，进沙箱试跑" : ev.reason}</b></div>`;
    } else if (ev.event === "strategy_trial") {
      let costLine;
      if (ev.degenerate) costLine = `<span class="ev-degen">${ev.cost_note}</span>`;
      else if (ev.cost_note) costLine = ev.cost_note;
      else if (ev.cost_vs_local) costLine = `本地成本 <b>${ev.cost_vs_local}</b>`;
      else costLine = "—";
      const verdictLine = ev.degenerate ? "只验证流程能跑通，不计入正式判决。"
        : ev.reason === "timeout" ? "试跑超时，自动撤回。" : "没打过现有最好方案 → 没上线。";
      body = `
        <div class="ev-title">${ev.strategy_id} · ${ev.degenerate ? "探针跑通流程" : ev.reason_cn}</div>
        <div class="ev-line">沙箱里隔离跑了一遍（耗时 ${fmt(ev.elapsed_ms, 1)} ms）。</div>
        <div class="ev-line">${costLine}</div>
        <div class="ev-line"><b>${verdictLine}</b></div>`;
    }
    $("eventCard").innerHTML = `
      <span class="ev-kind ${kind.cls}">${kind.label}</span>
      ${body}
      <div class="ev-meta">${ev.created_at || ""} · 真实落盘记录（evolution_memory.jsonl）</div>
      <div class="ev-whatis">这块是什么：把它离线试过的每一步，逐条放给你看。</div>`;
    $("evPos").textContent = `${evIdx + 1} / ${DATA.events.length}`;
    renderMiniRail();
    renderStageRail();
    lightCausal(ev);
  }
  // 因果联动: 当前事件点亮 ①看场景 / ②挑打法 / ③结果 之一
  function lightCausal(ev) {
    const map = { strategy_generated: "perceive", strategy_validated: "pick", strategy_trial: "result" };
    const lit = map[ev.event] || "";
    document.querySelectorAll("#causalStrip .causal-node").forEach((n) =>
      n.classList.toggle("is-lit", n.dataset.link === lit));
  }
  function renderMiniRail() {
    $("eventRailMini").innerHTML = DATA.events.map((ev, i) => {
      const k = kindOf(ev).cls;
      return `<div class="erm ${k} ${i === evIdx ? "is-cur" : ""}" data-i="${i}" title="${ev.event}"></div>`;
    }).join("");
    $("eventRailMini").querySelectorAll(".erm").forEach((d) =>
      d.addEventListener("click", () => { evIdx = +d.dataset.i; renderEventCard(); }));
  }
  function stepEvent(delta) {
    if (!DATA || !DATA.events.length) return;          // 空数据保护: 防 %0 → NaN
    evIdx = (evIdx + delta + DATA.events.length) % DATA.events.length;
    renderEventCard();
  }
  $("evPrev").addEventListener("click", () => stepEvent(-1));
  $("evNext").addEventListener("click", () => stepEvent(1));

  // ---------- 第3幕：折叠 — 成绩单（防自爆叙事）----------
  function renderEvidence() {
    const ss = DATA.strategies;
    const timeout = ss.filter((s) => s.last_reason === "timeout").length;
    const quality = ss.filter((s) => s.last_reason === "quality regression").length;
    const oc = DATA.baselines.official_case.value;
    const rows = ss.map((s) => {
      const tcls = s.last_reason === "timeout" ? "t" : "";
      const why = s.last_reason === "timeout" ? "试跑超时，自动撤回" : "成绩不如现有方案，质检拦下";
      return `<div class="strat-row">
        <span class="sid">${s.strategy_id} · ${s.regime_cn}</span>
        <span class="why ${tcls}">${why}</span></div>`;
    }).join("");
    $("evidenceBody").innerHTML = `
      <div class="shield-big">系统试造了 <b>${ss.length} 个</b>新打法，自己测出来都不如现有方案——
        于是<b>一个都没放进正式系统</b>，避免帮倒忙。</div>
      <div class="shield-note">类比：就像新员工的方案要先过试用，没通过就不上线。</div>
      <div class="shield-note">现有最好成绩 <b style="color:#ffd166">${fmt(oc, 2)}</b>（官方·大单量算例）← 没打过它就淘汰。</div>
      <div class="shield-note">⏱ ${timeout} 个超时撤回 · ⚖ ${quality} 个成绩不达标质检拦下（均已移出活跃池，未进 solver.py）。</div>
      ${rows}
      <div class="shield-note" style="margin-top:8px;color:#86a0b6">没采纳 = 帮你挡掉了不靠谱的新方案，不是没用。</div>`;
  }

  // ---------- 第3幕：折叠 — 学到了什么（best-so-far 真实阶梯）----------
  function renderLadder() {
    const ladder = (DATA.best_so_far && DATA.best_so_far.length) ? DATA.best_so_far : [];
    if (!ladder.length) { $("ladderBody").innerHTML = "<div class='shield-note'>暂无 best-so-far 记录</div>"; return; }
    const top = ladder[0].cost;
    const rows = ladder.map((s, i) => {
      const drop = i === 0 ? "" : `<span class="lad-drop">↓ ${(((ladder[i - 1].cost - s.cost) / ladder[i - 1].cost) * 100).toFixed(0)}%</span>`;
      const barW = Math.max(4, (s.cost / top) * 100);
      return `<div class="ladder-step">
          <span class="lad-l">${s.label}${drop}</span>
          <span class="lad-bar"><i style="width:${barW.toFixed(0)}%"></i></span>
          <span class="c">${fmt(s.cost, 1)}</span>
        </div>`;
    }).join("");
    $("ladderBody").innerHTML = `
      <div class="ladder">${rows}</div>
      <div class="shield-note" style="margin-top:8px">同一次求解里，"目前最好方案"被一路压低（真实 best_update 事件，
        离线跑 large_seed301 捕获 · ${(((top - ladder[ladder.length - 1].cost) / top) * 100).toFixed(1)}% 降幅）。
        这是确定性搜索的 anytime 改进，<b>不是 LLM、不改 solver</b>。</div>`;
  }

  // ---------- 第3幕：三层记忆 L0/L1/L2（v4 §16.10）----------
  function renderMemory() {
    if (!DATA) return;
    // L2 = 按状况(regime)分组的策略经验（registry target_regime）
    const byRegime = {};
    (DATA.strategies || []).forEach((s) => {
      const k = s.regime_cn || s.target_regime || "未标注状况";
      (byRegime[k] = byRegime[k] || []).push(s);
    });
    const chips = Object.entries(byRegime).map(([rg, arr]) =>
      `<span class="mem-chip">${rg} <b>×${arr.length}</b>　${arr.every((s) => s.accepted === 0) ? "都没过质检" : ""}</span>`).join("");
    const n = (DATA.events || []).length;
    $("memBody").innerHTML = `
      <div class="mem-stack">
        <div class="mem-row mem-l2">
          <span class="mem-tag">L2 · 策略经验</span>
          <div class="mem-desc">什么状况下、哪些打法试过（试过没用也记住，下次不再踩坑）${chips}</div>
        </div>
        <div class="mem-up">↑ 向上沉淀</div>
        <div class="mem-row mem-l1">
          <span class="mem-tag">L1 · 经历</span>
          <div class="mem-desc">每次"试造→检查→试跑→判决"都记下来（就是上面那 ${n} 条时间线）</div>
        </div>
        <div class="mem-up">↑ 向上沉淀</div>
        <div class="mem-row mem-l0">
          <span class="mem-tag">L0 · 运行态</span>
          <div class="mem-desc">这一次、此刻走到第几步（上方六阶段灯 + 时间线游标）</div>
        </div>
      </div>
      <div class="shield-note" style="margin-top:8px">一句话：L0 是"现在在干嘛"，L1 是"这场景历史上试过啥"，L2 是"什么状况该用什么打法"。</div>`;
  }

  // ---------- 第3幕：Q&A 速查（守诚实口径）----------
  function renderQA() {
    const QA = [
      ["这页在比什么（看不懂）", "左贪心、右 AutoSolver，喂同一份订单。只看顶上几个数和底下两条线：右边更好、绿线越跑越好。"],
      ["是真在学习，还是预录的？", "学习是真的，发生在离线。底层是真实落盘记录（28 条事件 / 5 个策略），现场是回放，已标「演示回放」，因为现场不联网。"],
      ["5 个策略全被拒，不是没学会吗？", "恰恰相反——1 个超时、4 个不如现有方案，证明安全门 / 质量门有判别力，会自动淘汰打不过基线的策略。机制的价值是它敢说「不」。"],
      ["现场会改 solver 吗？", "不改。正式 solver 一行不动、热路径零 LLM。学习在离线隔离轨道，现场只做确定性安全召回。"],
      ["657 / 68.7% 是官方分吗？", "不是。large_seed301 官方 654.29、整体 706.197。657 是本地复跑这一个算例的近似（同口径本地：贪心 2098→657，省 68.7%），已标「本地实时估算·非官方分」。"],
      ["进化的到底是什么？", "是对状况的识别，不是求解器。认得越准 → 挑的打法越对 → 结果越好。"],
      ["几个 agent / memory 怎么设计？", "对外四角色——感知 / 策略 / 执行评估 / 记忆进化——由一个统一控制器编排（内部映射 system.py 的 6 项能力），不是多进程。memory 三层 L0/L1/L2。"],
      ["ETA / deadline 可信吗？", "坐标 / deadline / 送达时间是仿真合成层、打了「演示」角标。关键：送达时间走路径几何、成本走独立的 _solution_expected_cost，两者不互喂，避免优化一个把另一个拆了。"],
    ];
    $("qaBody").innerHTML = QA.map(([q, a]) =>
      `<div class="qa-item"><div class="qa-q">${q}</div><div class="qa-a">${a}</div></div>`).join("");
  }

  // ---------- onboarding ----------
  function maybeOnboard() {
    const q = new URLSearchParams(location.search);
    if (q.get("noob") === "1") return;                 // 截图/深链: 跳过引导
    const seen = sessionStorage.getItem("mtg_v2_onboard");
    if (!seen) $("onboarding").classList.remove("is-hidden");
  }
  $("obStart").addEventListener("click", () => {
    sessionStorage.setItem("mtg_v2_onboard", "1");
    $("onboarding").classList.add("is-hidden");
  });
  $("replayBtn").addEventListener("click", () => $("onboarding").classList.remove("is-hidden"));

  // ---------- 键盘 a11y ----------
  document.addEventListener("keydown", (e) => {
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    // Esc 关引导
    if (e.key === "Escape") { $("onboarding").classList.add("is-hidden"); sessionStorage.setItem("mtg_v2_onboard", "1"); return; }
    // 引导开着时不抢键
    if (!$("onboarding").classList.contains("is-hidden")) return;
    if (e.key >= "1" && e.key <= "3") { showAct(parseInt(e.key, 10) - 1); e.preventDefault(); return; }   // 数字跳幕
    if (e.key === "ArrowRight") { ACTS[actI] === "act3" ? stepEvent(1) : showAct(actI + 1); e.preventDefault(); return; }
    if (e.key === "ArrowLeft") { ACTS[actI] === "act3" ? stepEvent(-1) : showAct(actI - 1); e.preventDefault(); return; }
  });

  // ---------- 加载 ----------
  function showError(msg) {
    let bar = $("globalError");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "globalError"; bar.className = "global-error";
      $("stage").prepend(bar);
    }
    bar.textContent = "⚠ " + msg;
  }
  async function load() {
    try {
      const r = await fetch("/api/meeting-v2/learning-trace");
      if (!r.ok) throw new Error("HTTP " + r.status);
      DATA = await r.json();
    } catch (e) {
      showError("数据加载失败，请刷新页面重试：" + e);
      return;
    }
    // 常驻诚实声明
    if (DATA.honest_note) $("honestBanner").textContent = "🎬 " + DATA.honest_note;
    renderVerdict();
    renderStageRail();
    renderEventCard();
    renderEvidence();
    renderLadder();
    renderMemory();
    renderQA();
    // 空数据时禁用事件翻页
    const empty = !DATA.events || !DATA.events.length;
    $("evPrev").disabled = empty; $("evNext").disabled = empty;
    const q = new URLSearchParams(location.search);
    const a = parseInt(q.get("act") || "1", 10);
    showAct(Number.isFinite(a) ? a - 1 : 0);
    if (q.get("open") === "1") document.querySelectorAll("details.fold").forEach((d) => (d.open = true));
    maybeOnboard();
  }
  load();
})();
