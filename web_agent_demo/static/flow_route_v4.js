// flow_route_v4.js —— 图一红框那种"发光 + 流动 + 粒子"线
// 源自 提交版原版/web_agent_demo/static_rg/app.js:779-814（smoothPath/cometAlong），整理为可复用接口。
(function () {
  const SVGNS = "http://www.w3.org/2000/svg";
  const REDUCE = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function el(tag, attrs) {
    const n = document.createElementNS(SVGNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  // Catmull-Rom → 贝塞尔（照搬源 :779-796）
  function smoothPath(points) {
    const p = points;
    if (!p || p.length < 2) return "";
    if (p.length === 2) {
      const a = p[0], b = p[1];
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
      const dx = b[0] - a[0], dy = b[1] - a[1], k = 0.14;
      return `M ${a[0]},${a[1]} Q ${(mx - dy * k).toFixed(2)},${(my + dx * k).toFixed(2)} ${b[0]},${b[1]}`;
    }
    let d = `M ${p[0][0]},${p[0][1]}`;
    for (let i = 0; i < p.length - 1; i++) {
      const p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ` C ${c1x.toFixed(2)},${c1y.toFixed(2)} ${c2x.toFixed(2)},${c2y.toFixed(2)} ${p2[0]},${p2[1]}`;
    }
    return d;
  }

  // 彗星：亮头 + 2 段渐隐拖尾，沿同一平滑路径 animateMotion，错开 begin（照搬源 :798-814）
  function cometAlong(layer, points, dur, phase) {
    const D = parseFloat(dur) || 2.6;
    const pathD = smoothPath(points);
    const trail = [[1.5, 1, 0], [1.05, 0.55, 0.05], [0.7, 0.32, 0.1]]; // viewBox 0..100,半径缩小
    trail.forEach(([rr, op, off], i) => {
      const dot = el("circle", { r: rr, fill: "#eafffb", opacity: op });
      if (i === 0) dot.setAttribute("filter", "url(#pinGlow4)");
      if (REDUCE) {
        if (i === 0) { const pp = points[Math.floor(points.length / 2)] || points[0]; dot.setAttribute("cx", pp[0]); dot.setAttribute("cy", pp[1]); layer.appendChild(dot); }
        return;
      }
      dot.appendChild(el("animateMotion", { dur, begin: ((phase + off) * D).toFixed(3) + "s", repeatCount: "indefinite", path: pathD }));
      layer.appendChild(dot);
    });
  }

  function ensureDefs(svg) {
    if (svg.querySelector("defs[data-v4]")) return;
    const defs = el("defs", { "data-v4": "1" });
    defs.innerHTML =
      '<filter id="glow4" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="1.1" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<filter id="pinGlow4" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="0.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<marker id="arrow4" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0,1 L8,5 L0,9 Z" fill="#1cf4d2"/></marker>';
    svg.insertBefore(defs, svg.firstChild);
  }

  // 右屏：四层叠加发光流动粒子线
  function renderFlowRoute(layer, points, opts) {
    opts = opts || {};
    const cyan = opts.color || "#1cf4d2";
    const dur = (opts.durationMs ? opts.durationMs / 1000 : 2.7) + "s";
    const d = smoothPath(points);
    layer.appendChild(el("path", { d, fill: "none", stroke: "rgba(28,244,210,.18)", "stroke-width": 2.6, "stroke-linecap": "round", filter: "url(#glow4)" })); // ① 发光底
    layer.appendChild(el("path", { d, fill: "none", stroke: cyan, "stroke-width": 1.1, "stroke-linecap": "round", "marker-end": "url(#arrow4)", filter: "url(#glow4)" })); // ② 青主线
    const flow = el("path", { d, fill: "none", stroke: "rgba(224,255,250,.9)", "stroke-width": 0.55, "stroke-dasharray": "0.1 2.4", "stroke-linecap": "round" }); // ③ 流动虚线
    if (!REDUCE) flow.appendChild(el("animate", { attributeName: "stroke-dashoffset", values: "0;-2.5", dur: "0.8s", repeatCount: "indefinite", calcMode: "linear" }));
    layer.appendChild(flow);
    if (opts.active !== false) cometAlong(layer, points, dur, opts.phase || 0); // ④ 彗星粒子
  }

  // 左屏：弱发光静态线（仅 ①②，无流动/粒子，形成对比）
  function renderPlainRoute(layer, points, opts) {
    opts = opts || {};
    const d = smoothPath(points);
    layer.appendChild(el("path", { d, fill: "none", stroke: "rgba(120,140,160,.25)", "stroke-width": 1.6, "stroke-linecap": "round" }));
    layer.appendChild(el("path", { d, fill: "none", stroke: opts.color || "#8aa0b4", "stroke-width": 0.7, "stroke-linecap": "round", "marker-end": "url(#arrow4)" }));
  }

  window.FlowRoute = { el, ensureDefs, renderFlowRoute, renderPlainRoute, smoothPath };
})();
