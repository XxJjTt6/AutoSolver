from __future__ import annotations

import json
from functools import lru_cache

from web_agent_demo.day_simulation import (
    DAY_SIMULATION_ENDPOINTS,
    DaySimulationControls,
    day_comparison_to_dict,
    run_full_day_comparison,
)
from web_agent_demo.dispatch_workbench_data import build_dispatch_workbench_payload


@lru_cache(maxsize=1)
def _bootstrap_payload() -> dict[str, object]:
    controls = DaySimulationControls(courier_count=18, order_scale=0.38, weather="mixed", congestion_profile="weekday")
    contract = run_full_day_comparison(seed="frontend-shell", controls=controls)
    return {
        "contract": day_comparison_to_dict(contract),
        "workbench": build_dispatch_workbench_payload(contract),
        "endpoints": dict(DAY_SIMULATION_ENDPOINTS),
        "mode": "dispatch-workbench-shell",
    }


def render_day_replay_index() -> str:
    boot_json = json.dumps(_bootstrap_payload(), ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>外卖配送智能调度工作台</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous">
  <script defer src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous"></script>
  <style>
    :root {
      --bg: #f3f5f8;
      --surface: #ffffff;
      --surface-2: #f8fafc;
      --surface-3: #edf1f5;
      --surface-glass: rgba(255,255,255,.92);
      --ink: #17212b;
      --ink-2: #2b3947;
      --muted: #647286;
      --line: #dfe5ec;
      --line-strong: #c9d3df;
      --nav: #121923;
      --nav-2: #1a2430;
      --nav-active: rgba(255,184,28,.14);
      --accent: #0f766e;
      --accent-2: #115e59;
      --amber: #b7791f;
      --red: #b42318;
      --blue: #2563eb;
      --green-soft: #e6f4f1;
      --amber-soft: #fbf1db;
      --red-soft: #fee4e2;
      --shadow: 0 14px 30px rgba(21, 32, 43, .08);
      --shadow-tight: 0 8px 18px rgba(21, 32, 43, .055);
      --shadow-card: 0 1px 2px rgba(15,23,42,.04), 0 10px 24px rgba(15,23,42,.055);
      --shadow-float: 0 22px 46px rgba(21, 32, 43, .10);
      --focus-ring: 0 0 0 3px rgba(15,118,110,.18);
      --radius-lg: 18px;
      --radius-md: 12px;
      --font: "HarmonyOS Sans SC", "MiSans", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
      --mono: "SFMono-Regular", "Cascadia Mono", "Menlo", monospace;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    html {
      color-scheme: light;
      scrollbar-color: #a9b6c2 transparent;
    }
    body {
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(255,255,255,.90), rgba(243,245,248,.96)),
        radial-gradient(circle at 88% 8%, rgba(255,184,28,.10), transparent 27%),
        radial-gradient(circle at 10% 0%, rgba(15,118,110,.07), transparent 31%),
        linear-gradient(90deg, rgba(100,116,139,.035) 1px, transparent 1px),
        linear-gradient(0deg, rgba(100,116,139,.032) 1px, transparent 1px),
        var(--bg);
      background-size: auto, auto, auto, 34px 34px, 34px 34px, auto;
      font-family: var(--font);
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
    }
    button, select, input { font: inherit; }
    button { cursor: pointer; }
    button, select, input, a {
      transition: border-color .16s ease, background-color .16s ease, color .16s ease, box-shadow .16s ease, transform .16s ease;
    }
    button:focus-visible, select:focus-visible, input:focus-visible, a:focus-visible {
      outline: 0;
      box-shadow: var(--focus-ring);
    }
    .workbench-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 278px minmax(0, 1fr);
      background: linear-gradient(90deg, rgba(18,25,35,.035), transparent 18%);
    }
    body[data-route="live"] { --route-accent: #0f766e; --route-soft: #e6f4f1; --route-ink: #115e59; }
    body[data-route="decisions"] { --route-accent: #1d4ed8; --route-soft: #dbeafe; --route-ink: #1e3a8a; }
    body[data-route="memory"] { --route-accent: #b7791f; --route-soft: #fbf1db; --route-ink: #92400e; }
    body[data-route="orders"] { --route-accent: #b45309; --route-soft: #ffedd5; --route-ink: #9a3412; }
    body[data-route="riders"] { --route-accent: #475569; --route-soft: #e2e8f0; --route-ink: #334155; }
    .workbench-nav {
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 18px 14px;
      color: #d8e1ea;
      background:
        linear-gradient(180deg, rgba(255,255,255,.035), transparent 28%),
        linear-gradient(180deg, var(--nav), var(--nav-2));
      border-right: 1px solid rgba(255,255,255,.08);
      box-shadow: inset -1px 0 rgba(15,23,42,.42), 8px 0 28px rgba(15,23,42,.05);
    }
    .brand {
      display: grid;
      grid-template-columns: 38px 1fr;
      gap: 10px;
      align-items: center;
      padding: 8px 8px 18px;
      border-bottom: 1px solid rgba(255,255,255,.10);
    }
    .brand-mark {
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      border-radius: 13px;
      color: #172026;
      background: linear-gradient(135deg, #ffd05a, #ffb81c);
      box-shadow: 0 10px 24px rgba(255,184,28,.18);
      font: 800 13px var(--mono);
    }
    .brand strong { display: block; color: #fff; font-size: 15px; }
    .brand span { color: #9fb0c0; font-size: 12px; }
    .nav-section-title {
      margin: 18px 10px 8px;
      color: #8192a3;
      font: 700 11px var(--mono);
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .nav-list { display: grid; gap: 8px; }
    .nav-link {
      display: grid;
      grid-template-columns: 30px 1fr;
      gap: 10px;
      align-items: start;
      padding: 11px 10px;
      border-radius: 14px;
      color: #c8d4df;
      text-decoration: none;
      border: 1px solid transparent;
      position: relative;
      overflow: hidden;
    }
    .nav-link:hover { background: rgba(255,255,255,.07); transform: translateX(1px); }
    .nav-link[aria-current="page"] {
      color: #fff;
      background: var(--nav-active);
      border-color: rgba(255,184,28,.22);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.035);
    }
    .nav-link[aria-current="page"]::before {
      position: absolute;
      inset: 10px auto 10px 0;
      width: 3px;
      border-radius: 999px;
      background: #ffb81c;
      content: "";
    }
    .nav-icon {
      width: 24px;
      height: 24px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,.08);
      font: 800 11px var(--mono);
    }
    .nav-link[aria-current="page"] .nav-icon {
      color: #172026;
      background: #ffb81c;
    }
    .nav-copy { min-width: 0; }
    .nav-title-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .nav-title-line strong {
      color: #eef7fb;
      font-size: 14px;
      letter-spacing: -.01em;
    }
    .nav-role {
      padding: 3px 6px;
      border-radius: 999px;
      color: #9fb0c0;
      background: rgba(255,255,255,.07);
      font: 800 9px var(--mono);
      white-space: nowrap;
    }
    .nav-hint {
      display: block;
      margin-top: 4px;
      color: #9fb0c0;
      font-size: 12px;
      line-height: 1.32;
    }
    .nav-module {
      display: block;
      margin-top: 5px;
      color: #7f93a5;
      font: 800 10px var(--mono);
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .nav-meta {
      position: absolute;
      left: 14px;
      right: 14px;
      bottom: 16px;
      padding: 12px;
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 14px;
      background: rgba(255,255,255,.06);
      color: #9fb0c0;
      font-size: 12px;
      line-height: 1.5;
    }
    .workbench-main {
      min-width: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
      min-height: 72px;
      padding: 14px 22px;
      background: rgba(255,255,255,.94);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(18px);
      box-shadow: 0 8px 18px rgba(15,23,42,.045);
    }
    .topbar h1 { margin: 0 0 3px; font-size: 18px; letter-spacing: -.02em; font-weight: 850; }
    .topbar p { margin: 0; color: var(--muted); font-size: 13px; }
    .topbar-stats {
      display: grid;
      grid-template-columns: repeat(4, auto);
      gap: 8px;
      align-items: center;
    }
    .stat-pill {
      min-width: 92px;
      padding: 8px 11px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.035);
    }
    .stat-pill b { display: block; font-size: 15px; }
    .stat-pill span {
      color: var(--muted);
      font: 700 10px var(--mono);
      letter-spacing: .05em;
      text-transform: uppercase;
    }
    .route-view {
      min-width: 0;
      padding: 24px 26px;
    }
    .page-head {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 280px;
      gap: 14px;
      align-items: stretch;
      margin-bottom: 18px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background:
        linear-gradient(90deg, var(--route-soft, var(--green-soft)), rgba(255,255,255,.92) 33%, rgba(255,255,255,.96)),
        #fff;
      box-shadow: var(--shadow-card);
      backdrop-filter: blur(12px);
      position: relative;
      overflow: hidden;
    }
    .page-head::before {
      position: absolute;
      inset: 0 auto 0 0;
      width: 5px;
      background: var(--route-accent, var(--accent));
      content: "";
    }
    .eyebrow {
      color: var(--route-ink, var(--accent-2));
      font-size: 12px;
      font-weight: 850;
      letter-spacing: .02em;
    }
    .page-head h2 { margin: 5px 0 6px; font-size: 29px; letter-spacing: -.04em; font-weight: 900; }
    .page-head p { margin: 0; max-width: 820px; color: var(--muted); line-height: 1.55; }
    .page-role-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 12px;
    }
    .page-role-strip span {
      padding: 6px 8px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--route-ink, var(--accent-2));
      background: rgba(255,255,255,.70);
      font: 800 11px var(--mono);
    }
    .page-role-card {
      display: grid;
      align-content: center;
      gap: 6px;
      padding: 12px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 16px;
      background: rgba(255,255,255,.82);
      box-shadow: inset 0 1px rgba(255,255,255,.72);
    }
    .page-role-card b {
      color: var(--route-ink, var(--accent-2));
      font-size: 15px;
    }
    .page-role-card span {
      color: var(--ink-2);
      font-size: 12px;
      line-height: 1.45;
    }
    .page-role-card em {
      color: var(--muted);
      font: 800 10px var(--mono);
      font-style: normal;
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .page-grid { display: grid; gap: 14px; }
    .live-grid {
      grid-template-columns: 1fr;
      align-items: start;
    }
    .live-advantage-hero {
      display: grid;
      grid-template-columns: minmax(260px, .72fr) minmax(0, 1.28fr);
      gap: 16px;
      padding: 16px;
      border: 1px solid rgba(15,118,110,.24);
      border-radius: 22px;
      background:
        linear-gradient(120deg, rgba(15,118,110,.10), rgba(255,255,255,.94) 43%),
        radial-gradient(circle at 14% 8%, rgba(34,197,94,.12), transparent 34%),
        #fff;
      box-shadow: var(--shadow-card);
      backdrop-filter: blur(14px);
    }
    .advantage-lead {
      display: grid;
      align-content: center;
      gap: 11px;
      padding: 8px 6px;
    }
    .advantage-kicker {
      display: inline-flex;
      width: fit-content;
      align-items: center;
      gap: 7px;
      padding: 6px 9px;
      border: 1px solid rgba(15,118,110,.20);
      border-radius: 999px;
      color: var(--accent-2);
      background: rgba(255,255,255,.70);
      font: 800 11px var(--mono);
      text-transform: uppercase;
      letter-spacing: .06em;
    }
    .advantage-kicker::before {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(15,118,110,.10);
      content: "";
    }
    .advantage-lead h3 {
      margin: 0;
      color: var(--ink);
      font-size: clamp(30px, 4.2vw, 56px);
      line-height: .96;
      letter-spacing: -.06em;
    }
    .advantage-lead p {
      margin: 0;
      max-width: 560px;
      color: var(--ink-2);
      font-size: 14px;
      line-height: 1.58;
    }
    .advantage-target-row {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }
    .advantage-target-row span {
      padding: 6px 8px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(255,255,255,.72);
      font: 800 11px var(--mono);
    }
    .live-advantage-metrics {
      display: grid;
      gap: 10px;
      min-width: 0;
    }
    .live-ops-shell {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 336px;
      gap: 14px;
      align-items: start;
    }
    .live-primary-column,
    .live-side-rail {
      display: grid;
      gap: 14px;
      min-width: 0;
    }
    .live-side-rail {
      position: sticky;
      top: 88px;
      align-self: start;
    }
    .live-run-panel .card-body {
      display: grid;
      gap: 12px;
    }
    .live-run-panel .event-list {
      max-height: 250px;
      overflow: auto;
    }
    .decision-grid {
      grid-template-columns: 280px minmax(0, 1fr) 340px;
      align-items: start;
    }
    .memory-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .memory-workspace { grid-template-columns: 1fr; }
    .hermes-memory-workspace {
      gap: 16px;
    }
    .memory-overview {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .memory-command-center {
      display: grid;
      grid-template-columns: minmax(280px, .8fr) minmax(0, 1.2fr);
      gap: 16px;
      padding: 16px;
      border: 1px solid rgba(183,121,31,.26);
      border-radius: 22px;
      background:
        linear-gradient(120deg, rgba(251,241,219,.86), rgba(255,255,255,.94) 46%),
        radial-gradient(circle at 12% 12%, rgba(183,121,31,.12), transparent 34%),
        #fff;
      box-shadow: var(--shadow-card);
      backdrop-filter: blur(14px);
    }
    .memory-command-copy {
      display: grid;
      align-content: center;
      gap: 11px;
      padding: 6px;
    }
    .memory-command-copy h3 {
      margin: 0;
      font-size: clamp(28px, 3.4vw, 48px);
      line-height: 1;
      letter-spacing: -.055em;
    }
    .memory-command-copy p {
      margin: 0;
      max-width: 620px;
      color: var(--ink-2);
      font-size: 14px;
      line-height: 1.6;
    }
    .memory-kicker {
      width: fit-content;
      padding: 6px 9px;
      border: 1px solid rgba(183,121,31,.25);
      border-radius: 999px;
      color: var(--route-ink);
      background: rgba(255,255,255,.74);
      font: 800 11px var(--mono);
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .memory-model-row {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }
    .memory-model-row span {
      padding: 6px 8px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(255,255,255,.74);
      font: 800 11px var(--mono);
    }
    .memory-command-metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      align-content: stretch;
    }
    .memory-operating-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 14px;
      align-items: start;
    }
    .memory-layer-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .memory-layer-card,
    .memory-profile,
    .memory-flow-step {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.035);
    }
    .memory-layer-card {
      display: grid;
      gap: 9px;
      min-height: 176px;
    }
    .memory-layer-top,
    .memory-profile-top,
    .memory-flow-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .memory-layer-top strong,
    .memory-profile-top strong,
    .memory-flow-top strong {
      font-size: 14px;
      letter-spacing: -.01em;
    }
    .memory-scope,
    .memory-profile-type,
    .memory-flow-index {
      padding: 4px 7px;
      border-radius: 999px;
      color: var(--route-ink);
      background: var(--route-soft);
      font: 800 10px var(--mono);
      white-space: nowrap;
    }
    .memory-layer-card p,
    .memory-profile p,
    .memory-flow-step p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.48;
    }
    .memory-layer-meta,
    .memory-profile-meta,
    .memory-effect-line {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .memory-layer-meta span,
    .memory-profile-meta span,
    .memory-effect-line span {
      padding: 5px 7px;
      border: 1px solid rgba(15,23,42,.07);
      border-radius: 999px;
      color: var(--muted);
      background: #fff;
      font: 800 10px var(--mono);
    }
    .memory-profile-board {
      display: grid;
      gap: 10px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, #fff, var(--surface-2));
      box-shadow: var(--shadow-card);
    }
    .memory-profile-board h3 {
      margin: 0;
      font-size: 15px;
    }
    .memory-profile-board > p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .memory-profile-list {
      display: grid;
      gap: 10px;
    }
    .memory-flow-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(0, .92fr);
      gap: 14px;
      align-items: start;
    }
    .memory-flow-lane {
      display: grid;
      gap: 10px;
    }
    .memory-flow-step {
      display: grid;
      gap: 9px;
      position: relative;
      overflow: hidden;
    }
    .memory-flow-step::before {
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: var(--route-accent);
      opacity: .65;
      content: "";
    }
    .memory-evidence {
      display: grid;
      gap: 8px;
      padding: 10px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 12px;
      background: rgba(255,255,255,.76);
    }
    .memory-evidence-head {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
    }
    .memory-evidence-head strong {
      font-size: 12px;
      font-family: var(--mono);
    }
    .memory-evidence-head span {
      color: var(--muted);
      font: 800 10px var(--mono);
    }
    .rider-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .card {
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: #fff;
      box-shadow: var(--shadow-card);
      overflow: hidden;
      backdrop-filter: blur(10px);
    }
    .card-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background:
        linear-gradient(90deg, rgba(255,255,255,.96), rgba(248,250,252,.94)),
        #fff;
    }
    .card-head h3 { margin: 0; font-size: 15px; font-weight: 850; letter-spacing: -.01em; }
    .card-head span { color: var(--muted); font-size: 12px; }
    .card-head span em { font-style: normal; }
    .card-body { padding: 14px 16px; }
    .control-dock {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,.94);
      box-shadow: var(--shadow-card);
      position: sticky;
      top: 88px;
      z-index: 12;
      backdrop-filter: blur(14px);
    }
    .live-control-dock {
      position: relative;
      top: auto;
      z-index: 7;
      align-items: center;
      box-shadow: var(--shadow-card);
    }
    .live-control-dock .runtime-strip {
      flex: 1 1 420px;
      width: auto;
      grid-template-columns: repeat(5, minmax(86px, 1fr));
    }
    .live-control-dock .inference-progress {
      flex: 1 0 100%;
    }
    .runtime-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
      width: 100%;
    }
    .runtime-cell {
      min-height: 58px;
      padding: 9px 10px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: #fff;
      box-shadow: inset 0 1px rgba(255,255,255,.82);
    }
    .runtime-cell b {
      display: block;
      font: 800 15px var(--mono);
      color: var(--ink);
    }
    .runtime-cell span {
      color: var(--muted);
      font: 700 10px var(--mono);
      letter-spacing: .05em;
      text-transform: uppercase;
    }
    .inference-progress {
      width: 100%;
      height: 8px;
      overflow: hidden;
      position: relative;
      border-radius: 999px;
      border: 0;
      padding: 0;
      background: #dbe4ed;
      cursor: pointer;
      box-shadow: inset 0 1px 2px rgba(15,23,42,.08);
    }
    .inference-progress:hover {
      background: #cfdbe6;
    }
    .inference-progress:focus-visible {
      outline: 0;
      box-shadow: var(--focus-ring), inset 0 1px 2px rgba(15,23,42,.08);
    }
    .inference-progress span {
      display: block;
      width: var(--progress, 0%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #22c55e);
      transition: width .28s ease;
      pointer-events: none;
    }
    .primary-button {
      border: 0;
      border-radius: 11px;
      padding: 9px 14px;
      color: #172026;
      background: linear-gradient(180deg, #ffd76d, #ffb81c);
      box-shadow: 0 8px 18px rgba(255,184,28,.20);
      font-weight: 850;
    }
    .primary-button:hover:not([disabled]) { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(255,184,28,.26); }
    .primary-button[disabled] {
      cursor: default;
      opacity: .62;
    }
    .ghost-button, .select-control {
      border: 1px solid var(--line-strong);
      border-radius: 11px;
      padding: 8px 11px;
      color: var(--ink);
      background: #fff;
    }
    .ghost-button:hover, .select-control:hover {
      border-color: var(--accent);
      background: #fff;
    }
    .map-panel { min-height: 520px; position: relative; }
    .real-map-stage,
    .schematic-map {
      position: relative;
      height: 478px;
      margin: 14px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 18px;
      isolation: isolate;
      background:
        linear-gradient(90deg, rgba(148,163,184,.16) 1px, transparent 1px),
        linear-gradient(0deg, rgba(148,163,184,.16) 1px, transparent 1px),
        radial-gradient(circle at 60% 40%, rgba(15,118,110,.10), transparent 32%),
        #f8fafc;
      background-size: 44px 44px, 44px 44px, auto, auto;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.55);
    }
    .leaflet-live-map {
      position: absolute;
      inset: 0;
      z-index: 1;
      background: #e8eef2;
    }
    .leaflet-container {
      color: var(--ink);
      font-family: var(--font);
      filter: saturate(.74) contrast(.98) brightness(1.02);
    }
    .leaflet-control-attribution {
      color: rgba(38,53,65,.62);
      background: rgba(255,255,255,.74) !important;
      font-size: 9px;
    }
    .fallback-map-overlay {
      position: absolute;
      inset: 0;
      z-index: 2;
      opacity: 1;
      pointer-events: none;
      background:
        linear-gradient(90deg, rgba(148,163,184,.13) 1px, transparent 1px),
        linear-gradient(0deg, rgba(148,163,184,.13) 1px, transparent 1px),
        radial-gradient(circle at 56% 38%, rgba(15,118,110,.10), transparent 30%);
      background-size: 44px 44px, 44px 44px, auto;
      transition: opacity .22s ease;
    }
    .real-map-stage[data-real-map-status="leaflet"] .fallback-map-overlay {
      opacity: 0;
    }
    .real-map-stage[data-real-map-status="fallback"] .leaflet-live-map::after,
    .real-map-stage[data-real-map-status="loading"] .leaflet-live-map::after {
      position: absolute;
      inset: 50% auto auto 50%;
      transform: translate(-50%, -50%);
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(255,255,255,.82);
      font: 800 11px var(--mono);
      content: "匿名无标签底图加载中 / 备用底图就绪";
      white-space: nowrap;
    }
    .real-map-stage[data-real-map-status="fallback"] .leaflet-live-map::after {
      content: "匿名备用底图";
    }
    .leaflet-control-zoom {
      border: 1px solid rgba(15,23,42,.12) !important;
      border-radius: 12px !important;
      overflow: hidden;
      box-shadow: 0 10px 22px rgba(15,23,42,.12);
    }
    .leaflet-control-zoom a {
      color: var(--ink) !important;
      background: rgba(255,255,255,.92) !important;
    }
    .map-action-status {
      position: absolute;
      z-index: 6;
      left: 58px;
      top: 14px;
      display: grid;
      gap: 3px;
      max-width: min(360px, calc(100% - 204px));
      padding: 10px 12px 10px 14px;
      border: 1px solid rgba(15,23,42,.10);
      border-radius: 14px;
      color: var(--ink);
      background: rgba(255,255,255,.90);
      box-shadow: 0 10px 24px rgba(15,23,42,.10);
      backdrop-filter: blur(10px);
      pointer-events: none;
    }
    .map-action-status::before {
      position: absolute;
      inset: 11px auto 11px 0;
      width: 3px;
      border-radius: 999px;
      background: var(--route-accent, var(--accent));
      content: "";
    }
    .map-action-status strong {
      font-size: 13px;
      letter-spacing: -.01em;
    }
    .map-action-status span {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }
    .map-mode-chip {
      position: absolute;
      z-index: 5;
      right: 14px;
      top: 14px;
      padding: 6px 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--accent-2);
      background: rgba(255,255,255,.86);
      font: 800 11px var(--mono);
      box-shadow: 0 8px 18px rgba(15,23,42,.10);
    }
    .map-legend {
      position: absolute;
      z-index: 5;
      left: 14px;
      bottom: 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      max-width: 72%;
      padding: 7px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(255,255,255,.88);
      box-shadow: 0 8px 18px rgba(15,23,42,.07);
    }
    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      color: var(--muted);
      font-size: 11px;
    }
    .legend-swatch {
      width: 18px;
      height: 3px;
      border-radius: 999px;
      background: var(--accent);
    }
    .legend-dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      border: 1px solid #fff;
      box-shadow: 0 0 0 1px rgba(15,23,42,.10);
      background: var(--blue);
    }
    .legend-dot[data-kind="rider"] { background: var(--accent); }
    .legend-dot[data-kind="merchant"] { background: var(--blue); }
    .legend-dot[data-kind="order"] { background: var(--amber); }
    .legend-dot[data-kind="hotspot"] {
      background: rgba(183,121,31,.44);
      box-shadow: 0 0 0 5px rgba(183,121,31,.12);
    }
    .legend-swatch[data-lane="baseline"] { background: var(--red); opacity: .48; }
    .legend-swatch[data-lane="difference"] { background: var(--amber); }
    .legend-swatch[data-lane="previous"] { background: #64748b; opacity: .36; }
    .map-route {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .route-line {
      fill: none;
      stroke: var(--accent);
      stroke-width: 2.2;
      stroke-linecap: round;
      opacity: .76;
      filter: drop-shadow(0 1px 2px rgba(255,255,255,.86));
      transition: opacity .32s ease, stroke-width .32s ease;
    }
    .route-line[data-lane="ours"] {
      stroke: var(--accent);
      stroke-width: 2.6;
      opacity: .82;
    }
    .route-line[data-lane="baseline"] {
      stroke: var(--red);
      stroke-width: 1.8;
      stroke-dasharray: 4 5;
      opacity: .34;
    }
    .route-line[data-lane="difference"] {
      stroke: var(--amber);
      stroke-width: 3.1;
      opacity: .88;
    }
    .route-line[data-lane="previous"] {
      stroke: #64748b;
      stroke-width: 1.4;
      stroke-dasharray: 2 7;
      opacity: .23;
    }
    .route-line[data-lane="active-progress"] {
      stroke: #059669;
      stroke-width: 4.2;
      opacity: .95;
      stroke-dasharray: 5 6;
      animation: route-progress-flow 1.1s linear infinite;
    }
    .map-dot {
      --size: 12px;
      position: absolute;
      left: calc(var(--x) * 1%);
      top: calc(var(--y) * 1%);
      width: var(--size);
      height: var(--size);
      transform: translate(-50%, -50%);
      border-radius: 999px;
      border: 2px solid #fff;
      box-shadow: 0 5px 16px rgba(15,23,42,.18);
      transition: left .55s linear, top .55s linear, opacity .25s ease;
    }
    .map-dot[data-kind="merchant"] { background: var(--blue); }
    .map-dot[data-kind="rider"] { --size: 14px; background: var(--accent); }
    .map-dot[data-kind="order"] { --size: 10px; background: var(--amber); }
    .map-dot[data-show-label="true"]::after {
      position: absolute;
      left: calc(100% + 4px);
      top: 50%;
      transform: translateY(-50%);
      padding: 2px 5px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--ink-2);
      background: rgba(255,255,255,.88);
      box-shadow: 0 4px 10px rgba(15,23,42,.08);
      content: attr(data-map-label);
      font: 800 9px var(--mono);
      white-space: nowrap;
    }
    .map-dot[data-motion="moving"] {
      outline: 5px solid rgba(15,118,110,.10);
    }
    .map-dot[data-motion="moving"]::before {
      position: absolute;
      inset: -7px;
      border: 1px solid rgba(15,118,110,.18);
      border-radius: 999px;
      content: "";
      animation: rider-drive-ring 1.45s ease-out infinite;
    }
    .map-dot[data-motion="moving"]::after {
      content: attr(data-map-label) " 移动中";
    }
    .map-dot[data-release="new"] {
      animation: order-enter-pulse 1.8s ease-in-out infinite;
    }
    .hotspot {
      position: absolute;
      left: calc(var(--x) * 1%);
      top: calc(var(--y) * 1%);
      width: calc(72px + var(--severity) * 56px);
      height: calc(72px + var(--severity) * 56px);
      transform: translate(-50%, -50%);
      border-radius: 999px;
      background: rgba(183,121,31,.13);
      border: 1px solid rgba(183,121,31,.24);
    }
    .hotspot[data-active="false"] {
      opacity: .34;
      background: rgba(148,163,184,.10);
      border-color: rgba(148,163,184,.22);
    }
    .leaflet-map-pin {
      border: 0;
      background: transparent;
    }
    .leaflet-map-pin-body {
      position: relative;
      display: block;
      width: 13px;
      height: 13px;
      border: 2px solid #fff;
      border-radius: 999px;
      background: var(--blue);
      box-shadow: 0 5px 14px rgba(15,23,42,.20);
    }
    .leaflet-map-pin-body[data-kind="rider"] {
      width: 16px;
      height: 16px;
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(15,118,110,.10), 0 7px 18px rgba(15,23,42,.18);
    }
    .leaflet-map-pin-body[data-kind="rider"][data-motion="moving"] {
      animation: rider-drive-ring 1.45s ease-out infinite;
    }
    .leaflet-map-pin-body[data-kind="rider"][data-motion="moving"]::after {
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-35%, -50%);
      color: #fff;
      content: "›";
      font: 900 14px var(--font);
      line-height: 1;
    }
    .leaflet-map-pin-body[data-kind="order"] {
      width: 12px;
      height: 12px;
      background: var(--amber);
    }
    .leaflet-map-pin-body[data-release="new"] {
      animation: order-enter-pulse 1.8s ease-in-out infinite;
    }
    .leaflet-map-pin-label {
      position: absolute;
      left: 18px;
      top: 50%;
      transform: translateY(-50%);
      padding: 2px 5px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--ink-2);
      background: rgba(255,255,255,.86);
      box-shadow: 0 5px 12px rgba(15,23,42,.08);
      font: 800 9px var(--mono);
      white-space: nowrap;
    }
    .score-stack { display: grid; gap: 10px; }
    .live-side-rail,
    .decision-grid > aside,
    .operations-grid > aside {
      position: sticky;
      top: 88px;
      align-self: start;
    }
    .algorithm-pair {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .score-card {
      padding: 13px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      box-shadow: inset 0 1px rgba(255,255,255,.75);
    }
    .score-card b { display: block; font-size: 22px; letter-spacing: -.03em; }
    .score-card span { color: var(--muted); font-size: 12px; }
    .score-card[data-tone="good"] { background: var(--green-soft); border-color: rgba(15,118,110,.24); }
    .score-card[data-tone="warn"] { background: var(--amber-soft); border-color: rgba(183,121,31,.24); }
    .score-card[data-tone="risk"] { background: var(--red-soft); border-color: rgba(180,35,24,.22); }
    .live-advantage-hero .algorithm-pair {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .live-advantage-hero .score-card {
      min-height: 0;
      padding: 10px;
      background: rgba(255,255,255,.78);
    }
    .live-advantage-hero .score-card b {
      margin: 3px 0 2px;
      font-size: 21px;
    }
    .live-advantage-hero .score-card span:last-child {
      display: block;
      max-height: 34px;
      overflow: hidden;
      line-height: 1.35;
    }
    .live-advantage-hero .score-card[data-tone="good"] {
      background: linear-gradient(180deg, rgba(230,244,241,.98), rgba(255,255,255,.86));
      border-color: rgba(15,118,110,.34);
    }
    .live-advantage-hero .score-card[data-tone="warn"] {
      background: linear-gradient(180deg, rgba(251,241,219,.98), rgba(255,255,255,.84));
    }
    .delta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .live-advantage-hero .delta-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .live-advantage-hero .delta-grid .score-card {
      min-height: 0;
    }
    .metric-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 9px;
    }
    .live-run-panel .metric-strip {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .metric-chip {
      padding: 11px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: #fff;
      box-shadow: inset 0 1px rgba(255,255,255,.82);
    }
    .metric-chip b { display: block; margin-bottom: 2px; font: 800 16px var(--mono); }
    .metric-chip span { display: block; color: var(--muted); font-size: 12px; }
    .live-grid[data-inference-state="running"] .map-panel {
      outline: 2px solid rgba(15,118,110,.14);
    }
    @keyframes order-enter-pulse {
      0%, 100% { box-shadow: 0 5px 16px rgba(15,23,42,.18); }
      50% { box-shadow: 0 0 0 7px rgba(183,121,31,.14), 0 5px 16px rgba(15,23,42,.18); }
    }
    @keyframes route-progress-flow {
      to { stroke-dashoffset: -22; }
    }
    @keyframes rider-drive-ring {
      0% { box-shadow: 0 0 0 0 rgba(15,118,110,.24), 0 7px 18px rgba(15,23,42,.18); }
      100% { box-shadow: 0 0 0 11px rgba(15,118,110,0), 0 7px 18px rgba(15,23,42,.18); }
    }
    .event-list, .timeline-list, .memory-list, .compact-list {
      display: grid;
      gap: 9px;
    }
    .list-item {
      padding: 10px 11px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.025);
    }
    .list-item strong { display: block; margin-bottom: 4px; font-size: 13px; }
    .list-item span, .list-item p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .event-item {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 8px;
      align-items: start;
    }
    .event-tag {
      padding: 4px 7px;
      border-radius: 999px;
      color: var(--accent-2);
      background: var(--green-soft);
      font: 800 10px var(--mono);
      white-space: nowrap;
    }
    .event-tag[data-family="order"] { color: #92400e; background: var(--amber-soft); }
    .event-tag[data-family="score"] { color: var(--accent-2); background: var(--green-soft); }
    .event-tag[data-family="memory"] { color: #1d4ed8; background: #dbeafe; }
    .event-tag[data-family="decision"] { color: #334155; background: #e2e8f0; }
    .round-summary-grid {
      display: grid;
      gap: 9px;
    }
    .timeline-item { text-align: left; width: 100%; border: 1px solid var(--line); background: #fff; border-radius: var(--radius-md); padding: 10px; box-shadow: 0 1px 2px rgba(15,23,42,.025); }
    .timeline-item:hover { border-color: rgba(15,118,110,.24); background: #fff; transform: translateY(-1px); }
    .timeline-item[data-active="true"] { border-color: rgba(15,118,110,.36); background: linear-gradient(180deg, rgba(230,244,241,.86), #fff); }
    .timeline-item strong { display: block; margin-bottom: 4px; font-size: 13px; }
    .timeline-item span { display: block; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .timeline-meta {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 7px;
      color: var(--muted);
      font: 700 10px var(--mono);
    }
    .decision-scroll { max-height: 690px; overflow: auto; }
    .decision-canvas { display: grid; gap: 12px; }
    .decision-advantage-hero,
    .input-command-center,
    .resource-command-center,
    .demand-command-center,
    .capacity-command-center {
      display: grid;
      grid-template-columns: minmax(260px, .8fr) minmax(0, 1.2fr);
      gap: 14px;
      padding: 14px;
      border: 1px solid rgba(15,23,42,.10);
      border-radius: 18px;
      background:
        linear-gradient(120deg, var(--route-soft, var(--green-soft)), rgba(255,255,255,.94) 44%),
        #fff;
      box-shadow: var(--shadow-card);
    }
    .decision-advantage-copy,
    .input-command-copy,
    .resource-command-copy,
    .demand-command-copy,
    .capacity-command-copy {
      display: grid;
      align-content: center;
      gap: 9px;
    }
    .decision-advantage-copy h3,
    .input-command-copy h3,
    .resource-command-copy h3,
    .demand-command-copy h3,
    .capacity-command-copy h3 {
      margin: 0;
      font-size: clamp(24px, 3vw, 42px);
      line-height: 1;
      letter-spacing: -.05em;
    }
    .decision-advantage-copy p,
    .input-command-copy p,
    .resource-command-copy p,
    .demand-command-copy p,
    .capacity-command-copy p {
      margin: 0;
      color: var(--ink-2);
      font-size: 13px;
      line-height: 1.55;
    }
    .reason-kicker,
    .input-kicker,
    .resource-kicker,
    .demand-kicker,
    .capacity-kicker {
      width: fit-content;
      padding: 5px 8px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 999px;
      color: var(--route-ink, var(--accent-2));
      background: rgba(255,255,255,.72);
      font: 800 10px var(--mono);
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .decision-advantage-metrics,
    .input-signal-grid,
    .resource-signal-grid,
    .demand-signal-grid,
    .capacity-signal-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 9px;
    }
    .reason-graph {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .reason-node {
      display: grid;
      gap: 7px;
      min-height: 146px;
      padding: 11px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      position: relative;
      overflow: hidden;
      box-shadow: 0 1px 2px rgba(15,23,42,.025);
    }
    .reason-node::before {
      position: absolute;
      inset: 0 0 auto;
      height: 4px;
      background: var(--route-accent, var(--accent));
      opacity: .76;
      content: "";
    }
    .reason-node[data-status="passed"] {
      border-color: rgba(15,118,110,.26);
      background: linear-gradient(180deg, rgba(230,244,241,.78), #fff);
    }
    .reason-node[data-status="rejected"] {
      border-color: rgba(148,163,184,.28);
      background: #f1f5f9;
      opacity: .76;
    }
    .reason-node[data-status="running"] {
      border-color: rgba(37,99,235,.26);
      background: linear-gradient(180deg, #dbeafe, #fff);
    }
    .reason-node-top,
    .candidate-path-top,
    .focus-card-top {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: flex-start;
    }
    .reason-node-top strong,
    .candidate-path-top strong,
    .focus-card-top strong {
      font-size: 13px;
    }
    .reason-node-index,
    .path-status,
    .focus-badge {
      padding: 4px 7px;
      border-radius: 999px;
      color: var(--route-ink, var(--accent-2));
      background: var(--route-soft, var(--green-soft));
      font: 800 10px var(--mono);
      white-space: nowrap;
    }
    .reason-node p,
    .candidate-path p,
    .order-focus-card p,
    .rider-focus-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .candidate-path-board {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .candidate-path {
      display: grid;
      gap: 8px;
      padding: 11px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
    }
    .candidate-path[data-status="selected"] {
      border-color: rgba(15,118,110,.34);
      background: linear-gradient(180deg, rgba(230,244,241,.90), #fff);
      box-shadow: inset 0 0 0 1px rgba(15,118,110,.08);
    }
    .candidate-path[data-status="rejected"] {
      background: #f8fafc;
      opacity: .82;
    }
    .decision-step-flow {
      display: grid;
      gap: 10px;
    }
    .decision-step-card {
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr);
      gap: 12px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 15px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.03), 0 8px 18px rgba(15,23,42,.035);
    }
    .decision-step-card[data-step-status="final"] {
      border-color: rgba(15,118,110,.28);
      background: linear-gradient(180deg, rgba(230,244,241,.84), #fff);
    }
    .decision-step-index {
      display: grid;
      place-items: center;
      width: 34px;
      height: 34px;
      border-radius: 12px;
      color: #fff;
      background: var(--route-accent, var(--accent));
      font: 900 13px var(--mono);
      box-shadow: 0 8px 18px rgba(15,118,110,.16);
    }
    .decision-step-body {
      display: grid;
      gap: 7px;
      min-width: 0;
    }
    .decision-step-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .decision-step-top strong {
      font-size: 14px;
      letter-spacing: -.01em;
    }
    .decision-step-top span,
    .decision-plan-status {
      padding: 4px 7px;
      border-radius: 999px;
      color: var(--route-ink, var(--accent-2));
      background: var(--route-soft, var(--green-soft));
      font: 800 10px var(--mono);
      white-space: nowrap;
    }
    .decision-step-card p,
    .decision-plan-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .decision-plan-board {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .decision-plan-card {
      display: grid;
      align-content: start;
      gap: 8px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 15px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.025);
    }
    .decision-plan-card[data-plan="accepted"] {
      border-color: rgba(15,118,110,.32);
      background: linear-gradient(180deg, rgba(230,244,241,.90), #fff);
    }
    .decision-plan-card[data-plan="rejected"] {
      background: #f8fafc;
    }
    .decision-plan-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .decision-plan-top strong {
      font-size: 14px;
    }
    .decision-proof-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 9px;
    }
    .decision-evidence-grid,
    .order-focus-list,
    .rider-focus-list,
    .coverage-grid {
      display: grid;
      gap: 9px;
    }
    .decision-evidence-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .order-focus-list,
    .rider-focus-list {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .order-focus-card,
    .rider-focus-card,
    .coverage-card {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.025);
    }
    .order-focus-card[data-risk="high"] {
      border-color: rgba(180,35,24,.18);
      background: linear-gradient(180deg, rgba(254,228,226,.48), #fff 54%);
    }
    .rider-focus-card[data-state="available"] {
      border-color: rgba(15,118,110,.18);
      background: linear-gradient(180deg, rgba(230,244,241,.56), #fff 54%);
    }
    .coverage-card {
      display: grid;
      gap: 8px;
      background: #fff;
    }
    .coverage-card b {
      display: block;
      font-size: 13px;
    }
    .coverage-bar {
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    .coverage-bar span {
      display: block;
      width: calc(var(--coverage) * 100%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--route-accent, var(--accent)), #22c55e);
    }
    .decision-stage {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface-2);
      overflow: hidden;
    }
    .decision-stage-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.62);
    }
    .decision-stage-head b { color: var(--accent-2); font-size: 13px; }
    .decision-stage-head span { color: var(--muted); font: 800 10px var(--mono); }
    .decision-stage-body { display: grid; gap: 8px; padding: 11px 12px; }
    .chip-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .data-chip {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--ink);
      background: #fff;
      font: 700 11px var(--mono);
    }
    .score-row {
      display: grid;
      grid-template-columns: 138px 1fr auto;
      gap: 9px;
      align-items: center;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #fff;
      box-shadow: 0 1px 2px rgba(15,23,42,.025);
    }
    .score-bar {
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    .score-bar span {
      display: block;
      width: calc(var(--score) * 100%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #22c55e);
    }
    .action-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .action-card {
      padding: 9px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #fff;
    }
    .action-card strong { display: block; margin-bottom: 4px; font-size: 12px; }
    .action-card p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .context-metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .stage-row {
      display: grid;
      grid-template-columns: 130px 1fr auto;
      gap: 12px;
      align-items: start;
      padding: 12px 0;
      border-bottom: 1px solid var(--line);
    }
    .stage-row:last-child { border-bottom: 0; }
    .stage-row b { color: var(--accent-2); font-size: 13px; }
    .stage-row span { color: var(--muted); font-size: 12px; }
    .table-shell {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--surface);
      box-shadow: var(--shadow-card);
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
    th { position: sticky; top: 0; z-index: 1; color: var(--muted); background: #f8fafc; font: 800 11px var(--mono); }
    tbody tr:hover { background: rgba(15,118,110,.035); }
    td span { color: var(--muted); font-size: 12px; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 8px;
      border-radius: 999px;
      color: var(--accent-2);
      background: var(--green-soft);
      font-size: 12px;
    }
    .badge[data-risk="high"], .badge[data-state="late_risk"] { color: var(--red); background: var(--red-soft); }
    .badge[data-risk="medium"] { color: var(--amber); background: var(--amber-soft); }
    .filter-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,.94);
      box-shadow: var(--shadow-card);
    }
    .input-workspace, .resource-workspace, .demand-workspace, .capacity-workspace { grid-template-columns: 1fr; }
    .operations-overview {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .operations-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 330px;
      gap: 14px;
      align-items: start;
    }
    .operations-grid[data-density="summary-first"] {
      grid-template-columns: minmax(0, 1fr) 360px;
    }
    .orders-table-shell { max-height: 430px; }
    .orders-table-shell[data-evidence-role="secondary"],
    .rider-board[data-evidence-role="secondary"] {
      box-shadow: var(--shadow-tight);
    }
    .filter-bar .filter-count {
      margin-left: auto;
      align-self: center;
      color: var(--muted);
      font: 800 11px var(--mono);
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .order-context-list, .rider-context-list {
      display: grid;
      gap: 9px;
    }
    .time-lane {
      display: grid;
      gap: 8px;
    }
    .time-lane-item {
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }
    .lane-bar {
      height: 7px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    .lane-bar span {
      display: block;
      width: calc(var(--weight) * 100%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #22c55e);
    }
    .result-pair {
      display: grid;
      gap: 2px;
      font-size: 12px;
    }
    .result-pair b { color: var(--ink); font-weight: 800; }
    .result-pair span { color: var(--muted); }
    .rider-board {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .rider-evidence-shell {
      display: grid;
      overflow: hidden;
    }
    .rider-evidence-shell .rider-board {
      padding: 14px;
    }
    .rider-card[data-state="busy"] { border-color: rgba(15,118,110,.30); }
    .rider-card[data-state="ending_shift"] { border-color: rgba(183,121,31,.30); }
    .rider-load {
      height: 7px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    .rider-load span {
      display: block;
      width: calc(var(--load) * 100%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #22c55e);
    }
    .mini-map .map-dot[data-kind="home"] { --size: 9px; background: #64748b; }
    .mini-map .map-dot[data-kind="linked-order"] { --size: 8px; background: var(--amber); }
    .memory-item {
      display: grid;
      gap: 8px;
    }
    .memory-item-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .memory-item-head strong { margin: 0; }
    .memory-stage {
      padding: 4px 7px;
      border-radius: 999px;
      color: var(--accent-2);
      background: var(--green-soft);
      font: 800 10px var(--mono);
      white-space: nowrap;
    }
    .memory-stage[data-stage="curated"] { color: #1d4ed8; background: #dbeafe; }
    .memory-stage[data-stage="active"] { color: #92400e; background: var(--amber-soft); }
    .memory-stage[data-stage="feedback"] { color: #334155; background: #e2e8f0; }
    .memory-field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px;
    }
    .memory-field {
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
    }
    .memory-field b {
      display: block;
      margin-bottom: 3px;
      color: var(--accent-2);
      font: 800 10px var(--mono);
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .memory-field span { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .memory-meter {
      height: 7px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    .memory-meter span {
      display: block;
      width: calc(var(--confidence) * 100%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #22c55e);
    }
    .recall-lane {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .recall-card {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface-2);
    }
    .recall-card strong { display: block; margin-bottom: 6px; font-size: 13px; }
    .recall-card p { margin: 0 0 8px; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .rider-card .card-body { display: grid; gap: 10px; }
    .mini-map {
      position: relative;
      height: 92px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background:
        linear-gradient(90deg, rgba(148,163,184,.14) 1px, transparent 1px),
        linear-gradient(0deg, rgba(148,163,184,.14) 1px, transparent 1px),
        radial-gradient(circle at 68% 34%, rgba(15,118,110,.08), transparent 30%),
        #f8fafc;
      background-size: 24px 24px;
    }
    .route-empty {
      padding: 30px;
      color: var(--muted);
      text-align: center;
    }
    @media (max-width: 1180px) {
      .workbench-shell { grid-template-columns: 184px minmax(0, 1fr); }
      .brand { grid-template-columns: 40px 1fr; }
      .brand span, .nav-section-title, .nav-meta, .nav-hint, .nav-module, .nav-role { display: none; }
      .nav-link { grid-template-columns: 40px 1fr; justify-items: stretch; }
      .nav-copy { display: block; min-width: 0; }
      .nav-title-line strong { font-size: 13px; }
      .live-grid, .decision-grid, .memory-grid, .rider-grid { grid-template-columns: 1fr; }
      .live-advantage-hero, .live-ops-shell, .decision-grid, .decision-advantage-hero, .input-command-center, .resource-command-center, .demand-command-center, .capacity-command-center, .memory-command-center, .memory-operating-grid, .memory-flow-grid { grid-template-columns: 1fr; }
      .live-side-rail, .decision-grid > aside, .operations-grid > aside, .control-dock { position: static; }
      .topbar { grid-template-columns: 1fr; }
      .topbar-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .runtime-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .metric-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .live-advantage-hero .delta-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .operations-overview, .operations-grid, .operations-grid[data-density="summary-first"], .rider-board, .reason-graph, .candidate-path-board, .decision-plan-board, .decision-evidence-grid, .decision-proof-grid, .order-focus-list, .rider-focus-list { grid-template-columns: 1fr; }
      .memory-overview, .memory-command-metrics, .memory-layer-grid, .recall-lane { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 720px) {
      .workbench-shell { grid-template-columns: minmax(0, 1fr); }
      .workbench-nav { position: sticky; top: 0; z-index: 30; height: auto; padding: 10px 12px 12px; }
      .brand { padding: 4px 4px 10px; border-bottom-color: rgba(255,255,255,.08); }
      .nav-list { grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; }
      .nav-link { grid-template-columns: 1fr; padding: 8px 4px; text-align: center; border-radius: 12px; }
      .nav-link[aria-current="page"]::before { inset: auto 18px 0; width: auto; height: 3px; }
      .nav-icon { display: none; }
      .nav-copy { display: block; }
      .nav-title-line strong { display: block; font-size: 12px; line-height: 1.2; }
      .route-view { padding: 14px 12px 18px; }
      .topbar { padding: 12px 14px; }
      .filter-bar .select-control { flex: 1 1 160px; min-width: 0; }
      .filter-bar .filter-count { width: 100%; margin-left: 0; }
      .page-head { grid-template-columns: 1fr; padding: 14px; border-radius: 18px; }
      .page-role-card { padding: 10px; }
      .algorithm-pair, .delta-grid, .metric-strip { grid-template-columns: 1fr; }
      .live-advantage-hero { padding: 12px; border-radius: 18px; }
      .live-advantage-hero .algorithm-pair, .live-advantage-hero .delta-grid { grid-template-columns: 1fr; }
      .live-control-dock .runtime-strip { flex-basis: 100%; grid-template-columns: 1fr; }
      .operations-overview { grid-template-columns: 1fr; }
      .memory-overview, .memory-command-metrics, .memory-layer-grid, .recall-lane, .memory-field-grid, .context-metric-grid, .decision-advantage-metrics, .input-signal-grid, .resource-signal-grid, .demand-signal-grid, .capacity-signal-grid, .reason-graph, .candidate-path-board, .decision-plan-board, .decision-evidence-grid, .decision-proof-grid, .order-focus-list, .rider-focus-list { grid-template-columns: 1fr; }
      .schematic-map, .real-map-stage { height: 360px; margin: 10px; }
      .map-action-status { left: 12px; top: 58px; max-width: calc(100% - 24px); }
      .map-mode-chip { right: 10px; top: 10px; }
      .map-legend { left: 10px; right: 10px; max-width: none; bottom: 10px; }
      .action-grid, .runtime-strip { grid-template-columns: 1fr; }
      .score-row, .stage-row, .time-lane-item { grid-template-columns: 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: .001ms !important;
      }
    }

    /* ===== v2 自解释改造新增样式 ===== */
    /* 阶段状态徽章：随 compare_due 切换高峰/平峰，让「数字不动」从「像卡死」变成「明确待机」 */
    .advantage-kicker-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }
    .phase-status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--line-strong);
      background: rgba(255,255,255,.78);
      color: var(--muted);
      font: 800 11px var(--mono);
      letter-spacing: .02em;
    }
    .phase-status-badge::before {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--muted);
      content: "";
    }
    .phase-status-badge[data-phase="comparing"] {
      color: var(--accent-2);
      border-color: rgba(15,118,110,.32);
      background: var(--green-soft);
    }
    .phase-status-badge[data-phase="comparing"]::before {
      background: var(--accent);
      box-shadow: 0 0 0 4px rgba(15,118,110,.14);
      animation: phase-live-pulse 1.6s ease-in-out infinite;
    }
    .phase-status-badge[data-phase="idle"] {
      color: var(--amber);
      border-color: rgba(183,121,31,.30);
      background: var(--amber-soft);
    }
    .phase-status-badge[data-phase="idle"]::before { background: var(--amber); }
    .phase-status-badge[data-phase="waiting"] { color: var(--muted); }
    .phase-status-badge[data-phase="finished"] {
      color: var(--accent-2);
      border-color: rgba(15,118,110,.32);
      background: var(--green-soft);
    }
    .phase-status-badge[data-phase="finished"]::before { background: var(--accent); }
    @keyframes phase-live-pulse {
      0%, 100% { box-shadow: 0 0 0 3px rgba(15,118,110,.16); }
      50% { box-shadow: 0 0 0 6px rgba(15,118,110,.04); }
    }

    /* 演前导览：开始前替换一排 0 值卡片，说清「这页要演什么」 */
    .advantage-prebrief {
      display: grid;
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(248,250,252,.86));
      box-shadow: var(--shadow-card);
    }
    .prebrief-intro p {
      margin: 0 0 8px;
      color: var(--ink-2);
      font-size: 14px;
      line-height: 1.62;
    }
    .prebrief-intro p:last-child { margin-bottom: 0; }
    .prebrief-intro b { color: var(--ink); }
    .prebrief-watch {
      padding: 9px 11px;
      border-left: 3px solid var(--amber);
      border-radius: 8px;
      background: var(--amber-soft);
    }
    .prebrief-watch b { color: var(--red); }
    .prebrief-shocks {
      display: grid;
      gap: 7px;
      padding-top: 12px;
      border-top: 1px dashed var(--line-strong);
    }
    .prebrief-shocks-title {
      color: var(--muted);
      font: 800 11px var(--mono);
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .prebrief-shocks ul {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .prebrief-shocks li {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border: 1px solid rgba(183,121,31,.26);
      border-radius: 999px;
      background: rgba(255,255,255,.7);
      color: var(--ink-2);
      font-size: 12px;
    }
    .prebrief-shocks li b { color: var(--amber); font: 800 12px var(--mono); }

    /* 进度条剧情节点：小三角标记 + 下方常驻图例，告诉观众精彩段在哪 */
    .storyline-ticks {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .storyline-tick {
      position: absolute;
      top: 0;
      left: var(--at);
      width: 2px;
      height: 100%;
      transform: translateX(-1px);
      background: var(--muted);
      opacity: .85;
    }
    .storyline-tick[data-tone="crisis"] { background: var(--red); }
    .storyline-tick[data-tone="shock"] { background: var(--amber); }
    .storyline-tick[data-tone="start"] { background: var(--accent); }
    .storyline-tick[data-tone="finish"] { background: var(--ink); }
    .storyline-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      width: 100%;
      margin-top: 2px;
    }
    .storyline-chip {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--ink-2);
      font-size: 11px;
      line-height: 1;
    }
    .storyline-chip b {
      font: 800 10.5px var(--mono);
      color: var(--muted);
    }
    .storyline-chip::before {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--muted);
      content: "";
    }
    .storyline-chip[data-tone="crisis"] { border-color: rgba(180,35,24,.3); }
    .storyline-chip[data-tone="crisis"]::before { background: var(--red); }
    .storyline-chip[data-tone="crisis"] b { color: var(--red); }
    .storyline-chip[data-tone="shock"] { border-color: rgba(183,121,31,.3); }
    .storyline-chip[data-tone="shock"]::before { background: var(--amber); }
    .storyline-chip[data-tone="start"] { border-color: rgba(15,118,110,.3); }
    .storyline-chip[data-tone="start"]::before { background: var(--accent); }
    .storyline-chip[data-tone="finish"]::before { background: var(--ink); }

    /* 订单点状态着色：在途/待派/已处理，订单不再「闪一下就消失」 */
    .map-dot[data-kind="order"][data-status="active"] {
      --size: 11px;
      background: var(--amber);
      box-shadow: 0 5px 16px rgba(15,23,42,.18), 0 0 0 4px rgba(183,121,31,.16);
    }
    .map-dot[data-kind="order"][data-status="pending"] { background: var(--amber); }
    .map-dot[data-kind="order"][data-status="settled"] {
      --size: 7px;
      background: rgba(183,121,31,.45);
      border-color: rgba(255,255,255,.7);
      box-shadow: none;
      opacity: .55;
    }
    .leaflet-map-pin-body[data-kind="order"][data-status="active"] {
      box-shadow: 0 0 0 4px rgba(183,121,31,.18);
    }
    .leaflet-map-pin-body[data-kind="order"][data-status="settled"] {
      width: 8px;
      height: 8px;
      background: rgba(183,121,31,.5);
      opacity: .55;
    }
    /* 图例上三种订单状态点：待派单 / 执行中 / 已完成，颜色与订单点着色语义一致。 */
    .legend-dot[data-status="pending"] { background: #fff; border: 2px solid var(--amber); }
    .legend-dot[data-status="active"] { background: var(--amber); box-shadow: 0 0 0 3px rgba(183,121,31,.16); }
    .legend-dot[data-status="settled"] { background: rgba(183,121,31,.5); opacity: .55; }

    /* ===== 长期记忆页 · 自主学习可视化 ===== */
    /* 系列色（已过 CVD 校验）：节省=青绿 #0d9488（我方绿系）、记忆/置信度=琥珀 var(--amber)、召回=蓝 var(--blue) */
    .memory-evidence-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      align-content: stretch;
    }
    .memory-evidence-tile {
      display: grid;
      align-content: center;
      gap: 6px;
      padding: 14px 15px;
      border: 1px solid rgba(15,23,42,.08);
      border-radius: 16px;
      background: rgba(255,255,255,.9);
      min-height: 118px;
    }
    .memory-evidence-tile > span {
      color: var(--muted);
      font: 800 11px var(--mono);
      letter-spacing: .04em;
    }
    .memory-evidence-tile > b {
      font-size: clamp(21px, 1.9vw, 30px);
      line-height: 1.08;
      letter-spacing: -.03em;
      color: var(--ink);
    }
    .memory-evidence-tile > b em {
      font-style: normal;
      font-size: .58em;
      font-weight: 700;
      color: var(--muted);
    }
    .memory-evidence-tile > small {
      color: var(--ink-2);
      font-size: 11.5px;
      line-height: 1.4;
    }
    .memory-evidence-tile[data-tone="gain"] > b { color: #0b7268; }
    .memory-evidence-tile[data-tone="memory"] > b { color: var(--amber); }
    .memory-term-row {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }
    .memory-term-row span {
      padding: 6px 8px;
      border: 1px solid rgba(183,121,31,.22);
      border-radius: 999px;
      color: var(--route-ink);
      background: rgba(255,255,255,.78);
      font: 800 10.5px var(--mono);
    }

    /* 学习曲线卡片 */
    .memory-curve-head-controls {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .memory-replay-btn {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 14px;
      border: 1px solid rgba(13,148,136,.4);
      border-radius: 999px;
      background: #0d9488;
      color: #fff;
      font: 800 12px var(--font);
      cursor: pointer;
      transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
    }
    .memory-replay-btn:hover { box-shadow: 0 6px 16px rgba(13,148,136,.3); transform: translateY(-1px); }
    .memory-replay-btn[data-state="running"] { background: var(--ink-2); border-color: rgba(23,33,43,.4); }
    .memory-replay-clock {
      min-width: 52px;
      font: 800 12.5px var(--mono);
      color: var(--ink-2);
    }
    .memory-curve-stage {
      position: relative;
      width: 100%;
    }
    .memory-curve-stage svg { display: block; width: 100%; }
    .memory-curve-stage .curve-grid { stroke: #e7ecf2; stroke-width: 1; }
    .memory-curve-stage .curve-axis-text {
      fill: var(--muted);
      font: 600 10.5px var(--mono);
      font-variant-numeric: tabular-nums;
    }
    .memory-curve-stage .curve-panel-label {
      fill: var(--ink-2);
      font: 800 11px var(--font);
    }
    .memory-curve-stage .curve-note {
      fill: var(--muted);
      font: 600 10.5px var(--font);
    }
    .memory-curve-stage .shock-band { fill: rgba(100,116,139,.09); }
    .memory-curve-stage .shock-label {
      fill: #64748b;
      font: 800 10px var(--font);
    }
    .memory-curve-stage .saved-area { fill: rgba(13,148,136,.1); }
    .memory-curve-stage .saved-line {
      fill: none;
      stroke: #0d9488;
      stroke-width: 2;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
    .memory-curve-stage .conf-line {
      fill: none;
      stroke: var(--amber);
      stroke-width: 2;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
    .memory-curve-stage .conf-area { fill: rgba(183,121,31,.08); }
    .memory-curve-stage .round-dot { stroke: #fff; stroke-width: 2; }
    .memory-curve-stage .round-dot[data-state="novel"],
    .memory-curve-stage .round-dot[data-state="cold"],
    .memory-curve-stage .round-dot[data-state="partial"] { fill: var(--amber); }
    .memory-curve-stage .round-dot[data-state="transfer"] { fill: var(--blue); }
    .memory-curve-stage .round-dot[data-state="repeat"] { fill: #0d9488; }
    .memory-curve-stage .round-dot-halo {
      fill: none;
      stroke: rgba(13,148,136,.4);
      stroke-width: 2;
      animation: memory-halo 2.2s ease-out infinite;
      transform-box: fill-box;
      transform-origin: center;
    }
    @keyframes memory-halo {
      0% { transform: scale(.6); opacity: .9; }
      70% { transform: scale(1.7); opacity: 0; }
      100% { transform: scale(1.7); opacity: 0; }
    }
    .memory-curve-stage .curve-callout-line { stroke: #94a3b8; stroke-width: 1; }
    .memory-curve-stage .curve-callout-text {
      fill: var(--ink-2);
      font: 700 10.5px var(--font);
    }
    .memory-curve-stage .curve-endpoint-label {
      fill: var(--ink);
      font: 800 11.5px var(--mono);
      font-variant-numeric: tabular-nums;
    }
    .memory-curve-stage .crosshair-line { stroke: #94a3b8; stroke-width: 1; }
    .memory-curve-stage .playhead-line { stroke: var(--amber); stroke-width: 1.6; }
    .memory-curve-stage .playhead-knob { fill: var(--amber); stroke: #fff; stroke-width: 2; }
    .memory-curve-tooltip {
      position: absolute;
      z-index: 6;
      min-width: 210px;
      max-width: 280px;
      padding: 10px 12px;
      border: 1px solid var(--line-strong);
      border-radius: 12px;
      background: rgba(255,255,255,.97);
      box-shadow: 0 12px 28px rgba(15,23,42,.14);
      pointer-events: none;
      display: none;
    }
    .memory-curve-tooltip[data-open="1"] { display: block; }
    .memory-curve-tooltip .tip-title {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
      font: 800 12px var(--mono);
      color: var(--ink);
    }
    .memory-curve-tooltip .tip-scene {
      margin-bottom: 7px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.45;
    }
    .memory-curve-tooltip .tip-row {
      display: flex;
      align-items: baseline;
      gap: 7px;
      font-size: 11.5px;
      color: var(--muted);
      line-height: 1.6;
    }
    .memory-curve-tooltip .tip-row b {
      color: var(--ink);
      font-variant-numeric: tabular-nums;
    }
    .memory-curve-tooltip .tip-key {
      width: 12px;
      height: 0;
      border-top: 3px solid var(--muted);
      border-radius: 2px;
      flex: none;
    }
    .memory-curve-tooltip .tip-key[data-series="saved"] { border-color: #0d9488; }
    .memory-curve-tooltip .tip-key[data-series="conf"] { border-color: var(--amber); }
    .memory-curve-tooltip .tip-key[data-series="transfer"] { border-color: var(--blue); }
    .memory-curve-tooltip .tip-badge {
      margin-left: auto;
      padding: 3px 7px;
      border-radius: 999px;
      font: 800 10px var(--mono);
      color: #0b7268;
      background: rgba(13,148,136,.12);
    }
    .memory-curve-tooltip .tip-badge[data-state="novel"],
    .memory-curve-tooltip .tip-badge[data-state="cold"],
    .memory-curve-tooltip .tip-badge[data-state="partial"] {
      color: var(--amber);
      background: var(--amber-soft);
    }
    .memory-curve-tooltip .tip-badge[data-state="transfer"] {
      color: #1d4ed8;
      background: rgba(37,99,235,.12);
    }
    .memory-curve-legend {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 11.5px;
    }
    .memory-curve-legend .lg {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .memory-curve-legend .lg i {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      border: 2px solid #fff;
      box-shadow: 0 0 0 1px rgba(15,23,42,.12);
    }
    .memory-curve-legend .lg i[data-kind="first"],
    .memory-curve-legend .lg i[data-kind="novel"] { background: var(--amber); }
    .memory-curve-legend .lg i[data-kind="transfer"] { background: var(--blue); }
    .memory-curve-legend .lg i[data-kind="reuse"] { background: #0d9488; }
    .memory-curve-legend .lg i[data-kind="line-saved"] { width: 14px; height: 0; border: none; border-radius: 2px; border-top: 3px solid #0d9488; box-shadow: none; }
    .memory-curve-legend .lg i[data-kind="line-conf"] { width: 14px; height: 0; border: none; border-radius: 2px; border-top: 3px solid var(--amber); box-shadow: none; }
    .memory-curve-legend .lg i[data-kind="shock"] { width: 12px; height: 12px; border: none; border-radius: 3px; background: rgba(100,116,139,.18); box-shadow: none; }
    .memory-method-note {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.5;
    }
    .memory-round-table-wrap { margin-top: 10px; }
    .memory-round-table-wrap summary {
      cursor: pointer;
      color: var(--ink-2);
      font: 700 12px var(--font);
    }
    .memory-round-table-wrap .table-scroll {
      max-height: 260px;
      overflow: auto;
      margin-top: 8px;
      border: 1px solid var(--line);
      border-radius: 10px;
    }
    .memory-round-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11.5px;
    }
    .memory-round-table th, .memory-round-table td {
      padding: 6px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
      font-variant-numeric: tabular-nums;
    }
    .memory-round-table th {
      position: sticky;
      top: 0;
      background: var(--surface-2);
      color: var(--muted);
      font: 800 10.5px var(--mono);
    }
    .memory-round-table td { color: var(--ink-2); }

    /* 场景经验库矩阵 */
    .memory-matrix-rows {
      display: grid;
      gap: 6px;
    }
    .memory-matrix-row {
      display: grid;
      grid-template-columns: minmax(240px, 300px) minmax(0, 1fr) minmax(150px, 190px);
      gap: 14px;
      align-items: center;
      padding: 8px 10px;
      border: 1px solid transparent;
      border-radius: 12px;
      cursor: pointer;
      transition: background .12s ease, border-color .12s ease;
    }
    .memory-matrix-row:hover { background: var(--surface-2); }
    .memory-matrix-row[data-selected="1"] {
      border-color: rgba(183,121,31,.4);
      background: rgba(251,241,219,.5);
    }
    .memory-matrix-name strong {
      display: block;
      font-size: 12.5px;
      letter-spacing: -.01em;
      color: var(--ink);
      line-height: 1.35;
    }
    .memory-matrix-name span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font: 600 10.5px var(--mono);
    }
    .memory-matrix-lane {
      position: relative;
      height: 52px;
    }
    .memory-matrix-lane .lane-arcs {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }
    .memory-matrix-lane .lane-arcs path {
      fill: none;
      stroke: rgba(13,148,136,.4);
      stroke-width: 1.4;
    }
    .memory-matrix-lane .lane-base {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 9px;
      border-top: 1px solid var(--line);
    }
    .memory-matrix-dot {
      position: absolute;
      bottom: 3px;
      transform: translateX(-50%);
      border-radius: 999px;
      border: 2px solid #fff;
      box-shadow: 0 0 0 1px rgba(15,23,42,.14);
      background: #0d9488;
      transition: opacity .18s ease;
    }
    .memory-matrix-dot[data-state="novel"],
    .memory-matrix-dot[data-state="cold"],
    .memory-matrix-dot[data-state="partial"] {
      background: #fff;
      border: 2.5px solid var(--amber);
      box-shadow: 0 0 0 1px rgba(183,121,31,.2);
    }
    .memory-matrix-dot[data-state="transfer"] {
      background: #fff;
      border: 2.5px solid var(--blue);
      box-shadow: 0 0 0 1px rgba(37,99,235,.22);
    }
    .memory-matrix-dot::after {
      /* 扩大命中区域，方便悬停 */
      content: "";
      position: absolute;
      inset: -8px;
    }
    .memory-matrix-dot[data-hidden="1"] { opacity: .12; }
    .memory-matrix-total {
      text-align: right;
      display: grid;
      gap: 3px;
      justify-items: end;
    }
    .memory-matrix-total b {
      font-size: 15px;
      color: #0b7268;
      font-variant-numeric: tabular-nums;
    }
    .memory-matrix-total span {
      color: var(--muted);
      font: 600 10.5px var(--mono);
    }
    .memory-matrix-axis {
      display: grid;
      grid-template-columns: minmax(240px, 300px) minmax(0, 1fr) minmax(150px, 190px);
      gap: 14px;
      padding: 0 10px;
    }
    .memory-matrix-axis .axis-track {
      position: relative;
      height: 16px;
    }
    .memory-matrix-axis .axis-track span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--muted);
      font: 600 10px var(--mono);
    }

    /* 召回链路流水线 */
    .memory-flow-grid2 {
      display: grid;
      grid-template-columns: minmax(0, 1.55fr) minmax(300px, 1fr);
      gap: 14px;
      align-items: start;
    }
    .memory-pipeline {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      position: relative;
    }
    .memory-pipe-stage {
      position: relative;
      display: grid;
      align-content: start;
      gap: 8px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      min-height: 190px;
      transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
    }
    .memory-pipe-stage[data-active="1"] {
      border-color: rgba(183,121,31,.5);
      box-shadow: 0 10px 24px rgba(183,121,31,.14);
      transform: translateY(-2px);
    }
    .memory-pipe-stage .pipe-step-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .memory-pipe-stage .pipe-step-head strong { font-size: 12.5px; }
    .memory-pipe-stage .pipe-step-head em {
      font: 800 9.5px var(--mono);
      font-style: normal;
      color: var(--route-ink);
      background: var(--route-soft);
      border-radius: 999px;
      padding: 3px 7px;
      white-space: nowrap;
    }
    .memory-pipe-stage > p {
      margin: 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.5;
    }
    .memory-pipe-stage:not(:last-child)::after {
      content: "";
      position: absolute;
      top: 50%;
      right: -12px;
      width: 12px;
      height: 2px;
      background: repeating-linear-gradient(90deg, rgba(183,121,31,.8) 0 4px, transparent 4px 7px);
      animation: memory-flow-dash 1s linear infinite;
    }
    @keyframes memory-flow-dash {
      from { background-position-x: 0; }
      to { background-position-x: 7px; }
    }
    .memory-sim-bars {
      display: grid;
      gap: 5px;
    }
    .memory-sim-bar {
      display: grid;
      grid-template-columns: 62px minmax(0, 1fr) 30px;
      align-items: center;
      gap: 7px;
      font: 600 10px var(--mono);
      color: var(--muted);
    }
    .memory-sim-bar .bar-track {
      height: 6px;
      border-radius: 999px;
      background: var(--surface-3);
      overflow: hidden;
    }
    .memory-sim-bar .bar-fill {
      height: 100%;
      border-radius: 999px;
      background: var(--blue);
      opacity: .78;
    }
    .memory-sim-bar b {
      text-align: right;
      color: var(--ink-2);
      font-variant-numeric: tabular-nums;
    }
    .memory-case-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .memory-case-chips span {
      padding: 4px 7px;
      border: 1px solid rgba(37,99,235,.24);
      border-radius: 999px;
      background: rgba(37,99,235,.07);
      color: #1d4ed8;
      font: 700 10px var(--mono);
    }
    .memory-conf-shift {
      display: flex;
      align-items: center;
      gap: 8px;
      font: 800 12px var(--mono);
      color: var(--ink);
      font-variant-numeric: tabular-nums;
    }
    .memory-conf-shift .conf-arrow { color: var(--amber); }
    .memory-conf-track {
      position: relative;
      height: 8px;
      border-radius: 999px;
      background: var(--amber-soft);
      overflow: hidden;
    }
    .memory-conf-track span {
      position: absolute;
      inset: 0 auto 0 0;
      border-radius: 999px;
      background: var(--amber);
      width: calc(var(--conf, 0) * 100%);
      transition: width .8s ease;
    }
    .memory-pipe-result {
      display: grid;
      gap: 4px;
      padding: 9px 10px;
      border-radius: 10px;
      background: var(--green-soft);
      color: #0b7268;
      font-size: 11px;
      line-height: 1.45;
    }
    .memory-pipe-result b { font-size: 13px; font-variant-numeric: tabular-nums; }

    /* 记忆分层 · Reflection 提炼漏斗 */
    .memory-funnel {
      display: grid;
      gap: 8px;
    }
    .memory-funnel-tier {
      position: relative;
      display: grid;
      gap: 4px;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #fff;
    }
    .memory-funnel-tier[data-tier="episodic"] { width: 100%; }
    .memory-funnel-tier[data-tier="semantic"] { width: 82%; }
    .memory-funnel-tier[data-tier="policy"] { width: 64%; }
    .memory-funnel-tier .tier-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
    }
    .memory-funnel-tier .tier-head strong { font-size: 12.5px; }
    .memory-funnel-tier .tier-head b {
      font: 800 16px var(--font);
      color: var(--amber);
      font-variant-numeric: tabular-nums;
    }
    .memory-funnel-tier p {
      margin: 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.5;
    }
    .memory-funnel-tier .tier-op {
      position: absolute;
      right: -4px;
      bottom: -15px;
      z-index: 2;
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid rgba(183,121,31,.3);
      background: #fff;
      color: var(--route-ink);
      font: 800 9.5px var(--mono);
    }
    .memory-hierarchy-note {
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.55;
    }
    .memory-rule-list {
      display: grid;
      gap: 6px;
      margin-top: 10px;
    }
    .memory-rule-list .rule-item {
      display: grid;
      gap: 3px;
      padding: 9px 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--surface-2);
    }
    .memory-rule-list .rule-item b {
      font-size: 11.5px;
      color: var(--ink);
      line-height: 1.4;
      font-weight: 700;
    }
    .memory-rule-list .rule-item span {
      color: var(--muted);
      font: 600 10px var(--mono);
    }

    /* 跨模块索引联动：曲线点 ↔ 数据表行、召回案例 → 场景经验行 */
    .memory-lead-note {
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 11.5px;
      line-height: 1.55;
    }
    .memory-round-table tbody tr { cursor: pointer; }
    .memory-round-table tbody tr td { transition: background .25s ease; }
    .memory-round-table tbody tr:hover td { background: var(--surface-2); }
    .memory-round-table tbody tr[data-flash="1"] td { background: rgba(251,241,219,.95); }
    /* 来源定位高亮用蓝色（与召回芯片同色系），与琥珀的“当前查看”选中态区分 */
    .memory-matrix-row[data-flash="1"] {
      border-color: rgba(37,99,235,.5);
      background: rgba(37,99,235,.07);
      box-shadow: 0 0 0 2px rgba(37,99,235,.14);
    }
    .memory-case-chips span[data-case-id] { cursor: pointer; transition: background .15s ease, border-color .15s ease; }
    .memory-case-chips span[data-case-id]:hover {
      background: rgba(37,99,235,.16);
      border-color: rgba(37,99,235,.5);
    }
    .memory-transfer-chip {
      padding: 4px 7px;
      border: 1px solid rgba(13,148,136,.35);
      border-radius: 999px;
      background: var(--green-soft);
      color: #0b7268;
      font: 700 10px var(--mono);
      cursor: pointer;
      transition: background .15s ease;
    }
    .memory-transfer-chip:hover { background: rgba(13,148,136,.16); }
    .memory-round-table td small { color: var(--muted); font-size: 10px; }
    .memory-curve-stage .memory-focus-halo {
      fill: none;
      stroke: #0d9488;
      stroke-width: 2.5;
      transform-box: fill-box;
      transform-origin: center;
      /* 脉冲 3 次吸引注意后停为静态选中圈，直到再次点击取消 */
      animation: memory-halo 1.15s ease-out 3;
    }
    @media (prefers-reduced-motion: reduce) {
      .memory-curve-stage .memory-focus-halo { animation: none; }
    }

    @media (max-width: 1280px) {
      .memory-evidence-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .memory-flow-grid2 { grid-template-columns: 1fr; }
      .memory-pipeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .memory-matrix-row, .memory-matrix-axis { grid-template-columns: minmax(190px, 230px) minmax(0, 1fr) minmax(110px, 130px); }
    }
    @media (prefers-reduced-motion: reduce) {
      .memory-curve-stage .round-dot-halo { animation: none; opacity: 0; }
      .memory-pipe-stage:not(:last-child)::after { animation: none; }
      .memory-replay-btn { transition: none; }
    }
  </style>
</head>
<body data-shell="dispatch-workbench-shell" data-visual-system="enterprise-dispatch-v2" data-visual-polish="chinese-enterprise-workbench-v3" data-density="high-information" data-secret-handling="env-only-redacted">
  <div id="dispatch-workbench-shell" class="workbench-shell" data-product-reference="kandbox-dispatch">
    <aside class="workbench-nav" aria-label="调度工作台导航">
      <div class="brand">
        <div class="brand-mark">调度</div>
        <div>
          <strong>外卖调度</strong>
          <span>智能推演工作台</span>
        </div>
      </div>
      <div class="nav-section-title">核心页面</div>
      <nav id="route-nav" class="nav-list"></nav>
      <div class="nav-meta">
        <strong>工作台导览</strong><br>
        先看实时推理优势，再追溯决策过程、长期记忆、订单池和骑手运力。
      </div>
    </aside>
    <main class="workbench-main">
      <header class="topbar">
        <div>
          <h1 id="route-title">外卖配送智能调度工作台</h1>
          <p id="route-subtitle">围绕订单、骑手、地图、决策和记忆构建的实时调度工作台。</p>
        </div>
        <div id="topbar-stats" class="topbar-stats"></div>
      </header>
      <section id="route-view" class="route-view" data-route-view="live" aria-live="polite"></section>
    </main>
  </div>
  <script id="dispatch-workbench-bootstrap" type="application/json">__BOOT_JSON__</script>
  <script>
    const dispatchBoot = JSON.parse(document.getElementById("dispatch-workbench-bootstrap").textContent);
    const workbench = dispatchBoot.workbench;
    const contract = dispatchBoot.contract;
    const routeCopy = {
      live: {
        icon: "推",
        title: "实时推理",
        navLabel: "实时推理",
        navRole: "主控台",
        navHint: "看系统自动推演、地图动作和累计优势。",
        module: "地图推演",
        outcome: "自动推演 + 优势证明",
        subtitle: "订单释放、骑手移动、路线变化和累计对比在同一个运营视图中联动。"
      },
      decisions: {
        icon: "决",
        title: "决策过程",
        navLabel: "决策过程",
        navRole: "可追溯",
        navHint: "看每一轮为什么这样派、放弃了什么。",
        module: "推导链路",
        outcome: "评分过程 + 动作回写",
        subtitle: "每一轮触发、过滤、评分、派单动作和结果回写独立成页。"
      },
      memory: {
        icon: "忆",
        title: "长期记忆",
        navLabel: "长期记忆",
        navRole: "自主学习",
        navHint: "看记忆如何沉淀、复用，并放大调度收益。",
        module: "经验沉淀",
        outcome: "学习曲线 + 复用证据",
        subtitle: "长期记忆视图：全天学习曲线、场景经验复用和召回链路，证明记忆确实让派单更强。"
      },
      orders: {
        icon: "单",
        title: "订单池",
        navLabel: "订单池",
        navRole: "需求视图",
        navHint: "看全天订单、时段、风险和进入推理状态。",
        module: "订单池",
        outcome: "需求全集 + 风险筛选",
        subtitle: "全天订单全集已预置，只用于调度可见性、筛选和风险判断。"
      },
      riders: {
        icon: "骑",
        title: "骑手运力",
        navLabel: "骑手运力",
        navRole: "供给视图",
        navHint: "看骑手班次、位置、负载和任务链。",
        module: "运力池",
        outcome: "供给盘点 + 负载判断",
        subtitle: "骑手班次、在线状态、位置、负载和任务链统一盘点。"
      }
    };
    const routeOrder = ["live", "decisions", "memory", "orders", "riders"];
    const inferenceState = {
      started: false,
      running: false,
      currentTimeS: workbench.timeline.start_s,
      speed: 1,
      mode: "current",
      timerId: null,
      tickMs: 700,
      lastTickAt: 0
    };
    let selectedDecisionId = workbench.decisions[0]?.id || "";
    const orderIndex = Object.fromEntries(workbench.entities.orders.map((order) => [order.id, order]));
    // ---- 订单生命周期模型（时间真值，前后端一致）----------------------------
    // 目标：地图上的每一个元素都严格由「真实时间戳」决定，绝不提前展示未来订单。
    // 每个订单在任意推演秒 T 下只有四种状态：
    //   unreleased 未释放 -> waiting 已释放待派单 -> dispatched 已派单执行中 -> completed 已完成
    // 关键时间点全部取自后端 payload：
    //   created_at_s  订单真实创建时间（释放时间）
    //   assign_at_s   派单时间 = 该订单所属决策轮的 trigger_time_s（真实触发时间）
    //   complete_at_s 完成时间 = assign_at_s + 路线 eta（真实预计送达）
    const ORDER_FADE_S = 300;      // 完成后仍在地图淡出保留的时长（便于追溯），之后移除
    const DEFAULT_SERVICE_S = 1500; // 未进入任何决策轮的订单（46 单）的估算服务时长
    const riderAliasBucket = (workbench.map.aliases && workbench.map.aliases.riders) || {};
    function riderLabelForId(courierId) {
      if (!courierId) return "";
      return riderAliasBucket[courierId] || courierId;
    }
    const decisionByOrderId = (() => {
      const map = {};
      for (const decision of workbench.decisions || []) {
        for (const action of decision.final_actions || []) {
          if (action.order_id && !(action.order_id in map)) map[action.order_id] = { decision, action };
        }
      }
      return map;
    })();
    const oursRouteByOrderId = (() => {
      const map = {};
      for (const route of workbench.map.routes || []) {
        if (route.lane === "ours" && route.order_id && !(route.order_id in map)) map[route.order_id] = route;
      }
      return map;
    })();
    const orderLifecycle = (() => {
      const life = {};
      for (const order of workbench.entities.orders || []) {
        const created = Number(order.created_at_s);
        const dispatch = decisionByOrderId[order.id];
        const route = oursRouteByOrderId[order.id];
        let assignAt = null;
        let courierId = "";
        let courierLabel = "";
        let completeAt;
        let dispatched = false;
        if (dispatch) {
          dispatched = true;
          assignAt = Number(dispatch.decision.trigger_time_s);
          courierId = dispatch.action.courier_id || (order.our_result && order.our_result.courier_id) || "";
          courierLabel = dispatch.action.courier_label || riderLabelForId(courierId);
          let etaS = route && Number.isFinite(Number(route.eta_s)) ? Number(route.eta_s) : NaN;
          if (!Number.isFinite(etaS) && order.our_result && Number.isFinite(Number(order.our_result.eta_min))) {
            etaS = Number(order.our_result.eta_min) * 60;
          }
          if (!Number.isFinite(etaS)) etaS = 600;
          completeAt = assignAt + Math.max(120, etaS);
        } else {
          // 已释放但未进入任何决策轮：按估算服务时长自然淡出，不虚构骑手归属。
          completeAt = created + DEFAULT_SERVICE_S;
        }
        life[order.id] = {
          id: order.id,
          map_label: order.map_label || "",
          created_at_s: created,
          assign_at_s: assignAt,
          courier_id: courierId,
          courier_label: courierLabel,
          complete_at_s: completeAt,
          dispatched,
          route_id: route ? route.id : ""
        };
      }
      return life;
    })();
    function orderStatusAt(orderId, simTimeS = inferenceState.currentTimeS) {
      const life = orderLifecycle[orderId];
      if (!life || !Number.isFinite(life.created_at_s)) return "unknown";
      if (simTimeS < life.created_at_s) return "unreleased";
      if (life.dispatched) {
        if (simTimeS < life.assign_at_s) return "waiting";
        if (simTimeS < life.complete_at_s) return "dispatched";
        return "completed";
      }
      return simTimeS < life.complete_at_s ? "waiting" : "completed";
    }
    const orderStatusLabels = {
      unreleased: "未释放",
      waiting: "已释放·待派单",
      dispatched: "已派单·执行中",
      completed: "已完成",
      unknown: "未知"
    };
    function orderStatusLabel(status) {
      return orderStatusLabels[status] || orderStatusLabels.unknown;
    }
    // ------------------------------------------------------------------------
    const orderFilterState = {
      timeBand: "all",
      area: "all",
      status: "all",
      risk: "all"
    };
    const riderFilterState = {
      area: "all",
      state: "all"
    };
    const inferenceModeLabels = {
      current: "当前算法",
      compare: "对比",
      overlay: "叠加"
    };
    const eventTypeClasses = {
      order_entered: "event-type-order_entered",
      decision_round: "event-type-decision_round",
      score_update: "event-type-score_update",
      memory_writeback: "event-type-memory_writeback",
      memory_recall: "event-type-memory_recall",
      future_policy_shift: "event-type-future_policy_shift"
    };
    const eventMeta = {
      order_entered: { label: "订单进入", family: "order" },
      decision_round: { label: "决策轮次", family: "decision" },
      score_update: { label: "累计更新", family: "score" },
      memory_writeback: { label: "记忆写入", family: "memory" },
      memory_recall: { label: "记忆命中", family: "memory" },
      future_policy_shift: { label: "策略整理", family: "memory" }
    };
    const statusLabels = {
      scheduled: "待释放",
      entered_inference: "已进推理",
      assigned: "已分配",
      delivered: "已送达",
      late_risk: "超时风险"
    };
    const riskLabels = {
      low: "低风险",
      medium: "中风险",
      high: "高风险"
    };
    const riderStateLabels = {
      available: "可接单",
      busy: "配送中",
      ending_shift: "临近下线",
      offline: "离线"
    };
    const memoryStageLabels = {
      new: "新沉淀",
      curated: "已整理",
      active: "命中中",
      feedback: "效果反馈"
    };
    const memoryScopeLabels = {
      GLOBAL: "全局",
      PROFILE: "画像",
      recall: "召回",
      working: "工作记忆",
      profile: "画像",
      policy: "策略"
    };
    const memoryChannelLabels = {
      "recall-before-scoring": "评分前召回",
      "decision-result-writeback": "结果回写",
      "future-policy-shift": "策略整理",
      memory_writeback: "记忆写入",
      memory_recall: "记忆召回",
      future_policy_shift: "策略整理",
      feedback: "效果反馈"
    };
    const profileTypeLabels = {
      rider: "骑手画像",
      area: "商圈画像",
      order: "订单画像"
    };
    const stageLabels = {
      order_release: "订单释放",
      rider_pool: "骑手池",
      time_window: "时间窗口",
      area_and_shift: "区域与班次",
      risk_guardrail: "风险保护",
      candidate_filter: "候选过滤",
      feasibility: "可行性",
      scoring: "综合评分",
      assignment: "派单输出",
      memory: "记忆回写"
    };
    const demandPhaseLabels = {
      breakfast: "早餐时段",
      "pre-dispatch": "推理开始前",
      lunch_peak: "午高峰",
      afternoon_tea: "下午茶",
      dinner_peak: "晚高峰",
      night_supply_gap: "夜间供给缺口"
    };
    const weatherLabels = {
      clear: "晴天",
      cloudy: "多云",
      mixed: "混合天气",
      rain: "雨天",
      light_rain: "小雨",
      heavy_rain: "强降雨"
    };
    const shockLabels = {
      rain_slowdown: "降雨降速",
      merchant_burst: "商家爆单",
      courier_shortage: "骑手短缺",
      traffic_block: "道路拥堵",
      road_congestion: "道路拥堵"
    };
    const liveTileLayer = {
      id: "cartodb-light-nolabels",
      url: "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
      attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
      subdomains: "abcd"
    };
    let liveLeafletMap = null;
    let liveLeafletOverlayGroup = null;
    let liveMapHydrationToken = "";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }

    function fmtNumber(value, digits = 0) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
      return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }

    function fmtSigned(value, digits = 1) {
      const numberValue = Number(value);
      if (Number.isNaN(numberValue)) return "-";
      const sign = numberValue > 0 ? "+" : "";
      return `${sign}${fmtNumber(numberValue, digits)}`;
    }

    function fmtFewer(value, unit, digits = 0) {
      const numberValue = Number(value) || 0;
      if (numberValue < 0) return `少 ${fmtNumber(Math.abs(numberValue), digits)} ${unit}`;
      if (numberValue > 0) return `多 ${fmtNumber(numberValue, digits)} ${unit}`;
      return `持平 ${fmtNumber(0, digits)} ${unit}`;
    }

    function displayFrom(map, value) {
      return map[value] || value || "-";
    }

    function displayStatus(value) {
      return displayFrom(statusLabels, value);
    }

    function displayRisk(value) {
      return displayFrom(riskLabels, value);
    }

    function displayRiderState(value) {
      return displayFrom(riderStateLabels, value);
    }

    function displayMemoryStage(value) {
      return displayFrom(memoryStageLabels, value);
    }

    function displayMemoryScope(value) {
      return displayFrom(memoryScopeLabels, value);
    }

    function displayMemoryChannel(value) {
      return displayFrom(memoryChannelLabels, value);
    }

    function displayProfileType(value) {
      return displayFrom(profileTypeLabels, value);
    }

    function displayStage(value) {
      return displayFrom(stageLabels, value);
    }

    function displayDemandPhase(value) {
      return displayFrom(demandPhaseLabels, value);
    }

    function displayWeather(value) {
      return displayFrom(weatherLabels, value);
    }

    function displayShock(value) {
      return displayFrom(shockLabels, value);
    }

    function displayTag(value) {
      return displayShock(displayWeather(displayDemandPhase(value)));
    }

    function displayTriggerReason(value) {
      const text = String(value || "");
      if (!text) return "-";
      if (text.startsWith("Pressure change:")) return `压力变化：${text.replace("Pressure change:", "").replace(".", "").trim()}`;
      if (text === "Planner comparison due under current order pressure.") return "当前订单压力达到阈值，触发算法对比。";
      const scheduled = text.match(/^Scheduled (.+) dispatch round\\.$/);
      if (scheduled) return `按计划进入${displayDemandPhase(scheduled[1])}派单轮次。`;
      return text;
    }

    function displayDecisionSummary(value) {
      const text = String(value || "");
      if (!text) return "-";
      const autoMatch = text.match(/^AutoSolver assigned (\\d+) orders with risk-aware availability scoring; avg ETA ([0-9.]+) min\\.$/);
      if (autoMatch) return `我方方案分配 ${autoMatch[1]} 单，综合骑手可用性和超时风险，平均预计 ${autoMatch[2]} 分钟。`;
      const greedyMatch = text.match(/^Nearest greedy assigned (\\d+) orders by pickup distance; avg ETA ([0-9.]+) min\\.$/);
      if (greedyMatch) return `最近距离基线分配 ${greedyMatch[1]} 单，只按取餐距离排序，平均预计 ${greedyMatch[2]} 分钟。`;
      if (text === "No orders in this time slice.") return "当前时间片没有新订单。";
      if (text === "Uses memory recall and risk scoring to choose a lower-timeout route.") return "召回历史经验并结合风险评分，选择更低超时风险的路线。";
      if (text === "Dispatches by nearest distance while ignoring rain congestion and future order pressure.") return "只按最近距离派单，未考虑雨天拥堵和后续订单压力。";
      if (text === "Decision outcome updates dispatch memory when the challenger improves cumulative cost or risk.") return "当我方方案改善累计成本或风险时，把结果写回调度记忆。";
      return text;
    }

    function displayCandidateReason(value) {
      const text = String(value || "");
      if (!text) return "-";
      if (text === "Baseline optimizes nearest pickup, so queueing and deadline risk can accumulate.") return "基线只优化最近取餐点，排队和承诺时效风险容易累积。";
      if (text === "AutoSolver evaluates availability, congestion, route cost and deadline pressure.") return "我方同时评估骑手可用性、拥堵、路线成本和承诺时效压力。";
      if (text === "Nearest distance gives a quick feasible answer but carries high rain congestion risk.") return "最近距离能快速给出可行解，但在雨天和拥堵下超时风险偏高。";
      if (text === "Memory recall matches rainy lunch peak and reduces timeout risk.") return "召回雨天午高峰经验后，超时风险更低。";
      return text;
    }

    function displayActionReason(value) {
      const text = String(value || "");
      if (!text || text === "Baseline nearest-only assignment was rejected by risk-balanced scoring.") {
        return "基线只看最近距离，本轮被我方综合时效、成本和风险评分淘汰。";
      }
      return displayCandidateReason(text);
    }

    function displayMemoryText(value) {
      const text = String(value || "");
      if (!text) return "-";
      const linkedDecision = text.match(/^linked decision (.+)$/);
      if (linkedDecision) return `关联${readableDecisionLabel(linkedDecision[1])}`;
      if (text === "Positive policy shift retained for similar contexts.") return "相似场景下保留正向策略调整。";
      if (text === "Historical context recalled before scoring candidates.") return "评分候选骑手前已召回历史上下文。";
      if (text === "Writeback confidence updated after round outcome.") return "本轮结果产生后，已更新回写置信度。";
      if (text.startsWith("For ") && text.includes("prefer AutoSolver risk-balanced dispatch over nearest greedy.")) {
        const match = text.match(/^For (.+) with (.+) and congestion ([0-9.]+), prefer AutoSolver risk-balanced dispatch over nearest greedy\\.$/);
        if (match) return `${displayDemandPhase(match[1])}、${displayWeather(match[2])}、拥堵 ${match[3]} 时，优先使用我方风险均衡派单，而不是最近距离基线。`;
      }
      if (text.startsWith("For ") && text.includes("keep greedy as a guardrail")) {
        const match = text.match(/^For (.+), keep greedy as a guardrail when risk-balanced dispatch has weak savings\\.$/);
        if (match) return `${displayDemandPhase(match[1])}下，如果风险均衡方案收益不明显，保留贪心基线作为保护。`;
      }
      if (text.startsWith("Future policy: assign ")) {
        const match = text.match(/^Future policy: assign (.+) priority to AutoSolver when context matches (.+) and courier supply is (\\d+)\\.$/);
        if (match) return `未来相似${displayDemandPhase(match[2])}且骑手供给为 ${match[3]} 时，提高我方方案优先级。`;
      }
      if (text.startsWith("Recall ") && text.includes("nearest-only matching")) return "召回相似历史场景，优先排序风险均衡派单，再比较最近距离方案。";
      if (text.includes("congestion") && text.includes("riders")) {
        return text
          .replaceAll("breakfast", "早餐时段")
          .replaceAll("lunch_peak", "午高峰")
          .replaceAll("afternoon_tea", "下午茶")
          .replaceAll("dinner_peak", "晚高峰")
          .replaceAll("night_supply_gap", "夜间供给缺口")
          .replaceAll("mixed", "混合天气")
          .replaceAll("clear", "晴天")
          .replaceAll("rain", "雨天")
          .replace("congestion", "拥堵")
          .replace("with", "，")
          .replace("riders under shock pressure", "名骑手，存在冲击压力")
          .replace("riders under steady pressure", "名骑手，压力稳定");
      }
      return text;
    }

    function displayMemoryScenario(value) {
      const text = String(value || "");
      if (!text) return "-";
      const labels = {
        breakfast: "早餐时段",
        lunch_peak: "午高峰",
        afternoon_tea: "下午茶",
        dinner_peak: "晚高峰",
        night_supply_gap: "夜间供给缺口",
        clear: "晴天",
        rain: "雨天",
        mixed: "混合天气",
        low_congestion: "低拥堵",
        medium_congestion: "中等拥堵",
        high_congestion: "高拥堵",
        scarce_supply: "供给偏紧",
        balanced_supply: "供给平衡",
        abundant_supply: "供给充足",
        shock: "有冲击事件",
        steady: "压力稳定"
      };
      if (text.includes("|")) {
        return text.split("|").map((item) => labels[item] || displayMemoryText(item)).join(" / ");
      }
      return displayMemoryText(text);
    }

    function displayMemoryStepSummary(step) {
      if (!step) return "-";
      if (step.id === "hit") return displayMemoryScenario(step.summary);
      return displayMemoryText(step.summary);
    }

    function displayRiderPerformance(value) {
      const text = String(value || "");
      if (text === "High-throughput rider with stable willingness during peaks.") return "高峰期承载能力稳定，接单意愿较高。";
      if (text === "Balanced rider used across multiple dispatch rounds.") return "多轮派单表现均衡，可作为稳定运力。";
      if (text === "Reserve capacity for local-area pressure relief.") return "本地商圈储备运力，可用于缓解局部压力。";
      return text;
    }

    function clock(seconds) {
      const value = Math.max(0, Math.floor(Number(seconds) || 0));
      const hours = String(Math.floor(value / 3600)).padStart(2, "0");
      const minutes = String(Math.floor((value % 3600) / 60)).padStart(2, "0");
      return `${hours}:${minutes}`;
    }

    function clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    }

    function timelineSpanS() {
      return Math.max(1, workbench.timeline.end_s - workbench.timeline.start_s);
    }

    function inferenceProgressPct() {
      const span = timelineSpanS();
      return Math.round(clamp((inferenceState.currentTimeS - workbench.timeline.start_s) / span, 0, 1) * 1000) / 10;
    }

    function zeroMetrics() {
      return {
        total_orders: 0,
        delivered_orders: 0,
        assigned_orders: 0,
        late_orders: 0,
        coverage_rate: 0,
        avg_eta_min: 0,
        p95_eta_min: 0,
        total_time_cost_min: 0,
        total_distance_km: 0,
        total_cost_yuan: 0,
        timeout_risk: 0,
        courier_utilization: 0,
        gross_revenue_yuan: 0
      };
    }

    function preDispatchScore(simTimeS) {
      return {
        frame_id: "pre-dispatch",
        time_s: simTimeS,
        time_label: clock(simTimeS),
        baseline: zeroMetrics(),
        ours: zeroMetrics(),
        deltas: {
          time_saved_s: 0,
          time_saved_min: 0,
          money_saved_yuan: 0,
          timeout_order_delta: 0,
          timeout_risk_delta: 0,
          empty_mileage_saved_m: 0,
          empty_mileage_saved_km: 0,
          revenue_delta_yuan: 0,
          profit_delta_yuan: 0,
          extra_delivered_orders: 0,
          utilization_delta: 0,
          headline: "等待首轮规划评分，订单正在进入推理队列。"
        }
      };
    }

    function scoreForTime(simTimeS) {
      const series = workbench.metrics.series;
      if (!series.length) return workbench.metrics.final || preDispatchScore(simTimeS);
      if (simTimeS < series[0].time_s) return preDispatchScore(simTimeS);
      let selected = series[0] || workbench.metrics.final;
      for (const item of series) {
        if (item.time_s <= simTimeS) selected = item;
        else break;
      }
      return selected;
    }

    // 当前推演时刻所处的时间片（携带 compare_due / demand_phase / weather / 拥堵 / 运力）。
    function currentTimeSlice(simTimeS) {
      const slices = workbench.timeline.time_slices || [];
      if (!slices.length) return null;
      let selected = slices[0];
      for (const slice of slices) {
        if (slice.start_s <= simTimeS) selected = slice;
        else break;
      }
      return selected;
    }

    // 此刻正在生效的冲击事件（雨/爆单/拥堵/缺人）中文名。
    function activeShockNames(simTimeS) {
      return (workbench.map.hotspots || [])
        .filter((hotspot) => hotspot.start_s <= simTimeS && simTimeS <= hotspot.end_s)
        .map((hotspot) => displayShock(hotspot.type));
    }

    // 推演阶段：ready 待启动 / waiting 等首轮 / comparing 高峰对比中 / idle 平峰待机 / finished 收官。
    function phaseStatus(simTimeS) {
      if (!inferenceState.started) return "ready";
      if (simTimeS >= workbench.timeline.end_s) return "finished";
      const series = workbench.metrics.series || [];
      if (!series.length || simTimeS < series[0].time_s) return "waiting";
      const slice = currentTimeSlice(simTimeS);
      return slice && slice.compare_due ? "comparing" : "idle";
    }

    const phaseStatusMeta = {
      ready: { text: "待启动" },
      waiting: { text: "等待首轮对比" },
      comparing: { text: "高峰对比中" },
      idle: { text: "平峰待机 · 数字暂不增长" },
      finished: { text: "推演完成" }
    };

    // 一句场景旁白：说清此刻在演什么、为什么数字动或不动。
    function sceneNarration(simTimeS) {
      const status = phaseStatus(simTimeS);
      if (status === "ready") {
        return "点开始推理：贪心基线与我方算法将在同一天 207 单上各跑一遍，从 07:00 演到 23:00。";
      }
      if (status === "waiting") {
        return "清晨平峰，订单零星进入推理队列；首轮算法对比要到午高峰才触发，此前累计优势恒为 0，属正常。";
      }
      const slice = currentTimeSlice(simTimeS) || {};
      const phase = displayDemandPhase(slice.demand_phase);
      const weather = displayWeather(slice.weather);
      const shocks = activeShockNames(simTimeS);
      const supply = slice.courier_supply;
      if (status === "finished") {
        const final = workbench.metrics.final.deltas;
        return `全天收官：我方比贪心基线少 ${fmtNumber(final.time_saved_min, 1)} 分钟、省 ${fmtNumber(final.money_saved_yuan, 1)} 元，超时单${fmtFewer(final.timeout_order_delta, "单")}。`;
      }
      if (status === "idle") {
        return `${phase}平峰（${weather}、运力 ${supply} 人），系统判断无需算法对比，累计优势暂不增长——这是设计如此，不是卡住。`;
      }
      // comparing
      const shockText = shocks.length ? `，叠加${shocks.join("、")}冲击` : "";
      return `${phase}对比进行中：${weather}${shockText}，运力 ${supply} 人。每隔一轮重算派单，我方相对贪心的优势正在累计。`;
    }

    // 数据驱动的剧情节点（用于进度条标记）：首轮对比、贪心首次超时、各冲击、收官。
    function storylineMarkers() {
      const markers = [];
      const span = timelineSpanS();
      const start = workbench.timeline.start_s;
      const pctOf = (timeS) => clamp((timeS - start) / span, 0, 1) * 100;
      const series = workbench.metrics.series || [];
      if (series.length) {
        markers.push({ time_s: series[0].time_s, label: "首轮算法对比", tone: "start" });
        const firstLate = series.find((item) => (item.baseline && item.baseline.late_orders > 0) || (item.deltas && item.deltas.timeout_order_delta < 0));
        if (firstLate) markers.push({ time_s: firstLate.time_s, label: "贪心首次超时", tone: "crisis" });
      }
      for (const hotspot of workbench.map.hotspots || []) {
        markers.push({ time_s: hotspot.start_s, label: displayShock(hotspot.type) + "冲击", tone: "shock" });
      }
      markers.push({ time_s: workbench.timeline.end_s, label: "全天收官", tone: "finish" });
      const seen = new Set();
      return markers
        .filter((marker) => {
          const key = Math.round(marker.time_s / 60) + ":" + marker.label;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .sort((a, b) => a.time_s - b.time_s)
        .map((marker) => ({ ...marker, pct: pctOf(marker.time_s), label_time: clock(marker.time_s) }));
    }

    // 进度条上常驻的剧情节点小三角（带 hover 提示）。
    function renderStorylineTicks() {
      return `<span class="storyline-ticks" aria-hidden="true">${storylineMarkers().map((marker) =>
        `<i class="storyline-tick" data-tone="${escapeHtml(marker.tone)}" style="--at:${marker.pct}%" title="${escapeHtml(`${marker.label_time} ${marker.label}`)}"></i>`
      ).join("")}</span>`;
    }

    // 进度条下方的剧情节点图例：钟点 + 事件名，让观众一眼知道精彩段在哪。
    function renderStorylineLegend() {
      return storylineMarkers().map((marker) =>
        `<span class="storyline-chip" data-tone="${escapeHtml(marker.tone)}"><b>${escapeHtml(marker.label_time)}</b>${escapeHtml(marker.label)}</span>`
      ).join("");
    }

    function preDispatchDecision(simTimeS) {
      const queuedOrders = workbench.map.anchors.orders.filter((order) => order.created_at_s <= simTimeS).slice(-8).map((order) => order.id);
      const onlineRiders = workbench.entities.riders.slice(0, 6).map((rider) => rider.id);
      return {
        id: "D-pre-dispatch",
        frame_id: "pre-dispatch",
        trigger_time_s: simTimeS,
        trigger_time_label: clock(simTimeS),
        trigger_reason: "等待首轮规划决策触发。",
        input_order_ids: queuedOrders,
        input_orders: [],
        candidate_rider_ids: onlineRiders,
        candidate_riders: [],
        filtering_process: [
          { stage: "order_release", remaining: queuedOrders.length, summary: "订单逐步进入推理队列，尚未触发首轮评分。" },
          { stage: "rider_pool", remaining: onlineRiders.length, summary: "在线骑手资源已预载，等待规划窗口开启。" }
        ],
        scoring_process: [],
        final_actions: [],
        abandoned_actions: [],
        round_result: {
          summary: "首轮决策尚未生成；当前仅展示已进入队列的订单和资源上下文。",
          time_saved_min: 0,
          cost_saved_yuan: 0,
          timeout_risk_delta: 0,
          extra_delivered_orders: 0
        },
        result_writeback: {
          memory_event_ids: [],
          writeback_count: 0,
          summary: "首轮规划前暂无记忆回写。"
        },
        context: {
          time_slice_id: "pre-dispatch",
          demand_phase: "pre-dispatch",
          weather: "pending",
          congestion_level: 0,
          courier_supply: onlineRiders.length,
          shock_ids: []
        }
      };
    }

    function decisionForTime(simTimeS) {
      if (!workbench.decisions.length || simTimeS < workbench.decisions[0].trigger_time_s) {
        return preDispatchDecision(simTimeS);
      }
      let selected = workbench.decisions[0];
      for (const item of workbench.decisions) {
        if (item.trigger_time_s <= simTimeS) selected = item;
        else break;
      }
      return selected || workbench.decisions[0];
    }

    function releasedEvents(simTimeS) {
      return workbench.timeline.events.filter((event) => event.time_s <= simTimeS);
    }

    function frameForTime(simTimeS) {
      const frames = contract.frames || [];
      let selected = frames[0];
      if (frames.length && simTimeS < frames[0].sim_time_s) {
        return preDispatchFrame(simTimeS);
      }
      for (const frame of frames) {
        if (frame.sim_time_s <= simTimeS) selected = frame;
        else break;
      }
      return selected || { id: "", sim_time_s: workbench.timeline.start_s, highlighted_order_ids: [], challenger: { route_overlays: [], simulation_trace: { courier_tracks: [] }, courier_positions: [] }, baseline: { route_overlays: [], assignments: [] } };
    }

    function preDispatchFrame(simTimeS) {
      return {
        id: "pre-dispatch",
        sim_time_s: simTimeS,
        highlighted_order_ids: [],
        challenger: {
          active_order_ids: [],
          route_overlays: [],
          simulation_trace: { courier_tracks: [] },
          courier_positions: workbench.map.anchors.riders.slice(0, 18).map((rider) => ({
            courier_id: rider.id,
            label: rider.label,
            position: rider.position,
            status: "online"
          }))
        },
        baseline: { route_overlays: [], assignments: [] }
      };
    }

    const MAP_ROUTE_CAP = 8;
    function baselineRouteByOrderId(orderId) {
      return (workbench.map.routes || []).find((route) => route.lane === "baseline" && route.order_id === orderId) || null;
    }
    function liveDispatchedRoutes(simTimeS = inferenceState.currentTimeS) {
      const rows = [];
      for (const order of workbench.map.anchors.orders) {
        if (orderStatusAt(order.id, simTimeS) !== "dispatched") continue;
        const route = oursRouteByOrderId[order.id];
        if (route) rows.push(route);
      }
      // 同级按派单时间排序，保留最近 MAP_ROUTE_CAP 条正在执行的路线。
      rows.sort((a, b) => (orderLifecycle[a.order_id]?.assign_at_s || 0) - (orderLifecycle[b.order_id]?.assign_at_s || 0));
      return rows.slice(-MAP_ROUTE_CAP);
    }
    function mapRouteRows(frame) {
      const ours = liveDispatchedRoutes();
      if (inferenceState.mode === "current") {
        return ours.map((route) => ({...route, renderLane: "ours"}));
      }
      // 对比 / 叠加模式：为当前执行中的订单补充基线路线，并标出「派给不同骑手」的差异。
      const rows = [];
      for (const route of ours) {
        const baseline = baselineRouteByOrderId(route.order_id);
        const isDiff = baseline && baseline.courier_id && baseline.courier_id !== route.courier_id;
        rows.push({...route, renderLane: isDiff ? "difference" : "ours"});
        if (baseline && (inferenceState.mode === "compare" || isDiff)) {
          rows.push({...baseline, renderLane: "baseline"});
        }
      }
      return rows;
    }

    // 严格按时间真值挑选地图订单点：
    //   - 只显示 created_at_s <= 当前秒 的订单（绝不提前展示未来订单）；
    //   - 跨时段保留（早餐订单不会在 10:00 突然消失，而是按各自生命周期推进）；
    //   - 已完成订单淡出保留 ORDER_FADE_S 后移除，且移除有明确语义（已完成）；
    //   - 每个点带上 status（映射自生命周期：waiting->pending / dispatched->active / completed->settled），供着色和图例解释。
    const MAP_ORDER_CAP = 72;
    const ORDER_STATUS_FROM_LIFECYCLE = { waiting: "pending", dispatched: "active", completed: "settled" };
    const ORDER_STATE_RANK = { active: 0, pending: 1, settled: 2 };
    function ordersForMap(frame) {
      const t = inferenceState.currentTimeS;
      const visible = [];
      for (const order of workbench.map.anchors.orders) {
        const lifecycleStatus = orderStatusAt(order.id, t);
        if (lifecycleStatus === "unreleased" || lifecycleStatus === "unknown") continue;
        if (lifecycleStatus === "completed") {
          const life = orderLifecycle[order.id];
          if (life && t > life.complete_at_s + ORDER_FADE_S) continue; // 已完成并超过淡出窗口 -> 从地图移除
        }
        visible.push({ ...order, status: ORDER_STATUS_FROM_LIFECYCLE[lifecycleStatus] });
      }
      if (visible.length <= MAP_ORDER_CAP) {
        return visible.sort((a, b) => a.created_at_s - b.created_at_s);
      }
      // 超过上限时优先保留「执行中 > 待派单 > 已完成」，同级取最新，避免地图过载。
      const trimmed = visible
        .slice()
        .sort((a, b) => (ORDER_STATE_RANK[a.status] - ORDER_STATE_RANK[b.status]) || (b.created_at_s - a.created_at_s))
        .slice(0, MAP_ORDER_CAP);
      return trimmed.sort((a, b) => a.created_at_s - b.created_at_s);
    }

    function riderPositionsForFrame(frame) {
      const moving = deriveMovingRiders(inferenceState.currentTimeS);
      if (moving.length) return dedupeRiderPositions(moving);
      const snapshots = (frame.challenger.courier_positions || []).slice(0, 18).map((snapshot) => ({
        id: snapshot.courier_id,
        label: riderLabelForId(snapshot.courier_id),
        map_label: riderLabelForId(snapshot.courier_id),
        position: snapshot.position,
        motion: "snapshot",
        phase: snapshot.status || "available"
      }));
      return dedupeRiderPositions(snapshots);
    }

    // 同一骑手任一时刻只保留一个当前位置，杜绝地图上出现两个同名骑手（“分身”）。
    function dedupeRiderPositions(riders = []) {
      const seen = new Map();
      for (const rider of riders) {
        if (!seen.has(rider.id)) seen.set(rider.id, rider);
      }
      return Array.from(seen.values());
    }

    // 移动骑手完全由「当前正在执行的派单路线 + 订单生命周期进度」推导，
    // 与后端每 15 分钟一帧、且只覆盖单个时段的 courier_tracks 解耦，从而保证：
    //   1) 长配送（ETA 跨多个时段帧）全程都有骑手和执行进度，不会中途消失；
    //   2) 骑手在派单时刻从路线起点出发（progress=0），绝不“凭空出现在半路”；
    //   3) 骑手只承接「已派单·执行中」的订单，与订单点/路线/状态文案三处严格一致。
    function deriveMovingRiders(simTimeS) {
      const byCourier = new Map();
      for (const route of liveDispatchedRoutes(simTimeS)) {
        const life = orderLifecycle[route.order_id];
        if (!life || !life.dispatched) continue;
        const list = byCourier.get(route.courier_id) || [];
        list.push({ route, life });
        byCourier.set(route.courier_id, list);
      }
      const riders = [];
      for (const [courierId, items] of byCourier) {
        items.sort((a, b) => (a.life.assign_at_s || 0) - (b.life.assign_at_s || 0));
        const primary = items[0];
        const span = Math.max(1, primary.life.complete_at_s - primary.life.assign_at_s);
        const progress = clamp((simTimeS - primary.life.assign_at_s) / span, 0, 1);
        const position = pointAlongPolyline(primary.route.polyline, progress);
        if (!position) continue;
        const taskOrderIds = uniqueIds(items.map((item) => item.route.order_id));
        riders.push({
          id: courierId,
          label: riderLabelForId(courierId),
          map_label: riderLabelForId(courierId),
          order_id: primary.route.order_id,
          task_order_ids: taskOrderIds,
          task_order_count: taskOrderIds.length,
          position,
          motion: "moving",
          phase: "delivering",
          progress
        });
      }
      return riders;
    }

    // 按进度沿折线取点（后端折线为粗粒度 3 点路径，分段等分近似即可）。
    function pointAlongPolyline(polyline = [], progress = 0) {
      const points = (polyline || []).filter((point) => point && Number.isFinite(Number(point.screen_x)));
      if (!points.length) return null;
      if (points.length === 1) return points[0];
      const clamped = clamp(Number(progress) || 0, 0, 1);
      const segs = points.length - 1;
      const scaled = clamped * segs;
      const index = Math.min(segs - 1, Math.floor(scaled));
      const ratio = scaled - index;
      return interpolateMapPoint(points[index], points[index + 1], ratio);
    }

    function interpolateMapPoint(start, end, ratio) {
      const mix = (left, right) => Number(left) + (Number(right) - Number(left)) * ratio;
      return {
        lat: mix(start.lat, end.lat),
        lng: mix(start.lng, end.lng),
        screen_x: mix(start.screen_x, end.screen_x),
        screen_y: mix(start.screen_y, end.screen_y)
      };
    }

    function uniqueIds(ids = []) {
      return [...new Set(ids.filter(Boolean))];
    }

    function routeFromHash() {
      const value = (window.location.hash || "#/live").replace(/^#\\/?/, "");
      return routeOrder.includes(value) ? value : "live";
    }

    function pageHeader(routeId, eyebrow, description) {
      const copy = routeCopy[routeId];
      return `
        <div class="page-head" data-page-identity="${escapeHtml(routeId)}" data-page-module="${escapeHtml(copy.module)}">
          <div>
            <div class="eyebrow">${escapeHtml(eyebrow)}</div>
            <h2>${escapeHtml(copy.title)}</h2>
            <p>${escapeHtml(description || copy.subtitle)}</p>
            <div class="page-role-strip" data-page-role-strip="${escapeHtml(routeId)}">
              <span>${escapeHtml(copy.navRole)}</span>
              <span>${escapeHtml(copy.module)}</span>
              <span>${escapeHtml(copy.outcome)}</span>
            </div>
          </div>
        </div>
      `;
    }

    function hydrateLivePage() {
      bindLiveControls();
      renderLiveRuntimeState();
    }

    function bindLiveControls() {
      const startButton = document.getElementById("start-inference");
      const pauseButton = document.getElementById("pause-inference");
      const speedSelect = document.getElementById("playback-speed");
      const modeSelect = document.getElementById("inference-mode");
      const progressControl = document.getElementById("inference-progress-control");
      if (!startButton || !pauseButton || !speedSelect || !modeSelect) return;
      startButton.addEventListener("click", startInference);
      pauseButton.addEventListener("click", toggleInferencePause);
      speedSelect.value = String(inferenceState.speed);
      modeSelect.value = inferenceState.mode;
      speedSelect.addEventListener("change", () => setInferenceSpeed(Number(speedSelect.value)));
      modeSelect.addEventListener("change", () => setInferenceMode(modeSelect.value));
      if (progressControl) {
        progressControl.addEventListener("click", seekInferenceFromProgressEvent);
        progressControl.addEventListener("keydown", handleProgressKeyboardSeek);
      }
    }

    function startInference() {
      inferenceState.started = true;
      inferenceState.running = true;
      inferenceState.currentTimeS = workbench.timeline.start_s;
      inferenceState.lastTickAt = Date.now();
      scheduleInferenceTick();
      renderLiveRuntimeState();
    }

    function toggleInferencePause() {
      if (!inferenceState.started) {
        startInference();
        return;
      }
      inferenceState.running = !inferenceState.running;
      if (inferenceState.running) {
        inferenceState.lastTickAt = Date.now();
        scheduleInferenceTick();
      } else {
        clearInferenceTimer();
      }
      renderLiveRuntimeState();
    }

    function setInferenceSpeed(speed) {
      inferenceState.speed = [1, 2, 4].includes(speed) ? speed : 1;
      if (inferenceState.running) {
        inferenceState.lastTickAt = Date.now();
        scheduleInferenceTick();
      }
      renderLiveRuntimeState();
    }

    function setInferenceMode(mode) {
      inferenceState.mode = Object.prototype.hasOwnProperty.call(inferenceModeLabels, mode) ? mode : "current";
      renderLiveRuntimeState();
    }

    function seekInferenceFromProgressEvent(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      if (!rect.width) return;
      const ratio = clamp((event.clientX - rect.left) / rect.width, 0, 1);
      seekInferenceTime(workbench.timeline.start_s + ratio * timelineSpanS());
    }

    function handleProgressKeyboardSeek(event) {
      const stepS = event.shiftKey ? 1800 : 600;
      let nextTimeS = null;
      if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        nextTimeS = inferenceState.currentTimeS - stepS;
      } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        nextTimeS = inferenceState.currentTimeS + stepS;
      } else if (event.key === "Home") {
        nextTimeS = workbench.timeline.start_s;
      } else if (event.key === "End") {
        nextTimeS = workbench.timeline.end_s;
      }
      if (nextTimeS === null) return;
      event.preventDefault();
      seekInferenceTime(nextTimeS);
    }

    function seekInferenceTime(nextTimeS) {
      const snappedTimeS = Math.round(Number(nextTimeS || 0) / 60) * 60;
      inferenceState.started = true;
      inferenceState.running = false;
      inferenceState.lastTickAt = Date.now();
      clearInferenceTimer();
      setInferenceTime(snappedTimeS);
    }

    function clearInferenceTimer() {
      if (inferenceState.timerId !== null) {
        clearInterval(inferenceState.timerId);
        inferenceState.timerId = null;
      }
    }

    function stopLiveRuntime() {
      inferenceState.running = false;
      clearInferenceTimer();
    }

    function scheduleInferenceTick() {
      clearInferenceTimer();
      inferenceState.timerId = setInterval(advanceInferenceTick, inferenceState.tickMs);
    }

    function advanceInferenceTick() {
      if (!inferenceState.running) return;
      const now = Date.now();
      const elapsedMs = inferenceState.lastTickAt ? now - inferenceState.lastTickAt : inferenceState.tickMs;
      inferenceState.lastTickAt = now;
      const simulatedStepS = Math.max(60, elapsedMs / 1000 * 900 * inferenceState.speed);
      setInferenceTime(inferenceState.currentTimeS + simulatedStepS);
    }

    function setInferenceTime(nextTimeS) {
      inferenceState.currentTimeS = clamp(nextTimeS, workbench.timeline.start_s, workbench.timeline.end_s);
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        inferenceState.running = false;
        clearInferenceTimer();
      }
      renderLiveRuntimeState();
    }

    function renderLiveRuntimeState() {
      const liveGrid = document.querySelector("[data-page='live']");
      if (!liveGrid) return;
      const inferenceFinished = inferenceState.started && inferenceState.currentTimeS >= workbench.timeline.end_s;
      const stateLabel = inferenceState.running ? "自动推理中" : inferenceFinished ? "推演完成" : inferenceState.started ? "已暂停" : "未开始";
      const events = releasedEvents(inferenceState.currentTimeS);
      const currentScore = scoreForTime(inferenceState.currentTimeS);
      const currentDecision = decisionForTime(inferenceState.currentTimeS);
      liveGrid.dataset.inferenceState = inferenceState.running ? "running" : inferenceState.started ? "paused" : "ready";
      setText("inference-state-label", stateLabel);
      setText("inference-clock", clock(inferenceState.currentTimeS));
      setText("inference-speed-label", `${inferenceState.speed}x`);
      setText("inference-mode-label", inferenceModeLabels[inferenceState.mode]);
      setText("inference-event-count", events.length);
      setText("live-advantage-headline", liveAdvantageHeadline(currentScore));
      setText("live-advantage-copy", liveAdvantageCopy(currentScore));
      const phaseBadge = document.getElementById("phase-status-badge");
      if (phaseBadge) {
        const status = phaseStatus(inferenceState.currentTimeS);
        phaseBadge.dataset.phase = status;
        phaseBadge.textContent = phaseStatusMeta[status].text;
      }
      const targetRow = document.getElementById("advantage-target-row");
      if (targetRow) targetRow.innerHTML = renderAdvantageTargetRow(currentScore);
      setText("map-runtime-hint", `${stateLabel} / ${clock(inferenceState.currentTimeS)} / ${inferenceModeLabels[inferenceState.mode]}`);
      setText("event-flow-caption", `${events.length} 个事件已自动释放`);
      setText("cumulative-metrics-caption", `${currentScore.time_label} 累计优势`);
      setText("round-summary-time", currentDecision.trigger_time_label);
      const progressPct = inferenceProgressPct();
      const progressControl = document.getElementById("inference-progress-control");
      if (progressControl) {
        progressControl.setAttribute("aria-valuenow", String(progressPct));
        progressControl.setAttribute("aria-valuetext", `${clock(inferenceState.currentTimeS)} / ${fmtNumber(progressPct, 1)}%`);
        progressControl.title = `点击跳转到对应推演时间；当前 ${clock(inferenceState.currentTimeS)}，${fmtNumber(progressPct, 1)}%`;
      }
      const progressBar = document.getElementById("inference-progress-bar");
      if (progressBar) progressBar.style.setProperty("--progress", `${progressPct}%`);
      const mapStage = document.getElementById("live-map-stage");
      if (mapStage) {
        const frame = frameForTime(inferenceState.currentTimeS);
        const routes = mapRouteRows(frame);
        const riders = riderPositionsForFrame(frame);
        const orders = ordersForMap(frame);
        mapStage.dataset.mapMode = inferenceState.mode;
        mapStage.dataset.frameId = frame.id;
        const actionStatus = mapStage.querySelector("#map-action-status");
        if (actionStatus) actionStatus.innerHTML = renderMapActionStatus(frame, routes, riders, orders);
        if (!updateLiveLeafletOverlay(frame, routes, riders, orders)) {
          destroyLiveMap();
          mapStage.innerHTML = renderLiveMapLayer(frame, routes, riders, orders);
          queueLiveMapHydration(frame, routes, riders, orders);
        }
      }
      const startButton = document.getElementById("start-inference");
      if (startButton) {
        startButton.disabled = inferenceState.started && inferenceState.running;
        startButton.textContent = inferenceState.started ? "重新开始" : "开始推理";
      }
      const pauseButton = document.getElementById("pause-inference");
      if (pauseButton) {
        pauseButton.textContent = inferenceState.running ? "暂停" : inferenceFinished ? "已完成" : "继续";
        pauseButton.disabled = inferenceFinished && !inferenceState.running;
      }
      const scoreStack = document.getElementById("live-score-stack");
      if (scoreStack) scoreStack.innerHTML = renderLiveScoreCards(currentScore);
      const eventFlow = document.getElementById("live-event-flow");
      if (eventFlow) eventFlow.innerHTML = events.slice(-4).reverse().map(renderEventItem).join("") || `<div class="list-item"><strong>等待开始</strong><p>点击开始推理后，订单进入、候选分配和累计结果将自动释放。</p></div>`;
      const cumulativeMetrics = document.getElementById("live-cumulative-metrics");
      if (cumulativeMetrics) cumulativeMetrics.innerHTML = renderLiveCumulativeMetrics(currentScore);
      const summary = document.getElementById("live-round-summary");
      if (summary) summary.innerHTML = renderRoundSummary(currentDecision, true);
      const dispatchList = document.getElementById("live-dispatch-list");
      if (dispatchList) dispatchList.innerHTML = renderLiveDispatchList();
    }

    function setText(id, value) {
      const node = document.getElementById(id);
      if (node) node.textContent = String(value);
    }

    function renderTopbarStats() {
      const stats = workbench.inspection;
      document.getElementById("topbar-stats").innerHTML = [
        ["订单", stats.order_count],
        ["骑手", stats.rider_count],
        ["决策轮次", stats.decision_count],
        ["优势验证", "开始后累计"]
      ].map(([label, value]) => `
        <div class="stat-pill"><b>${escapeHtml(value)}</b><span>${escapeHtml(label)}</span></div>
      `).join("");
    }

    // 大字只承载一个核心数字（累计省时），其余信息交给徽章/旁白/卡片，避免重复。
    function liveAdvantageHeadline(score) {
      const delta = score.deltas || {};
      const timeSaved = Number(delta.time_saved_min || 0);
      if (!inferenceState.started) {
        return "贪心基线 vs 我方算法 · 全天对决";
      }
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        return `全天为站点省下 ${fmtNumber(timeSaved, 1)} 分钟`;
      }
      if (timeSaved <= 0) {
        return "等待午高峰首轮对比";
      }
      return `已累计省下 ${fmtNumber(timeSaved, 1)} 分钟`;
    }

    // 副文案专职「场景旁白」：解释此刻在演什么、数字为何动或不动，不再重复数字。
    function liveAdvantageCopy(score) {
      return sceneNarration(inferenceState.currentTimeS);
    }

    // target-row 专职「场景事实」：阶段 / 天气 / 运力 / 冲击，提供数字之外的上下文。
    function renderAdvantageTargetRow(score) {
      if (!inferenceState.started) {
        const shockCount = (workbench.map.hotspots || []).length;
        return `
          <span>207 单 · 18 骑手</span>
          <span>07:00 → 23:00</span>
          <span>重点看 ${shockCount} 个压力时刻</span>
        `;
      }
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        const finalOurs = workbench.metrics.final.ours || {};
        const finalBase = workbench.metrics.final.baseline || {};
        return `
          <span>双方均送达 ${finalOurs.delivered_orders || finalBase.delivered_orders || 0} 单</span>
          <span>我方全天 ${finalOurs.late_orders || 0} 超时</span>
          <span>进度 100%</span>
        `;
      }
      const slice = currentTimeSlice(inferenceState.currentTimeS) || {};
      const shocks = activeShockNames(inferenceState.currentTimeS);
      const facts = [
        `阶段 ${displayDemandPhase(slice.demand_phase)}`,
        `天气 ${displayWeather(slice.weather)}`,
        `运力 ${slice.courier_supply === undefined ? "-" : slice.courier_supply} 人`
      ];
      if (shocks.length) facts.push(`冲击 ${shocks.join("·")}`);
      return facts.map((fact) => `<span>${escapeHtml(fact)}</span>`).join("");
    }

    function renderNav() {
      document.getElementById("route-nav").innerHTML = workbench.routes.map((route) => {
        const copy = routeCopy[route.id];
        const roleBadge = copy.navRole && copy.navRole !== copy.navLabel ? `<em class="nav-role">${escapeHtml(copy.navRole)}</em>` : "";
        return `
          <a class="nav-link" href="${escapeHtml(route.path)}" data-route-link="${escapeHtml(route.id)}" data-route-role="${escapeHtml(copy.navRole)}" data-kandbox-module="${escapeHtml(copy.module)}" aria-label="${escapeHtml(`${copy.navLabel}：${copy.navHint}`)}">
            <span class="nav-icon">${escapeHtml(copy.icon)}</span>
            <div class="nav-copy">
              <span class="nav-title-line"><strong>${escapeHtml(copy.navLabel || route.label)}</strong>${roleBadge}</span>
              <span class="nav-hint">${escapeHtml(copy.navHint)}</span>
              <span class="nav-module">${escapeHtml(copy.module || route.kandbox_module)}</span>
            </div>
          </a>
        `;
      }).join("");
    }

    function setRoute(routeId) {
      const safeRoute = routeOrder.includes(routeId) ? routeId : "live";
      if (window.location.hash !== `#/${safeRoute}`) {
        history.replaceState(null, "", `#/${safeRoute}`);
      }
      document.body.dataset.route = safeRoute;
      document.getElementById("route-title").textContent = routeCopy[safeRoute].title;
      document.getElementById("route-subtitle").textContent = routeCopy[safeRoute].subtitle;
      for (const link of document.querySelectorAll("[data-route-link]")) {
        link.setAttribute("aria-current", link.dataset.routeLink === safeRoute ? "page" : "false");
      }
      renderRoute(safeRoute);
    }

    function renderRoute(routeId) {
      const view = document.getElementById("route-view");
      if (routeId !== "live") stopLiveRuntime();
      if (routeId !== "memory") teardownMemoryPage();
      destroyLiveMap();
      view.dataset.routeView = routeId;
      const renderers = {
        live: renderLivePage,
        decisions: renderDecisionsPage,
        memory: renderMemoryPage,
        orders: renderOrdersPage,
        riders: renderRidersPage
      };
      view.innerHTML = renderers[routeId]();
      if (routeId === "live") {
        hydrateLivePage();
      } else if (routeId === "decisions") {
        hydrateDecisionPage();
      } else if (routeId === "memory") {
        hydrateMemoryPage();
      } else if (routeId === "orders") {
        hydrateOrdersPage();
      } else if (routeId === "riders") {
        hydrateRidersPage();
      }
    }

    function renderLivePage() {
      const currentScore = scoreForTime(inferenceState.currentTimeS);
      const events = releasedEvents(inferenceState.currentTimeS).slice(-4).reverse();
      const currentDecision = decisionForTime(inferenceState.currentTimeS);
      const currentFrame = frameForTime(inferenceState.currentTimeS);
      return `
        ${pageHeader("live", "实时推演总览", "首屏先回答算法是否更强：实时地图承接推理动作，右侧只保留当前决策和运行信号。")}
        <div class="page-grid live-grid" data-page="live" data-inference-state="${inferenceState.running ? "running" : inferenceState.started ? "paused" : "ready"}">
          <section id="live-advantage-hero" class="live-advantage-hero" data-live-priority="advantage-first">
            <div class="advantage-lead">
              <span class="advantage-kicker-row">
                <span class="advantage-kicker">实时累计对比栏</span>
                <span id="phase-status-badge" class="phase-status-badge" data-phase="${escapeHtml(phaseStatus(inferenceState.currentTimeS))}">${escapeHtml(phaseStatusMeta[phaseStatus(inferenceState.currentTimeS)].text)}</span>
              </span>
              <h3 id="live-advantage-headline">${escapeHtml(liveAdvantageHeadline(currentScore))}</h3>
              <p id="live-advantage-copy">${escapeHtml(liveAdvantageCopy(currentScore))}</p>
              <div id="advantage-target-row" class="advantage-target-row" aria-label="全天最终优势目标">
                ${renderAdvantageTargetRow(currentScore)}
              </div>
            </div>
            <div id="live-score-stack" class="live-advantage-metrics" data-score-role="dominant-advantage">
              ${renderLiveScoreCards(currentScore)}
            </div>
          </section>
          <div class="live-ops-shell">
            <div class="live-primary-column">
              <div class="control-dock live-control-dock" data-control-strip="live">
              <button id="start-inference" class="primary-button" data-control="start-inference">开始推理</button>
              <button id="pause-inference" class="ghost-button" data-control="pause-resume">暂停/继续</button>
              <select id="playback-speed" class="select-control" data-control="speed"><option value="1">1x</option><option value="2">2x</option><option value="4">4x</option></select>
              <select id="inference-mode" class="select-control" data-control="mode"><option value="current">当前算法</option><option value="compare">对比</option><option value="overlay">叠加</option></select>
              <div class="runtime-strip" data-inference-runtime="status">
                <div class="runtime-cell"><span>状态</span><b id="inference-state-label">未开始</b></div>
                <div class="runtime-cell"><span>推演时间</span><b id="inference-clock">${escapeHtml(clock(inferenceState.currentTimeS))}</b></div>
                <div class="runtime-cell"><span>倍速</span><b id="inference-speed-label">${inferenceState.speed}x</b></div>
                <div class="runtime-cell"><span>模式</span><b id="inference-mode-label">${escapeHtml(inferenceModeLabels[inferenceState.mode])}</b></div>
                <div class="runtime-cell"><span>释放事件</span><b id="inference-event-count">${releasedEvents(inferenceState.currentTimeS).length}</b></div>
              </div>
              <div id="inference-progress-control" class="inference-progress" role="slider" tabindex="0" aria-label="点击跳转到对应推演时间" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${inferenceProgressPct()}" aria-valuetext="${escapeHtml(`${clock(inferenceState.currentTimeS)} / ${fmtNumber(inferenceProgressPct(), 1)}%`)}" title="点击进度条跳转到对应推演时间"><span id="inference-progress-bar" style="--progress:${inferenceProgressPct()}%"></span>${renderStorylineTicks()}</div>
              <div class="storyline-legend" aria-label="全天剧情节点">${renderStorylineLegend()}</div>
              </div>
              <div class="card map-panel">
              <div class="card-head"><h3>实时地图层</h3><span id="map-runtime-hint">商家 / 订单 / 骑手 / 路线 / 热点</span></div>
              <div id="live-map-stage" class="real-map-stage schematic-map" data-map-layer="primary" data-real-map-provider="leaflet" data-tile-layer="cartodb-light-nolabels" data-real-map-status="loading" data-map-mode="${escapeHtml(inferenceState.mode)}" data-frame-id="${escapeHtml(currentFrame.id)}">
                ${renderLiveMapLayer(currentFrame)}
              </div>
              </div>
            </div>
            <aside class="live-side-rail">
              <div class="card">
                <div class="card-head"><h3>当前决策摘要</h3><span id="round-summary-time">${escapeHtml(currentDecision.trigger_time_label)}</span></div>
                <div id="live-round-summary" class="card-body compact-list">
                  ${renderRoundSummary(currentDecision, true)}
                </div>
              </div>
              <div class="card">
                <div class="card-head"><h3>地图执行中订单</h3><span id="dispatch-list-caption">与地图一一对应</span></div>
                <div id="live-dispatch-list" class="card-body compact-list">
                  ${renderLiveDispatchList()}
                </div>
              </div>
              <div class="card live-run-panel">
                <div class="card-head"><h3>运行信号</h3><span><em id="cumulative-metrics-caption">${escapeHtml(currentScore.time_label)} 累计优势</em> / <em id="event-flow-caption">按全天推演时间释放</em></span></div>
                <div class="card-body">
                  <div id="live-cumulative-metrics" class="metric-strip" aria-label="compact cumulative advantage">
                    ${renderLiveCumulativeMetrics(currentScore)}
                  </div>
                  <div id="live-event-flow" class="event-list">${events.map(renderEventItem).join("") || `<div class="list-item"><strong>等待开始</strong><p>点击开始推理后，订单进入、候选分配和累计结果将自动释放。</p></div>`}</div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      `;
    }

    function renderDecisionsPage() {
      const decision = selectedDecision();
      return `
        ${pageHeader("decisions", "算法推理过程", "按时间回放每一轮派单推理：先看为什么触发，再看订单、骑手、过滤、评分、采纳和放弃原因。")}
        <div class="page-grid decision-grid" data-page="decisions" data-decision-route="reasoning">
          <div class="card">
            <div class="card-head"><h3>决策轮次时间线</h3><span id="decision-route-status">${workbench.decisions.length} 轮决策</span></div>
            <div id="decision-timeline" class="card-body timeline-list decision-scroll">
              ${renderDecisionTimeline(decision.id)}
            </div>
          </div>
          <div class="card">
            <div class="card-head"><h3>本轮推理说明</h3><span id="decision-reasoning-phase">${escapeHtml(displayDemandPhase(decision.context.demand_phase))}</span></div>
            <div id="decision-reasoning-canvas" class="card-body decision-canvas">
              ${renderDecisionReasoning(decision)}
            </div>
          </div>
          <aside class="card">
            <div class="card-head"><h3>本轮输入与输出</h3><span id="decision-context-slice">${escapeHtml(displayDemandPhase(decision.context.demand_phase))}场景</span></div>
            <div id="decision-context-pane" class="card-body compact-list">
              ${renderDecisionContext(decision)}
            </div>
          </aside>
        </div>
      `;
    }

    function renderMemoryPage() {
      const evidence = memoryEvidence();
      return `
        ${pageHeader("memory", "长期记忆中心", "调度经验按 Read / Write / Reflection 循环沉淀与复用：看学习曲线、场景复遇增益和召回链路，验证记忆确实让派单更强。")}
        <div class="page-grid memory-workspace hermes-memory-workspace" data-page="memory" data-memory-route="hermes-long-term" data-memory-model="episodic-semantic-policy-loop">
          <section id="memory-command-center" class="memory-command-center" aria-label="长期记忆自主学习证据">
            <div class="memory-command-copy">
              <span class="memory-kicker">长期记忆 · 自主学习</span>
              <h3>看见系统越跑越聪明</h3>
              <p>每轮派单结束后，结果经 Reflexion 反思回写进经验库（Write）；再次遇到相似场景时，先做元数据过滤、再按相似度召回历史经验注入决策（Read）——签名不同但足够相似的新场景，也能迁移复用旧经验；跨轮经验被提炼成画像与全局策略（Reflection）。下面全部数据来自同一天基线与我方的双跑对比，逐轮可复现。</p>
              <div class="memory-term-row">
                <span>Read / Write / Reflection</span>
                <span>Reflexion 反思回写</span>
                <span>检索增强决策</span>
                <span>记忆注入时机</span>
              </div>
            </div>
            <div id="memory-evidence-grid" class="memory-evidence-grid">
              ${renderMemoryEvidenceTiles(evidence)}
            </div>
          </section>
          <section class="card memory-curve-card" id="memory-curve-card">
            <div class="card-head">
              <h3>全天学习曲线</h3>
              <span>记忆沉淀 → 复遇召回 → 收益放大；下方细带为记忆置信度；点击圆点定位数据表，再点一次取消</span>
              <div class="memory-curve-head-controls">
                <span id="memory-replay-clock" class="memory-replay-clock"></span>
                <button type="button" id="memory-replay-btn" class="memory-replay-btn" data-state="idle">▶ 回放全天学习过程</button>
              </div>
            </div>
            <div class="card-body">
              <div id="memory-curve" class="memory-curve-stage" aria-label="全天累计节省与记忆置信度学习曲线">
                <div id="memory-curve-tooltip" class="memory-curve-tooltip" data-open="0"></div>
              </div>
              <div class="memory-curve-legend">
                <span class="lg"><i data-kind="line-saved"></i>累计节省（分钟）</span>
                <span class="lg"><i data-kind="line-conf"></i>记忆置信度（回写后）</span>
                <span class="lg"><i data-kind="novel"></i>新经验沉淀 · 冷启动 / 低相似借鉴</span>
                <span class="lg"><i data-kind="transfer"></i>高相似迁移 · 旧经验当主力直接搬用</span>
                <span class="lg"><i data-kind="reuse"></i>同景复遇 · 记忆完全命中</span>
                <span class="lg"><i data-kind="shock"></i>冲击时段</span>
              </div>
              <p class="memory-method-note">方法说明：场景按签名「时段 | 天气 | 拥堵 | 运力 | 冲击」归类，记忆相关性是<b>连续相似度</b>而非有无二值（与 Mem0 / Generative Agents 等主流记忆框架的检索思想一致）。签名完全命中记为“同景复遇”；签名首现时与已有场景算加权相似度（权重与召回打分同源：时段 0.18 / 天气 0.14 / 拥堵 0.14 / 运力 0.18 / 冲击 0.14，同景加成 0.22）：相似度 ≥ 0.5 记“高相似迁移”（旧经验当主力直接搬用）、0 到 0.5 之间记“低相似借鉴”（旧经验只当辅助，主要靠本轮新沉淀）、当天无任何历史记“冷启动”。“可借鉴经验”= 强相关（相似度 ≥ 0.5，同景 + 相似）轮数，低相似借鉴轮额外标注弱相关轮数；召回时先在经验池粗筛、再按相似度精选 Top-K 注入。节省分钟数来自基线（最近距离贪心）与我方在同一天、同一订单流上的逐轮对比。</p>
              <details class="memory-round-table-wrap">
                <summary>查看全部 ${memoryLearningRounds().length} 轮决策数据表（点击行/圆点互相定位并高亮，再点同一处取消）</summary>
                <div class="table-scroll">${renderMemoryRoundTable()}</div>
              </details>
            </div>
          </section>
          <section class="card memory-matrix-card" id="memory-matrix-card">
            <div class="card-head">
              <h3>场景经验库 · 沉淀与复用</h3>
              <span>每行一类场景：空心橙点=冷启动/低相似借鉴开局，空心蓝点=高相似迁移开局（旧经验直接搬用），实心点=同景复遇（点越大该轮节省越多）；点击行查看召回链路，再点取消选择</span>
            </div>
            <div class="card-body">
              <div id="memory-matrix" class="memory-matrix-rows">
                ${renderMemoryMatrixRows()}
              </div>
              <div class="memory-matrix-axis">
                <span></span>
                <div class="axis-track">${renderMemoryMatrixAxis()}</div>
                <span></span>
              </div>
            </div>
          </section>
          <div class="memory-flow-grid2">
            <section class="card" id="memory-pipeline-card">
              <div class="card-head">
                <h3>单轮召回链路 · 检索增强决策</h3>
                <span id="memory-pipeline-caption"></span>
                <div class="memory-curve-head-controls">
                  <button type="button" id="memory-pipeline-replay" class="memory-replay-btn" data-state="idle">↻ 重放召回</button>
                </div>
              </div>
              <div class="card-body">
                <p class="memory-lead-note">打开一轮决策看内部：①当前场景编码成查询 → ②按相似度召回历史经验（点击案例芯片可定位它来自哪类场景经验）→ ③经验注入后决策 → ④结果回写强化置信度。点击上方场景行可切换轮次。</p>
                <div id="memory-pipeline" class="memory-pipeline"></div>
              </div>
            </section>
            <section class="card" id="memory-hierarchy-card">
              <div class="card-head"><h3>记忆分层 · Reflection 提炼</h3><span>情景 → 语义 → 策略</span></div>
              <div class="card-body">
                ${renderMemoryHierarchy()}
              </div>
            </section>
          </div>
        </div>
      `;
    }

    function renderOrdersPage() {
      const orders = filteredOrders();
      return `
        ${pageHeader("orders", "订单池看板", "全天订单已经预置并按时间进入推理，这里只看需求压力、风险结构和算法结果。")}
        <div class="page-grid demand-workspace" data-page="orders" data-orders-route="preloaded-demand-pool">
          <section id="orders-command" class="demand-command-center" data-orders-surface="preloaded-order-pool">
            <div class="demand-command-copy">
              <span class="demand-kicker">只读订单池</span>
              <h3>今天订单怎么来</h3>
              <p>不录入、不编辑。调度员只按时间段、商圈、状态和风险筛选，先判断哪批订单会影响超时、成本和骑手负载。</p>
            </div>
            <div id="orders-overview" class="demand-signal-grid">
              ${renderOrdersOverview(orders)}
            </div>
          </section>
          <div id="orders-filter-bar" class="filter-bar" data-filter-bar="orders">
            <select id="orders-filter-time" class="select-control" data-order-filter="timeBand">
              <option value="all">全部时间段</option>
              ${workbench.filters.order_time_bands.map((item) => `<option value="${escapeHtml(item.id)}"${item.id === orderFilterState.timeBand ? " selected" : ""}>${escapeHtml(displayDemandPhase(item.id))} / ${escapeHtml(item.time_label)}</option>`).join("")}
            </select>
            <select id="orders-filter-area" class="select-control" data-order-filter="area">
              <option value="all">全部商圈</option>
              ${workbench.filters.areas.map((item) => `<option value="${escapeHtml(item)}"${item === orderFilterState.area ? " selected" : ""}>${escapeHtml(item)}</option>`).join("")}
            </select>
            <select id="orders-filter-status" class="select-control" data-order-filter="status">
              <option value="all">全部状态</option>
              ${workbench.filters.statuses.map((item) => `<option value="${escapeHtml(item)}"${item === orderFilterState.status ? " selected" : ""}>${escapeHtml(displayStatus(item))}</option>`).join("")}
            </select>
            <select id="orders-filter-risk" class="select-control" data-order-filter="risk">
              <option value="all">全部风险</option>
              ${workbench.filters.risk_levels.map((item) => `<option value="${escapeHtml(item)}"${item === orderFilterState.risk ? " selected" : ""}>${escapeHtml(displayRisk(item))}</option>`).join("")}
            </select>
            <span id="orders-result-count" class="filter-count">${orders.length} / ${workbench.entities.orders.length} 单</span>
          </div>
          <div class="operations-grid" data-density="summary-first">
            <div class="card" id="orders-priority-panel" data-orders-surface="priority-demand">
              <div class="card-head"><h3>优先关注订单</h3><span>先看可能影响超时和收益的订单</span></div>
              <div id="orders-priority-list" class="card-body order-focus-list">
                ${renderOrderFocusList(orders)}
              </div>
            </div>
            <aside class="card" id="orders-context-panel">
              ${renderOrdersContext(orders)}
            </aside>
          </div>
          <div class="table-shell orders-table-shell" data-order-universe="full-day" data-evidence-role="secondary">
              <div class="card-head"><h3>订单全集核对</h3><span>只读证据，不做录入维护</span></div>
              <table>
                <thead><tr><th>订单</th><th>商家/商圈</th><th>时间窗口</th><th>状态/风险</th><th>推理状态</th><th>基线结果</th><th>我方结果</th></tr></thead>
                <tbody id="orders-table-body">${orders.map(renderOrderRow).join("")}</tbody>
              </table>
          </div>
        </div>
      `;
    }

    function renderRidersPage() {
      const riders = filteredRiders();
      return `
        ${pageHeader("riders", "骑手运力看板", "全天骑手班次已经预置，这里只看当前可用性、区域覆盖、负载和预计空闲。")}
        <div class="page-grid capacity-workspace" data-page="riders" data-riders-route="capacity-board">
          <section id="riders-command" class="capacity-command-center" data-riders-surface="capacity-board">
            <div class="capacity-command-copy">
              <span class="capacity-kicker">只读运力池</span>
              <h3>现在运力够不够</h3>
              <p>不是人事后台。调度员先看哪些区域有可接单骑手、哪些骑手负载偏高、哪些班次快结束，再进入候选骑手判断。</p>
            </div>
            <div id="riders-overview" class="capacity-signal-grid">
              ${renderRidersOverview(riders)}
            </div>
          </section>
          <div id="riders-filter-bar" class="filter-bar" data-filter-bar="riders">
            <select id="riders-filter-area" class="select-control" data-rider-filter="area">
              <option value="all">全部区域</option>
              ${workbench.filters.areas.map((item) => `<option value="${escapeHtml(item)}"${item === riderFilterState.area ? " selected" : ""}>${escapeHtml(item)}</option>`).join("")}
            </select>
            <select id="riders-filter-state" class="select-control" data-rider-filter="state">
              <option value="all">全部在线状态</option>
              ${workbench.filters.rider_states.map((item) => `<option value="${escapeHtml(item)}"${item === riderFilterState.state ? " selected" : ""}>${escapeHtml(displayRiderState(item))}</option>`).join("")}
            </select>
            <span id="riders-result-count" class="filter-count">${riders.length} / ${workbench.entities.riders.length} 名骑手</span>
          </div>
          <div class="operations-grid" data-density="summary-first">
            <div class="card" id="riders-capacity-panel" data-riders-surface="capacity-focus">
              <div class="card-head"><h3>优先可用骑手</h3><span>先看状态、负载和预计空闲</span></div>
              <div id="riders-capacity-list" class="card-body rider-focus-list">
                ${renderRiderFocusList(riders)}
              </div>
            </div>
            <aside class="card" id="rider-context-panel">
              ${renderRidersContext(riders)}
            </aside>
          </div>
          <section class="card rider-evidence-shell" id="rider-evidence-panel" data-evidence-role="secondary">
            <div class="card-head"><h3>骑手小地图核对</h3><span>位置、负载和任务链，仅作二级证据</span></div>
            <div id="rider-resource-board" class="rider-board">
              ${riders.slice(0, 8).map(renderRiderCard).join("")}
            </div>
          </section>
        </div>
      `;
    }

    function renderLiveMapLayer(frame, routes = mapRouteRows(frame), riders = riderPositionsForFrame(frame), orders = ordersForMap(frame)) {
      const focusOrderIds = focusedMapOrderIds(routes, riders);
      return `
        <div id="map-action-status" class="map-action-status" data-map-action="active">${renderMapActionStatus(frame, routes, riders, orders)}</div>
        <div class="map-mode-chip">${escapeHtml(inferenceModeLabels[inferenceState.mode])} / ${escapeHtml(frame.id)}</div>
        <div id="leaflet-live-map" class="leaflet-live-map" data-leaflet-map="live" data-tile-provider="${escapeHtml(workbench.map.tile_provider || liveTileLayer.id)}" aria-label="匿名无标签真实地图"></div>
        <div class="fallback-map-overlay" data-fallback-map="screen-coordinate" aria-hidden="true">
          ${renderMapRoutes(routes, riders)}
          ${renderHotspots()}
          ${renderMapDots("merchant", workbench.map.anchors.merchants.slice(0, 16), "position")}
          ${renderMapDots("rider", riders.slice(0, 14), "position")}
          ${renderMapDots("order", orders.slice(0, 40), "dropoff", focusOrderIds)}
        </div>
        ${renderMapLegend()}
      `;
    }

    function renderMapRoutes(routes, riders = []) {
      if (!routes.length) return "";
      const progressLines = activeProgressRoutes(routes, riders);
      return `
        <svg class="map-route" data-route-count="${routes.length}" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          ${routes.map((route) => {
            const points = route.polyline.map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="${escapeHtml(route.renderLane || route.lane)}" data-order-ref="${escapeHtml(actionDisplayLabel("order", route))}" data-rider-ref="${escapeHtml(actionDisplayLabel("rider", route))}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
          ${progressLines.map((route) => {
            const points = route.progressPolyline.map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="active-progress" data-order-ref="${escapeHtml(actionDisplayLabel("order", route))}" data-rider-ref="${escapeHtml(actionDisplayLabel("rider", route))}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
        </svg>
      `;
    }

    function activeMapRider(riders = []) {
      return riders.find((rider) => rider.motion === "moving") || null;
    }

    function activeProgressRoutes(routes = [], riders = []) {
      const movingByPair = new Map(riders.filter((rider) => rider.motion === "moving").map((rider) => [`${rider.id}:${rider.order_id}`, rider]));
      return routes
        .filter((route) => !["baseline", "previous"].includes(route.renderLane || route.lane))
        .map((route) => {
          const rider = movingByPair.get(`${route.courier_id}:${route.order_id}`);
          if (!rider) return null;
          const progressPolyline = progressPolylineForRoute(route, rider);
          return progressPolyline.length >= 2 ? {...route, progressPolyline} : null;
        })
        .filter(Boolean)
        .slice(0, 4);
    }

    function progressPolylineForRoute(route, rider) {
      const points = route.polyline || [];
      if (points.length < 2) return [];
      const progress = clamp(Number(rider.progress || 0), 0, 1);
      const keep = Math.max(1, Math.ceil((points.length - 1) * progress));
      const polyline = points.slice(0, keep + 1);
      if (rider.position) polyline.push(rider.position);
      return polyline;
    }

    function orderStateCounts(orders = []) {
      const counts = { pending: 0, active: 0, settled: 0 };
      for (const order of orders) {
        const state = order.status || "pending";
        if (state in counts) counts[state] += 1;
      }
      return counts;
    }

    function orderStateSummaryText(orders = []) {
      const counts = orderStateCounts(orders);
      return `待派单 ${counts.pending} · 执行中 ${counts.active} · 已完成 ${counts.settled}`;
    }

    // 状态转移解释：说明「上一状态 -> 当前状态」是什么触发的，避免画面突变没有原因。
    function latestTransitionReason(simTimeS = inferenceState.currentTimeS) {
      const events = releasedEvents(simTimeS);
      const last = events.length ? events[events.length - 1] : null;
      if (!last) return "时间线尚未释放事件。";
      const gap = Math.max(0, simTimeS - Number(last.time_s || simTimeS));
      const when = `${clock(Number(last.time_s || simTimeS))}`;
      const typeText = {
        order_entered: "新订单释放进入订单池",
        decision_round: "规划轮触发，重新比较基线与我方并派单",
        score_update: "累计优势指标刷新",
        memory_writeback: "记忆回写：本轮结果沉淀到记忆库",
        memory_recall: "记忆召回：调用历史经验辅助决策",
        future_policy_shift: "策略切换：进入新的供需时段"
      }[last.type] || "推演状态更新";
      const within = gap <= 90 ? "（刚刚）" : "";
      return `${when} ${typeText}${within}。`;
    }

    function renderMapActionStatus(frame, routes = [], riders = [], orders = []) {
      if (!inferenceState.started) {
        return `<strong>等待开始推理</strong><span>点击开始后，订单、骑手、路线和优势指标会按全天时间自动推进。</span>`;
      }
      const reason = latestTransitionReason();
      const stateText = orderStateSummaryText(orders);
      const moving = activeMapRider(riders);
      if (moving) {
        const movingAction = { order_id: moving.order_id, courier_id: moving.id };
        const orderLabel = moving.order_id ? actionDisplayLabel("order", movingAction) : "当前订单";
        const riderLabel = actionDisplayLabel("rider", movingAction);
        const extraOrders = orderLabelsForIds(moving.task_order_ids || []).filter((label) => label !== orderLabel);
        const taskChain = extraOrders.length ? `，同一骑手本轮还承接 ${extraOrders.join("、")}` : "";
        return `<strong>${escapeHtml(riderLabel)} 正在执行 ${escapeHtml(orderLabel)}</strong><span>路线进度 ${fmtNumber((moving.progress || 0) * 100, 0)}%${escapeHtml(taskChain)}。当前地图：${escapeHtml(stateText)}。变化原因：${escapeHtml(reason)}</span>`;
      }
      const route = routes.find((item) => (item.renderLane || item.lane) === "ours") || routes[0];
      if (route) {
        return `<strong>本轮路线已接管：${escapeHtml(actionPairLabel(route))}</strong><span>当前地图：${escapeHtml(stateText)}。变化原因：${escapeHtml(reason)}</span>`;
      }
      return `<strong>等待首轮路线</strong><span>已释放 ${orders.length} 个订单点（${escapeHtml(stateText)}）；只显示已真实释放的订单，尚未到派单决策时刻。变化原因：${escapeHtml(reason)}</span>`;
    }

    // 右侧「地图执行中订单」列表：数据源与地图完全一致（liveDispatchedRoutes + orderStatusAt），
    // 确保凡是地图上高亮/画线的执行中订单，都能在右侧逐条找到「订单 → 骑手 / 状态」的解释（§3.8）。
    function renderLiveDispatchList() {
      if (!inferenceState.started) {
        return `<div class="list-item"><strong>尚未开始</strong><p>开始推理后，这里会列出地图上每一条执行中派单（订单 → 骑手），与地图严格一一对应。</p></div>`;
      }
      const t = inferenceState.currentTimeS;
      const dispatched = liveDispatchedRoutes(t);
      const anchors = workbench.map.anchors.orders;
      const waitingCount = anchors.filter((order) => orderStatusAt(order.id, t) === "waiting").length;
      if (!dispatched.length) {
        return `<div class="list-item"><strong>暂无执行中派单</strong><p>当前有 ${waitingCount} 个已释放订单在等待下一次派单决策；地图上的订单点均为「待派单」状态。</p></div>`;
      }
      const rows = dispatched
        .slice()
        .sort((a, b) => (orderLifecycle[a.order_id]?.assign_at_s || 0) - (orderLifecycle[b.order_id]?.assign_at_s || 0))
        .map((route) => {
          const life = orderLifecycle[route.order_id] || {};
          const remainingMin = Math.max(0, ((life.complete_at_s || t) - t) / 60);
          const orderLabel = actionDisplayLabel("order", route);
          const riderLabel = actionDisplayLabel("rider", route);
          return `<div class="list-item" data-dispatch-order="${escapeHtml(orderLabel)}"><strong>${escapeHtml(orderLabel)} → ${escapeHtml(riderLabel)}</strong><p>已派单·执行中 / 预计还需 ${fmtNumber(remainingMin, 1)} 分钟送达</p></div>`;
        })
        .join("");
      const tail = waitingCount ? `<div class="list-item"><strong>另有 ${waitingCount} 个待派单</strong><p>已释放、等待下一次派单决策，地图上以「待派单」样式显示。</p></div>` : "";
      return rows + tail;
    }

    function renderHotspots() {
      return workbench.map.hotspots.map((hotspot, index) => {
        const active = hotspot.start_s <= inferenceState.currentTimeS && inferenceState.currentTimeS <= hotspot.end_s;
        const label = mapEntityLabel("hotspot", hotspot, index);
        return `<div class="hotspot" data-active="${active}" data-map-ref="${escapeHtml(label)}" title="${escapeHtml(mapEntityTitle("hotspot", label, {phase: active ? "active" : "inactive"}))}" style="--x:${hotspot.center.screen_x};--y:${hotspot.center.screen_y};--severity:${hotspot.severity}"></div>`;
      }).join("");
    }

    function renderMapDots(kind, items, positionKey, focusOrderIds = new Set()) {
      return items.map((item, index) => {
        const pos = item[positionKey];
        const status = kind === "order" ? (item.status || "pending") : "";
        const release = kind === "order" && status === "pending" && item.created_at_s >= inferenceState.currentTimeS - 900 ? "new" : "stable";
        const motion = kind === "rider" ? (item.motion || "snapshot") : "";
        const label = mapEntityLabel(kind, item, index);
        const showLabel = shouldShowMapLabel(kind, item, index, label, focusOrderIds);
        return `<span class="map-dot" data-kind="${escapeHtml(kind)}" data-map-ref="${escapeHtml(label)}" data-map-label="${escapeHtml(label)}" data-show-label="${showLabel}" data-release="${escapeHtml(release)}" data-status="${escapeHtml(status)}" data-motion="${escapeHtml(motion)}" data-phase="${escapeHtml(item.phase || "")}" title="${escapeHtml(mapEntityTitle(kind, label, item))}" aria-label="${escapeHtml(mapEntityTitle(kind, label, item))}" style="--x:${pos.screen_x};--y:${pos.screen_y}"></span>`;
      }).join("");
    }

    function renderMapLegend() {
      const entityItems = [
        ["rider", "骑手"],
        ["merchant", "商家"],
        ["hotspot", "热点"]
      ];
      // 订单点按生命周期着色，图例逐一解释，避免“点消失/变色看不懂”。
      const orderStateItems = [
        ["pending", "订单·待派单"],
        ["active", "订单·执行中"],
        ["settled", "订单·已完成"]
      ];
      // 线条语义与实际绘制严格一致：默认只画我方规划/执行；对比模式才出现基线与差异线。
      const routeItems = [
        ["ours", "我方规划/执行路线"],
        ["active-progress", "执行进度"]
      ];
      if (inferenceState.mode !== "current") {
        routeItems.push(["baseline", "基线路线"]);
        routeItems.push(["difference", "差异路线（派给不同骑手）"]);
      }
      return `
        <div class="map-legend">
          ${entityItems.map(([kind, label]) => `<span class="legend-item"><i class="legend-dot" data-kind="${escapeHtml(kind)}"></i>${escapeHtml(label)}</span>`).join("")}
          ${orderStateItems.map(([state, label]) => `<span class="legend-item"><i class="legend-dot" data-kind="order" data-status="${escapeHtml(state)}"></i>${escapeHtml(label)}</span>`).join("")}
          ${routeItems.map(([lane, label]) => `<span class="legend-item"><i class="legend-swatch" data-lane="${escapeHtml(lane)}"></i>${escapeHtml(label)}</span>`).join("")}
        </div>
      `;
    }

    function mapEntityLabel(kind, item = {}, index = 0) {
      const id = item.id || item.courier_id || item.order_id || item.merchant_id || "";
      const aliasBuckets = workbench.map.aliases || {};
      const bucketName = kind === "merchant" ? "merchants" : kind === "rider" ? "riders" : kind === "order" ? "orders" : "";
      if (item.map_label) return item.map_label;
      if (bucketName && aliasBuckets[bucketName] && aliasBuckets[bucketName][id]) return aliasBuckets[bucketName][id];
      const prefix = kind === "merchant" ? "M" : kind === "rider" ? "R" : kind === "order" ? "O" : "H";
      const width = kind === "order" ? 3 : 2;
      return `${prefix}-${String(index + 1).padStart(width, "0")}`;
    }

    function actionDisplayLabel(kind, item) {
      const labelKey = kind === "order" ? "order_label" : kind === "rider" ? "courier_label" : "";
      if (labelKey && item?.[labelKey]) return item[labelKey];
      const id = kind === "order" ? item?.order_id : kind === "rider" ? item?.courier_id : item?.id;
      return mapEntityLabel(kind, { id: id || item?.id || "" });
    }

    function actionPairLabel(item) {
      return `${actionDisplayLabel("order", item)} -> ${actionDisplayLabel("rider", item)}`;
    }

    function actionSentenceLabel(item) {
      return `${actionDisplayLabel("order", item)} 派给 ${actionDisplayLabel("rider", item)}`;
    }

    function orderLabelsForIds(orderIds = []) {
      return uniqueIds(orderIds).map((orderId) => actionDisplayLabel("order", { order_id: orderId }));
    }

    function focusedMapOrderIds(routes = [], riders = []) {
      const ids = new Set();
      for (const route of routes) {
        const lane = route.renderLane || route.lane;
        if (route.order_id && !["baseline", "previous"].includes(lane)) ids.add(route.order_id);
      }
      for (const rider of riders) {
        if (rider.motion === "moving" && rider.order_id) ids.add(rider.order_id);
      }
      return ids;
    }

    function shouldShowMapLabel(kind, item, index, label, focusOrderIds = new Set()) {
      if (kind === "rider") return true;
      if (kind !== "order") return false;
      // 待派单 / 执行中的订单必须显示编号；已完成的淡出点默认不显示，除非被聚焦。
      if (item.status === "settled") return focusOrderIds.has(item.id);
      return true;
    }

    function mapEntityTitle(kind, label, item = {}) {
      const kindLabel = {
        merchant: "商家",
        rider: "骑手",
        order: "订单",
        hotspot: "热点"
      }[kind] || "实体";
      const details = [];
      // 仅对实时地图上的订单点补充生命周期信息（这些对象带有 status），
      // 不影响其他页面（订单页/骑手页小地图）复用同一 tooltip 函数时的展示。
      const orderStatusText = { active: "已派单·执行中", pending: "已释放·待派单", settled: "已完成" };
      if (kind === "order" && orderStatusText[item.status]) {
        const life = orderLifecycle[item.id];
        details.push(`状态:${orderStatusText[item.status]}`);
        if (life && life.created_at_s != null) details.push(`释放:${clock(life.created_at_s)}`);
        if (life && life.dispatched && life.courier_label) details.push(`派给:${life.courier_label}`);
      }
      if (item.risk_level) details.push(`风险:${displayRisk(item.risk_level)}`);
      if (item.phase) details.push(displayRiderState(item.phase));
      if (kind === "rider" && item.task_order_ids?.length > 1) details.push(`任务链:${orderLabelsForIds(item.task_order_ids).join(" + ")}`);
      return `${kindLabel} ${label}${details.length ? ` / ${details.join(" / ")}` : ""}`;
    }

    function queueLiveMapHydration(frame, routes, riders, orders) {
      const token = `${frame.id}:${Math.round(inferenceState.currentTimeS)}:${inferenceState.mode}`;
      liveMapHydrationToken = token;
      window.requestAnimationFrame(() => {
        if (liveMapHydrationToken === token) hydrateLiveMap(frame, routes, riders, orders);
      });
    }

    function destroyLiveMap() {
      liveMapHydrationToken = "";
      liveLeafletOverlayGroup = null;
      if (liveLeafletMap) {
        liveLeafletMap.remove();
        liveLeafletMap = null;
      }
    }

    function updateLiveLeafletOverlay(frame, routes, riders, orders) {
      const stage = document.getElementById("live-map-stage");
      if (!window.L || !stage || !liveLeafletMap || !liveLeafletOverlayGroup || stage.dataset.realMapStatus !== "leaflet") return false;
      try {
        stage.dataset.leafletRouteCount = String(routes.length);
        stage.dataset.leafletMarkerCount = String(workbench.map.anchors.merchants.slice(0, 16).length + riders.slice(0, 14).length + orders.slice(0, 40).length);
        const chip = stage.querySelector(".map-mode-chip");
        if (chip) chip.textContent = `${inferenceModeLabels[inferenceState.mode]} / ${frame.id}`;
        liveLeafletOverlayGroup.clearLayers();
        renderLeafletMapLayers(liveLeafletOverlayGroup, routes, riders, orders);
        return true;
      } catch (error) {
        console.warn("Live map overlay update fell back to rebuild", error);
        return false;
      }
    }

    function hydrateLiveMap(frame, routes, riders, orders) {
      const stage = document.getElementById("live-map-stage");
      const container = document.getElementById("leaflet-live-map");
      if (!stage || !container) return;
      if (!window.L) {
        stage.dataset.realMapStatus = "fallback";
        stage.dataset.leafletRouteCount = "0";
        stage.dataset.leafletMarkerCount = "0";
        return;
      }
      try {
        stage.dataset.realMapStatus = "loading";
        stage.dataset.leafletRouteCount = String(routes.length);
        stage.dataset.leafletMarkerCount = String(workbench.map.anchors.merchants.slice(0, 16).length + riders.slice(0, 14).length + orders.slice(0, 40).length);
        const map = window.L.map(container, {
          attributionControl: true,
          boxZoom: true,
          doubleClickZoom: true,
          preferCanvas: true,
          scrollWheelZoom: true,
          zoomControl: false
        });
        liveLeafletMap = map;
        window.L.control.zoom({ position: "bottomright" }).addTo(map);
        window.L.tileLayer(liveTileLayer.url, {
          attribution: liveTileLayer.attribution,
          maxZoom: 19,
          subdomains: liveTileLayer.subdomains
        }).addTo(map);
        const bounds = mapBounds();
        if (bounds) map.fitBounds(bounds, { animate: false, padding: [18, 18] });
        else map.setView(mapPoint(workbench.map.center), 14);
        liveLeafletOverlayGroup = window.L.layerGroup().addTo(map);
        renderLeafletMapLayers(liveLeafletOverlayGroup, routes, riders, orders);
        stage.dataset.realMapStatus = "leaflet";
        window.setTimeout(() => {
          if (liveLeafletMap === map && container.isConnected) map.invalidateSize(false);
        }, 0);
      } catch (error) {
        console.warn("Live map fell back to deterministic anonymous layer", error);
        destroyLiveMap();
        stage.dataset.realMapStatus = "fallback";
        stage.dataset.leafletRouteCount = "0";
        stage.dataset.leafletMarkerCount = "0";
      }
    }

    function renderLeafletMapLayers(layerGroup, routes, riders, orders) {
      renderLeafletHotspots(layerGroup);
      renderLeafletRoutes(layerGroup, routes, riders);
      renderLeafletMarkers(layerGroup, "merchant", workbench.map.anchors.merchants.slice(0, 16), "position");
      renderLeafletMarkers(layerGroup, "rider", riders.slice(0, 14), "position");
      renderLeafletMarkers(layerGroup, "order", orders.slice(0, 40), "dropoff", focusedMapOrderIds(routes, riders));
    }

    function mapBounds() {
      if (!window.L || !workbench.map.bounds || workbench.map.bounds.length < 2) return null;
      return window.L.latLngBounds(workbench.map.bounds.map(mapPoint));
    }

    function mapPoint(point) {
      return [Number(point.lat), Number(point.lng)];
    }

    function renderLeafletHotspots(map) {
      workbench.map.hotspots.forEach((hotspot, index) => {
        const active = hotspot.start_s <= inferenceState.currentTimeS && inferenceState.currentTimeS <= hotspot.end_s;
        const label = mapEntityLabel("hotspot", hotspot, index);
        window.L.circle(mapPoint(hotspot.center), {
          radius: 230 + Number(hotspot.severity || 1) * 220,
          color: active ? "#b7791f" : "#94a3b8",
          fillColor: active ? "#b7791f" : "#94a3b8",
          fillOpacity: active ? .13 : .08,
          opacity: active ? .34 : .18,
          weight: 1
        }).bindTooltip(escapeHtml(mapEntityTitle("hotspot", label, {phase: active ? "active" : "inactive"})), { sticky: true }).addTo(map);
      });
    }

    function renderLeafletRoutes(map, routes, riders = []) {
      const progressRoutes = activeProgressRoutes(routes, riders);
      for (const route of routes) {
        const points = (route.polyline || []).map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        if (points.length < 2) continue;
        const lane = route.renderLane || route.lane;
        window.L.polyline(points, routeHaloStyle(lane)).addTo(map);
        window.L.polyline(points, routeStyle(lane)).bindTooltip(escapeHtml(routeTooltip(route)), { sticky: true }).addTo(map);
      }
      for (const route of progressRoutes) {
        const points = route.progressPolyline.map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        if (points.length < 2) continue;
        window.L.polyline(points, routeProgressStyle()).bindTooltip(escapeHtml(`当前执行 / ${routeTooltip(route)}`), { sticky: true }).addTo(map);
      }
    }

    function routeStyle(lane) {
      const styles = {
        ours: { color: "#0f766e", weight: 4, opacity: .78 },
        previous: { color: "#64748b", weight: 2, opacity: .28, dashArray: "3 8" },
        baseline: { color: "#b42318", weight: 3, opacity: .34, dashArray: "5 7" },
        difference: { color: "#b7791f", weight: 5, opacity: .82 }
      };
      return styles[lane] || styles.ours;
    }

    function routeHaloStyle(lane) {
      const style = routeStyle(lane);
      return {
        color: "#ffffff",
        weight: Number(style.weight || 3) + 5,
        opacity: lane === "previous" ? .18 : .62,
        dashArray: style.dashArray || null,
        interactive: false
      };
    }

    function routeProgressStyle() {
      return {
        color: "#059669",
        dashArray: "5 7",
        interactive: false,
        opacity: .94,
        weight: 6
      };
    }

    function routeTooltip(route) {
      const laneLabel = {
        ours: "我方路线",
        previous: "旧路线",
        baseline: "基线差异",
        difference: "叠加差异"
      }[route.renderLane || route.lane] || "路线";
      return `${laneLabel} / ${actionPairLabel(route)}`;
    }

    function renderLeafletMarkers(map, kind, items, positionKey, focusOrderIds = new Set()) {
      items.forEach((item, index) => {
        const pos = item[positionKey];
        if (!pos || !Number.isFinite(Number(pos.lat)) || !Number.isFinite(Number(pos.lng))) return;
        const label = mapEntityLabel(kind, item, index);
        const status = kind === "order" ? (item.status || "pending") : "";
        const release = kind === "order" && status === "pending" && item.created_at_s >= inferenceState.currentTimeS - 900 ? "new" : "stable";
        const motion = kind === "rider" ? (item.motion || "snapshot") : "";
        window.L.marker(mapPoint(pos), {
          icon: renderLeafletMarker(kind, label, release, motion, index, shouldShowMapLabel(kind, item, index, label, focusOrderIds), status),
          keyboard: false,
          zIndexOffset: kind === "rider" ? 500 : kind === "order" ? (status === "active" ? 350 : 300) : 100
        }).bindTooltip(escapeHtml(mapEntityTitle(kind, label, item)), { direction: "top", opacity: .92, sticky: true }).addTo(map);
      });
    }

    function renderLeafletMarker(kind, label, release, motion, index = 0, showLabel = null, status = "") {
      const visible = showLabel ?? (kind === "rider" || (kind === "order" && index < 4));
      return window.L.divIcon({
        className: "leaflet-map-pin",
        html: `<span class="leaflet-map-pin-body" data-kind="${escapeHtml(kind)}" data-release="${escapeHtml(release)}" data-status="${escapeHtml(status)}" data-motion="${escapeHtml(motion)}"></span>${visible ? `<span class="leaflet-map-pin-label">${escapeHtml(label)}</span>` : ""}`,
        iconAnchor: [8, 8],
        iconSize: [16, 16]
      });
    }

    function renderScoreCard(label, value, detail, tone, metricId = "") {
      const metricAttrs = metricId ? ` id="${escapeHtml(metricId)}" data-metric="${escapeHtml(metricId)}"` : "";
      return `<div class="score-card" data-tone="${escapeHtml(tone)}"${metricAttrs}><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`;
    }

    // 开始前的「演前导览」：用一段说明 + 全天压力时刻替换一排 0 值卡片。
    function renderAdvantagePrebrief() {
      const shocks = (workbench.map.hotspots || []).slice().sort((a, b) => a.start_s - b.start_s);
      const shockItems = shocks.map((hotspot) =>
        `<li><b>${escapeHtml(clock(hotspot.start_s))}</b><span>${escapeHtml(displayShock(hotspot.type))}</span></li>`
      ).join("");
      return `
        <div class="advantage-prebrief" data-score-section="prebrief">
          <div class="prebrief-intro">
            <p>这是一场<b>同数据对照实验</b>：贪心基线与我方算法，在同一天的 207 单上各跑一遍（07:00 → 23:00），右侧实时累计「我方比贪心好多少」。</p>
            <p class="prebrief-watch">看点：平峰时两者差不多；<b>一旦遇到压力，贪心会开始超时，而我方要稳住 0 超时</b>。</p>
          </div>
          <div class="prebrief-shocks">
            <span class="prebrief-shocks-title">全天 ${shocks.length} 个压力时刻</span>
            <ul>${shockItems}</ul>
          </div>
        </div>
      `;
    }

    function renderLiveScoreCards(score) {
      if (!inferenceState.started) {
        return renderAdvantagePrebrief();
      }
      const timeoutTone = score.deltas.timeout_order_delta <= 0 ? "good" : "risk";
      const moneyTone = score.deltas.money_saved_yuan >= 0 ? "good" : "risk";
      // 累计成本对照：贪心基线（对照） vs 我方算法（实验）。
      return `
        <div class="algorithm-pair" data-score-section="algorithm-cumulative">
          ${renderScoreCard("贪心基线（对照）", `${fmtNumber(score.baseline.total_cost_yuan, 1)} 元`, `累计 ${fmtNumber(score.baseline.total_time_cost_min, 1)} 分钟 / ${score.baseline.late_orders} 超时单`, "warn", "metric-baseline-cumulative")}
          ${renderScoreCard("我方算法（实验）", `${fmtNumber(score.ours.total_cost_yuan, 1)} 元`, `累计 ${fmtNumber(score.ours.total_time_cost_min, 1)} 分钟 / ${score.ours.late_orders} 超时单`, "good", "metric-ours-cumulative")}
        </div>
        <div class="delta-grid" data-score-section="advantage-deltas">
          ${renderScoreCard("省时间", `${fmtNumber(score.deltas.time_saved_min, 1)} 分钟`, `贪心 ${fmtNumber(score.baseline.total_time_cost_min, 0)} → 我方 ${fmtNumber(score.ours.total_time_cost_min, 0)} 分钟`, "good", "metric-time-delta")}
          ${renderScoreCard("省成本", `${fmtNumber(score.deltas.money_saved_yuan, 1)} 元`, `贪心 ${fmtNumber(score.baseline.total_cost_yuan, 0)} → 我方 ${fmtNumber(score.ours.total_cost_yuan, 0)} 元`, moneyTone, "metric-money-delta")}
          ${renderScoreCard("超时单", fmtFewer(score.deltas.timeout_order_delta, "单"), `贪心 ${score.baseline.late_orders} 单 → 我方 ${score.ours.late_orders} 单`, timeoutTone, "metric-timeout-delta")}
        </div>
      `;
    }

    function renderMetricChip(metricId, label, value, detail) {
      return `<div class="metric-chip" id="metric-chip-${escapeHtml(metricId)}" data-metric="${escapeHtml(metricId)}"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`;
    }

    // 与首屏对比栏口径一致：省时间 / 省成本 / 超时单，去掉重复的「收益/成本差异」。
    function renderLiveCumulativeMetrics(score) {
      return [
        renderMetricChip("time-delta", "省时间", `${fmtNumber(score.deltas.time_saved_min, 1)} 分钟`, `贪心 ${fmtNumber(score.baseline.total_time_cost_min, 0)} / 我方 ${fmtNumber(score.ours.total_time_cost_min, 0)}`),
        renderMetricChip("money-delta", "省成本", `${fmtNumber(score.deltas.money_saved_yuan, 1)} 元`, `贪心 ${fmtNumber(score.baseline.total_cost_yuan, 0)} / 我方 ${fmtNumber(score.ours.total_cost_yuan, 0)}`),
        renderMetricChip("timeout-delta", "超时单", fmtFewer(score.deltas.timeout_order_delta, "单"), `贪心 ${score.baseline.late_orders} / 我方 ${score.ours.late_orders}`)
      ].join("");
    }

    function actionSummary(actions, limit = 3) {
      if (!actions || !actions.length) return "暂无动作";
      const preview = actions.slice(0, limit).map((item) => {
        const eta = item.total_eta_min === undefined ? "" : ` / ${fmtNumber(item.total_eta_min, 1)}分钟`;
        return `${actionPairLabel(item)}${eta}`;
      }).join(", ");
      return actions.length > limit ? `${preview} +${actions.length - limit} 项` : preview;
    }

    function decisionById(decisionId) {
      return workbench.decisions.find((item) => item.id === decisionId) || workbench.decisions[0];
    }

    function selectedDecision() {
      const decision = decisionById(selectedDecisionId);
      selectedDecisionId = decision?.id || "";
      return decision;
    }

    function hydrateDecisionPage() {
      const timeline = document.getElementById("decision-timeline");
      if (!timeline) return;
      timeline.addEventListener("click", (event) => {
        const button = event.target.closest("[data-decision-id]");
        if (button) selectDecisionRound(button.dataset.decisionId);
      });
      selectDecisionRound(selectedDecisionId || workbench.decisions[0]?.id);
    }

    function selectDecisionRound(decisionId) {
      const decision = decisionById(decisionId);
      if (!decision) return;
      selectedDecisionId = decision.id;
      const timeline = document.getElementById("decision-timeline");
      if (timeline) {
        for (const item of timeline.querySelectorAll("[data-decision-id]")) {
          item.dataset.active = item.dataset.decisionId === decision.id ? "true" : "false";
        }
      }
      setText("decision-route-status", `${decision.trigger_time_label} / ${readableDecisionLabel(decision.id)}`);
      setText("decision-reasoning-phase", displayDemandPhase(decision.context.demand_phase));
      setText("decision-context-slice", `${displayDemandPhase(decision.context.demand_phase)}场景`);
      const reasoning = document.getElementById("decision-reasoning-canvas");
      if (reasoning) reasoning.innerHTML = renderDecisionReasoning(decision);
      const contextPane = document.getElementById("decision-context-pane");
      if (contextPane) contextPane.innerHTML = renderDecisionContext(decision);
    }

    function renderDecisionTimeline(activeId) {
      return workbench.decisions.map((item, index) => `
        <button class="timeline-item" data-decision-id="${escapeHtml(item.id)}" data-active="${item.id === activeId}">
          <strong>第 ${index + 1} 轮 / ${escapeHtml(item.trigger_time_label)}</strong>
          <span>${escapeHtml(displayTriggerReason(item.trigger_reason))}</span>
          <span class="timeline-meta">
            <em>${item.input_order_ids.length} 单</em>
            <em>${item.candidate_rider_ids.length} 名骑手</em>
            <em>${escapeHtml(displayDemandPhase(item.context.demand_phase))}</em>
          </span>
        </button>
      `).join("");
    }

    function renderDecisionStage(stageId, title, count, body) {
      return `
        <section class="decision-stage" id="${escapeHtml(stageId)}" data-decision-stage="${escapeHtml(stageId)}">
          <div class="decision-stage-head"><b>${escapeHtml(title)}</b><span>${escapeHtml(count)}</span></div>
          <div class="decision-stage-body">${body}</div>
        </section>
      `;
    }

    function renderChipList(items, emptyLabel = "None") {
      const values = (items || []).filter(Boolean);
      if (!values.length) return `<p>${escapeHtml(emptyLabel)}</p>`;
      return `<div class="chip-list">${values.map((item) => `<span class="data-chip">${escapeHtml(item)}</span>`).join("")}</div>`;
    }

    function readableDecisionLabel(decisionId) {
      const index = workbench.decisions.findIndex((item) => item.id === decisionId);
      return index >= 0 ? `第 ${index + 1} 轮` : "当前轮次";
    }

    function readableMemoryLabel(memoryId) {
      const index = workbench.memory.items.findIndex((item) => item.id === memoryId);
      if (index >= 0) return `记忆 ${String(index + 1).padStart(2, "0")}`;
      const text = String(memoryId || "");
      if (text.includes("recall")) return "召回记忆";
      if (text.includes("writeback")) return "回写记忆";
      if (text.includes("policy")) return "策略记忆";
      return "调度记忆";
    }

    function renderMemoryChipList(memoryIds, emptyLabel = "无回写记忆") {
      return renderChipList((memoryIds || []).map(readableMemoryLabel), emptyLabel);
    }

    function memoryReferenceText(memoryIds) {
      const values = (memoryIds || []).filter(Boolean);
      if (!values.length) return "无";
      return values.map(readableMemoryLabel).join("、");
    }

    function recalledCaseText(caseIds) {
      const count = (caseIds || []).filter(Boolean).length;
      return count ? `${count} 个相似场景` : "暂无召回样本";
    }

    function renderDecisionScoreRows(scores) {
      if (!scores.length) return `<p>等待评分</p>`;
      const maxScore = Math.max(...scores.map((item) => Number(item.score) || 0), 1);
      return scores.map((item) => {
        const normalized = clamp((Number(item.score) || 0) / maxScore, 0.04, 1);
        return `
          <div class="score-row" data-algorithm-id="${escapeHtml(item.algorithm_id)}">
            <b>${escapeHtml(candidateLabel(item.algorithm_id))}</b>
            <div>
              <div class="score-bar" style="--score:${normalized}"><span></span></div>
              <p>${escapeHtml(displayCandidateReason(item.reason))}</p>
            </div>
            <em>${fmtNumber(item.score, 3)}</em>
          </div>
        `;
      }).join("");
    }

    function renderDecisionActions(actions, kind) {
      if (!actions.length) return `<p>暂无动作</p>`;
      return `<div class="action-grid">${actions.map((item) => {
        const detail = kind === "final"
          ? `预计 ${fmtNumber(item.total_eta_min, 1)} 分钟 / 成本 ${fmtNumber(item.expected_cost_yuan, 1)} 元 / 风险 ${fmtNumber(item.timeout_risk, 3)}`
          : displayActionReason(item.reason);
        return `
          <div class="action-card" data-action-kind="${escapeHtml(kind)}">
            <strong>${escapeHtml(actionPairLabel(item))}</strong>
            <p>${escapeHtml(detail)}</p>
          </div>
        `;
      }).join("")}</div>`;
    }

    function decisionInputOrderIds(decision) {
      return (decision.input_orders || []).length ? decision.input_orders.map((item) => item.id) : (decision.input_order_ids || []);
    }

    function decisionCandidateRiderIds(decision) {
      return (decision.candidate_riders || []).length ? decision.candidate_riders.map((item) => item.id) : (decision.candidate_rider_ids || []);
    }

    function decisionInputOrderLabels(decision) {
      return decisionInputOrderIds(decision).map((orderId) => actionDisplayLabel("order", { order_id: orderId }));
    }

    function decisionCandidateRiderLabels(decision) {
      return decisionCandidateRiderIds(decision).map((courierId) => actionDisplayLabel("rider", { courier_id: courierId }));
    }

    function topDecisionScore(decision) {
      return [...(decision.scoring_process || [])].sort((left, right) => Number(right.score || 0) - Number(left.score || 0))[0] || null;
    }

    function decisionFilterSentence(decision) {
      const parts = (decision.filtering_process || []).map((stage) => `${displayStage(stage.stage)}后剩 ${stage.remaining}`);
      return parts.length ? parts.join("，") : "暂无过滤记录";
    }

    function decisionScoreSentence(decision) {
      const scores = decision.scoring_process || [];
      if (!scores.length) return "当前轮还没有评分结果。";
      const best = topDecisionScore(decision);
      const compared = scores.map((item) => `${candidateLabel(item.algorithm_id)} ${fmtNumber(item.score, 3)}`).join("，");
      return `综合比较时间、成本、风险和可用性：${compared}。本轮保留 ${candidateLabel(best.algorithm_id)}。`;
    }

    function decisionActionSentence(actions, limit = 3) {
      if (!actions || !actions.length) return "暂无动作";
      const text = actions.slice(0, limit).map((item) => {
        const eta = item.total_eta_min === undefined ? "" : `，预计 ${fmtNumber(item.total_eta_min, 1)} 分钟`;
        return `${actionSentenceLabel(item)}${eta}`;
      }).join("；");
      return actions.length > limit ? `${text}；另有 ${actions.length - limit} 个动作` : text;
    }

    function decisionAdvantageHeadline(decision) {
      const result = decision.round_result || {};
      return `本轮节省 ${fmtNumber(result.time_saved_min || 0, 1)} 分钟`;
    }

    function renderDecisionAdvantageHero(decision) {
      const result = decision.round_result || {};
      return `
        <section class="decision-advantage-hero" data-reasoning-surface="advantage-first">
          <div class="decision-advantage-copy">
            <span class="reason-kicker">本轮结论</span>
            <h3>${escapeHtml(decisionAdvantageHeadline(decision))}</h3>
            <p>先解释为什么我方方案优于基线：候选策略经过场景识别、可行性校验、风险评分和结果回写，最终保留能降低时间、成本和超时风险的动作。</p>
          </div>
          <div class="decision-advantage-metrics">
            ${renderMetricChip("reason-time-advantage", "时间优势", `${fmtNumber(result.time_saved_min || 0, 1)} 分钟`, "相对最近距离基线")}
            ${renderMetricChip("reason-cost-advantage", "成本优势", `${fmtNumber(result.cost_saved_yuan || 0, 1)} 元`, "兼顾风险后的成本")}
            ${renderMetricChip("reason-risk-advantage", "超时风险变化", fmtSigned(result.timeout_risk_delta || 0, 3), "数值越低越好")}
            ${renderMetricChip("reason-actions", "最终动作", `${decision.final_actions.length}`, `${decision.abandoned_actions.length} 个被放弃`)}
          </div>
        </section>
      `;
    }

    function renderDecisionStep(stepId, index, title, status, body, metaItems = []) {
      return `
        <article class="decision-step-card" id="${escapeHtml(stepId)}" data-decision-step="${escapeHtml(stepId)}" data-step-status="${escapeHtml(status)}">
          <div class="decision-step-index">${index}</div>
          <div class="decision-step-body">
            <div class="decision-step-top"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(status === "final" ? "已输出" : "已完成")}</span></div>
            <p>${body}</p>
            ${renderChipList(metaItems, "暂无补充信息")}
          </div>
        </article>
      `;
    }

    function renderDecisionStepFlow(decision) {
      const inputOrderIds = decisionInputOrderIds(decision);
      const candidateRiderIds = decisionCandidateRiderIds(decision);
      const inputOrderLabels = decisionInputOrderLabels(decision);
      const candidateRiderLabels = decisionCandidateRiderLabels(decision);
      const bestScore = topDecisionScore(decision);
      return `
        <section id="decision-step-flow" class="decision-step-flow" data-reasoning-pattern="plain-six-step">
          ${renderDecisionStep("decision-trigger-time", 1, "为什么触发这一轮", "done", `${escapeHtml(decision.trigger_time_label)}，${escapeHtml(displayTriggerReason(decision.trigger_reason))}`, [readableDecisionLabel(decision.id), displayDemandPhase(decision.context.demand_phase)])}
          ${renderDecisionStep("decision-input-orders", 2, "看哪些订单", "done", `本轮把 ${inputOrderIds.length} 个已经进入推理窗口的订单放进同一批判断，不让单个订单孤立决策。`, inputOrderLabels.slice(0, 8))}
          ${renderDecisionStep("decision-candidate-riders", 3, "候选骑手怎么选", "done", `系统只从在线、同区域或可及时赶到的骑手里选候选，共 ${candidateRiderIds.length} 名。`, candidateRiderLabels.slice(0, 8))}
          ${renderDecisionStep("decision-filtering-process", 4, "先过滤不可行方案", "done", `先按时间窗口、区域班次、拥堵和承诺送达时间过滤，${escapeHtml(decisionFilterSentence(decision))}。`, (decision.filtering_process || []).map((stage) => `${displayStage(stage.stage)} ${stage.remaining}`))}
          ${renderDecisionStep("decision-scoring-process", 5, "再给可行方案打分", "done", `${escapeHtml(decisionScoreSentence(decision))}`, bestScore ? [candidateLabel(bestScore.algorithm_id), `评分 ${fmtNumber(bestScore.score, 3)}`, `风险 ${fmtNumber(bestScore.risk_score, 3)}`] : ["等待评分"])}
          ${renderDecisionStep("decision-final-actions", 6, "输出派单并回写记忆", "final", `最终输出 ${decision.final_actions.length} 个派单动作，放弃 ${decision.abandoned_actions.length} 个基线动作；本轮节省 ${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟，回写 ${decision.result_writeback.writeback_count} 条有效记忆。`, [`成本优势 ${fmtNumber(decision.round_result.cost_saved_yuan, 1)} 元`, `风险变化 ${fmtSigned(decision.round_result.timeout_risk_delta, 3)}`])}
        </section>
      `;
    }

    function candidateStatus(score, index, scores) {
      const best = Math.max(...scores.map((item) => Number(item.score) || 0), 0);
      if ((Number(score.score) || 0) >= best && best > 0) return "selected";
      return index === 0 ? "rejected" : "rejected";
    }

    function candidateLabel(algorithmId) {
      if (algorithmId === "nearest_greedy") return "最近距离基线";
      if (algorithmId === "cost_greedy") return "成本优先基线";
      if (algorithmId === "risk_aware_greedy") return "风险感知基线";
      if (algorithmId === "min_cost_matching") return "最小成本匹配";
      if (algorithmId === "flow_mcf") return "流式最小成本方案";
      if (algorithmId === "autosolver_agent") return "我方智能调度方案";
      return algorithmId.replaceAll("_", " ");
    }

    function candidateRejectReason(score) {
      if (score.algorithm_id === "nearest_greedy") return "路线和距离局部最短，但没有同时保护承诺时效、骑手负载和后续风险。";
      return "未成为当前最高综合评分候选。";
    }

    function renderDecisionPlanComparison(decision) {
      const scores = decision.scoring_process || [];
      const acceptedScore = topDecisionScore(decision);
      return `
        <section id="decision-plan-comparison" class="decision-plan-board" data-reasoning-pattern="accepted-and-rejected">
          <article id="decision-accepted-plan" class="decision-plan-card" data-plan="accepted">
            <div class="decision-plan-top">
              <strong>采纳方案</strong>
              <span class="decision-plan-status">${escapeHtml(acceptedScore ? candidateLabel(acceptedScore.algorithm_id) : "等待评分")}</span>
            </div>
            <p>${escapeHtml(acceptedScore ? displayCandidateReason(acceptedScore.reason) : "等待评分结果。")}</p>
            <p>${escapeHtml(decisionActionSentence(decision.final_actions, 4))}</p>
            <div class="context-metric-grid">
              ${renderMetricChip("accepted-score", "综合评分", acceptedScore ? fmtNumber(acceptedScore.score, 3) : "-", "分数高者保留")}
              ${renderMetricChip("accepted-risk", "超时风险", acceptedScore ? fmtNumber(acceptedScore.risk_score, 3) : "-", "风险越低越好")}
              ${renderMetricChip("accepted-time", "时间优势", `${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟`, "相对基线")}
              ${renderMetricChip("accepted-cost", "成本优势", `${fmtNumber(decision.round_result.cost_saved_yuan, 1)} 元`, "本轮")}
            </div>
          </article>
          <article id="decision-rejected-plan" class="decision-plan-card" data-plan="rejected">
            <div class="decision-plan-top">
              <strong>放弃方案</strong>
              <span class="decision-plan-status">基线备选</span>
            </div>
            <p>${escapeHtml(decision.abandoned_actions.length ? "以下动作来自最近距离基线，但在综合时效、成本和风险评分中被淘汰。" : "本轮没有需要放弃的基线动作。")}</p>
            ${renderDecisionActions(decision.abandoned_actions.slice(0, 4), "abandoned")}
          </article>
          <article id="decision-score-comparison" class="decision-plan-card" data-plan="scores">
            <div class="decision-plan-top">
              <strong>评分对比</strong>
              <span class="decision-plan-status">${scores.length} 个方案</span>
            </div>
            ${renderDecisionScoreRows(scores)}
          </article>
        </section>
      `;
    }

    function renderDecisionEvidence(decision) {
      const inputOrderIds = decisionInputOrderIds(decision);
      const candidateRiderIds = decisionCandidateRiderIds(decision);
      const inputOrderLabels = decisionInputOrderLabels(decision);
      const candidateRiderLabels = decisionCandidateRiderLabels(decision);
      return `
        <section id="decision-proof-panel" class="decision-proof-grid" data-reasoning-surface="required-fields">
          ${renderDecisionStage("decision-trigger-reason", "触发时间与原因", decision.trigger_time_label, `<p>${escapeHtml(displayTriggerReason(decision.trigger_reason))}</p>`)}
          ${renderDecisionStage("decision-input-orders", "输入订单集合", `${inputOrderIds.length} 单`, renderChipList(inputOrderLabels.slice(0, 20), "当前轮无释放订单"))}
          ${renderDecisionStage("decision-candidate-riders", "候选骑手集合", `${candidateRiderIds.length} 名骑手`, renderChipList(candidateRiderLabels.slice(0, 20), "暂无候选骑手"))}
          ${renderDecisionStage("decision-filtering-process", "过滤过程", `${(decision.filtering_process || []).length} 步`, `<p>${escapeHtml(decisionFilterSentence(decision))}</p>`)}
          ${renderDecisionStage("decision-scoring-process", "评分过程", `${(decision.scoring_process || []).length} 个方案`, `<p>${escapeHtml(decisionScoreSentence(decision))}</p>`)}
          ${renderDecisionStage("decision-abandoned-actions", "被放弃动作", `${decision.abandoned_actions.length} 个备选`, renderDecisionActions(decision.abandoned_actions.slice(0, 4), "abandoned"))}
          ${renderDecisionStage("decision-round-result", "本轮结果", `节省 ${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟`, `<p>${escapeHtml(displayDecisionSummary(decision.round_result.summary))}</p>`)}
          ${renderDecisionStage("decision-result-writeback", "结果回写", `${decision.result_writeback.writeback_count} 次回写`, `<p>${escapeHtml(displayDecisionSummary(decision.result_writeback.summary))}</p>${renderMemoryChipList(decision.result_writeback.memory_event_ids, "无回写记忆")}`)}
        </section>
      `;
    }

    function renderDecisionReasoning(decision) {
      return `
        ${renderDecisionAdvantageHero(decision)}
        ${renderDecisionStepFlow(decision)}
        ${renderDecisionPlanComparison(decision)}
        ${renderDecisionEvidence(decision)}
      `;
    }

    function renderDecisionContext(decision) {
      const inputOrderIds = decisionInputOrderIds(decision);
      const candidateRiderIds = decisionCandidateRiderIds(decision);
      const inputOrderLabels = decisionInputOrderLabels(decision);
      const candidateRiderLabels = decisionCandidateRiderLabels(decision);
      return `
        <div class="list-item" id="decision-context-input">
          <strong>这轮发生在什么场景</strong>
          <p>${escapeHtml(decision.trigger_time_label)} / ${escapeHtml(displayDemandPhase(decision.context.demand_phase))} / ${escapeHtml(displayWeather(decision.context.weather))} / 拥堵 ${fmtNumber(decision.context.congestion_level, 2)} / 在线供给 ${decision.context.courier_supply} 名</p>
          <p>冲击事件：${decision.context.shock_ids.length ? decision.context.shock_ids.map((item) => escapeHtml(displayShock(item))).join(", ") : "无"}</p>
        </div>
        <div class="list-item" id="decision-context-orders">
          <strong>输入订单</strong>
          <p>${inputOrderIds.length} 单进入本轮推理。</p>
          ${renderChipList(inputOrderLabels.slice(0, 8), "暂无订单")}
        </div>
        <div class="list-item" id="decision-context-riders">
          <strong>候选骑手</strong>
          <p>${candidateRiderIds.length} 名骑手进入候选集合。</p>
          ${renderChipList(candidateRiderLabels.slice(0, 8), "暂无骑手")}
        </div>
        <div class="list-item" id="decision-output-result">
          <strong>输出结果</strong>
          <p>${escapeHtml(displayDecisionSummary(decision.round_result.summary))}</p>
        </div>
        <div class="context-metric-grid">
          ${renderMetricChip("decision-time-saved", "时间收益", `${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟`, "本轮")}
          ${renderMetricChip("decision-cost-saved", "成本收益", `${fmtNumber(decision.round_result.cost_saved_yuan, 1)} 元`, "本轮")}
          ${renderMetricChip("decision-risk-delta", "风险变化", fmtSigned(decision.round_result.timeout_risk_delta, 3), "超时风险")}
          ${renderMetricChip("decision-extra-delivered", "额外交付", `${decision.round_result.extra_delivered_orders} 单`, "相对基线")}
        </div>
        <div class="list-item" id="decision-round-summary">
          <strong>最终动作</strong>
          <p>${escapeHtml(decisionActionSentence(decision.final_actions, 5))}</p>
        </div>
        <div class="list-item" id="decision-abandoned-summary">
          <strong>被放弃动作</strong>
          <p>输入 ${decision.input_order_ids.length} 单，候选 ${decision.candidate_rider_ids.length} 名骑手，最终 ${decision.final_actions.length} 个动作，放弃 ${decision.abandoned_actions.length} 个基线动作。</p>
        </div>
        <div class="list-item" id="decision-writeback-summary">
          <strong>结果回写</strong>
          <p>${decision.result_writeback.writeback_count} 次有效回写，形成 ${decision.result_writeback.memory_event_ids.length} 条可召回记忆。</p>
        </div>
      `;
    }

    function renderRoundSummary(decision, compact = false) {
      const finalActions = actionSummary(decision.final_actions, 3);
      const abandonedActions = actionSummary(decision.abandoned_actions, 3);
      const filterSummary = decision.filtering_process.slice(0, 3).map((stage) => `${displayStage(stage.stage)}: ${stage.remaining}`).join(" / ");
      const scoreSummary = decision.scoring_process.slice(0, 3).map((item) => `${candidateLabel(item.algorithm_id)} ${fmtNumber(item.score, 3)}`).join(" / ") || "等待评分";
      const writebackIds = memoryReferenceText(decision.result_writeback.memory_event_ids.slice(0, 4));
      if (compact) {
        return `
          <div class="round-summary-grid" data-decision-id="${escapeHtml(decision.id)}" data-density="compact">
            <div class="list-item" id="round-trigger"><strong>触发原因</strong><p>${escapeHtml(displayTriggerReason(decision.trigger_reason))}</p></div>
            <div class="list-item" id="round-final-actions"><strong>最终动作</strong><p>${escapeHtml(finalActions)}</p></div>
            <div class="list-item" id="round-abandoned-actions"><strong>被放弃动作</strong><p>${escapeHtml(abandonedActions)}</p></div>
            <div class="list-item" id="round-writeback"><strong>结果回写</strong><p>${decision.result_writeback.writeback_count} 次回写 / ${escapeHtml(writebackIds)}</p></div>
            <div class="list-item" id="round-metric-impact"><strong>本轮结果</strong><p>${escapeHtml(displayDecisionSummary(decision.round_result.summary))}；节省 ${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟，成本优势 ${fmtNumber(decision.round_result.cost_saved_yuan, 1)} 元。</p></div>
          </div>
        `;
      }
      return `
        <div class="round-summary-grid" data-decision-id="${escapeHtml(decision.id)}">
          <div class="list-item" id="round-trigger"><strong>触发原因</strong><p>${escapeHtml(displayTriggerReason(decision.trigger_reason))}</p></div>
          <div class="list-item" id="round-input-context"><strong>输入上下文</strong><p>${decision.input_order_ids.length} 单 / ${decision.candidate_rider_ids.length} 名骑手 / ${escapeHtml(displayWeather(decision.context.weather))} / 拥堵 ${fmtNumber(decision.context.congestion_level, 2)}</p></div>
          <div class="list-item" id="round-filtering"><strong>过滤过程</strong><p>${escapeHtml(filterSummary)}</p></div>
          <div class="list-item" id="round-scoring"><strong>评分过程</strong><p>${escapeHtml(scoreSummary)}</p></div>
          <div class="list-item" id="round-final-actions"><strong>最终动作</strong><p>${escapeHtml(finalActions)}</p></div>
          <div class="list-item" id="round-abandoned-actions"><strong>被放弃动作</strong><p>${escapeHtml(abandonedActions)}</p></div>
          <div class="list-item" id="round-writeback"><strong>结果回写</strong><p>${decision.result_writeback.writeback_count} 次回写 / ${escapeHtml(writebackIds)}</p></div>
          <div class="list-item" id="round-metric-impact"><strong>本轮结果</strong><p>${escapeHtml(displayDecisionSummary(decision.round_result.summary))}；节省 ${fmtNumber(decision.round_result.time_saved_min, 1)} 分钟，节省 ${fmtNumber(decision.round_result.cost_saved_yuan, 1)} 元，风险差异 ${fmtSigned(decision.round_result.timeout_risk_delta, 3)}。</p></div>
        </div>
      `;
    }

    function renderEventItem(event) {
      const meta = eventMeta[event.type] || { label: event.type, family: "decision" };
      const typeClass = eventTypeClasses[event.type] || "event-type-other";
      const detailParts = [];
      if (event.order_id) detailParts.push(`订单 ${event.order_id}`);
      if (event.order_ids) detailParts.push(`${event.order_ids.length} 单`);
      if (event.courier_ids) detailParts.push(`${event.courier_ids.length} 名骑手`);
      if (event.business_area) detailParts.push(event.business_area);
      if (event.memory_id) detailParts.push(`记忆 ${event.memory_id}`);
      const detail = detailParts.join(" / ");
      return `
        <div class="list-item event-item ${escapeHtml(typeClass)}" data-event-type="${escapeHtml(event.type)}" data-event-sequence="${escapeHtml(event.sequence)}">
          <span class="event-tag" data-family="${escapeHtml(meta.family)}">${escapeHtml(meta.label)}</span>
          <div>
            <strong>${escapeHtml(event.time_label)} ${escapeHtml(meta.label)}</strong>
            <p>${escapeHtml(event.summary)}</p>
            ${detail ? `<p>${escapeHtml(detail)}</p>` : ""}
          </div>
        </div>
      `;
    }

    function renderStageRow(label, count, summary) {
      return `<div class="stage-row"><b>${escapeHtml(label)}</b><span>${escapeHtml(summary || "待处理")}</span><em>${escapeHtml(count)}</em></div>`;
    }

    function memoryItemsForSection(sectionId, byId = null) {
      const itemById = byId || Object.fromEntries(workbench.memory.items.map((item) => [item.id, item]));
      return (workbench.memory.sections[sectionId] || [])
        .map((id) => itemById[id])
        .filter(Boolean)
        .sort((a, b) => (b.latest_hit_time_s || 0) - (a.latest_hit_time_s || 0));
    }

    function memoryStats() {
      const items = workbench.memory.items;
      const totalConfidence = items.reduce((sum, item) => sum + (Number(item.confidence) || 0), 0);
      const totalRecalls = items.reduce((sum, item) => sum + (Number(item.recall_count) || 0), 0);
      const latest = items.reduce((selected, item) => !selected || item.latest_hit_time_s > selected.latest_hit_time_s ? item : selected, null);
      return {
        total: items.length,
        avgConfidence: items.length ? totalConfidence / items.length : 0,
        totalRecalls,
        latestHitLabel: latest?.latest_hit_time_label || "-",
        linkedDecisionCount: new Set(items.map((item) => item.linked_decision_id)).size
      };
    }

    function renderMemoryOverview(stats, system = {}) {
      const total = system.memory_count ?? stats.total;
      const avgConfidence = system.avg_confidence ?? stats.avgConfidence;
      const totalRecalls = system.recall_count ?? stats.totalRecalls;
      const latestHit = system.latest_hit_time_label || stats.latestHitLabel;
      return [
        renderMetricChip("memory-total", "长期记忆总量", `${total}`, "来自全天推演回放"),
        renderMetricChip("memory-confidence", "平均置信度", fmtNumber(avgConfidence, 2), "全局 / 画像 / 召回 / 反馈"),
        renderMetricChip("memory-recalls", "累计召回", `${totalRecalls}`, "评分前命中的历史经验"),
        renderMetricChip("memory-latest-hit", "最近命中", latestHit, `${system.linked_decision_count ?? stats.linkedDecisionCount} 个关联决策`)
      ].join("");
    }

    function renderMemoryLayerCard(layer) {
      const confidence = Number(layer.avg_confidence || 0);
      return `
        <article class="memory-layer-card" data-memory-layer="${escapeHtml(layer.id)}">
          <div class="memory-layer-top">
            <strong>${escapeHtml(layer.label)}</strong>
            <span class="memory-scope">${escapeHtml(displayMemoryScope(layer.scope))}</span>
          </div>
          <div class="memory-layer-meta">
            <span>${escapeHtml(layer.memory_count)} 条记忆</span>
            <span>${escapeHtml(layer.recall_count)} 次召回</span>
            <span>${escapeHtml(layer.latest_hit_time_label)}</span>
          </div>
          <p>${escapeHtml(layer.summary)}</p>
          <div class="memory-meter" style="--confidence:${clamp(confidence, 0, 1)}"><span></span></div>
          <p><b>用于调度：</b>${escapeHtml(layer.dispatch_use)}</p>
          <div class="memory-effect-line"><span>${escapeHtml(layer.effect)}</span></div>
        </article>
      `;
    }

    function renderMemoryProfile(profile) {
      return `
        <article class="memory-profile" data-memory-profile="${escapeHtml(profile.id)}" data-profile-type="${escapeHtml(profile.profile_type)}">
          <div class="memory-profile-top">
            <strong>${escapeHtml(profile.label)}</strong>
            <span class="memory-profile-type">${escapeHtml(displayProfileType(profile.profile_type))}</span>
          </div>
          <p>${escapeHtml(displayMemoryText(profile.context))}</p>
          <p><b>策略摘要：</b>${escapeHtml(displayMemoryText(profile.strategy))}</p>
          <div class="memory-profile-meta">
            <span>置信度 ${fmtNumber(profile.confidence || 0, 2)}</span>
            <span>最近命中 ${escapeHtml(profile.latest_hit_time_label)}</span>
          </div>
          <p>${escapeHtml(displayMemoryText(profile.dispatch_effect))}</p>
        </article>
      `;
    }

    function memoryItemsByIds(itemIds, byId, limit = 1) {
      return (itemIds || [])
        .map((id) => byId[id])
        .filter(Boolean)
        .slice(0, limit);
    }

    function renderMemoryRecallStep(step, byId, index) {
      const evidence = memoryItemsByIds(step.item_ids, byId, 1)[0];
      return `
        <article class="memory-flow-step" data-memory-chain-step="${escapeHtml(step.id)}">
          <div class="memory-flow-top">
            <strong>${escapeHtml(step.label)}</strong>
            <span class="memory-flow-index">${index + 1}</span>
          </div>
          <p>${escapeHtml(displayMemoryStepSummary(step))}</p>
          <p>${escapeHtml(displayMemoryText(step.evidence))}</p>
          ${renderMemoryEvidenceItem(evidence)}
        </article>
      `;
    }

    function renderMemoryWritebackStep(step, byId, index) {
      const evidence = memoryItemsByIds(step.item_ids, byId, 1)[0];
      const sectionId = step.id.replace("-memory", "");
      return `
        <article class="memory-flow-step" data-memory-section="${escapeHtml(sectionId)}" data-memory-loop-step="${escapeHtml(step.id)}">
          <div class="memory-flow-top">
            <strong>${escapeHtml(step.label)}</strong>
            <span class="memory-flow-index">${index + 1}</span>
          </div>
          <p>${escapeHtml(displayMemoryStepSummary(step))}</p>
          ${renderMemoryEvidenceItem(evidence)}
        </article>
      `;
    }

    function renderMemoryEvidenceItem(item) {
      if (!item) {
        return `<div class="memory-evidence"><p>等待推理产生可验证的记忆证据。</p></div>`;
      }
      return `
        <div class="memory-evidence" data-memory-id="${escapeHtml(item.id)}" data-memory-stage="${escapeHtml(item.stage)}" data-memory-scope="${escapeHtml(item.memory_scope || "")}">
          <div class="memory-evidence-head">
            <strong>${escapeHtml(item.latest_hit_time_label)} / ${escapeHtml(readableMemoryLabel(item.id))}</strong>
            <span>${escapeHtml(displayMemoryChannel(item.formation_channel || item.event_type))}</span>
          </div>
          <div class="memory-field-grid">
            ${renderMemoryField("触发场景", displayMemoryScenario(item.trigger_scenario))}
            ${renderMemoryField("上下文摘要", displayMemoryText(item.context_summary))}
            ${renderMemoryField("策略摘要", displayMemoryText(item.strategy_summary))}
            ${renderMemoryField("决策结果", displayDecisionSummary(item.decision_result))}
            ${renderMemoryField("效果反馈", displayMemoryText(item.effect_feedback))}
            ${renderMemoryField("最近命中时间", item.latest_hit_time_label)}
          </div>
          <div class="context-metric-grid">
            ${renderMetricChip(`${item.id}-confidence`, "置信度", fmtNumber(item.confidence, 2), `更新前 ${fmtNumber(item.confidence_before, 2)} / 更新后 ${fmtNumber(item.confidence_after, 2)}`)}
            ${renderMetricChip(`${item.id}-recall`, "召回次数", `${item.recall_count}`, recalledCaseText(item.recalled_case_ids))}
          </div>
        </div>
      `;
    }

    function renderMemoryRecallCard(item) {
      if (!item) return "";
      return `
        <div class="recall-card" data-memory-id="${escapeHtml(item.id)}" data-memory-recall="active">
          <strong>${escapeHtml(item.latest_hit_time_label)} / ${escapeHtml(displayMemoryScenario(item.trigger_scenario))}</strong>
          <p>${escapeHtml(displayMemoryText(item.strategy_summary))}</p>
          <div class="memory-meter" style="--confidence:${clamp(item.confidence, 0, 1)}"><span></span></div>
          <p>关联${escapeHtml(readableDecisionLabel(item.linked_decision_id))} / 召回 ${item.recall_count} 次</p>
        </div>
      `;
    }

    function renderMemoryField(label, value) {
      return `<div class="memory-field"><b>${escapeHtml(label)}</b><span>${escapeHtml(value || "-")}</span></div>`;
    }

    function renderMemoryItem(item) {
      if (!item) return "";
      return `
        <div class="list-item memory-item" data-memory-id="${escapeHtml(item.id)}" data-memory-stage="${escapeHtml(item.stage)}">
          <div class="memory-item-head">
            <strong>${escapeHtml(item.latest_hit_time_label)} / ${escapeHtml(readableMemoryLabel(item.id))}</strong>
            <span class="memory-stage" data-stage="${escapeHtml(item.stage)}">${escapeHtml(displayMemoryStage(item.stage))}</span>
          </div>
          <div class="memory-field-grid">
            ${renderMemoryField("触发场景", displayMemoryScenario(item.trigger_scenario))}
            ${renderMemoryField("上下文摘要", displayMemoryText(item.context_summary))}
            ${renderMemoryField("策略摘要", displayMemoryText(item.strategy_summary))}
            ${renderMemoryField("决策结果", displayDecisionSummary(item.decision_result))}
            ${renderMemoryField("效果反馈", displayMemoryText(item.effect_feedback))}
            ${renderMemoryField("最近命中时间", item.latest_hit_time_label)}
          </div>
          <div class="context-metric-grid">
            ${renderMetricChip(`${item.id}-confidence`, "置信度", fmtNumber(item.confidence, 2), `更新前 ${fmtNumber(item.confidence_before, 2)} / 更新后 ${fmtNumber(item.confidence_after, 2)}`)}
            ${renderMetricChip(`${item.id}-recall`, "召回次数", `${item.recall_count}`, recalledCaseText(item.recalled_case_ids))}
          </div>
          <div class="chip-list">
            <span class="data-chip">关联${escapeHtml(readableDecisionLabel(item.linked_decision_id))}</span>
            ${item.tags.map((tag) => `<span class="data-chip">${escapeHtml(displayTag(tag))}</span>`).join("")}
          </div>
        </div>
      `;
    }

    // ===== 长期记忆页 · 自主学习可视化 =====
    // 所有数字都在浏览器端由 workbench.decisions + workbench.memory.items 实时推导，
    // 不预置任何结论；场景按签名「时段|天气|拥堵|运力|冲击」归类，首遇=沉淀、复遇=召回。
    let memoryRoundsCache = null;
    let memoryCurveGeom = null;
    let memorySelectedSignature = null;
    const memoryReplay = { running: false, hasRun: false, raf: null, startedAt: 0, durationMs: 13000 };
    let memoryPipelineTimers = [];
    let memoryResizeHandler = null;

    // 真实召回打分权重，与 memory_engine._feature_similarity 一致（合计 1.0）。
    const memorySimilarityWeights = [
      ["场景ID", 0.22],
      ["时段类型", 0.18],
      ["天气", 0.14],
      ["订单压力", 0.14],
      ["运力压力", 0.10],
      ["接单意愿", 0.08],
      ["交通画像", 0.08],
      ["拥堵水平", 0.06]
    ];
    const memoryShockNames = {
      "S-rain-lunch": "降雨",
      "S-merchant-burst-lunch": "商家爆单",
      "S-road-dinner": "道路拥堵",
      "S-courier-night": "夜间缺人"
    };

    // 签名五维相似度：权重由真实召回权重按维度归并——
    // 时段 0.18｜天气 0.14｜拥堵 0.14(拥堵水平0.06+交通画像0.08)｜运力 0.18(运力压力0.10+接单意愿0.08)｜冲击 0.14(订单压力)，
    // 五维全同再加“同景加成”0.22（对应场景ID 权重），合计 1.0，与召回链路①的权重表同源。
    const memoryDimWeights = [0.18, 0.14, 0.14, 0.18, 0.14];
    const memoryTransferThreshold = 0.5;

    function memorySignatureSimilarity(sigA, sigB) {
      const a = String(sigA || "").split("|");
      const b = String(sigB || "").split("|");
      let sim = 0;
      let allMatch = true;
      for (let i = 0; i < 5; i += 1) {
        if ((a[i] || "") === (b[i] || "")) sim += memoryDimWeights[i];
        else allMatch = false;
      }
      if (allMatch) sim += 0.22;
      return Math.round(sim * 100) / 100;
    }

    const memorySignatureDimNames = ["时段", "天气", "拥堵", "运力", "冲击"];
    function memoryMatchedDims(sigA, sigB) {
      const a = String(sigA || "").split("|");
      const b = String(sigB || "").split("|");
      const dims = [];
      for (let i = 0; i < 5; i += 1) {
        if ((a[i] || "") === (b[i] || "")) dims.push(memorySignatureDimNames[i]);
      }
      return dims;
    }

    function memoryLearningRounds() {
      if (memoryRoundsCache) return memoryRoundsCache;
      const byId = Object.fromEntries(workbench.memory.items.map((item) => [item.id, item]));
      const decisions = [...workbench.decisions].sort((a, b) => a.trigger_time_s - b.trigger_time_s);
      const encounterBySig = new Map();
      const seenSignatures = [];
      const previousSignatures = [];
      const firstSeenLabelBySig = new Map();
      let prevCum = 0;
      memoryRoundsCache = decisions.map((decision, index) => {
        const linked = (decision.result_writeback.memory_event_ids || []).map((id) => byId[id]).filter(Boolean);
        const recall = linked.find((item) => item.event_type === "memory_recall") || null;
        const writeback = linked.find((item) => item.event_type === "memory_writeback") || null;
        const policy = linked.find((item) => item.event_type === "future_policy_shift") || null;
        const cumSaved = Number(decision.round_result.time_saved_min) || 0;
        const deltaSaved = Math.max(0, Math.round((cumSaved - prevCum) * 10) / 10);
        prevCum = cumSaved;
        const signature = recall ? recall.trigger_scenario : (writeback ? writeback.trigger_scenario : "unknown");
        const encounter = encounterBySig.has(signature) ? encounterBySig.get(signature) + 1 : 0;
        // 记忆状态四级（对齐 Mem0 / Generative Agents 的连续相关性检索，不做“有/无经验”二值化）：
        // 同景复遇（签名完全命中）/ 高相似迁移（最高相似 ≥ 0.5，旧经验当主力）/
        // 低相似借鉴（0 < 最高相似 < 0.5，旧经验只当辅助）/ 冷启动（当天无任何历史）。
        let state = "repeat";
        let transferFrom = null;
        let transferSim = 0;
        if (!encounterBySig.has(signature)) {
          for (const prevSig of seenSignatures) {
            const sim = memorySignatureSimilarity(signature, prevSig);
            if (sim > transferSim) { transferSim = sim; transferFrom = prevSig; }
          }
          state = transferSim >= memoryTransferThreshold ? "transfer" : (transferSim > 0 ? "partial" : "cold");
          seenSignatures.push(signature);
        }
        encounterBySig.set(signature, encounter);
        const matchedDims = transferFrom ? memoryMatchedDims(signature, transferFrom) : [];
        // 可借鉴经验池：强相关 = 相似度 ≥ 0.5（含同景），弱相关 = 0 < 相似度 < 0.5（仅部分维度匹配）。
        // 与召回机制同构：经验池是粗筛候选，注入的 Top-K 案例是精排结果。
        let similarPool = 0;
        let weakPool = 0;
        for (const prevSig of previousSignatures) {
          if (prevSig === signature) continue;
          const sim = memorySignatureSimilarity(signature, prevSig);
          if (sim >= memoryTransferThreshold) similarPool += 1;
          else if (sim > 0) weakPool += 1;
        }
        const experiencePool = { same: encounter, similar: similarPool, weak: weakPool, total: encounter + similarPool };
        if (!firstSeenLabelBySig.has(signature)) firstSeenLabelBySig.set(signature, decision.trigger_time_label);
        const firstSeenLabel = firstSeenLabelBySig.get(signature);
        previousSignatures.push(signature);
        return {
          index,
          decision,
          recall,
          writeback,
          policy,
          timeS: decision.trigger_time_s,
          timeLabel: decision.trigger_time_label,
          cumSaved,
          deltaSaved,
          signature,
          encounter,
          state,
          transferFrom,
          transferSim,
          matchedDims,
          experiencePool,
          firstSeenLabel,
          confidenceBefore: writeback ? Number(writeback.confidence_before) : null,
          confidenceAfter: policy ? Number(policy.confidence_after) : (writeback ? Number(writeback.confidence_after) : null),
          recalledCases: recall ? (recall.recalled_case_ids || []) : []
        };
      });
      return memoryRoundsCache;
    }

    const memoryStateLabels = { cold: "冷启动", partial: "低相似借鉴", transfer: "高相似迁移", repeat: "同景复遇" };

    function memoryRoundStateLabel(round) {
      if (!round) return "-";
      return memoryStateLabels[round.state] || round.state;
    }

    function memoryRoundShortState(round) {
      if (!round) return "-";
      if (round.state === "repeat") return `同景第 ${round.encounter} 次复遇`;
      return memoryRoundStateLabel(round);
    }

    function memoryRoundStateDetail(round) {
      if (!round) return "";
      if (round.state === "cold") return "当天首轮 · 记忆库为空";
      if (round.state === "partial" || round.state === "transfer") {
        const dims = (round.matchedDims || []).join("、") || "-";
        return `← ${memorySignatureTitle(round.transferFrom)} · 相似 ${fmtNumber(round.transferSim, 2)}（匹配：${dims}）`;
      }
      return `本景第 ${round.encounter} 次 · 首现 ${round.firstSeenLabel}`;
    }

    function memoryPoolText(round) {
      const pool = round && round.experiencePool;
      if (!pool) return "0 轮";
      if (!pool.total) {
        // 无强相关时展示弱相关，避免“低相似借鉴却写着可借鉴 0 轮”的自相矛盾。
        return pool.weak ? `弱相关 ${pool.weak} 轮（无 ≥0.5 强相关）` : "0 轮";
      }
      return `${pool.total} 轮（同景 ${pool.same} + 相似 ${pool.similar}）`;
    }

    function memorySignatureGroups() {
      const groups = new Map();
      for (const round of memoryLearningRounds()) {
        if (!groups.has(round.signature)) groups.set(round.signature, []);
        groups.get(round.signature).push(round);
      }
      return [...groups.entries()].map(([signature, rounds]) => ({
        signature,
        rounds,
        firstTimeS: rounds[0].timeS,
        totalSaved: Math.round(rounds.reduce((sum, r) => sum + r.deltaSaved, 0) * 10) / 10,
        reuseSaved: Math.round(rounds.slice(1).reduce((sum, r) => sum + r.deltaSaved, 0) * 10) / 10,
        peakConfidence: Math.max(0, ...rounds.map((r) => r.confidenceAfter || 0))
      })).sort((a, b) => a.firstTimeS - b.firstTimeS);
    }

    function memoryEvidence() {
      const rounds = memoryLearningRounds();
      if (!rounds.length) {
        return { rounds, coldRounds: [], partialRounds: [], lowRounds: [], transferRounds: [], repeatRounds: [], avgLow: 0, avgMemory: 0, gainRatio: 0, totalSaved: 0, memorySaved: 0, memoryShare: 0, confStart: 0, confPeak: 0, sceneCount: 0, itemCount: 0, bestRound: null };
      }
      const coldRounds = rounds.filter((r) => r.state === "cold");
      const partialRounds = rounds.filter((r) => r.state === "partial");
      const lowRounds = rounds.filter((r) => r.state === "cold" || r.state === "partial");
      const transferRounds = rounds.filter((r) => r.state === "transfer");
      const repeatRounds = rounds.filter((r) => r.state === "repeat");
      const memoryRounds = rounds.filter((r) => r.state === "transfer" || r.state === "repeat");
      const avgLow = lowRounds.length ? lowRounds.reduce((s, r) => s + r.deltaSaved, 0) / lowRounds.length : 0;
      const avgMemory = memoryRounds.length ? memoryRounds.reduce((s, r) => s + r.deltaSaved, 0) / memoryRounds.length : 0;
      const totalSaved = rounds[rounds.length - 1].cumSaved;
      const memorySaved = memoryRounds.reduce((s, r) => s + r.deltaSaved, 0);
      const bestRound = rounds.reduce((sel, r) => (r.deltaSaved > (sel ? sel.deltaSaved : -1) ? r : sel), null);
      return {
        rounds,
        coldRounds,
        partialRounds,
        lowRounds,
        transferRounds,
        repeatRounds,
        avgLow,
        avgMemory,
        gainRatio: avgLow > 0 ? avgMemory / avgLow : 0,
        totalSaved,
        memorySaved: Math.round(memorySaved * 10) / 10,
        memoryShare: totalSaved > 0 ? memorySaved / totalSaved * 100 : 0,
        confStart: rounds[0].confidenceBefore || 0,
        confPeak: Math.max(...rounds.map((r) => r.confidenceAfter || 0)),
        sceneCount: memorySignatureGroups().length,
        itemCount: workbench.memory.items.length,
        bestRound
      };
    }

    function memoryShockLabel(shockId) {
      return memoryShockNames[shockId] || displayShock(shockId) || shockId;
    }

    // 把连续含冲击的时间片合并成时间窗，重叠窗合并、标签取并集。
    function memoryShockWindows() {
      const slices = workbench.timeline.time_slices || [];
      const windows = [];
      let current = null;
      for (const slice of slices) {
        const shocks = slice.shock_ids || [];
        if (shocks.length) {
          if (!current) {
            current = { startS: slice.start_s, endS: slice.end_s, names: new Set() };
          } else {
            current.endS = slice.end_s;
          }
          shocks.forEach((id) => current.names.add(memoryShockLabel(id)));
        } else if (current) {
          windows.push(current);
          current = null;
        }
      }
      if (current) windows.push(current);
      return windows.map((w) => ({ startS: w.startS, endS: w.endS, label: [...w.names].join("+") }));
    }

    // 单个场景 token 的中文名（displayMemoryScenario 只翻译整串签名，这里补 token 级映射）。
    function memoryScenarioToken(token) {
      const labels = {
        breakfast: "早餐时段",
        lunch_peak: "午高峰",
        afternoon_tea: "下午茶",
        dinner_peak: "晚高峰",
        night_supply_gap: "夜间供给缺口",
        clear: "晴天",
        rain: "雨天",
        mixed: "混合天气",
        cloudy: "多云",
        low_congestion: "低拥堵",
        medium_congestion: "中拥堵",
        high_congestion: "高拥堵",
        scarce_supply: "运力偏紧",
        balanced_supply: "运力平衡",
        abundant_supply: "运力充足",
        steady: "无冲击"
      };
      return labels[token] || token;
    }

    function memorySignatureParts(signature) {
      const parts = String(signature || "").split("|");
      const shockPart = parts[4] || "steady";
      const shockText = shockPart === "steady"
        ? "无冲击"
        : shockPart.split(",").map((id) => memoryShockLabel(id)).join("+");
      return {
        phase: memoryScenarioToken(parts[0] || ""),
        weather: memoryScenarioToken(parts[1] || ""),
        congestion: memoryScenarioToken(parts[2] || ""),
        supply: memoryScenarioToken(parts[3] || ""),
        shock: shockText
      };
    }

    // 场景显示名：默认「时段 · 天气 · 拥堵」，但只要带冲击、或与其他签名前缀撞名，
    // 就必须把冲击维度带上——否则表里会出现两类场景同名、复遇计数看似矛盾的误导。
    let memoryTitleBySig = null;
    function memorySignatureTitle(signature) {
      if (!memoryTitleBySig) {
        memoryTitleBySig = new Map();
        const groups = memorySignatureGroups();
        const prefixCount = new Map();
        const prefixOf = (sig) => {
          const p = memorySignatureParts(sig);
          return `${p.phase} · ${p.weather} · ${p.congestion}`;
        };
        for (const group of groups) {
          const prefix = prefixOf(group.signature);
          prefixCount.set(prefix, (prefixCount.get(prefix) || 0) + 1);
        }
        for (const group of groups) {
          const p = memorySignatureParts(group.signature);
          const prefix = prefixOf(group.signature);
          const needShock = prefixCount.get(prefix) > 1 || p.shock !== "无冲击";
          memoryTitleBySig.set(group.signature, needShock ? `${prefix} · ${p.shock}` : prefix);
        }
      }
      return memoryTitleBySig.get(signature) || memorySignatureFull(signature);
    }

    function memorySignatureFull(signature) {
      const p = memorySignatureParts(signature);
      return `${p.phase} / ${p.weather} / ${p.congestion} / ${p.supply} / ${p.shock}`;
    }

    function memoryCaseName(caseId) {
      const text = String(caseId || "");
      if (text.startsWith("current-")) return "本轮新写入";
      const parts = text.split("-");
      const prefixLabels = { steady: "平稳", shock: "冲击", similar: "相似" };
      const prefix = prefixLabels[parts[0]] || parts[0];
      const scene = memoryScenarioToken(parts.slice(1, -1).join("-"));
      const num = parts[parts.length - 1];
      return `${prefix}·${scene} #${num}`;
    }

    function renderMemoryEvidenceTiles(evidence) {
      const ratioText = evidence.gainRatio > 0 ? `×${fmtNumber(evidence.gainRatio, 1)}` : "-";
      return `
        <div class="memory-evidence-tile" data-tone="gain">
          <span>全天累计节省</span>
          <b><span id="memory-tile-cum">${fmtNumber(evidence.totalSaved, 1)}</span> <em>分钟</em></b>
          <small>低经验开局仅 ${evidence.lowRounds.length} 轮（冷启动 ${evidence.coldRounds.length} + 低相似借鉴 ${evidence.partialRounds.length}）；记忆参与的 ${evidence.transferRounds.length + evidence.repeatRounds.length} 轮贡献 ${fmtNumber(evidence.memorySaved, 1)} 分钟（${fmtNumber(evidence.memoryShare, 0)}%）</small>
        </div>
        <div class="memory-evidence-tile" data-tone="gain">
          <span>记忆参与增益</span>
          <b id="memory-tile-gain">${ratioText}</b>
          <small>低经验开局均省 ${fmtNumber(evidence.avgLow, 1)} 分钟/轮 → 记忆参与（迁移+复遇）均省 ${fmtNumber(evidence.avgMemory, 1)} 分钟/轮</small>
        </div>
        <div class="memory-evidence-tile" data-tone="memory">
          <span>置信度学习轨迹</span>
          <b id="memory-tile-conf">${fmtNumber(evidence.confStart, 2)} → ${fmtNumber(evidence.confPeak, 2)}</b>
          <small>Reflexion 回写按每轮实际收益强化或抑制策略置信度</small>
        </div>
        <div class="memory-evidence-tile" data-tone="memory">
          <span>经验库规模</span>
          <b id="memory-tile-lib">${evidence.sceneCount} <em>类场景</em></b>
          <small><span id="memory-tile-lib-sub">${evidence.itemCount} 条记忆事件 · 冷启动 ${evidence.coldRounds.length} / 低相似借鉴 ${evidence.partialRounds.length} / 迁移 ${evidence.transferRounds.length} / 复遇 ${evidence.repeatRounds.length}</span></small>
        </div>
      `;
    }

    function renderMemoryRoundTable() {
      const rows = memoryLearningRounds().map((round) => `
        <tr data-round-index="${round.index}" title="点击反查曲线上的这一轮，再点一次取消">
          <td>${escapeHtml(round.timeLabel)}</td>
          <td>${escapeHtml(memorySignatureTitle(round.signature))}</td>
          <td>${escapeHtml(memoryRoundStateLabel(round))} <small>${escapeHtml(memoryRoundStateDetail(round))}</small></td>
          <td>${fmtSigned(round.deltaSaved, 1)}</td>
          <td>${fmtNumber(round.cumSaved, 1)}</td>
          <td>${fmtNumber(round.confidenceBefore, 2)} → ${fmtNumber(round.confidenceAfter, 2)}</td>
          <td>${escapeHtml(memoryPoolText(round))}</td>
        </tr>
      `).join("");
      return `
        <table class="memory-round-table">
          <thead><tr><th>时间</th><th>场景</th><th>记忆状态</th><th>本轮节省(分)</th><th>累计节省(分)</th><th>置信度回写</th><th>可借鉴经验</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    function renderMemoryMatrixRows() {
      const groups = memorySignatureGroups();
      const startS = workbench.timeline.start_s;
      const spanS = timelineSpanS();
      const maxDelta = Math.max(1, ...memoryLearningRounds().map((r) => r.deltaSaved));
      const selectedSig = memorySelectedSignature ?? (memoryEvidence().bestRound || {}).signature;
      return groups.map((group) => {
        const parts = memorySignatureParts(group.signature);
        const firstPct = (group.rounds[0].timeS - startS) / spanS * 100;
        const arcs = group.rounds.slice(1).map((round) => {
          const pct = (round.timeS - startS) / spanS * 100;
          const x1 = firstPct * 10;
          const x2 = pct * 10;
          const peakY = Math.max(6, 40 - Math.min(30, 8 + (x2 - x1) * 0.035));
          return `<path d="M ${x1.toFixed(1)} 40 Q ${((x1 + x2) / 2).toFixed(1)} ${peakY.toFixed(1)} ${x2.toFixed(1)} 40"></path>`;
        }).join("");
        const dots = group.rounds.map((round) => {
          const pct = (round.timeS - startS) / spanS * 100;
          const size = 8 + Math.sqrt(round.deltaSaved / maxDelta) * 13;
          const transferNote = round.state === "transfer" ? ` · 借用「${memorySignatureTitle(round.transferFrom)}」经验（相似 ${fmtNumber(round.transferSim, 2)}）` : "";
          const tip = `${round.timeLabel} · ${memoryRoundShortState(round)}${transferNote} · 可借鉴 ${memoryPoolText(round)} · 本轮 ${fmtSigned(round.deltaSaved, 1)} 分钟 · 置信度 ${fmtNumber(round.confidenceBefore, 2)}→${fmtNumber(round.confidenceAfter, 2)}`;
          return `<i class="memory-matrix-dot" data-state="${escapeHtml(round.state)}" data-time-s="${round.timeS}" style="left:${pct.toFixed(2)}%;width:${size.toFixed(1)}px;height:${size.toFixed(1)}px;" title="${escapeHtml(tip)}"></i>`;
        }).join("");
        const firstRound = group.rounds[0];
        let openLabel;
        if (firstRound.state === "transfer") {
          openLabel = `高相似迁移开局 ${firstRound.timeLabel} ← ${memorySignatureTitle(firstRound.transferFrom)}`;
        } else if (firstRound.state === "partial") {
          openLabel = `低相似借鉴开局 ${firstRound.timeLabel} ← ${memorySignatureTitle(firstRound.transferFrom)}（相似 ${fmtNumber(firstRound.transferSim, 2)}）`;
        } else {
          openLabel = `冷启动开局 ${firstRound.timeLabel}`;
        }
        return `
          <div class="memory-matrix-row" data-signature="${escapeHtml(group.signature)}" data-selected="${group.signature === selectedSig ? 1 : 0}" role="button" tabindex="0" aria-label="${escapeHtml(memorySignatureFull(group.signature))}">
            <div class="memory-matrix-name">
              <strong>${escapeHtml(memorySignatureTitle(group.signature))}</strong>
              <span>${escapeHtml(`${parts.supply} · ${openLabel} · 复遇 ${group.rounds.length - 1} 次`)}</span>
            </div>
            <div class="memory-matrix-lane">
              <svg class="lane-arcs" viewBox="0 0 1000 52" preserveAspectRatio="none" aria-hidden="true">${arcs}</svg>
              <div class="lane-base"></div>
              ${dots}
            </div>
            <div class="memory-matrix-total">
              <b>${fmtSigned(group.totalSaved, 1)} 分钟</b>
              <span>复用贡献 ${fmtNumber(group.reuseSaved, 1)} 分 · 置信峰值 ${fmtNumber(group.peakConfidence, 2)}</span>
            </div>
          </div>
        `;
      }).join("");
    }

    function renderMemoryMatrixAxis() {
      const startS = workbench.timeline.start_s;
      const endS = workbench.timeline.end_s;
      const spanS = timelineSpanS();
      const ticks = [];
      for (let ts = startS; ts <= endS; ts += 7200) {
        ticks.push(`<span style="left:${((ts - startS) / spanS * 100).toFixed(2)}%">${clock(ts)}</span>`);
      }
      return ticks.join("");
    }

    function memoryDistinctPolicyRules() {
      const counts = new Map();
      for (const round of memoryLearningRounds()) {
        const rule = round.policy ? round.policy.strategy_summary : "";
        if (!rule) continue;
        const entry = counts.get(rule) || { rule, count: 0, peakConfidence: 0 };
        entry.count += 1;
        entry.peakConfidence = Math.max(entry.peakConfidence, round.policy.confidence_after || 0);
        counts.set(rule, entry);
      }
      return [...counts.values()].sort((a, b) => b.count - a.count);
    }

    function renderMemoryHierarchy() {
      const evidence = memoryEvidence();
      const policyRules = memoryDistinctPolicyRules();
      const profileCount = (workbench.memory.profiles || []).length;
      const topRules = policyRules.slice(0, 3).map((entry) => `
        <div class="rule-item">
          <b>${escapeHtml(displayMemoryText(entry.rule))}</b>
          <span>命中 ${entry.count} 轮 · 置信峰值 ${fmtNumber(entry.peakConfidence, 2)}</span>
        </div>
      `).join("");
      return `
        <p class="memory-lead-note">记忆不是流水账：原始经历被逐层提炼，复遇场景召回的是已提炼的画像与策略，而不是重放全部原始事件——Read 一条顶多条，检索既快又稳。</p>
        <div class="memory-funnel">
          <div class="memory-funnel-tier" data-tier="episodic">
            <div class="tier-head"><strong>情景记忆 · 原始决策事件</strong><b>${evidence.itemCount} 条</b></div>
            <p>每轮派单沉淀召回 / 回写 / 策略三类事件，保留完整现场：场景、动作与结果。</p>
            <span class="tier-op">Write 逐轮写入</span>
          </div>
          <div class="memory-funnel-tier" data-tier="semantic">
            <div class="tier-head"><strong>语义记忆 · 场景画像</strong><b>${evidence.sceneCount} 类</b></div>
            <p>相似轮次被归纳成场景签名画像，并派生骑手 / 商圈 / 订单 ${profileCount} 类画像记忆。</p>
            <span class="tier-op">Reflection 归纳</span>
          </div>
          <div class="memory-funnel-tier" data-tier="policy">
            <div class="tier-head"><strong>策略记忆 · 全局先验</strong><b>${policyRules.length} 条</b></div>
            <p>跨时段仍然成立的调度规则，进入 Planner 前作为全局先验直接注入。</p>
            <span class="tier-op">Reflection 提炼</span>
          </div>
        </div>
        <p class="memory-hierarchy-note">下面是命中最多的全局策略，右侧标注它在全天被复用的轮数：</p>
        <div class="memory-rule-list">${topRules}</div>
      `;
    }

    function memoryPipelineRound() {
      const groups = memorySignatureGroups();
      if (!groups.length) return null;
      const fallbackSig = (memoryEvidence().bestRound || groups[0].rounds[0]).signature;
      const sig = memorySelectedSignature || fallbackSig;
      const group = groups.find((g) => g.signature === sig) || groups[0];
      const repeats = group.rounds.filter((r) => r.encounter > 0);
      const pool = repeats.length ? repeats : group.rounds;
      return pool.reduce((sel, r) => (r.deltaSaved > (sel ? sel.deltaSaved : -1) ? r : sel), null);
    }

    function renderMemoryPipeline() {
      const round = memoryPipelineRound();
      const host = document.getElementById("memory-pipeline");
      const caption = document.getElementById("memory-pipeline-caption");
      if (!host || !round) return;
      if (caption) {
        caption.textContent = `${round.timeLabel} 决策轮 · ${memorySignatureTitle(round.signature)} · ${memoryRoundShortState(round)}`;
      }
      const maxWeight = memorySimilarityWeights[0][1];
      const simBars = memorySimilarityWeights.map(([label, weight]) => `
        <div class="memory-sim-bar">
          <span>${escapeHtml(label)}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${(weight / maxWeight * 100).toFixed(0)}%"></div></div>
          <b>${(weight * 100).toFixed(0)}%</b>
        </div>
      `).join("");
      const caseChips = round.recalledCases.map((id) => `<span data-case-id="${escapeHtml(id)}" title="点击定位该案例来自哪类场景经验，再点一次取消高亮" role="button" tabindex="0">${escapeHtml(memoryCaseName(id))}</span>`).join("")
        || "<span>暂无历史案例</span>";
      let recallLead;
      if (round.state === "cold") {
        recallLead = `当天首轮，场景库为空（冷启动），命中的是跨天记忆库里的 ${round.recalledCases.length} 条历史案例：`;
      } else if (round.state === "partial") {
        recallLead = `低相似借鉴：旧经验只有「${(round.matchedDims || []).join("、")}」维度接得上（最高相似 ${fmtNumber(round.transferSim, 2)}），以本轮新沉淀为主、旧经验为辅；另有 ${round.experiencePool.weak} 轮弱相关可参考：`;
      } else if (round.state === "transfer") {
        recallLead = `高相似迁移：该签名当天首次出现，可借鉴经验 ${memoryPoolText(round)}；从中按相似度精选 Top-${round.recalledCases.length} 注入：`;
      } else {
        recallLead = `同景第 ${round.encounter} 次复遇，可借鉴经验 ${memoryPoolText(round)}；粗筛后按相似度精选 Top-${round.recalledCases.length} 注入：`;
      }
      const sourceChipOf = (srcRound, prefix) => `<span class="memory-transfer-chip" data-signature-link="${escapeHtml(srcRound.transferFrom)}" title="点击定位它借用的场景经验行，再点一次取消高亮" role="button" tabindex="0">${prefix} ← ${escapeHtml(memorySignatureTitle(srcRound.transferFrom))} · 相似 ${fmtNumber(srcRound.transferSim, 2)}</span>`;
      let transferChip = "";
      if (round.state === "transfer") {
        transferChip = sourceChipOf(round, "高相似迁移");
      } else if (round.state === "partial") {
        transferChip = sourceChipOf(round, "低相似借鉴");
      } else {
        // 该场景若是“高相似迁移/低相似借鉴开局”，即使当前展示的是后续复遇轮，也把开局来源亮出来（可点击回跳）。
        const group = memorySignatureGroups().find((g) => g.signature === round.signature);
        const originRound = group ? group.rounds[0] : null;
        if (originRound && originRound.state === "transfer") {
          transferChip = sourceChipOf(originRound, `开局高相似迁移 ${escapeHtml(originRound.timeLabel)}`);
        } else if (originRound && originRound.state === "partial") {
          transferChip = sourceChipOf(originRound, `开局低相似借鉴 ${escapeHtml(originRound.timeLabel)}`);
        }
      }
      const strategyText = round.recall ? displayMemoryText(round.recall.strategy_summary) : "-";
      const policyText = round.policy ? displayMemoryText(round.policy.strategy_summary) : "-";
      const actionCount = (round.decision.final_actions || []).length;
      host.innerHTML = `
        <article class="memory-pipe-stage" data-stage="encode" data-active="0">
          <div class="pipe-step-head"><strong>① 场景编码</strong><em>元数据过滤</em></div>
          <p>${escapeHtml(memorySignatureFull(round.signature))}</p>
          <div class="memory-sim-bars">${simBars}</div>
          <p>按以上真实权重计算与历史场景的加权相似度，相似度 ≤ 0 的经验直接过滤。</p>
        </article>
        <article class="memory-pipe-stage" data-stage="recall" data-active="0">
          <div class="pipe-step-head"><strong>② 相似经验召回</strong><em>Read · Top-K</em></div>
          <p>${escapeHtml(recallLead)}</p>
          <div class="memory-case-chips">${transferChip}${caseChips}</div>
          <p>记忆注入时机：候选算法评分之前，作为决策上下文的一部分。</p>
        </article>
        <article class="memory-pipe-stage" data-stage="decide" data-active="0">
          <div class="pipe-step-head"><strong>③ 决策执行</strong><em>Generator-Critic</em></div>
          <p>${escapeHtml(strategyText)}</p>
          <div class="memory-pipe-result">
            <span>本轮派出 ${actionCount} 个动作</span>
            <b>较基线节省 ${fmtSigned(round.deltaSaved, 1)} 分钟</b>
          </div>
        </article>
        <article class="memory-pipe-stage" data-stage="writeback" data-active="0">
          <div class="pipe-step-head"><strong>④ 结果回写</strong><em>Reflexion · Write</em></div>
          <div class="memory-conf-shift">
            <span>${fmtNumber(round.confidenceBefore, 2)}</span>
            <span class="conf-arrow">→</span>
            <span>${fmtNumber(round.confidenceAfter, 2)}</span>
          </div>
          <div class="memory-conf-track"><span style="--conf:${clamp(round.confidenceAfter || 0, 0, 1)}"></span></div>
          <p>按本轮真实收益更新策略置信度，再提炼一条全局策略：</p>
          <p>${escapeHtml(policyText)}</p>
        </article>
      `;
      playMemoryPipeline();
    }

    function playMemoryPipeline() {
      const stages = [...document.querySelectorAll("#memory-pipeline .memory-pipe-stage")];
      memoryPipelineTimers.forEach(clearTimeout);
      memoryPipelineTimers = [];
      stages.forEach((stage) => { stage.dataset.active = "0"; });
      const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      stages.forEach((stage, index) => {
        const delay = reduced ? 0 : 120 + index * 430;
        memoryPipelineTimers.push(setTimeout(() => { stage.dataset.active = "1"; }, delay));
      });
    }

    // --- 学习曲线（单一 X 轴，上下两个面板避免双轴误读） ---
    function buildMemoryCurveSvg(width) {
      const rounds = memoryLearningRounds();
      const startS = workbench.timeline.start_s;
      const endS = workbench.timeline.end_s;
      const mL = 48;
      const mR = 20;
      const mT = 30;
      const hA = 188;
      const gapAB = 36;
      const hB = 60;
      const hX = 26;
      const height = mT + hA + gapAB + hB + hX;
      const plotW = Math.max(120, width - mL - mR);
      const x = (t) => mL + (t - startS) / Math.max(1, endS - startS) * plotW;
      const maxCum = Math.max(100, ...rounds.map((r) => r.cumSaved));
      const yMax = Math.ceil(maxCum / 100) * 100;
      const yA = (v) => mT + hA - v / yMax * hA;
      const bTop = mT + hA + gapAB;
      const yB = (v) => bTop + hB - (clamp(v, 0.5, 1) - 0.5) / 0.5 * hB;
      const pieces = [];

      // 网格与坐标
      const gridTicks = [];
      for (let v = 0; v <= yMax; v += yMax / 4) {
        gridTicks.push(`<line class="curve-grid" x1="${mL}" y1="${yA(v)}" x2="${mL + plotW}" y2="${yA(v)}"></line>`);
        gridTicks.push(`<text class="curve-axis-text" x="${mL - 7}" y="${yA(v) + 3.5}" text-anchor="end">${fmtNumber(v, 0)}</text>`);
      }
      [0.5, 0.75, 1].forEach((v) => {
        gridTicks.push(`<line class="curve-grid" x1="${mL}" y1="${yB(v)}" x2="${mL + plotW}" y2="${yB(v)}"></line>`);
        gridTicks.push(`<text class="curve-axis-text" x="${mL - 7}" y="${yB(v) + 3.5}" text-anchor="end">${v.toFixed(2)}</text>`);
      });
      for (let ts = startS; ts <= endS; ts += 7200) {
        gridTicks.push(`<text class="curve-axis-text" x="${x(ts)}" y="${height - 8}" text-anchor="middle">${clock(ts)}</text>`);
      }
      pieces.push(gridTicks.join(""));

      // 冲击时段底纹（跨两个面板）
      for (const win of memoryShockWindows()) {
        const x1 = x(win.startS);
        const x2 = x(win.endS);
        pieces.push(`<rect class="shock-band" x="${x1}" y="${mT}" width="${Math.max(2, x2 - x1)}" height="${hA + gapAB + hB}"></rect>`);
        pieces.push(`<text class="shock-label" x="${(x1 + x2) / 2}" y="${mT + 13}" text-anchor="middle">${escapeHtml(win.label)}</text>`);
      }

      // 面板标题
      pieces.push(`<text class="curve-panel-label" x="${mL}" y="16">累计节省（分钟）｜我方 vs 贪心基线</text>`);
      pieces.push(`<text class="curve-panel-label" x="${mL}" y="${bTop - 9}">记忆置信度（Reflexion 回写后）</text>`);

      if (rounds.length) {
        const first = rounds[0];
        const last = rounds[rounds.length - 1];
        // 冷启动与平峰说明
        if (first.timeS - startS > 3600) {
          pieces.push(`<text class="curve-note" x="${(x(startS) + x(first.timeS)) / 2}" y="${yA(yMax * 0.45)}" text-anchor="middle">冷启动 · 记忆库为空</text>`);
        }
        let gapStart = null;
        let gapLen = 0;
        for (let i = 1; i < rounds.length; i += 1) {
          const gap = rounds[i].timeS - rounds[i - 1].timeS;
          if (gap > gapLen) { gapLen = gap; gapStart = rounds[i - 1]; }
        }
        if (gapStart && gapLen > 5400) {
          pieces.push(`<text class="curve-note" x="${x(gapStart.timeS + gapLen / 2)}" y="${yA(gapStart.cumSaved) - 12}" text-anchor="middle">平峰期 · 无高峰决策轮</text>`);
        }

        // 累计节省面积 + 折线（含起点 0 与收尾平延）
        const savedPts = [[x(startS), yA(0)], ...rounds.map((r) => [x(r.timeS), yA(r.cumSaved)]), [x(endS), yA(last.cumSaved)]];
        const lineD = savedPts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
        const areaD = `${lineD} L ${x(endS).toFixed(1)} ${yA(0)} L ${x(startS).toFixed(1)} ${yA(0)} Z`;
        // 置信度线 + 淡面积
        const confPts = rounds.filter((r) => r.confidenceAfter != null).map((r) => [x(r.timeS), yB(r.confidenceAfter)]);
        const confD = confPts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
        const confAreaD = confPts.length
          ? `${confD} L ${confPts[confPts.length - 1][0].toFixed(1)} ${bTop + hB} L ${confPts[0][0].toFixed(1)} ${bTop + hB} Z`
          : "";
        const best = memoryEvidence().bestRound;
        const dots = rounds.map((r) => {
          const halo = best && r.index === best.index
            ? `<circle class="round-dot-halo" cx="${x(r.timeS).toFixed(1)}" cy="${yA(r.cumSaved).toFixed(1)}" r="9"></circle>`
            : "";
          return `${halo}<circle class="round-dot" data-state="${r.state}" cx="${x(r.timeS).toFixed(1)}" cy="${yA(r.cumSaved).toFixed(1)}" r="4.5"></circle>`;
        }).join("");

        pieces.push(`
          <clipPath id="memory-reveal"><rect id="memory-reveal-rect" x="0" y="0" width="${width}" height="${height}"></rect></clipPath>
          <g clip-path="url(#memory-reveal)">
            <path class="saved-area" d="${areaD}"></path>
            <path class="saved-line" d="${lineD}"></path>
            ${confAreaD ? `<path class="conf-area" d="${confAreaD}"></path>` : ""}
            ${confD ? `<path class="conf-line" d="${confD}"></path>` : ""}
            ${dots}
          </g>
        `);

        // 终点直标 + 高光轮标注
        pieces.push(`<text class="curve-endpoint-label" x="${x(endS) - 4}" y="${yA(last.cumSaved) - 8}" text-anchor="end">${fmtNumber(last.cumSaved, 0)} 分钟</text>`);
        if (confPts.length) {
          const lastConf = rounds.filter((r) => r.confidenceAfter != null).pop();
          pieces.push(`<text class="curve-endpoint-label" x="${x(endS) - 4}" y="${yB(lastConf.confidenceAfter) - 7}" text-anchor="end">${fmtNumber(lastConf.confidenceAfter, 2)}</text>`);
        }
        if (best) {
          const bx = x(best.timeS);
          const by = yA(best.cumSaved);
          const anchorEnd = bx > mL + plotW * 0.62;
          const tx = anchorEnd ? bx - 10 : bx + 10;
          const bestState = memoryRoundShortState(best);
          pieces.push(`<line class="curve-callout-line" x1="${bx}" y1="${by - 8}" x2="${bx}" y2="${by - 30}"></line>`);
          pieces.push(`
            <text class="curve-callout-text" x="${tx}" y="${by - 50}" text-anchor="${anchorEnd ? "end" : "start"}">
              <tspan x="${tx}" dy="0">${escapeHtml(memorySignatureTitle(best.signature))}</tspan>
              <tspan x="${tx}" dy="14">${escapeHtml(`${bestState} · 召回记忆后单轮 ${fmtSigned(best.deltaSaved, 1)} 分钟`)}</tspan>
            </text>
          `);
        }
      }

      // 十字线与回放游标（初始隐藏）
      pieces.push(`<line id="memory-crosshair" class="crosshair-line" x1="0" y1="${mT}" x2="0" y2="${bTop + hB}" style="display:none"></line>`);
      pieces.push(`
        <g id="memory-playhead" style="display:none">
          <line class="playhead-line" x1="0" y1="${mT - 6}" x2="0" y2="${bTop + hB}"></line>
          <circle class="playhead-knob" cx="0" cy="${mT - 10}" r="5"></circle>
        </g>
      `);

      memoryCurveGeom = {
        width,
        height,
        mL,
        mR,
        mT,
        plotW,
        startS,
        endS,
        bottomY: bTop + hB,
        xOf: x,
        roundXs: rounds.map((r) => ({ x: x(r.timeS), y: yA(r.cumSaved), round: r }))
      };
      return `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img">${pieces.join("")}</svg>`;
    }

    function drawMemoryCurve() {
      const stage = document.getElementById("memory-curve");
      if (!stage) return;
      const tooltip = document.getElementById("memory-curve-tooltip");
      const width = Math.max(320, stage.clientWidth || 960);
      [...stage.querySelectorAll("svg")].forEach((node) => node.remove());
      stage.insertAdjacentHTML("beforeend", buildMemoryCurveSvg(width));
      if (tooltip) stage.appendChild(tooltip);
      // SVG 重建后光环随之消失，同步清掉选中状态
      memoryLinkState.curveRound = null;
    }

    function memoryNearestRoundItem(clientX) {
      const stage = document.getElementById("memory-curve");
      if (!stage || !memoryCurveGeom || !memoryCurveGeom.roundXs.length) return null;
      const rect = stage.getBoundingClientRect();
      const px = clientX - rect.left;
      let nearest = memoryCurveGeom.roundXs[0];
      for (const item of memoryCurveGeom.roundXs) {
        if (Math.abs(item.x - px) < Math.abs(nearest.x - px)) nearest = item;
      }
      return { nearest, px };
    }

    function showMemoryRoundTooltip(item) {
      const stage = document.getElementById("memory-curve");
      const tooltip = document.getElementById("memory-curve-tooltip");
      const crosshair = document.getElementById("memory-crosshair");
      if (!stage || !tooltip || !crosshair || !item) return;
      const rect = stage.getBoundingClientRect();
      const round = item.round;
      crosshair.style.display = "";
      crosshair.setAttribute("x1", item.x);
      crosshair.setAttribute("x2", item.x);
      tooltip.dataset.open = "1";
      tooltip.innerHTML = `
        <div class="tip-title">
          <span>${escapeHtml(round.timeLabel)} · 第 ${round.index + 1} 轮</span>
          <span class="tip-badge" data-state="${escapeHtml(round.state)}">${escapeHtml(memoryRoundShortState(round))}</span>
        </div>
        <div class="tip-scene">${escapeHtml(memorySignatureFull(round.signature))}</div>
        ${(round.state === "transfer" || round.state === "partial") ? `<div class="tip-row"><i class="tip-key" data-series="transfer"></i>${round.state === "transfer" ? "迁移来源" : "借鉴来源"} <b>${escapeHtml(`${memorySignatureTitle(round.transferFrom)} · 相似 ${fmtNumber(round.transferSim, 2)}（匹配：${(round.matchedDims || []).join("、") || "-"}）`)}</b></div>` : ""}
        <div class="tip-row"><i class="tip-key" data-series="saved"></i>本轮新增节省 <b>${fmtSigned(round.deltaSaved, 1)} 分钟</b></div>
        <div class="tip-row"><i class="tip-key" data-series="saved"></i>累计节省 <b>${fmtNumber(round.cumSaved, 1)} 分钟</b></div>
        <div class="tip-row"><i class="tip-key" data-series="conf"></i>置信度回写 <b>${fmtNumber(round.confidenceBefore, 2)} → ${fmtNumber(round.confidenceAfter, 2)}</b></div>
        <div class="tip-row"><i class="tip-key" data-series="transfer"></i>可借鉴经验 <b>${escapeHtml(memoryPoolText(round))}</b></div>
        <div class="tip-row"><i class="tip-key" data-series="conf"></i>精选注入 <b>Top-${round.recalledCases.length}</b></div>
      `;
      const tipW = tooltip.offsetWidth || 230;
      const flip = item.x + tipW + 26 > rect.width;
      tooltip.style.left = `${flip ? Math.max(4, item.x - tipW - 14) : item.x + 14}px`;
      tooltip.style.top = "34px";
    }

    function memoryCurvePointerMove(event) {
      const found = memoryNearestRoundItem(event.clientX);
      if (found) showMemoryRoundTooltip(found.nearest);
    }

    function memoryCurvePointerLeave() {
      const tooltip = document.getElementById("memory-curve-tooltip");
      const crosshair = document.getElementById("memory-crosshair");
      if (tooltip) tooltip.dataset.open = "0";
      if (crosshair) crosshair.style.display = "none";
    }

    // --- 跨模块双向索引：曲线点 ↔ 数据表行、召回案例 → 场景经验行 ---
    // 所有联动高亮都是「切换」语义：点一下=持续高亮，再点同一目标=取消恢复原状，点别的目标=切换。
    let memoryFlashTimers = [];
    const memoryLinkState = { tableRow: null, curveRound: null, matrixKey: null };

    function clearMemoryTableHighlight() {
      for (const row of document.querySelectorAll('.memory-round-table tr[data-flash="1"]')) row.dataset.flash = "0";
      memoryLinkState.tableRow = null;
    }

    // 曲线点被点击 → 展开数据表、滚到对应行并持续高亮；再点同一个点则取消
    function focusMemoryTableRow(roundIndex) {
      if (memoryLinkState.tableRow === roundIndex) {
        clearMemoryTableHighlight();
        return;
      }
      const wrap = document.querySelector(".memory-round-table-wrap");
      if (wrap && !wrap.open) wrap.open = true;
      const row = document.querySelector(`.memory-round-table tr[data-round-index="${roundIndex}"]`);
      const scroller = document.querySelector(".memory-round-table-wrap .table-scroll");
      if (!row || !scroller) return;
      clearMemoryTableHighlight();
      scroller.scrollTop = Math.max(0, row.offsetTop - scroller.clientHeight / 2 + row.clientHeight / 2);
      if (wrap) wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
      row.dataset.flash = "1";
      memoryLinkState.tableRow = roundIndex;
    }

    function clearMemoryCurveHighlight() {
      const svg = document.querySelector("#memory-curve svg");
      const halo = svg ? svg.querySelector(".memory-focus-halo") : null;
      if (halo) halo.remove();
      memoryCurvePointerLeave();
      memoryLinkState.curveRound = null;
    }

    // 数据表行被点击 → 曲线滚入视野、对应点持续光环 + 十字线 + tooltip；再点同一行则取消
    function pulseMemoryCurveDot(item) {
      const svg = document.querySelector("#memory-curve svg");
      if (!svg || !item) return;
      const old = svg.querySelector(".memory-focus-halo");
      if (old) old.remove();
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("class", "memory-focus-halo");
      circle.setAttribute("cx", item.x);
      circle.setAttribute("cy", item.y);
      circle.setAttribute("r", 10);
      svg.appendChild(circle);
    }

    function focusMemoryCurveRound(roundIndex) {
      if (!memoryCurveGeom) return;
      if (memoryLinkState.curveRound === roundIndex) {
        clearMemoryCurveHighlight();
        return;
      }
      const item = memoryCurveGeom.roundXs.find((entry) => entry.round.index === roundIndex);
      if (!item) return;
      const stage = document.getElementById("memory-curve");
      if (stage) stage.scrollIntoView({ behavior: "smooth", block: "center" });
      showMemoryRoundTooltip(item);
      pulseMemoryCurveDot(item);
      memoryLinkState.curveRound = roundIndex;
      // tooltip 短暂展示后自动收起（悬停可再看），光环作为选中态持续保留直到取消
      memoryFlashTimers.push(setTimeout(memoryCurvePointerLeave, 3800));
    }

    // 召回案例 → 它来自哪类场景经验：按案例前缀解析维度反查签名
    // steady-<时段>=该时段无冲击场景；shock-<时段>=该时段冲击场景；similar-<天气>=同天气场景
    function memoryCaseTargets(caseId) {
      const text = String(caseId || "");
      if (!text || text.startsWith("current-")) return [];
      const parts = text.split("-");
      const prefix = parts[0];
      const middle = parts.slice(1, -1).join("-");
      return memorySignatureGroups().filter((group) => {
        const sigParts = String(group.signature).split("|");
        if (prefix === "steady") return sigParts[0] === middle && (sigParts[4] || "steady") === "steady";
        if (prefix === "shock") return sigParts[0] === middle && (sigParts[4] || "steady") !== "steady";
        if (prefix === "similar") return sigParts[1] === middle;
        return false;
      }).map((group) => group.signature);
    }

    function clearMemoryMatrixHighlight() {
      for (const row of document.querySelectorAll('.memory-matrix-row[data-flash="1"]')) row.dataset.flash = "0";
      memoryLinkState.matrixKey = null;
    }

    // 芯片被点击 → 来源场景行持续高亮；再点同一枚芯片则取消
    function focusMemoryMatrixRows(signatures) {
      if (!signatures.length) return;
      const key = signatures.join("||");
      if (memoryLinkState.matrixKey === key) {
        clearMemoryMatrixHighlight();
        return;
      }
      const rows = signatures
        .map((sig) => document.querySelector(`.memory-matrix-row[data-signature="${CSS.escape(sig)}"]`))
        .filter(Boolean);
      if (!rows.length) return;
      clearMemoryMatrixHighlight();
      rows[0].scrollIntoView({ behavior: "smooth", block: "center" });
      rows.forEach((row) => { row.dataset.flash = "1"; });
      memoryLinkState.matrixKey = key;
    }

    // --- 回放：从 07:00 扫到 23:00，看记忆从零累积、收益随复遇放大 ---
    function applyMemoryReplayTime(simTimeS, finished) {
      const geom = memoryCurveGeom;
      if (!geom) return;
      const rounds = memoryLearningRounds();
      const px = geom.xOf(simTimeS);
      const revealRect = document.getElementById("memory-reveal-rect");
      if (revealRect) revealRect.setAttribute("width", finished ? geom.width : Math.max(0, px));
      const playhead = document.getElementById("memory-playhead");
      if (playhead) {
        playhead.style.display = finished ? "none" : "";
        const line = playhead.querySelector("line");
        const knob = playhead.querySelector("circle");
        if (line) { line.setAttribute("x1", px); line.setAttribute("x2", px); }
        if (knob) knob.setAttribute("cx", px);
      }
      setText("memory-replay-clock", finished ? "" : clock(simTimeS));
      const seen = rounds.filter((r) => r.timeS <= simTimeS || finished);
      const lastSeen = seen.length ? seen[seen.length - 1] : null;
      const seenSigs = new Set(seen.map((r) => r.signature));
      setText("memory-tile-cum", fmtNumber(lastSeen ? lastSeen.cumSaved : 0, 1));
      const evidence = memoryEvidence();
      const confPeakSeen = seen.length ? Math.max(...seen.map((r) => r.confidenceAfter || 0)) : 0;
      setText("memory-tile-conf", seen.length ? `${fmtNumber(evidence.confStart, 2)} → ${fmtNumber(confPeakSeen, 2)}` : "—");
      const libTile = document.getElementById("memory-tile-lib");
      if (libTile) libTile.firstChild.textContent = String(seenSigs.size);
      const seenLow = seen.filter((r) => r.state === "cold" || r.state === "partial").length;
      const seenTransfer = seen.filter((r) => r.state === "transfer").length;
      const seenRepeat = seen.filter((r) => r.state === "repeat").length;
      setText("memory-tile-lib-sub", `${seen.length * 3} 条记忆事件 · 冷启动/低相似借鉴 ${seenLow} / 迁移 ${seenTransfer} / 复遇 ${seenRepeat}`);
      for (const dot of document.querySelectorAll(".memory-matrix-dot")) {
        dot.dataset.hidden = !finished && Number(dot.dataset.timeS) > simTimeS ? "1" : "0";
      }
    }

    function stopMemoryReplay(jumpToEnd) {
      memoryReplay.running = false;
      if (memoryReplay.raf) cancelAnimationFrame(memoryReplay.raf);
      memoryReplay.raf = null;
      const btn = document.getElementById("memory-replay-btn");
      if (btn) { btn.dataset.state = "idle"; btn.textContent = memoryReplay.hasRun ? "↻ 重新回放" : "▶ 回放全天学习过程"; }
      if (jumpToEnd) applyMemoryReplayTime(workbench.timeline.end_s, true);
    }

    function startMemoryReplay() {
      const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (memoryReplay.running || reduced) {
        memoryReplay.hasRun = true;
        stopMemoryReplay(true);
        return;
      }
      memoryReplay.hasRun = true;
      memoryReplay.running = true;
      memoryReplay.startedAt = performance.now();
      const btn = document.getElementById("memory-replay-btn");
      if (btn) { btn.dataset.state = "running"; btn.textContent = "⏸ 播放中 · 点击跳到结果"; }
      const tick = (now) => {
        if (!memoryReplay.running) return;
        const progress = clamp((now - memoryReplay.startedAt) / memoryReplay.durationMs, 0, 1);
        const simTimeS = workbench.timeline.start_s + progress * timelineSpanS();
        applyMemoryReplayTime(simTimeS, progress >= 1);
        if (progress >= 1) {
          stopMemoryReplay(false);
        } else {
          memoryReplay.raf = requestAnimationFrame(tick);
        }
      };
      memoryReplay.raf = requestAnimationFrame(tick);
    }

    function hydrateMemoryPage() {
      drawMemoryCurve();
      renderMemoryPipeline();
      const stage = document.getElementById("memory-curve");
      if (stage) {
        stage.addEventListener("pointermove", memoryCurvePointerMove);
        stage.addEventListener("pointerleave", memoryCurvePointerLeave);
        stage.addEventListener("click", (event) => {
          const found = memoryNearestRoundItem(event.clientX);
          if (found && Math.abs(found.nearest.x - found.px) <= 24) {
            focusMemoryTableRow(found.nearest.round.index);
          }
        });
      }
      const tableWrap = document.querySelector(".memory-round-table-wrap");
      if (tableWrap) {
        tableWrap.addEventListener("click", (event) => {
          const row = event.target.closest("tr[data-round-index]");
          if (row) focusMemoryCurveRound(Number(row.dataset.roundIndex));
        });
      }
      const replayBtn = document.getElementById("memory-replay-btn");
      if (replayBtn) replayBtn.addEventListener("click", startMemoryReplay);
      const pipelineBtn = document.getElementById("memory-pipeline-replay");
      if (pipelineBtn) pipelineBtn.addEventListener("click", playMemoryPipeline);
      const pipelineHost = document.getElementById("memory-pipeline");
      if (pipelineHost) {
        pipelineHost.addEventListener("click", (event) => {
          const link = event.target.closest("[data-signature-link]");
          if (link) { focusMemoryMatrixRows([link.dataset.signatureLink]); return; }
          const chip = event.target.closest("[data-case-id]");
          if (chip) focusMemoryMatrixRows(memoryCaseTargets(chip.dataset.caseId));
        });
        pipelineHost.addEventListener("keydown", (event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          const link = event.target.closest("[data-signature-link]");
          if (link) { event.preventDefault(); focusMemoryMatrixRows([link.dataset.signatureLink]); return; }
          const chip = event.target.closest("[data-case-id]");
          if (chip) { event.preventDefault(); focusMemoryMatrixRows(memoryCaseTargets(chip.dataset.caseId)); }
        });
      }
      const matrix = document.getElementById("memory-matrix");
      if (matrix) {
        matrix.addEventListener("click", (event) => {
          const row = event.target.closest(".memory-matrix-row");
          if (!row) return;
          if (memorySelectedSignature === row.dataset.signature) {
            // 再点已选中的行 → 取消选择，召回链路恢复默认场景
            memorySelectedSignature = null;
            const defaultSig = (memoryEvidence().bestRound || {}).signature;
            for (const item of matrix.querySelectorAll(".memory-matrix-row")) {
              item.dataset.selected = item.dataset.signature === defaultSig ? "1" : "0";
            }
            renderMemoryPipeline();
            return;
          }
          memorySelectedSignature = row.dataset.signature;
          for (const item of matrix.querySelectorAll(".memory-matrix-row")) {
            item.dataset.selected = item === row ? "1" : "0";
          }
          renderMemoryPipeline();
        });
        matrix.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            const row = event.target.closest(".memory-matrix-row");
            if (row) { event.preventDefault(); row.click(); }
          }
        });
      }
      memoryResizeHandler = () => {
        const curveStage = document.getElementById("memory-curve");
        if (!curveStage) return;
        const nextWidth = Math.max(320, curveStage.clientWidth || 960);
        if (memoryCurveGeom && Math.abs(nextWidth - memoryCurveGeom.width) < 4) return;
        stopMemoryReplay(true);
        drawMemoryCurve();
        applyMemoryReplayTime(workbench.timeline.end_s, true);
      };
      window.addEventListener("resize", memoryResizeHandler);
    }

    function teardownMemoryPage() {
      memoryReplay.running = false;
      if (memoryReplay.raf) cancelAnimationFrame(memoryReplay.raf);
      memoryReplay.raf = null;
      memoryPipelineTimers.forEach(clearTimeout);
      memoryPipelineTimers = [];
      memoryFlashTimers.forEach(clearTimeout);
      memoryFlashTimers = [];
      memoryLinkState.tableRow = null;
      memoryLinkState.curveRound = null;
      memoryLinkState.matrixKey = null;
      if (memoryResizeHandler) {
        window.removeEventListener("resize", memoryResizeHandler);
        memoryResizeHandler = null;
      }
    }

    function orderTimeBandById(timeBandId) {
      return workbench.filters.order_time_bands.find((item) => item.id === timeBandId) || null;
    }

    function orderMatchesFilters(order) {
      const band = orderTimeBandById(orderFilterState.timeBand);
      const inBand = !band || (order.created_at_s >= band.start_s && order.created_at_s <= band.end_s);
      const inArea = orderFilterState.area === "all" || order.business_area === orderFilterState.area;
      const inRisk = orderFilterState.risk === "all" || order.risk_level === orderFilterState.risk;
      const inStatus = orderFilterState.status === "all"
        || order.status === orderFilterState.status
        || (orderFilterState.status === "entered_inference" && order.entered_inference);
      return inBand && inArea && inRisk && inStatus;
    }

    function filteredOrders() {
      return workbench.entities.orders.filter(orderMatchesFilters);
    }

    function riderMatchesFilters(rider) {
      const inArea = riderFilterState.area === "all" || rider.business_area === riderFilterState.area;
      const inState = riderFilterState.state === "all" || rider.online_state === riderFilterState.state;
      return inArea && inState;
    }

    function filteredRiders() {
      return workbench.entities.riders.filter(riderMatchesFilters);
    }

    function renderOrdersOverview(orders) {
      const entered = orders.filter((order) => order.entered_inference).length;
      const highRisk = orders.filter((order) => order.risk_level === "high").length;
      const assigned = orders.filter((order) => order.our_result.state === "assigned").length;
      const improved = orders.filter((order) => {
        const ours = Number(order.our_result.eta_min);
        const baseline = Number(order.baseline_result.eta_min);
        return Number.isFinite(ours) && Number.isFinite(baseline) && ours < baseline;
      }).length;
      return [
        renderMetricChip("orders-visible", "当前可见", `${orders.length}`, `全天 ${workbench.entities.orders.length} 单`),
        renderMetricChip("orders-entered", "已进入推理", `${entered}`, "按下单时间释放"),
        renderMetricChip("orders-high-risk", "高风险", `${highRisk}`, "优先保护承诺送达"),
        renderMetricChip("orders-improved", "已见改善", `${improved}/${assigned}`, "我方预计更快")
      ].join("");
    }

    function orderEtaAdvantage(order) {
      const ours = Number(order.our_result?.eta_min);
      const baseline = Number(order.baseline_result?.eta_min);
      if (!Number.isFinite(ours) || !Number.isFinite(baseline)) return 0;
      return baseline - ours;
    }

    function orderFocusScore(order) {
      const riskWeight = order.risk_level === "high" ? 100 : order.risk_level === "medium" ? 45 : 0;
      const enteredWeight = order.entered_inference ? 20 : 0;
      return riskWeight + enteredWeight + Math.max(0, orderEtaAdvantage(order));
    }

    function renderOrderFocusList(orders) {
      const focusOrders = [...orders]
        .sort((left, right) => orderFocusScore(right) - orderFocusScore(left) || left.created_at_s - right.created_at_s)
        .slice(0, 6);
      if (!focusOrders.length) {
        return `<div class="list-item"><strong>当前筛选无订单</strong><p>调整时间段、商圈、状态或风险筛选。</p></div>`;
      }
      return focusOrders.map((order) => {
        const etaGain = orderEtaAdvantage(order);
        const advantage = etaGain > 0 ? `我方预计快 ${fmtNumber(etaGain, 1)} 分钟` : "等待对比结果";
        return `
          <article class="order-focus-card" data-order-focus="${escapeHtml(order.id)}" data-risk="${escapeHtml(order.risk_level)}">
            <div class="focus-card-top">
              <strong>${escapeHtml(order.id)}</strong>
              <span class="focus-badge">${escapeHtml(displayRisk(order.risk_level))}</span>
            </div>
            <p>${escapeHtml(order.merchant_label)} / ${escapeHtml(order.business_area)}</p>
            <p>${escapeHtml(order.created_at_label)} 下单，${escapeHtml(order.promised_at_label)} 前送达。</p>
            <p>${escapeHtml(advantage)}；${order.entered_inference ? "已进入推理" : "等待按时间释放"}。</p>
            <div class="chip-list">
              <span class="data-chip">基线 ${escapeHtml(displayStatus(order.baseline_result?.state || "scheduled"))}</span>
              <span class="data-chip">我方 ${escapeHtml(displayStatus(order.our_result?.state || "scheduled"))}</span>
            </div>
          </article>
        `;
      }).join("");
    }

    function countBy(items, keyFn) {
      return items.reduce((counts, item) => {
        const key = keyFn(item) || "-";
        counts[key] = (counts[key] || 0) + 1;
        return counts;
      }, {});
    }

    function renderCountChips(counts, limit = 6, labelFn = null) {
      const rows = Object.entries(counts).sort((left, right) => right[1] - left[1]).slice(0, limit);
      if (!rows.length) return `<p>当前筛选无数据</p>`;
      return `<div class="chip-list">${rows.map(([key, value]) => `<span class="data-chip">${escapeHtml(labelFn ? labelFn(key) : key)} ${value}</span>`).join("")}</div>`;
    }

    function renderOrderTimeLane(orders) {
      const maxCount = Math.max(...workbench.filters.order_time_bands.map((band) => orders.filter((order) => order.created_at_s >= band.start_s && order.created_at_s <= band.end_s).length), 1);
      return `
        <div class="time-lane">
          ${workbench.filters.order_time_bands.map((band) => {
            const count = orders.filter((order) => order.created_at_s >= band.start_s && order.created_at_s <= band.end_s).length;
            return `
              <div class="time-lane-item" data-order-time-band="${escapeHtml(band.id)}">
                <b>${escapeHtml(displayDemandPhase(band.id))}</b>
                <div class="lane-bar" style="--weight:${count / maxCount}"><span></span></div>
                <span>${count}</span>
              </div>
            `;
          }).join("")}
        </div>
      `;
    }

    function renderOrdersContext(orders) {
      const riskCounts = countBy(orders, (order) => order.risk_level);
      const areaCounts = countBy(orders, (order) => order.business_area);
      const statusCounts = countBy(orders, (order) => order.entered_inference ? "entered_inference" : order.status);
      return `
        <div class="card-head"><h3>需求概览</h3><span id="orders-context-count">${orders.length} 单可见</span></div>
        <div class="card-body order-context-list">
          <div class="list-item" id="orders-time-distribution"><strong>释放节奏</strong>${renderOrderTimeLane(orders)}</div>
          <div class="list-item" id="orders-area-distribution"><strong>商圈热度</strong>${renderCountChips(areaCounts)}</div>
          <div class="list-item" id="orders-risk-distribution"><strong>风险结构</strong>${renderCountChips(riskCounts, 6, displayRisk)}</div>
          <div class="list-item" id="orders-status-distribution"><strong>推理进度</strong>${renderCountChips(statusCounts, 6, displayStatus)}<p>订单全集只用于解释推理，不作为数据维护主叙事。</p></div>
        </div>
      `;
    }

    function renderAlgorithmResult(result) {
      if (!result || result.state !== "assigned") {
        return `<div class="result-pair"><b>未释放</b><span>${escapeHtml(candidateLabel(result?.algorithm_id || "-"))}</span></div>`;
      }
      return `
        <div class="result-pair">
          <b>${escapeHtml(result.courier_id)} / ${fmtNumber(result.eta_min, 1)} 分钟</b>
          <span>${fmtNumber(result.expected_cost_yuan, 1)} 元 / 风险 ${fmtNumber(result.timeout_risk, 3)}</span>
        </div>
      `;
    }

    function hydrateOrdersPage() {
      for (const control of document.querySelectorAll("[data-order-filter]")) {
        control.addEventListener("change", () => {
          orderFilterState[control.dataset.orderFilter] = control.value;
          updateOrdersView();
        });
      }
      updateOrdersView();
    }

    function updateOrdersView() {
      const orders = filteredOrders();
      const overview = document.getElementById("orders-overview");
      if (overview) overview.innerHTML = renderOrdersOverview(orders);
      const priority = document.getElementById("orders-priority-list");
      if (priority) priority.innerHTML = renderOrderFocusList(orders);
      const body = document.getElementById("orders-table-body");
      if (body) body.innerHTML = orders.map(renderOrderRow).join("") || `<tr><td colspan="7">当前筛选无订单，调整时间段、商圈、状态或风险。</td></tr>`;
      const context = document.getElementById("orders-context-panel");
      if (context) context.innerHTML = renderOrdersContext(orders);
      setText("orders-result-count", `${orders.length} / ${workbench.entities.orders.length} 单`);
    }

    function renderCoverageCards(counts, total, limit = 5) {
      const rows = Object.entries(counts).sort((left, right) => right[1] - left[1]).slice(0, limit);
      if (!rows.length) return `<p>当前筛选无区域供给。</p>`;
      const max = Math.max(...rows.map((row) => row[1]), 1);
      return `
        <div class="coverage-grid">
          ${rows.map(([area, value]) => `
            <div class="coverage-card" data-coverage-area="${escapeHtml(area)}">
              <b>${escapeHtml(area)}</b>
              <div class="coverage-bar" style="--coverage:${value / max}"><span></span></div>
              <p>${value} 名骑手 / 可见供给 ${fmtNumber(value / Math.max(1, total) * 100, 1)}%</p>
            </div>
          `).join("")}
        </div>
      `;
    }

    function renderRidersOverview(riders) {
      const busy = riders.filter((rider) => rider.online_state === "busy").length;
      const available = riders.filter((rider) => rider.online_state === "available").length;
      const ending = riders.filter((rider) => rider.online_state === "ending_shift").length;
      const avgLoad = riders.length ? riders.reduce((sum, rider) => sum + rider.current_load / Math.max(1, rider.capacity), 0) / riders.length : 0;
      return [
        renderMetricChip("riders-visible", "当前可见", `${riders.length}`, `全天 ${workbench.entities.riders.length} 名`),
        renderMetricChip("riders-available", "可接单", `${available}`, "可进入候选集合"),
        renderMetricChip("riders-busy", "配送中", `${busy}`, `${ending} 名临近下线`),
        renderMetricChip("riders-avg-load", "平均负载", fmtNumber(avgLoad, 2), "当前负载 / 容量")
      ].join("");
    }

    function riderFocusScore(rider) {
      const stateWeight = rider.online_state === "available" ? 70 : rider.online_state === "busy" ? 42 : rider.online_state === "ending_shift" ? 12 : 0;
      const loadRatio = rider.current_load / Math.max(1, rider.capacity);
      return stateWeight + (1 - loadRatio) * 30 + Math.min(12, rider.task_chain_size);
    }

    function renderRiderFocusList(riders) {
      const focusRiders = [...riders]
        .sort((left, right) => riderFocusScore(right) - riderFocusScore(left) || left.id.localeCompare(right.id))
        .slice(0, 6);
      if (!focusRiders.length) {
        return `<div class="list-item"><strong>当前筛选无骑手</strong><p>调整区域或在线状态筛选。</p></div>`;
      }
      return focusRiders.map((rider) => {
        const loadRatio = clamp(rider.current_load / Math.max(1, rider.capacity), 0, 1);
        return `
          <article class="rider-focus-card" data-rider-focus="${escapeHtml(rider.id)}" data-state="${escapeHtml(rider.online_state)}">
            <div class="focus-card-top">
              <strong>骑手 ${escapeHtml(rider.id)}</strong>
              <span class="focus-badge">${escapeHtml(displayRiderState(rider.online_state))}</span>
            </div>
            <div class="rider-load" style="--load:${loadRatio}"><span></span></div>
            <p>${escapeHtml(rider.business_area)} / 班次 ${escapeHtml(rider.shift_label)}</p>
            <p>当前负载 ${rider.current_load}/${rider.capacity}；${escapeHtml(rider.estimated_free_at_label)} 预计空闲；任务链 ${rider.task_chain_size} 单。</p>
          </article>
        `;
      }).join("");
    }

    function renderRidersContext(riders) {
      const stateCounts = countBy(riders, (rider) => rider.online_state);
      const areaCounts = countBy(riders, (rider) => rider.business_area);
      const topChains = [...riders].sort((left, right) => right.task_chain_size - left.task_chain_size).slice(0, 5);
      return `
        <div class="card-head"><h3>区域覆盖与班次压力</h3><span id="riders-context-count">${riders.length} 名可见</span></div>
        <div class="card-body rider-context-list">
          <div class="list-item" id="rider-state-distribution"><strong>在线状态</strong>${renderCountChips(stateCounts, 6, displayRiderState)}</div>
          <div class="list-item" id="rider-area-distribution"><strong>区域覆盖</strong>${renderCoverageCards(areaCounts, riders.length)}</div>
          <div class="list-item" id="rider-chain-focus">
            <strong>任务链较长</strong>
            ${topChains.length ? topChains.map((rider) => `<p>骑手 ${escapeHtml(rider.id)} / ${rider.task_chain_size} 单任务 / ${escapeHtml(rider.estimated_free_at_label)} 空闲</p>`).join("") : "<p>当前筛选无骑手</p>"}
          </div>
        </div>
      `;
    }

    function hydrateRidersPage() {
      for (const control of document.querySelectorAll("[data-rider-filter]")) {
        control.addEventListener("change", () => {
          riderFilterState[control.dataset.riderFilter] = control.value;
          updateRidersView();
        });
      }
      updateRidersView();
    }

    function updateRidersView() {
      const riders = filteredRiders();
      const overview = document.getElementById("riders-overview");
      if (overview) overview.innerHTML = renderRidersOverview(riders);
      const focus = document.getElementById("riders-capacity-list");
      if (focus) focus.innerHTML = renderRiderFocusList(riders);
      const board = document.getElementById("rider-resource-board");
      if (board) board.innerHTML = riders.slice(0, 8).map(renderRiderCard).join("") || `<div class="list-item"><strong>当前筛选无骑手</strong><p>调整区域或在线状态筛选。</p></div>`;
      const context = document.getElementById("rider-context-panel");
      if (context) context.innerHTML = renderRidersContext(riders);
      setText("riders-result-count", `${riders.length} / ${workbench.entities.riders.length} 名骑手`);
    }

    function renderOrderRow(order) {
      return `
        <tr data-order-id="${escapeHtml(order.id)}" data-order-status="${escapeHtml(order.status)}" data-order-risk="${escapeHtml(order.risk_level)}" data-order-area="${escapeHtml(order.business_area)}">
          <td>${escapeHtml(order.id)}</td>
          <td>${escapeHtml(order.merchant_label)}<br><span>${escapeHtml(order.business_area)}</span></td>
          <td>${escapeHtml(order.created_at_label)} 下单<br><span>${escapeHtml(order.promised_at_label)} 承诺送达</span></td>
          <td><span class="badge" data-state="${escapeHtml(order.status)}">${escapeHtml(displayStatus(order.status))}</span><br><span class="badge" data-risk="${escapeHtml(order.risk_level)}">${escapeHtml(displayRisk(order.risk_level))}</span></td>
          <td>${order.entered_inference ? "已进入" : "等待释放"}</td>
          <td>${renderAlgorithmResult(order.baseline_result)}</td>
          <td>${renderAlgorithmResult(order.our_result)}</td>
        </tr>
      `;
    }

    function renderRiderMiniMap(rider) {
      const linkedOrders = rider.mini_map.linked_order_ids.map((orderId) => orderIndex[orderId]).filter(Boolean).slice(0, 4);
      const riderMapLabel = mapEntityLabel("rider", rider);
      return `
        <div class="mini-map" data-rider-mini-map="${escapeHtml(rider.id)}">
          <span class="map-dot" data-kind="home" title="驻点" style="--x:${rider.mini_map.home.screen_x};--y:${rider.mini_map.home.screen_y}"></span>
          <span class="map-dot" data-kind="rider" data-map-ref="${escapeHtml(riderMapLabel)}" title="${escapeHtml(mapEntityTitle("rider", riderMapLabel, {phase: rider.online_state}))}" style="--x:${rider.position.screen_x};--y:${rider.position.screen_y}"></span>
          ${linkedOrders.map((order) => {
            const orderMapLabel = mapEntityLabel("order", order);
            return `<span class="map-dot" data-kind="linked-order" data-map-ref="${escapeHtml(orderMapLabel)}" title="${escapeHtml(mapEntityTitle("order", orderMapLabel, {risk_level: order.risk_level}))}" style="--x:${order.dropoff_position.screen_x};--y:${order.dropoff_position.screen_y}"></span>`;
          }).join("")}
        </div>
      `;
    }

    function renderRiderCard(rider) {
      const loadRatio = clamp(rider.current_load / Math.max(1, rider.capacity), 0, 1);
      return `
        <article class="card rider-card" data-rider-id="${escapeHtml(rider.id)}" data-state="${escapeHtml(rider.online_state)}" data-area="${escapeHtml(rider.business_area)}">
          <div class="card-head"><h3>骑手 ${escapeHtml(rider.id)}</h3><span>${escapeHtml(displayRiderState(rider.online_state))} / ${escapeHtml(rider.business_area)}</span></div>
          <div class="card-body">
            ${renderRiderMiniMap(rider)}
            <div class="rider-load" style="--load:${loadRatio}"><span></span></div>
            <div class="compact-list">
              <div class="list-item"><strong>班次与负载</strong><p>${escapeHtml(rider.shift_label)} / ${rider.current_load}/${rider.capacity} / ${escapeHtml(rider.estimated_free_at_label)} 空闲</p></div>
              <div class="list-item"><strong>当前任务链 ${rider.task_chain_size} 单</strong><p>${rider.task_chain.slice(0, 5).map((item) => `${item.order_id}(${fmtNumber(item.eta_min, 1)}分钟)`).join(", ") || "暂无任务"}</p></div>
              <div class="list-item"><strong>历史表现摘要</strong><p>${escapeHtml(displayRiderPerformance(rider.performance.summary))} / 接单意愿 ${fmtNumber(rider.performance.willingness, 2)}</p></div>
            </div>
          </div>
        </article>
      `;
    }

    function isShortcutInputTarget(target) {
      return Boolean(target?.closest?.("input, textarea, select, a, [contenteditable='true']"));
    }

    function isNativePauseButtonTarget(target) {
      return target?.closest?.("button")?.id === "pause-inference";
    }

    function handleGlobalPlaybackShortcut(event) {
      if (event.repeat || (event.code !== "Space" && event.key !== " ")) return;
      if (isShortcutInputTarget(event.target)) return;
      if (isNativePauseButtonTarget(event.target)) return;
      if (document.body.dataset.route !== "live") return;
      if (!document.querySelector("[data-page='live']")) return;
      const inferenceFinished = inferenceState.started && inferenceState.currentTimeS >= workbench.timeline.end_s;
      if (inferenceFinished && !inferenceState.running) return;
      event.preventDefault();
      toggleInferencePause();
    }

    function bootstrapDispatchWorkbench() {
      renderNav();
      renderTopbarStats();
      setRoute(routeFromHash());
      window.addEventListener("hashchange", () => setRoute(routeFromHash()));
      window.addEventListener("keydown", handleGlobalPlaybackShortcut);
    }

    document.addEventListener("DOMContentLoaded", bootstrapDispatchWorkbench);
    window.__DISPATCH_WORKBENCH__ = {
      boot: dispatchBoot,
      workbench,
      routeFromHash,
      setRoute,
      renderRoute,
      renderLivePage,
      renderDecisionsPage,
      renderDecisionTimeline,
      renderDecisionReasoning,
      renderDecisionContext,
      renderDecisionAdvantageHero,
      renderDecisionStepFlow,
      renderDecisionPlanComparison,
      hydrateDecisionPage,
      selectDecisionRound,
      renderMemoryPage,
      memoryStats,
      memoryItemsForSection,
      renderMemoryLayerCard,
      renderMemoryProfile,
      renderMemoryRecallStep,
      renderMemoryWritebackStep,
      renderMemoryEvidenceItem,
      renderMemoryRecallCard,
      renderMemoryItem,
      renderOrdersPage,
      hydrateOrdersPage,
      updateOrdersView,
      filteredOrders,
      orderFilterState,
      renderOrderFocusList,
      renderOrdersOverview,
      renderOrdersContext,
      renderRidersPage,
      hydrateRidersPage,
      updateRidersView,
      filteredRiders,
      riderFilterState,
      renderCoverageCards,
      renderRiderFocusList,
      renderRidersOverview,
      renderRidersContext,
      renderLiveCumulativeMetrics,
      inferenceState,
      startInference,
      toggleInferencePause,
      setInferenceSpeed,
      setInferenceMode,
      setInferenceTime,
      seekInferenceTime,
      advanceInferenceTick,
      scoreForTime,
      decisionForTime,
      releasedEvents
    };
  </script>
</body>
</html>
"""
    return template.replace("__BOOT_JSON__", boot_json)
