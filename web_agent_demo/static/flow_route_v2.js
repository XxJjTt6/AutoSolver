/* 会议方案 v4 · 流动粒子线 (flow_route_v2)
   图一红框那条"流动感 + 粒子感"的线 = 四层叠加:
   ① 发光底  ② 青主线+箭头  ③ 流动能量虚线(stroke-dashoffset 动画=流动感)  ④ 彗星粒子(亮头+渐隐拖尾=粒子感)
   真实源码: /Users/比赛/美团黑客松决赛/AI-Hackahton_meituan_提交版原版/web_agent_demo/static_rg/app.js:765-944
   对外接口: FlowRoute.ensureDefs(svg) + FlowRoute.render(layer, points, opts) + FlowRoute.smoothPath(points) */
(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CYAN = "#1cf4d2";

  function el(tag, attrs) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function addAnim(node, tag, attrs) {        // 减弱动效时不挂 SMIL, 元素静态可见
    if (!REDUCE) node.appendChild(el(tag, attrs));
    return node;
  }
  // Catmull-Rom → 贝塞尔: 让路线像绕路的城市路网, 而非直线
  function smoothPath(points) {
    const p = points;
    if (!p || p.length < 2) return "";
    if (p.length === 2) {
      const a = p[0], b = p[1];
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1], k = 0.14;
      return `M ${a[0]},${a[1]} Q ${(mx - dy * k).toFixed(1)},${(my + dx * k).toFixed(1)} ${b[0]},${b[1]}`;
    }
    let d = `M ${p[0][0]},${p[0][1]}`;
    for (let i = 0; i < p.length - 1; i++) {
      const p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ` C ${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2[0]},${p2[1]}`;
    }
    return d;
  }
  // 彗星: 亮头 + 渐隐拖尾, 沿同一路径错开 begin (粒子感)
  function cometAlong(layer, points, dur, group, phase = 0) {
    const D = parseFloat(dur) || 2.6;
    const pathD = smoothPath(points);
    const trail = [[3.4, 1, 0], [2.4, 0.55, 0.05], [1.6, 0.32, 0.1]];  // [半径, 透明度, begin偏移]
    trail.forEach(([rr, op, off], i) => {
      const dot = el("circle", { r: rr, fill: "#eafffb", opacity: op });
      dot.dataset.group = group;
      if (i === 0) dot.setAttribute("filter", "url(#flowPinGlow)");
      if (REDUCE) {
        if (i === 0) { const pp = points[Math.floor(points.length / 2)] || points[0];
          dot.setAttribute("cx", pp[0]); dot.setAttribute("cy", pp[1]); layer.appendChild(dot); }
        return;
      }
      dot.appendChild(el("animateMotion", { dur, begin: ((phase + off) * D).toFixed(3) + "s",
        repeatCount: "indefinite", path: pathD }));
      layer.appendChild(dot);
    });
  }
  // 注入一次滤镜/marker (glow / pinGlow / arrow)
  function ensureDefs(svg) {
    if (svg.querySelector("#flowGlow")) return;
    const defs = el("defs");
    defs.innerHTML =
      `<filter id="flowGlow" x="-60%" y="-60%" width="220%" height="220%">
         <feGaussianBlur stdDeviation="4" result="b"/>
         <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
       <filter id="flowPinGlow" x="-80%" y="-80%" width="260%" height="260%">
         <feGaussianBlur stdDeviation="2.4" result="b"/>
         <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
       <marker id="flowArrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6"
               orient="auto-start-reverse"><path d="M0,1 L8,5 L0,9 Z" fill="${CYAN}"/></marker>`;
    svg.insertBefore(defs, svg.firstChild);
  }
  // 把一条采纳路线渲染成四层流动粒子线
  function render(layer, points, opts = {}) {
    const cyan = opts.color || CYAN;
    const dur = opts.durationMs ? (opts.durationMs / 1000) + "s" : "2.7s";
    const group = opts.id || "route";
    const d = smoothPath(points);
    // ① 发光底
    layer.appendChild(el("path", { "data-group": group, d, fill: "none",
      stroke: "rgba(28,244,210,.2)", "stroke-width": 7.5, "stroke-linejoin": "round",
      "stroke-linecap": "round", filter: "url(#flowGlow)", "vector-effect": "non-scaling-stroke" }));
    // ② 青主线 + 箭头
    layer.appendChild(el("path", { "data-group": group, d, fill: "none", stroke: cyan,
      "stroke-width": 3.4, "stroke-linejoin": "round", "stroke-linecap": "round",
      "marker-end": "url(#flowArrow)", filter: "url(#flowGlow)", "vector-effect": "non-scaling-stroke" }));
    // ③ 流动能量虚线 (流动感)
    const flow = el("path", { "data-group": group, d, fill: "none",
      stroke: "rgba(224,255,250,.9)", "stroke-width": 1.8, "stroke-dasharray": "0.1 10",
      "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" });
    addAnim(flow, "animate", { attributeName: "stroke-dashoffset", values: "0;-10.1",
      dur: "0.8s", repeatCount: "indefinite", calcMode: "linear" });
    layer.appendChild(flow);
    // ④ 彗星粒子 (粒子感)
    if (opts.active !== false) cometAlong(layer, points, dur, group, opts.phase || 0);
  }
  // 朴素弱线 (左屏贪心: 只画一条暗淡静态线, 形成对比)
  function renderPlain(layer, points, opts = {}) {
    layer.appendChild(el("path", { d: smoothPath(points), fill: "none",
      stroke: opts.color || "rgba(255,157,77,.5)", "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round",
      "stroke-dasharray": opts.dash || "4 5", "vector-effect": "non-scaling-stroke" }));
  }

  window.FlowRoute = { ensureDefs, render, renderPlain, smoothPath, el };
})();
