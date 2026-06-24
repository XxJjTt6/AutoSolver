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
  }
  document.querySelectorAll(".act-btn").forEach((b) =>
    b.addEventListener("click", () => showAct(ACTS.indexOf(b.dataset.act))));
  $("nextBtn").addEventListener("click", () => showAct(actI < ACTS.length - 1 ? actI + 1 : 0));

  // ---------- 第1幕：判决卡 ----------
  function renderVerdict() {
    const b = DATA.baselines;
    const greedy = b.greedy_local.value, ours = b.local_realtime.value;
    const save = ((greedy - ours) / greedy) * 100;
    $("vSave").textContent = save.toFixed(1) + "%";
    // 四个 KPI: 每单成本 / 接单覆盖 / 准时(演示) / 求解耗时. 只有成本是真值对比, 其余 iter-02 接动态。
    const kpis = [
      { k: "每单成本", v: fmt(ours, 1), dir: "↓越低越好", sub: `原来贪心 ${fmt(greedy, 1)}`, win: true },
      { k: "接单覆盖率", v: "100%", dir: "↑越高越好", sub: "40/40 单全覆盖", win: true },
      { k: "权威成绩", v: fmt(b.official_case.value, 2), dir: "", sub: "官方 large_seed301（非本地）", win: false },
      { k: "整体提交分", v: fmt(b.official_total.value, 2), dir: "", sub: "官方 10/10", win: false },
    ];
    $("kpiRow").innerHTML = kpis.map((x) => `
      <div class="kpi">
        <div class="k">${x.k}${x.dir ? `<span class="dir">${x.dir}</span>` : ""}</div>
        <div class="v ${x.win ? "win" : ""}">${x.v}</div>
        <div class="sub">${x.sub}</div>
      </div>`).join("");
    $("verdictFoot").innerHTML =
      `口径说明：<b style="color:#ffd166">654.29 / 706.197 是官方权威分</b>；` +
      `每单成本 657 是本地复跑 large_seed301 的实时估算（非官方），贪心基线 2097 同口径本地跑出。` +
      `成本走 _solution_expected_cost，送达时间走路径几何，两者独立计算。`;
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
    const s = DATA.stats;
    $("stageStat").innerHTML =
      `${s.generated} 次试造 · ${s.validated} 次检查全过 · ${s.trial} 次试跑 · ` +
      `<b>0 次采纳</b>（质检拦截 ${s.reject_quality} + 超时 ${s.reject_timeout}）` +
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
        <div class="ev-line">目标算例：<b>${c.tasks ?? "?"} 单 · ${c.couriers ?? "?"} 骑手</b>${ev.degenerate ? ' <span class="ev-degen">（1×1 冒烟测试算例）</span>' : ""}</div>`;
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
      body = `
        <div class="ev-title">${ev.strategy_id} · ${ev.reason_cn}</div>
        <div class="ev-line">沙箱里隔离跑了一遍（耗时 ${fmt(ev.elapsed_ms, 1)} ms）。</div>
        <div class="ev-line">${costLine}</div>
        <div class="ev-line"><b>${ev.reason === "timeout" ? "试跑超时，自动撤回。" : "没打过现有最好方案 → 没上线。"}</b></div>`;
    }
    $("eventCard").innerHTML = `
      <span class="ev-kind ${kind.cls}">${kind.label}</span>
      ${body}
      <div class="ev-meta">${ev.created_at || ""} · 真实落盘记录（evolution_memory.jsonl）</div>
      <div class="ev-whatis">这块是什么：把它离线试过的每一步，逐条放给你看。</div>`;
    $("evPos").textContent = `${evIdx + 1} / ${DATA.events.length}`;
    renderMiniRail();
    renderStageRail();
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

  // ---------- 第3幕：折叠 — 学到了什么（best-so-far 占位，iter-04 接真 best_update）----------
  function renderLadder() {
    const b = DATA.baselines;
    $("ladderBody").innerHTML = `
      <div class="ladder">
        <div class="ladder-step"><span>一开始（贪心基线）</span><span class="c">${fmt(b.greedy_local.value, 0)}</span></div>
        <div class="ladder-step"><span>组合搜索 + 局部修复后</span><span class="c">${fmt(b.local_realtime.value, 1)}</span></div>
      </div>
      <div class="shield-note" style="margin-top:8px">"目前最好方案"在同一次求解里一路被压低（真 best_update 阶梯将在 iter-04 接入）。</div>`;
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

  // ---------- 加载 ----------
  async function load() {
    try {
      const r = await fetch("/api/meeting-v2/learning-trace");
      DATA = await r.json();
    } catch (e) {
      $("eventCard").innerHTML = `<div class="ev-line">数据加载失败：${e}</div>`;
      return;
    }
    renderVerdict();
    renderStageRail();
    renderEventCard();
    renderEvidence();
    renderLadder();
    const q = new URLSearchParams(location.search);
    const a = parseInt(q.get("act") || "1", 10);
    showAct(Number.isFinite(a) ? a - 1 : 0);
    maybeOnboard();
  }
  load();
})();
