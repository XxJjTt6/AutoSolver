// dashboard_v4.js —— 双屏动态对比 + 三泳道曲线 + 流动粒子线播放。
(function () {
  const FR = window.FlowRoute, CH = window.Charts;
  let trace = null, tick = 0, timer = null;
  const acc = { greedy: [], cold: [], warm: [] };   // 累计派单(按泳道)
  const costSeries = { greedy: [], cold: [], warm: [] };

  const $ = (id) => document.getElementById(id);

  async function loadScenarios() {
    try {
      const r = await (await fetch("/api/v4/scenarios")).json();
      const sel = $("scenario");
      sel.innerHTML = "";
      (r.scenarios || []).forEach((s) => { const o = document.createElement("option"); o.value = s.id; o.textContent = s.label; sel.appendChild(o); });
    } catch (e) {}
  }

  async function loadTrace() {
    stop();
    const scenario = $("scenario").value || "weekday_peaks";
    $("src").textContent = "加载中…";
    const r = await (await fetch(`/api/v4/dynamic?case=large_seed301&scenario=${scenario}`)).json();
    if (r.error) { $("src").textContent = "错误: " + r.error; return; }
    trace = r;
    $("src").textContent = (r.source === "live" ? "现场重算" : "演示回放") + " · " + (r.summary?.scenario_label || "");
    reset();
    FR.ensureDefs($("mapL")); FR.ensureDefs($("mapR"));
    drawArrival();
    fastForward();   // 载入即渲染完整静态预览（便于一眼看懂/截图）；点播放再动画
  }

  function reset() {
    tick = 0; acc.greedy = []; acc.cold = []; acc.warm = [];
    costSeries.greedy = []; costSeries.cold = []; costSeries.warm = [];
  }
  function fastForward() { while (trace && tick < trace.steps.length) stepOnce(); }
  function animate() { if (!trace) { loadTrace(); return; } stop(); reset(); drawArrival(); timer = setInterval(stepOnce, 650); }
  function play() { animate(); }
  function stop() { if (timer) clearInterval(timer); timer = null; }

  function stepOnce() {
    if (!trace || tick >= trace.steps.length) { stop(); return; }
    const step = trace.steps[tick];
    const mm = (step.clock_min || 0);
    $("clock").textContent = String(Math.floor(mm / 60)).padStart(2, "0") + ":" + String(mm % 60).padStart(2, "0") + (step.speed_factor < 1 ? "  ⚠拥堵" : "");
    ["greedy", "cold", "warm"].forEach((ln) => {
      const lane = step.lanes[ln];
      if (lane && lane.new_assignments) acc[ln] = acc[ln].concat(lane.new_assignments);
      costSeries[ln].push(lane ? lane.metrics.total_cost : null);
    });
    renderMap($("mapL"), acc.greedy, false);
    renderMap($("mapR"), acc.warm, true);
    renderVerdict(step);
    drawCost();
    tick++;
    if (tick >= trace.steps.length) stop();
  }

  function renderMap(svg, assigns, flow) {
    // 清掉非 defs 节点
    Array.from(svg.children).forEach((c) => { if (c.tagName !== "defs") svg.removeChild(c); });
    const routesLayer = FR.el("g", {});
    const ptsLayer = FR.el("g", {});
    // 降噪：地图只展示"最近在途"的少量派单线（导师明确否决把所有策略线堆地图上）
    const shown = assigns.slice(-8);
    shown.forEach((a, i) => {
      const pts = [a.courier_from, a.pickup, a.dropoff].filter(Boolean);
      if (pts.length >= 2) {
        if (flow) FR.renderFlowRoute(routesLayer, pts, { phase: (i % 4) / 4, durationMs: 2600, active: i >= shown.length - 4 });
        else FR.renderPlainRoute(routesLayer, pts, {});
      }
    });
    // 所有已派点位淡淡铺底（给空间感，但不连线）
    assigns.slice(-40).forEach((a) => {
      ptsLayer.appendChild(FR.el("circle", { cx: a.pickup[0], cy: a.pickup[1], r: 0.7, fill: "#ffb648", opacity: 0.55 }));
      ptsLayer.appendChild(FR.el("circle", { cx: a.dropoff[0], cy: a.dropoff[1], r: 0.6, fill: "#5fd0ff", opacity: 0.5 }));
    });
    shown.forEach((a) => {
      if (a.courier_from) ptsLayer.appendChild(FR.el("circle", { cx: a.courier_from[0], cy: a.courier_from[1], r: 0.9, fill: flow ? "#1cf4d2" : "#9fb3c8" }));
    });
    svg.appendChild(routesLayer);
    svg.appendChild(ptsLayer);
  }

  function renderVerdict(step) {
    const g = step.lanes.greedy?.metrics, w = step.lanes.warm?.metrics;
    if (!g || !w) return;
    const pct = g.total_cost ? ((g.total_cost - w.total_cost) / g.total_cost * 100) : 0;
    const cards = [
      ["每单期望成本", w.total_cost, g.total_cost, "AutoSolver ↓ " + pct.toFixed(0) + "%"],
      ["平均配送时长", w.avg_eta_min + "m", g.avg_eta_min + "m", ""],
      ["准时率", (w.on_time_rate * 100).toFixed(0) + "%", (g.on_time_rate * 100).toFixed(0) + "%", ""],
      ["覆盖", w.coverage_str, g.coverage_str, ""],
      ["场景识别命中率", (w.regime_hit_rate * 100).toFixed(0) + "%", "—", "warm 记忆"],
    ];
    $("verdict").innerHTML = cards.map((c) =>
      `<div class=vcard><div class=vk>${c[0]}</div><div class=vv><span class=auto>${c[1]}</span> <span class=base>vs ${c[2]}</span></div><div class=vn>${c[3]}</div></div>`
    ).join("");
  }

  function drawCost() {
    if (!CH) return;
    CH.lineChart($("costChart"), [
      { name: "greedy", color: "#ff8c42", data: costSeries.greedy },
      { name: "cold", color: "#5fa8ff", data: costSeries.cold },
      { name: "warm", color: "#1cf4d2", width: 1.1, data: costSeries.warm },
    ], { zeroBase: true, marker: tick - 1 });
  }
  function drawArrival() {
    if (!CH || !trace) return;
    CH.barChart($("arrChart"), trace.meta?.arrival_hist || [], { color: "#3a6ea5", marker: tick });
  }

  async function boot() {
    await loadScenarios();
    $("play").onclick = () => { if (timer) { stop(); $("play").textContent = "▶ 播放动态仿真"; } else { animate(); $("play").textContent = "⏸ 暂停"; } };
    loadTrace();   // 自动载入默认场景的静态预览
  }
  if (document.readyState !== "loading") boot(); else document.addEventListener("DOMContentLoaded", boot);
})();
