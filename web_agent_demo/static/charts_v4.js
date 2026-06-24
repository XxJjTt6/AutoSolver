// charts_v4.js —— 轻量 SVG 折线/柱状图（无第三方依赖，viewBox 0..100 非等比）
(function () {
  const SVGNS = "http://www.w3.org/2000/svg";
  const el = (t, a) => { const n = document.createElementNS(SVGNS, t); for (const k in a) n.setAttribute(k, a[k]); return n; };

  // series: [{name,color,data:[y...]}], 共享 x = index。auto y-range。
  function lineChart(svg, series, opts) {
    opts = opts || {};
    svg.innerHTML = "";
    const W = 100, H = 100, padL = 2, padR = 2, padT = 6, padB = 6;
    const n = Math.max(1, ...series.map((s) => s.data.length));
    let lo = Infinity, hi = -Infinity;
    series.forEach((s) => s.data.forEach((v) => { if (v == null || !isFinite(v)) return; lo = Math.min(lo, v); hi = Math.max(hi, v); }));
    if (!isFinite(lo)) { lo = 0; hi = 1; }
    if (lo === hi) hi = lo + 1;
    if (opts.zeroBase) lo = Math.min(lo, 0);
    const x = (i) => padL + (W - padL - padR) * (n <= 1 ? 0 : i / (n - 1));
    const y = (v) => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo));
    // baseline
    svg.appendChild(el("line", { x1: padL, y1: H - padB, x2: W - padR, y2: H - padB, stroke: "rgba(255,255,255,.12)", "stroke-width": 0.3 }));
    series.forEach((s) => {
      let d = "";
      s.data.forEach((v, i) => { if (v == null || !isFinite(v)) return; d += (d ? " L" : "M") + x(i).toFixed(2) + "," + y(v).toFixed(2); });
      if (d) svg.appendChild(el("path", { d, fill: "none", stroke: s.color, "stroke-width": s.width || 0.8, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      // 末点高亮
      const last = s.data.length - 1;
      if (last >= 0 && isFinite(s.data[last])) svg.appendChild(el("circle", { cx: x(last), cy: y(s.data[last]), r: 0.9, fill: s.color }));
    });
    if (opts.marker != null) { // 当前播放位置竖线
      const mx = x(opts.marker);
      svg.appendChild(el("line", { x1: mx, y1: padT, x2: mx, y2: H - padB, stroke: "rgba(255,255,255,.35)", "stroke-width": 0.3, "stroke-dasharray": "1 1" }));
    }
  }

  function barChart(svg, data, opts) {
    opts = opts || {};
    svg.innerHTML = "";
    const W = 100, H = 100, padB = 6, padT = 6;
    const n = data.length || 1;
    const hi = Math.max(1, ...data);
    const bw = (W / n) * 0.7, gap = (W / n) * 0.3;
    data.forEach((v, i) => {
      const h = (H - padT - padB) * (v / hi);
      svg.appendChild(el("rect", { x: i * (W / n) + gap / 2, y: H - padB - h, width: bw, height: Math.max(0, h), fill: opts.color || "#3a6ea5", rx: 0.4 }));
    });
    if (opts.marker != null && opts.marker < n) {
      svg.appendChild(el("rect", { x: opts.marker * (W / n) + gap / 2, y: padT, width: bw, height: H - padT - padB, fill: "rgba(255,255,255,.10)" }));
    }
  }

  window.Charts = { lineChart, barChart };
})();
