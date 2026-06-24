/* 会议方案 v4 · 第2幕 动态双屏 (dynamic_dashboard_v2)
   左=普通贪心(朴素橙线) / 右=AutoSolver(流动粒子线) 喂同一份订单; 底部"平均送达时间"两线对比 + 仿真播放。
   诚实: 地图坐标/路线/送达时间均为【仿真合成·演示层】, 已在工具栏与曲线头打🏷标; 真值在第1幕判决卡。 */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const el = (t, a) => { const n = document.createElementNS(NS, t); for (const k in a) n.setAttribute(k, a[k]); return n; };

  // 确定性 RNG, 保证每次演示一致 (可复现)
  function mulberry32(seed) { return () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  // ---- 合成派单几何 (演示层) ----
  function buildGroups() {
    const rnd = mulberry32(20260625);
    const W = 460, H = 300, groups = [];
    const G = 4;
    for (let g = 0; g < G; g++) {
      const cx = 90 + (g % 2) * 230 + rnd() * 30;
      const cy = 70 + Math.floor(g / 2) * 130 + rnd() * 20;
      const merchant = [cx, cy];
      const couriers = [];
      const nc = 1 + (g % 2);
      for (let i = 0; i < nc; i++) couriers.push([cx - 60 - rnd() * 30, cy + (i - (nc - 1) / 2) * 46 + rnd() * 10]);
      const orders = [];
      const no = 2 + (g % 2);
      for (let i = 0; i < no; i++) orders.push([cx + 55 + rnd() * 40, cy + (i - (no - 1) / 2) * 44 + rnd() * 10]);
      groups.push({ g, merchant, couriers, orders });
    }
    return { W, H, groups };
  }
  const MODEL = buildGroups();

  function routePoints(group) {
    // 骑手→商家→订单 的折线 (取第一个骑手)
    const pts = [];
    pts.push(group.couriers[0]);
    pts.push(group.merchant);
    group.orders.forEach((o) => pts.push(o));
    return pts;
  }

  function drawNodes(svg, group) {
    // 商家=金方块, 骑手=青圆, 订单=小点
    svg.appendChild(el("rect", { x: group.merchant[0] - 5, y: group.merchant[1] - 5, width: 10, height: 10, rx: 2,
      fill: "#ffd166", stroke: "rgba(0,0,0,.3)", "stroke-width": .6 }));
    group.couriers.forEach((c) => svg.appendChild(el("circle", { cx: c[0], cy: c[1], r: 4.2, fill: "#34d39a" })));
    group.orders.forEach((o) => svg.appendChild(el("circle", { cx: o[0], cy: o[1], r: 3, fill: "#9fe0ff" })));
  }

  function renderMaps() {
    const left = $("mapLeft"), right = $("mapRight");
    if (!left || !right) return;
    left.innerHTML = ""; right.innerHTML = "";
    // 暗色底
    [left, right].forEach((s) => s.appendChild(el("rect", { x: 0, y: 0, width: MODEL.W, height: MODEL.H, fill: "rgba(8,18,30,.6)" })));
    window.FlowRoute && FlowRoute.ensureDefs(right);
    MODEL.groups.forEach((grp) => {
      const pts = routePoints(grp);
      // 左屏: 朴素橙线 (贪心, 不流动)
      if (window.FlowRoute) FlowRoute.renderPlain(left, pts, { color: "rgba(255,157,77,.55)" });
      // 右屏: 流动粒子线 (AutoSolver 采纳路线)
      if (window.FlowRoute) FlowRoute.render(right, pts, { id: "g" + grp.g, durationMs: 2700, phase: grp.g * 0.18 });
      drawNodes(left, grp); drawNodes(right, grp);
    });
  }

  // ---- 合成一天曲线: 平均送达时间(分钟) ----
  // 订单到达形态(早/午/晚密) + 两条送达时间线: 普通贪心(高) vs AutoSolver(低), 高峰处差距拉大。
  function dayCurve() {
    const pts = [];
    for (let m = 0; m <= 1440; m += 20) {
      const h = m / 60;
      const peak = Math.exp(-((h - 8) ** 2) / 3) * 0.6 + Math.exp(-((h - 12.5) ** 2) / 2) * 1.0 + Math.exp(-((h - 18.5) ** 2) / 2.5) * 0.9;
      const load = Math.min(1, peak);                       // 0..1 订单密度
      const base = 24 + load * 26;                          // AutoSolver 送达时间
      const greedy = 24 + load * 26 * 1.95 + load * load * 10;  // 贪心: 高峰非线性恶化
      pts.push({ m, load, ours: base, greedy });
    }
    return pts;
  }
  const CURVE = dayCurve();
  const CMAX = Math.max(...CURVE.map((p) => p.greedy)) * 1.05;

  function curveXY(p, w, h) {
    return { x: (p.m / 1440) * w, oursY: h - (p.ours / CMAX) * h, grY: h - (p.greedy / CMAX) * h, loadY: h - p.load * h * 0.32 };
  }
  function pathFrom(pts, key, w, h) {
    return pts.map((p, i) => { const xy = curveXY(p, w, h); return `${i ? "L" : "M"} ${xy.x.toFixed(1)},${xy[key].toFixed(1)}`; }).join(" ");
  }

  // 静态层只画一次(密度柱/标注/两条path壳); 动画帧只改 path 的 d, 避免每帧全树重建。
  let _grPath = null, _oursPath = null, _curveBuilt = false;
  const CW = 960, CH = 200;
  function buildCurveStatic() {
    const svg = $("curveSvg"); if (!svg) return; svg.innerHTML = "";
    CURVE.forEach((p) => { const xy = curveXY(p, CW, CH);
      svg.appendChild(el("rect", { x: xy.x, y: xy.loadY, width: 6, height: CH - xy.loadY, fill: "rgba(134,160,182,.14)" })); });
    const lunch = curveXY(CURVE.find((p) => p.m === 760) || CURVE[0], CW, CH);
    svg.appendChild(el("line", { x1: lunch.x, y1: 0, x2: lunch.x, y2: CH, stroke: "rgba(255,209,102,.3)", "stroke-dasharray": "3 4" }));
    const t = el("text", { x: lunch.x + 6, y: 16, fill: "#ffd166", "font-size": 12 }); t.textContent = "订单最密时段"; svg.appendChild(t);
    _grPath = el("path", { fill: "none", stroke: "#ff9d4d", "stroke-width": 2.4 }); svg.appendChild(_grPath);
    _oursPath = el("path", { fill: "none", stroke: "#1cf4d2", "stroke-width": 2.6 }); svg.appendChild(_oursPath);
    _curveBuilt = true;
  }
  function renderCurve(uptoFrac = 1) {
    if (!_curveBuilt) buildCurveStatic();
    if (!_grPath) return;
    const shown = CURVE.slice(0, Math.max(2, Math.round(CURVE.length * uptoFrac)));
    _grPath.setAttribute("d", pathFrom(shown, "grY", CW, CH));
    _oursPath.setAttribute("d", pathFrom(shown, "oursY", CW, CH));
  }

  // ---- 播放 ----
  let playing = false, raf = 0, pausedMs = 0;   // pausedMs 记录已播放进度, 实现真·继续
  function regimeAt(m) {
    const h = m / 60;
    if (h >= 11.5 && h <= 13.5) return ["大单量场景", "s-warn"];
    if (h >= 17.5 && h <= 19.5) return ["运力紧张", "s-warn"];
    if (h >= 7 && h <= 9) return ["大单量场景", "s-ok"];
    return ["小单量平峰", "s-ok"];
  }
  function setClock(m) {
    const hh = String(Math.floor(m / 60)).padStart(2, "0"), mm = String(m % 60).padStart(2, "0");
    $("dynClock").textContent = `${hh}:${mm}`;
    const [rg] = regimeAt(m); $("dynRegime").textContent = rg;
  }
  function play() {
    if (playing) return; playing = true;
    const dur = 8000, t0 = performance.now() - pausedMs;   // 从已播放进度续上
    const step = (now) => {
      const f = Math.min(1, (now - t0) / dur);
      pausedMs = now - t0;                                  // 记录进度, 暂停后可续
      setClock(Math.round(f * 1440 / 20) * 20);
      renderCurve(f);
      if (f < 1 && playing) raf = requestAnimationFrame(step);
      else if (f >= 1) { playing = false; pausedMs = 0; $("dynPlay").textContent = "↻ 再放一遍"; setClock(1440); renderCurve(1); }
    };
    $("dynPlay").textContent = "⏸ 仿真中…";
    raf = requestAnimationFrame(step);
  }

  // 切幕时暂停/恢复右屏 SMIL 动画(隐藏时省电、避免投屏发热; SVGSVGElement API)
  function setActive(isAct2) {
    const r = $("mapRight");
    if (r && r.pauseAnimations) {
      try { isAct2 ? r.unpauseAnimations() : r.pauseAnimations(); } catch (e) { /* 忽略不支持的浏览器 */ }
    }
    // 离开第2幕且仿真在跑: 停曲线 rAF(保留 pausedMs 可续), 别在后台空转。
    if (!isAct2 && playing) {
      playing = false; cancelAnimationFrame(raf);
      const btn = $("dynPlay"); if (btn) btn.textContent = "▶ 继续";
    }
  }

  function init() {
    renderMaps();
    buildCurveStatic();
    renderCurve(1);
    setClock(0);
    const btn = $("dynPlay");
    if (btn) btn.addEventListener("click", () => {
      if (playing) { playing = false; cancelAnimationFrame(raf); btn.textContent = "▶ 继续"; }
      else play();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  window.DynamicDashboard = { init, renderMaps, renderCurve, setActive };
})();
