// llm_trace_v4.js —— Hermes 式"自主学习"轨道：展证据，不展空动画。
// 轮次时间带(按 outcome 上色) + 选中轮证据流(intent/tool/patch/smoke/judge) + best-so-far 学习曲线。
(function () {
  const ICON = { round_start: "▶", intent: "💭", tool: "🔧", patch: "🟩", safety: "🛡", smoke: "🧪", judge: "⚖", memory: "🧠", round_end: "✓", teacher_review: "🎓" };

  function byId(id) { return document.getElementById(id); }

  async function init() {
    let lineage, events;
    try {
      lineage = await (await fetch("/api/v4/llm/lineage")).json();
      events = (await (await fetch("/api/v4/llm/events")).json()).events || [];
    } catch (e) { return; }
    if (!lineage || lineage.error) { byId("learnSub").textContent = "（暂无离线学习记录）"; return; }

    byId("learnSub").textContent =
      ` · ${lineage.model || "deepseek"} · 贪心基线 ${lineage.baseline_greedy_cost} → LLM最优 ${lineage.best_llm_cost}` +
      ` · accepted ${lineage.accepted_count}/${lineage.rounds}` +
      (lineage.production_solver_cost ? ` · 生产求解器 ${lineage.production_solver_cost}` : "");

    // 按 round 分组事件
    const byRound = {};
    events.forEach((e) => { if (e.round != null) (byRound[e.round] = byRound[e.round] || []).push(e); });

    // 时间带
    const ribbon = byId("ribbon");
    ribbon.innerHTML = "";
    (lineage.lineage || []).forEach((l) => {
      const chip = document.createElement("button");
      chip.className = "chip " + (l.accepted ? "ok" : "bad");
      chip.textContent = "R" + l.round + (l.cost != null ? " · " + l.cost : "");
      chip.title = l.reason || "";
      chip.onclick = () => { document.querySelectorAll(".chip").forEach((c) => c.classList.remove("sel")); chip.classList.add("sel"); renderRound(l.round, byRound[l.round] || []); };
      ribbon.appendChild(chip);
    });

    // best-so-far 学习曲线（accepted 成本的 running min）
    let best = Infinity;
    const bestSeries = (lineage.lineage || []).map((l) => { if (l.accepted && l.cost != null) best = Math.min(best, l.cost); return isFinite(best) ? best : null; });
    const series = [{ name: "best", color: "#1cf4d2", width: 1.1, data: bestSeries }];
    // 贪心基线(上)与生产求解器(下)参考线：一眼看出 LLM 学习从基线往生产口径逼近的进度（同为全量算例口径，可比）
    if (lineage.baseline_greedy_cost) series.push({ name: "greedy", color: "#ff8c42", width: 0.5, data: bestSeries.map(() => lineage.baseline_greedy_cost) });
    if (lineage.production_solver_cost) series.push({ name: "production", color: "#5fa8ff", width: 0.5, data: bestSeries.map(() => lineage.production_solver_cost) });
    if (window.Charts) window.Charts.lineChart(byId("bestChart"), series, { zeroBase: false });

    // 默认展开第一轮
    const first = (lineage.lineage || [])[0];
    if (first) { const c = ribbon.querySelector(".chip"); if (c) c.classList.add("sel"); renderRound(first.round, byRound[first.round] || []); }
  }

  function renderRound(round, evs) {
    const box = byId("roundStream");
    box.innerHTML = "";
    if (!evs.length) { box.innerHTML = "<div class=ev>（本轮无事件）</div>"; return; }
    evs.forEach((e) => {
      const row = document.createElement("div");
      row.className = "ev ev-" + e.type;
      let txt = "";
      if (e.type === "intent") txt = e.text;
      else if (e.type === "tool") txt = `${e.name}(${e.args || ""}) ${e.ok ? "✓" : "✗"} — ${trim(e.result, 160)}`;
      else if (e.type === "patch") txt = "策略代码 draft (" + (e.code ? e.code.length : 0) + "b)";
      else if (e.type === "smoke") txt = `烟测 legal=${e.legal} cost=${e.cost} cover=${e.coverage || ""}`;
      else if (e.type === "judge") txt = `Genius裁决: baseline ${e.baseline} → candidate ${e.candidate} · ${e.accepted ? "ACCEPTED" : "REJECTED"} · ${trim(e.reason, 80)}`;
      else if (e.type === "round_end") txt = `本轮结果: ${e.outcome}${e.best_so_far != null ? " · best-so-far " + e.best_so_far : ""}`;
      else if (e.type === "round_start") txt = `第 ${e.round} 轮开始 · regime=${e.regime}`;
      else txt = JSON.stringify(e).slice(0, 160);
      row.innerHTML = `<span class=ico>${ICON[e.type] || "·"}</span><span class=evt>${escapeHtml(txt)}</span>`;
      if (e.type === "patch" && e.code) {
        const pre = document.createElement("pre"); pre.className = "code"; pre.textContent = trim(e.code, 600); row.appendChild(pre);
      }
      box.appendChild(row);
    });
    box.scrollTop = 0;
  }

  function trim(s, n) { s = s == null ? "" : String(s); return s.length > n ? s.slice(0, n) + "…" : s; }
  function escapeHtml(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  window.LLMTrace = { init };
  if (document.readyState !== "loading") init(); else document.addEventListener("DOMContentLoaded", init);
})();
