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
      display: grid;
      grid-template-columns: max-content max-content minmax(74px, .22fr) minmax(124px, .34fr) minmax(118px, .30fr) minmax(560px, 1fr);
      position: relative;
      top: auto;
      z-index: 7;
      align-items: stretch;
      box-shadow: var(--shadow-card);
    }
    .live-control-dock .primary-button,
    .live-control-dock .ghost-button,
    .live-control-dock .select-control {
      min-height: 58px;
      min-width: 0;
      padding-inline: 10px;
      white-space: nowrap;
    }
    .live-control-dock .runtime-strip {
      min-width: 0;
      width: 100%;
      grid-template-columns: repeat(6, minmax(76px, 1fr));
    }
    .live-control-dock .inference-progress {
      grid-column: 1 / -1;
    }
    .runtime-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
      width: 100%;
    }
    .runtime-cell {
      min-height: 58px;
      min-width: 0;
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
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .runtime-cell span {
      color: var(--muted);
      font: 700 10px var(--mono);
      letter-spacing: .05em;
      text-transform: uppercase;
    }
    /* 推演时间要完整显示 HH:MM:SS，不做省略号截断 */
    .live-control-dock .runtime-strip { grid-template-columns: repeat(6, minmax(84px, 1fr)); }
    .runtime-cell[data-runtime="clock"] b {
      font-size: 13px;
      letter-spacing: -.02em;
      overflow: visible;
      text-overflow: clip;
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
    .map-panel {
      height: var(--live-map-panel-height, 640px);
      min-height: 360px;
      max-height: min(94vh, 1800px);
      position: relative;
      display: grid;
      grid-template-rows: auto 16px minmax(0, 1fr) 18px;
    }
    .map-resize-handle-top { cursor: ns-resize; }
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
    .map-panel .real-map-stage,
    .map-panel .schematic-map {
      height: auto;
      min-height: 360px;
      margin: 14px 14px 0;
    }
    .card-head-tools { display: flex; align-items: center; gap: 10px; }
    .map-fullscreen-btn {
      border: 1px solid var(--line-strong);
      background: #fff;
      color: var(--ink-2);
      border-radius: 999px;
      padding: 4px 11px;
      font: 700 12px var(--font);
      white-space: nowrap;
    }
    .map-fullscreen-btn:hover { border-color: var(--accent); color: var(--accent-2); box-shadow: var(--shadow-tight); }
    /* 全屏：地图面板铺满整个视口，评委看得更清楚；ESC / 再点退出回到小窗口 */
    .map-panel:fullscreen, .map-panel:-webkit-full-screen {
      width: 100vw; height: 100vh; max-height: none; min-height: 0;
      border-radius: 0; padding: 0; background: var(--surface);
      grid-template-rows: auto minmax(0, 1fr);
    }
    .map-panel:fullscreen .map-resize-handle,
    .map-panel:-webkit-full-screen .map-resize-handle { display: none; }
    .map-panel:fullscreen, .map-panel:-webkit-full-screen { grid-template-rows: auto minmax(0, 1fr); }
    .map-panel:fullscreen .card-head,
    .map-panel:-webkit-full-screen .card-head { padding: 12px 18px; }
    .map-resize-handle {
      height: 18px;
      display: grid;
      place-items: center;
      color: var(--muted);
      background: linear-gradient(180deg, rgba(255,255,255,.64), rgba(248,250,252,.92));
      cursor: ns-resize;
      touch-action: none;
      user-select: none;
    }
    .map-resize-handle::before {
      width: 54px;
      height: 4px;
      border-radius: 999px;
      background: #cbd5e1;
      content: "";
    }
    .map-resize-handle:hover::before,
    .map-resize-handle:focus-visible::before {
      background: var(--accent);
    }
    .map-panel[data-resizing-map="true"] {
      user-select: none;
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
    .legend-swatch[data-lane="active-progress"] {
      background: repeating-linear-gradient(90deg, #059669 0 5px, transparent 5px 9px);
      height: 4px;
    }
    /* 已送达路线：成功绿细虚线、半透明（刚送达的淡出痕迹）*/
    .legend-swatch[data-lane="completed-route"] {
      background: repeating-linear-gradient(90deg, rgba(22,163,74,.5) 0 4px, transparent 4px 8px);
      height: 3px;
      border-radius: 2px;
    }
    .legend-swatch[data-lane="pickup"] {
      background: repeating-linear-gradient(90deg, #ea580c 0 7px, transparent 7px 11px);
      height: 4px;
      border-radius: 2px;
    }
    .legend-swatch[data-lane="pending-link"] {
      background: repeating-linear-gradient(90deg, #4f46e5 0 2px, transparent 2px 6px);
      height: 4px;
      border-radius: 2px;
    }
    .legend-dot[data-kind="merchant"] { background: var(--blue); border-radius: 2px; }
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
      stroke-width: 3.4;
      stroke-linecap: round;
      opacity: .95;
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
    /* 取餐段：骑手 → 商家（橙色粗虚线）；配送段沿用 ours 实线绿 */
    .route-line[data-lane="pickup"] {
      stroke: #ea580c;
      stroke-width: 3.2;
      stroke-dasharray: 4 3;
      stroke-linecap: round;
      opacity: .95;
    }
    /* 已送达：成功绿细虚线、半透明（不用灰，灰会和灰底糊在一起）*/
    .route-line[data-lane="completed-route"] {
      stroke: #16a34a;
      stroke-width: 2.2;
      stroke-dasharray: 3 5;
      stroke-linecap: round;
      opacity: .5;
    }
    /* 待派单订单的“商家⋯客户”关系连线（下单后、派单前，靛蓝点线）*/
    .route-line[data-lane="pending-link"] {
      stroke: #4f46e5;
      stroke-width: 2.4;
      stroke-dasharray: .5 3.4;
      stroke-linecap: round;
      opacity: .92;
    }
    .route-assignment-label {
      fill: #12352f;
      stroke: rgba(255,255,255,.94);
      stroke-width: .62;
      paint-order: stroke;
      font: 800 2.15px var(--mono);
      letter-spacing: 0;
      pointer-events: none;
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
    /* 商家=取餐点，用圆角方块与圆形的骑手/客户区分开 */
    .map-dot[data-kind="merchant"] { --size: 13px; background: var(--blue); border-radius: 4px; }
    .map-dot[data-kind="rider"] { --size: 14px; background: var(--accent); }
    /* 空闲骑手：空心青环（待命），与实心+动效的“配送中”骑手区分 */
    .map-dot[data-kind="rider"][data-motion="idle"] { background: #fff; box-shadow: 0 0 0 2px var(--accent), 0 4px 10px rgba(15,23,42,.14); opacity: .82; }
    .map-dot[data-kind="order"] { --size: 10px; background: var(--amber); }
    .map-dot[data-dim="true"] { opacity: .3; }
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
    /* 订单生命周期状态：已释放待派单 / 已派单执行中 / 已完成（淡出） */
    .map-dot[data-kind="order"][data-order-state="waiting"] {
      background: #fff;
      border-color: var(--amber);
      box-shadow: 0 0 0 3px rgba(183,121,31,.16), 0 5px 14px rgba(15,23,42,.16);
    }
    /* 执行中：实心橙（客户单一直是橙色系，不会被误当成绿色骑手）*/
    .map-dot[data-kind="order"][data-order-state="dispatched"] {
      background: #ee8b1f;
      border-color: #fff;
      box-shadow: 0 0 0 3px rgba(238,139,31,.22), 0 5px 14px rgba(15,23,42,.18);
    }
    /* 已送达：成功绿 + ✓（不用灰色，灰色会和灰底地图糊在一起看不清）*/
    .map-dot[data-kind="order"][data-order-state="completed"] {
      background: #16a34a;
      opacity: .95;
      box-shadow: 0 0 0 2px rgba(22,163,74,.25), 0 3px 8px rgba(15,23,42,.16);
    }
    .map-dot[data-kind="order"][data-order-state="completed"]::before {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      content: "✓";
      font: 900 7px var(--font);
      line-height: 1;
    }
    .leaflet-map-pin-body[data-kind="order"][data-order-state="waiting"] {
      background: #fff;
      border-color: var(--amber);
      box-shadow: 0 0 0 3px rgba(183,121,31,.18);
    }
    .leaflet-map-pin-body[data-kind="order"][data-order-state="dispatched"] {
      background: #ee8b1f;
      box-shadow: 0 0 0 3px rgba(238,139,31,.22);
    }
    .leaflet-map-pin-body[data-kind="order"][data-order-state="completed"] {
      background: #16a34a;
      opacity: .96;
    }
    .leaflet-map-pin-body[data-kind="order"][data-order-state="completed"]::after {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      content: "✓";
      font: 900 9px var(--font);
      line-height: 1;
    }
    .legend-dot[data-order-state="waiting"] { background: #fff; border: 2px solid var(--amber); }
    .legend-dot[data-order-state="dispatched"] { background: #ee8b1f; }
    .legend-dot[data-order-state="completed"] { background: #16a34a; }
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
    /* 空闲骑手：白心青环（待命），与实心青“配送中”骑手区分 */
    .leaflet-map-pin-body[data-kind="rider"][data-motion="idle"] {
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(15,118,110,.55), 0 4px 10px rgba(15,23,42,.14);
      opacity: .9;
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
    /* 商家=取餐点：圆角方块，区别于圆形骑手/客户 */
    .leaflet-map-pin-body[data-kind="merchant"] {
      width: 13px;
      height: 13px;
      border-radius: 4px;
      background: var(--blue);
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
    .leaflet-route-assignment {
      border: 0;
      background: transparent;
      pointer-events: none;
    }
    .leaflet-route-assignment span {
      display: inline-flex;
      align-items: center;
      max-width: 116px;
      min-height: 20px;
      padding: 3px 7px;
      border: 1px solid rgba(15,118,110,.20);
      border-radius: 999px;
      color: #12352f;
      background: rgba(255,255,255,.90);
      box-shadow: 0 8px 18px rgba(15,23,42,.12);
      font: 850 10px var(--mono);
      white-space: nowrap;
    }
    /* 待派连线中点的订单标签：靛蓝，和配送段的 O→R 标签区分开 */
    .leaflet-pending-label span {
      color: #3730a3;
      border-color: rgba(79,70,229,.35);
      background: rgba(238,242,255,.94);
      font-size: 9px;
      padding: 2px 6px;
      min-height: 16px;
    }
    .route-assignment-label[data-lane="pending-link"] {
      fill: #3730a3;
      font-size: 1.9px;
    }
    /* 地图标签抗遮挡：底色更实、字号更小、悬停置顶，减少聚集时互相压盖看不清 */
    .leaflet-map-pin-label {
      background: rgba(255,255,255,.97);
      border-color: rgba(15,23,42,.16);
      font-size: 8.5px;
    }
    .leaflet-map-pin:hover { z-index: 10000 !important; }
    .leaflet-map-pin:hover .leaflet-map-pin-label {
      box-shadow: 0 0 0 2px rgba(15,118,110,.28), 0 8px 16px rgba(15,23,42,.22);
    }
    /* 底部「每条线说明」面板 */
    .line-explain-panel { margin-top: 12px; }
    .line-explain-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(232px, 1fr));
      gap: 10px;
      padding: 4px 2px 6px;
      /* 可上下拖动改变面板高度：拖右下角手柄；卡片多时内部滚动 */
      resize: vertical;
      overflow: auto;
      min-height: 130px;
      max-height: 78vh;
    }
    .line-explain-panel .card-head span::after { content: "（右下角可上下拖动调整高度）"; color: var(--muted); font-weight: 600; margin-left: 6px; }
    /* 全屏时的「每条线说明」悬浮面板（HUD）：默认隐藏，进入全屏才浮现在地图底部，磨砂玻璃质感 */
    .fs-explain-dock { display: none; }
    /* 全屏元素浏览器默认 position:fixed，已能作为绝对定位的包含块，无需再改 map-panel 定位 */
    .map-panel[data-fullscreen="true"] .fs-explain-dock {
      display: flex; flex-direction: column;
      position: absolute; left: 16px; right: 78px; bottom: 16px; /* 右侧留出缩放按钮的位置 */
      max-height: 38vh; z-index: 1200;
      background: rgba(255,255,255,.86);
      -webkit-backdrop-filter: blur(14px) saturate(1.12);
      backdrop-filter: blur(14px) saturate(1.12);
      border: 1px solid rgba(15,23,42,.12);
      border-radius: 16px;
      box-shadow: 0 16px 44px rgba(15,23,42,.24);
      overflow: hidden;
      animation: fs-dock-in .22s ease;
    }
    @keyframes fs-dock-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
    .fs-explain-dock-head {
      display: flex; align-items: center; gap: 10px; flex: none;
      padding: 9px 14px; border-bottom: 1px solid rgba(15,23,42,.08);
      background: linear-gradient(180deg, rgba(255,255,255,.55), rgba(255,255,255,0));
    }
    .fs-explain-dock-head b { font-size: 13px; color: var(--ink); white-space: nowrap; }
    .fs-explain-caption { flex: 1; min-width: 0; color: var(--muted); font-weight: 600; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .fs-explain-toggle { flex: none; border: 1px solid var(--line); background: rgba(255,255,255,.75); color: var(--ink-2); border-radius: 9px; padding: 3px 11px; cursor: pointer; font-weight: 700; font-size: 12px; }
    .fs-explain-toggle:hover { border-color: var(--line-strong); }
    .fs-explain-dock-body { overflow: auto; padding: 10px 12px 12px; }
    /* 收起时只隐藏卡片正文；进度条行 + 标题栏(含“展开”按钮/播放控件)始终保留、可见可点 */
    .fs-explain-dock[data-collapsed="true"] .fs-explain-dock-body { display: none; }
    /* 移入悬浮面板后，交给面板体控制高度/滚动，去掉网格自身的 resize 与高度限制 */
    .fs-explain-dock #live-line-explain { resize: none; max-height: none; min-height: 0; overflow: visible; padding: 0; }
    /* 透明命中线：整条描边都可命中（不受不透明度影响），让细/虚/淡的线也易于双击反查 */
    .route-hit-line { pointer-events: stroke !important; cursor: pointer; }
    /* 全屏悬浮面板顶部的进度条一行：推演时间 + 可拖动进度条 + 方向键提示 */
    .fs-progress-row { display: flex; align-items: center; gap: 12px; padding: 11px 14px 3px; flex: none; }
    .fs-progress-row .fs-clock { flex: none; font: 800 13px var(--mono); color: var(--ink); white-space: nowrap; }
    .fs-progress-row .fs-progress-slot { flex: 1; min-width: 0; }
    .fs-progress-row .fs-progress-slot .inference-progress { width: 100%; margin: 0; }
    .fs-progress-row .fs-progress-hint { flex: none; font-size: 11px; color: var(--muted); font-weight: 600; white-space: nowrap; }
    /* 全屏悬浮面板头部内嵌的播放控件（倍速 / 播放方式 / 暂停），随头部常驻，收起也能用 */
    .fs-dock-controls { display: inline-flex; align-items: center; gap: 8px; flex: none; }
    .fs-dock-controls .fs-ctrl { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: var(--muted); font-weight: 700; }
    .fs-dock-controls select { border: 1px solid var(--line); background: rgba(255,255,255,.92); color: var(--ink); border-radius: 9px; padding: 3px 8px; font-size: 12px; font-weight: 700; cursor: pointer; }
    .fs-dock-btn { border: 1px solid var(--line); background: var(--accent); color: #fff; border-radius: 9px; padding: 4px 12px; font-size: 12px; font-weight: 800; cursor: pointer; }
    .fs-dock-btn[data-state="paused"] { background: var(--accent); }
    .fs-dock-btn:hover { filter: brightness(1.04); }
    .fs-dock-sep { width: 1px; align-self: stretch; background: rgba(15,23,42,.12); margin: 2px 2px; }
    /* 全屏时把图例从底部（被悬浮面板盖住）移到左上信息卡下方，磨砂卡片形式常驻 */
    .map-panel[data-fullscreen="true"] .map-legend {
      bottom: auto; top: 128px; left: 16px; right: auto;
      max-width: 300px; z-index: 1100;
      background: rgba(255,255,255,.9);
      -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
      box-shadow: 0 12px 30px rgba(15,23,42,.16);
    }
    .line-explain-empty {
      color: var(--muted);
      font-size: 13px;
      padding: 10px 4px;
      line-height: 1.7;
    }
    .line-explain-card {
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: #fff;
      padding: 10px 12px;
      box-shadow: 0 1px 2px rgba(15,23,42,.04);
    }
    .line-explain-card[data-pending="1"] { background: #f6f7ff; border-color: rgba(79,70,229,.22); }
    .line-explain-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
    .line-explain-head b { font: 800 13px var(--mono); color: var(--ink); }
    .line-explain-badge { font: 800 11px var(--font); padding: 2px 9px; border-radius: 999px; color: #fff; white-space: nowrap; }
    .line-explain-badge[data-phase="deliver"] { background: var(--accent); }
    .line-explain-badge[data-phase="pickup"] { background: #ea580c; }
    .line-explain-badge[data-phase="pending"] { background: #4f46e5; }
    .line-explain-badge[data-phase="done"] { background: #16a34a; }
    .line-explain-card[data-done="1"] { background: #f0fdf4; opacity: .96; }
    .leg-swatch[data-lane="completed-route"] { background: repeating-linear-gradient(90deg, #16a34a 0 4px, transparent 4px 8px); }
    .line-explain-leg { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--ink-2); padding: 3px 0; }
    .line-explain-leg span { flex: 1; }
    .line-explain-leg em { font-style: normal; color: var(--muted); font-size: 11px; white-space: nowrap; }
    .leg-swatch { width: 16px; height: 4px; border-radius: 2px; flex: none; }
    .leg-swatch[data-lane="pickup"] { background: repeating-linear-gradient(90deg, #ea580c 0 5px, transparent 5px 8px); }
    .leg-swatch[data-lane="ours"] { background: var(--accent); }
    .leg-swatch[data-lane="pending-link"] { background: repeating-linear-gradient(90deg, #4f46e5 0 2px, transparent 2px 5px); }
    .line-explain-foot { margin-top: 5px; font: 800 11px var(--mono); color: var(--accent-2); }
    /* 每条线卡片可点选：悬停/选中反馈 */
    .line-explain-card { cursor: pointer; transition: box-shadow .16s ease, border-color .16s ease, transform .08s ease; }
    .line-explain-card:hover { border-color: var(--line-strong); box-shadow: 0 5px 14px rgba(15,23,42,.10); transform: translateY(-1px); }
    .line-explain-card[data-selected="1"] { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(15,118,110,.38), 0 6px 16px rgba(15,23,42,.12); }
    /* 点选后地图对应线段：闪烁两下 + 持续描边光晕 */
    @keyframes route-flash-blink { 0%, 100% { opacity: 1; } 50% { opacity: .12; } }
    .route-flash { animation: route-flash-blink .35s ease-in-out 2; }
    .route-highlighted { filter: drop-shadow(0 0 2.5px rgba(15,118,110,.95)) drop-shadow(0 0 6px rgba(15,118,110,.55)); }
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
      grid-template-columns: repeat(5, minmax(0, 1fr));
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
      grid-template-columns: repeat(2, minmax(0, 1fr));
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
      .live-control-dock { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .live-control-dock .runtime-strip { grid-column: 1 / -1; }
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
      .live-control-dock { grid-template-columns: 1fr; }
      .live-control-dock .runtime-strip { grid-template-columns: 1fr; }
      .operations-overview { grid-template-columns: 1fr; }
      .memory-overview, .memory-command-metrics, .memory-layer-grid, .recall-lane, .memory-field-grid, .context-metric-grid, .decision-advantage-metrics, .input-signal-grid, .resource-signal-grid, .demand-signal-grid, .capacity-signal-grid, .reason-graph, .candidate-path-board, .decision-plan-board, .decision-evidence-grid, .decision-proof-grid, .order-focus-list, .rider-focus-list { grid-template-columns: 1fr; }
      .schematic-map, .real-map-stage { height: 360px; margin: 10px; }
      .map-panel {
        height: var(--live-map-panel-height, 460px);
        min-height: 420px;
        max-height: 78vh;
      }
      .map-panel .schematic-map,
      .map-panel .real-map-stage {
        height: auto;
        min-height: 300px;
        margin: 10px 10px 0;
      }
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
    /* ===== 双屏对比页 ===== */
    .compare-grid { display: flex; flex-direction: column; gap: 12px; }
    .compare-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 10px 14px; }
    .compare-clock-cell { display: flex; flex-direction: column; }
    .compare-clock-cell span { font-size: 10px; color: var(--muted); }
    .compare-clock-cell b { font: 800 14px var(--mono); }
    .compare-controls .inference-progress { flex: 1; min-width: 220px; }
    .compare-stage-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .compare-panel { display: flex; flex-direction: column; border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: #fff; }
    .compare-panel[data-algo="baseline"] { box-shadow: inset 0 3px 0 #f1a5a5; }
    .compare-panel[data-algo="ours"] { box-shadow: inset 0 3px 0 #5eead4; }
    .compare-panel-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 8px 12px; border-bottom: 1px solid var(--line); }
    .compare-algo { display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .compare-algo b { font-weight: 800; }
    .compare-badge { font: 800 11px var(--font); padding: 2px 9px; border-radius: 999px; color: #fff; }
    .compare-badge[data-algo="baseline"] { background: #dc2626; }
    .compare-badge[data-algo="ours"] { background: #0f766e; }
    .compare-mini { font-size: 11.5px; color: var(--muted); white-space: nowrap; }
    .compare-mini b { color: var(--ink); }
    .compare-mini .cmp-bad { color: #dc2626; }
    .compare-mini .cmp-good { color: #0f766e; }
    .compare-grid [data-control="mode"] { display: none; } /* 每屏各画单一算法，隐藏“对比/叠加”模式选择 */
    .compare-map { height: 460px; background: #e8eef2; }
    .compare-map.leaflet-container { background: #e8eef2; }
    .compare-bottom { display: grid; grid-template-columns: 1.1fr 1fr; gap: 12px; }
    .compare-section-title { font-size: 13px; font-weight: 800; margin-bottom: 8px; }
    .compare-hint { font-size: 11px; color: var(--muted); font-weight: 600; margin-left: 6px; }
    .compare-scoreboard-wrap, .compare-trend-wrap { border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; background: #fff; }
    .compare-scoreboard { display: flex; flex-direction: column; gap: 4px; }
    .cmp-row { display: grid; grid-template-columns: 1.3fr 1fr 1fr 1.1fr; align-items: center; gap: 8px; padding: 5px 8px; border-radius: 8px; font-size: 12.5px; }
    .cmp-row.cmp-head { color: var(--muted); font-weight: 700; font-size: 11px; }
    .cmp-row .cmp-b { color: #b91c1c; font: 800 13px var(--mono); }
    .cmp-row .cmp-o { color: #0f766e; font: 800 13px var(--mono); }
    .cmp-row .cmp-gap { font-weight: 800; font-size: 12px; text-align: right; }
    .cmp-row[data-cmp="win"] { background: rgba(16,185,129,.09); }
    .cmp-row[data-cmp="win"] .cmp-gap { color: #059669; }
    .cmp-row[data-cmp="lose"] { background: rgba(220,38,38,.07); }
    .cmp-row[data-cmp="lose"] .cmp-gap { color: #dc2626; }
    .cmp-row[data-cmp="tie"] .cmp-gap { color: var(--muted); }
    .compare-fs-wrap { display: flex; flex-direction: column; gap: 12px; }
    /* 图例条：复用 renderMapLegend()，改成静态横排一行 */
    .compare-legend-bar { border: 1px solid var(--line); border-radius: 12px; padding: 6px 12px; background: #fff; }
    .compare-legend-bar .map-legend { position: static; box-shadow: none; border: 0; padding: 0; max-width: none; background: transparent; gap: 10px 14px; }
    /* 指标趋势小图矩阵（2×2）：每格一个指标，随时间逐渐展开 */
    .compare-trends { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .cmp-mini-card { border: 1px solid var(--line); border-radius: 10px; padding: 6px 9px 4px; background: #fff; }
    .cmp-mini-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 2px; }
    .cmp-mini-head b { font-size: 12px; font-weight: 800; }
    .cmp-mini-vals { font-size: 11px; color: var(--muted); white-space: nowrap; }
    .cmp-mini-vals .cmp-b { color: #b91c1c; font: 800 12px var(--mono); font-style: normal; }
    .cmp-mini-vals .cmp-o { color: #0f766e; font: 800 12px var(--mono); font-style: normal; }
    .cmp-mini-vals .cmp-mini-gap { color: #059669; font-style: normal; font-weight: 800; }
    .cmp-mini-svg { width: 100%; height: 44px; display: block; }
    /* 双屏全屏：控件+两图+图例+指标一起铺满，地图占据剩余高度 */
    .compare-fs-wrap[data-fullscreen="true"] { height: 100vh; box-sizing: border-box; padding: 10px 14px; gap: 8px; background: var(--bg, #eef1f4); overflow: hidden; }
    .compare-fs-wrap[data-fullscreen="true"] .control-dock,
    .compare-fs-wrap[data-fullscreen="true"] .compare-legend-bar { flex: 0 0 auto; }
    .compare-fs-wrap[data-fullscreen="true"] .compare-stage-row { flex: 1 1 auto; min-height: 0; }
    .compare-fs-wrap[data-fullscreen="true"] .compare-panel { min-height: 0; }
    .compare-fs-wrap[data-fullscreen="true"] .compare-map { flex: 1 1 auto; height: auto; min-height: 0; }
    .compare-fs-wrap[data-fullscreen="true"] .compare-bottom { flex: 0 0 auto; max-height: 30vh; overflow: auto; }
    @media (max-width: 1100px) { .compare-stage-row, .compare-bottom { grid-template-columns: 1fr; } .compare-map { height: 340px; } .compare-trends { grid-template-columns: 1fr; } }
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
        navRole: "长期记忆",
        navHint: "看系统沉淀、召回和验证的调度经验。",
        module: "经验沉淀",
        outcome: "记忆沉淀 + 召回反馈",
        subtitle: "长期记忆视图：展示新沉淀、已整理、当前命中和效果反馈，而不是资产表。"
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
      },
      compare: {
        icon: "比",
        title: "双屏对比",
        navLabel: "双屏对比",
        navRole: "对比验证",
        navHint: "同一时间轴，左基线贪心 vs 右我方算法，一眼看出差距。",
        module: "对比验证",
        outcome: "双屏对照 + 指标分化",
        subtitle: "同一批订单、同一条时间轴：左侧最近贪心基线，右侧我方 AutoSolver，下方指标实时分化。"
      }
    };
    const routeOrder = ["live", "compare", "decisions", "memory", "orders", "riders"];
    const inferenceState = {
      started: false,
      running: false,
      currentTimeS: workbench.timeline.start_s,
      speed: 1,
      playbackPace: "demo",
      mode: "current",
      timerId: null,
      tickMs: 1000,
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
    const ORDER_FADE_S = 300;      // 完成后订单点淡出保留时长（旧值，已由 COMPLETED_TRAIL_S 接管）
    const COMPLETED_TRAIL_S = 1800; // 已送达“淡线+绿✓点”滚动保留窗口=30分钟：保留最近半小时的配送轨迹，
                                    // 超过自动滚动移除，既有“刚走过的完整感”，又不会全天堆积成几百条线。
    const COMPLETED_TRAIL_CAP = 16; // 同时最多保留 16 条已送达淡线（高峰期封顶，防止过密）。
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
    const orderAliasBucket = (workbench.map.aliases && workbench.map.aliases.orders) || {};
    function orderDisplayLabelForId(orderId) {
      return orderAliasBucket[orderId] || orderId;
    }
    function _screenDist(a, b) {
      if (!a || !b) return 0;
      return Math.hypot((Number(a.screen_x) || 0) - (Number(b.screen_x) || 0), (Number(a.screen_y) || 0) - (Number(b.screen_y) || 0));
    }
    // 为“未进入决策帧的订单”（早餐/下午茶等）合成一条完整的取餐→配送流程，让全天展示一致：
    // 骑手先去商家取餐、再送到客户。位置真实（商家=下单取餐点、客户=送达点），骑手就近且不与
    // 其他合成单时间冲突；仅“骑手身份/派单时刻/预计时长”属演示合成（订单真实下单时间不变）。
    const SYNTH_PICKUP_WAIT_S = 120;
    // 把「按某算法的路线建立订单生命周期（含合成早/下午单 + 同骑手串行）」封装成可复用的算法模型。
    // 同一套实时地图渲染管线，切到不同算法模型就得到不同推演——双屏对比正是由此而来（左基线/右我方）。
    function buildAlgoModel(realRouteMap) {
      const syntheticRouteByOrderId = {};
      const orderLifecycle = (() => {
        const life = {};
        for (const order of workbench.entities.orders || []) {
          const created = Number(order.created_at_s);
          const dispatch = decisionByOrderId[order.id];
          const route = realRouteMap[order.id];
          if (dispatch && route) {
            // 全部用后端真值：优先用路线携带的真实“开始执行/送达”时刻（后端已按骑手可用时间串行化，
            // 因此同骑手多单天然不重叠、无孤儿路线）；缺失时才回退到 决策时刻+eta。绝不前端造假。
            let etaS = Number.isFinite(Number(route.eta_s)) ? Number(route.eta_s) : NaN;
            if (!Number.isFinite(etaS) && order.our_result && Number.isFinite(Number(order.our_result.eta_min))) etaS = Number(order.our_result.eta_min) * 60;
            if (!Number.isFinite(etaS)) etaS = 600;
            const assignAt = Number.isFinite(Number(route.assign_at_s)) ? Number(route.assign_at_s) : Number(dispatch.decision.trigger_time_s);
            const completeAt = Number.isFinite(Number(route.complete_at_s)) ? Number(route.complete_at_s) : (assignAt + Math.max(120, etaS));
            const courierId = route.courier_id || dispatch.action.courier_id || (order.our_result && order.our_result.courier_id) || "";
            life[order.id] = {
              id: order.id, map_label: order.map_label || orderDisplayLabelForId(order.id),
              created_at_s: created, assign_at_s: assignAt,
              courier_id: courierId, courier_label: route.courier_label || dispatch.action.courier_label || riderLabelForId(courierId),
              complete_at_s: completeAt, dispatched: true, route_id: route.id, synthetic: false
            };
          } else {
            // 后端没派这单（改造后理论上不再出现）：仅留“待派单”占位，绝不前端合成一条假路线。
            life[order.id] = { id: order.id, map_label: order.map_label || orderDisplayLabelForId(order.id), created_at_s: created, assign_at_s: null, courier_id: "", courier_label: "", complete_at_s: created + DEFAULT_SERVICE_S, dispatched: false, route_id: "", synthetic: false };
          }
        }
        return life;
      })();
      const demoEventTimes = (() => {
        const set = new Set();
        for (const id in orderLifecycle) {
          const l = orderLifecycle[id];
          if (Number.isFinite(l.created_at_s)) set.add(Math.round(l.created_at_s));
          if (l.dispatched && Number.isFinite(l.assign_at_s) && Number.isFinite(l.complete_at_s)) {
            set.add(Math.round(l.assign_at_s));
            set.add(Math.round((l.assign_at_s + l.complete_at_s) / 2));
            set.add(Math.round(l.complete_at_s));
          }
        }
        return Array.from(set).sort((a, b) => a - b);
      })();
      const ordersByCourier = (() => {
        const map = {};
        for (const id in orderLifecycle) {
          const l = orderLifecycle[id];
          if (!l.dispatched || !l.courier_id) continue;
          (map[l.courier_id] = map[l.courier_id] || []).push(id);
        }
        for (const courier in map) {
          map[courier].sort((a, b) => (orderLifecycle[a].assign_at_s || 0) - (orderLifecycle[b].assign_at_s || 0));
        }
        return map;
      })();
      const routeForOrder = (orderId) => realRouteMap[orderId] || syntheticRouteByOrderId[orderId] || null;
      return { orderLifecycle, ordersByCourier, syntheticRouteByOrderId, demoEventTimes, routeForOrder };
    }
    const baselineRouteMap = (() => {
      const m = {};
      for (const route of workbench.map.routes || []) {
        if (route.lane === "baseline" && route.order_id && !(route.order_id in m)) m[route.order_id] = route;
      }
      return m;
    })();
    const oursModel = buildAlgoModel(oursRouteByOrderId);       // 我方 AutoSolver
    const baselineModel = buildAlgoModel(baselineRouteMap);      // 基线 最近贪心
    // 下面这些原本是 const（只绑我方），现改成 let 并由 setActiveModel 切换；所有既有读取处不用改。
    let orderLifecycle = oursModel.orderLifecycle;
    let ordersByCourier = oursModel.ordersByCourier;
    let syntheticRouteByOrderId = oursModel.syntheticRouteByOrderId;
    let demoEventTimes = oursModel.demoEventTimes;
    let routeForOrder = oursModel.routeForOrder;
    let activeAlgoModel = oursModel;
    function setActiveModel(m) {
      activeAlgoModel = m;
      orderLifecycle = m.orderLifecycle;
      ordersByCourier = m.ordersByCourier;
      syntheticRouteByOrderId = m.syntheticRouteByOrderId;
      demoEventTimes = m.demoEventTimes;
      routeForOrder = m.routeForOrder;
    }
    function nextLifecycleEventTime(t) {
      for (let i = 0; i < demoEventTimes.length; i++) {
        if (demoEventTimes[i] > t + 0.001) return demoEventTimes[i];
      }
      return null;
    }
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
    const playbackPaceLabels = {
      demo: "演示快进",
      realtime: "逐秒播放"
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
      mixed: "混合天气",
      rain: "雨天",
      light_rain: "小雨",
      heavy_rain: "强降雨"
    };
    const shockLabels = {
      rain_slowdown: "降雨降速",
      merchant_burst: "商家爆单",
      courier_shortage: "骑手短缺",
      traffic_block: "道路拥堵"
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
    // 性能：推演自动播放时，侧栏/明细/卡片降频重建（肉眼无差别），地图+时钟仍每 tick 更新；
    // 缩放/拖动地图期间暂停图层重建，避免几百个路径反复销毁重建把交互拖卡。
    let lastHeavyRenderAt = 0;
    let liveMapInteracting = false;
    const HEAVY_RENDER_MIN_MS = 700;
    // 点选「每条线说明」卡片时，高亮地图上对应的那条线（闪烁两下 + 持续加粗描边 + 显示 O→R 标签）
    let highlightedOrderId = null;
    let flashPending = false;
    let timelineKeysBound = false;
    let fullscreenBound = false;
    function toggleLiveMapFullscreen() {
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      if (!panel) return;
      const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
      if (fsEl) {
        (document.exitFullscreen || document.webkitExitFullscreen || function () {}).call(document);
      } else {
        (panel.requestFullscreen || panel.webkitRequestFullscreen || function () {}).call(panel);
      }
    }
    function handleLiveMapFullscreenChange() {
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
      const isFs = Boolean(fsEl && panel && fsEl === panel);
      if (panel) panel.dataset.fullscreen = isFs ? "true" : "false";
      const btn = document.getElementById("live-map-fullscreen");
      if (btn) btn.textContent = isFs ? "⛶ 退出全屏" : "⛶ 全屏";
      syncFullscreenLineExplain(isFs); // 全屏时把「每条线说明」移入地图悬浮面板，退出时移回底部
      // 容器尺寸变化后 Leaflet 需要重算（延时两次，兼容全屏动画）
      window.setTimeout(() => { if (liveLeafletMap) liveLeafletMap.invalidateSize(false); }, 60);
      window.setTimeout(() => { if (liveLeafletMap) liveLeafletMap.invalidateSize(false); }, 280);
    }
    // 全屏时把底部「每条线说明」整块 #live-line-explain 移入地图内的悬浮面板；退出全屏移回原处。
    // 移动的是同一个元素，卡片点选/双击反查的监听、逐 tick 的 innerHTML 更新都随它一起走，无需重复渲染。
    function syncFullscreenLineExplain(isFs) {
      const grid = document.getElementById("live-line-explain");
      const slot = document.getElementById("live-fs-explain-slot");
      const home = document.querySelector(".line-explain-panel");
      const dock = document.getElementById("live-fs-explain-dock");
      if (grid) {
        if (isFs && slot) {
          if (grid.parentElement !== slot) slot.appendChild(grid);
          if (dock) dock.setAttribute("aria-hidden", "false");
          const cap = document.getElementById("line-explain-caption");
          const fsCap = document.getElementById("fs-explain-caption");
          if (cap && fsCap) fsCap.textContent = cap.textContent || "";
        } else if (home && grid.parentElement !== home) {
          home.appendChild(grid); // 移回底部面板（排在标题 card-head 之后，恢复原顺序）
          if (dock) dock.setAttribute("aria-hidden", "true");
        }
      }
      // 进度条同样移入/移出全屏悬浮面板（同一元素，拖动seek监听与逐tick更新都跟着走）
      const prog = document.getElementById("inference-progress-control");
      const progSlot = document.getElementById("live-fs-progress-slot");
      const progHome = document.querySelector("[data-control-strip='live']");
      if (prog) {
        if (isFs && progSlot) { if (prog.parentElement !== progSlot) progSlot.appendChild(prog); }
        else if (progHome && prog.parentElement !== progHome) { progHome.appendChild(prog); } // 移回主控（排在末尾，恢复原位）
      }
    }
    function highlightRoute(orderId) {
      highlightedOrderId = highlightedOrderId === orderId ? null : orderId; // 再次点击取消高亮
      flashPending = highlightedOrderId !== null;
      renderRuntimeState();
      flashPending = false;
    }
    // 反向联动：双击地图上的线 → 高亮该线，并把底部「每条线说明」滚动定位到对应卡片。
    function selectRouteFromMap(orderId, ev) {
      if (ev && ev.originalEvent && window.L && window.L.DomEvent) window.L.DomEvent.stop(ev.originalEvent);
      if (!orderId) return;
      highlightRoute(orderId);                       // 与点卡片一致：切换高亮（再次双击同一条可取消）
      if (highlightedOrderId === orderId) scrollLineCardIntoView(orderId); // 变为选中态才滚动定位卡片
    }
    function scrollLineCardIntoView(orderId) {
      const container = document.getElementById("live-line-explain");
      if (!container) return;
      // 用 getAttribute 逐个匹配，避开订单内部 id 里的特殊字符对 querySelector 的影响。
      const cards = container.querySelectorAll(".line-explain-card[data-order-id]");
      for (const card of cards) {
        if (card.getAttribute("data-order-id") === orderId) {
          card.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
          return;
        }
      }
    }
    // 透明加宽“命中线”：真正承接 悬浮tooltip + 双击反查 的是这条看不见的粗线（className 用
    // pointer-events:stroke，整条 22px 宽都可命中，且不受不透明度影响）。这样再细/再淡/带虚线的
    // 路线（如已送达的淡绿虚线，虚线只有实线段可点）也能轻松双击命中。叠在可见线之上，不改变外观。
    function bindRouteHit(map, latlngs, orderId, tooltipHtml) {
      if (!latlngs || latlngs.length < 2) return null;
      return window.L.polyline(latlngs, { className: "route-hit-line", color: "#000", weight: 22, opacity: 0, lineCap: "round", lineJoin: "round" })
        .bindTooltip(tooltipHtml, { sticky: true })
        .on("dblclick", (ev) => selectRouteFromMap(orderId, ev))
        .addTo(map);
    }
    // 聚焦模式：点选某单后，只让该任务链（该订单的商家/骑手/客户）保持醒目，其余全部淡化，
    // 让评委在任意时刻都能从密集画面里一眼锁定一条线。未选中时不淡化任何元素。
    function focusMerchantId() {
      const order = highlightedOrderId ? orderAnchorById[highlightedOrderId] : null;
      return order ? order.merchant_id : null;
    }
    function focusCourierId() {
      const life = highlightedOrderId ? orderLifecycle[highlightedOrderId] : null;
      return life ? life.courier_id : null;
    }
    function isFocusEntity(kind, item = {}) {
      if (!highlightedOrderId) return true; // 未聚焦：全部视为“在焦点内”，不淡化
      if (kind === "order") return item.id === highlightedOrderId;
      if (kind === "merchant") return item.id === focusMerchantId();
      if (kind === "rider") return item.id === focusCourierId() || item.order_id === highlightedOrderId || (item.task_order_ids || []).includes(highlightedOrderId);
      return false;
    }
    function isDimmed(kind, item = {}) {
      return Boolean(highlightedOrderId) && !isFocusEntity(kind, item);
    }
    const progressDragState = {
      active: false,
      pointerId: null
    };
    const liveMapResizeState = {
      active: false,
      pointerId: null,
      startY: 0,
      startHeight: 574
    };

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

    function clockPrecise(seconds) {
      const value = Math.max(0, Math.floor(Number(seconds) || 0));
      const hours = String(Math.floor(value / 3600)).padStart(2, "0");
      const minutes = String(Math.floor((value % 3600) / 60)).padStart(2, "0");
      const secondsPart = String(value % 60).padStart(2, "0");
      return `${hours}:${minutes}:${secondsPart}`;
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

    function effectiveFrameTime(frame) {
      const orderIds = new Set([
        ...(frame?.challenger?.active_order_ids || []),
        ...(frame?.highlighted_order_ids || [])
      ]);
      for (const assignment of frame?.baseline?.assignments || []) {
        if (assignment.order_id) orderIds.add(assignment.order_id);
      }
      for (const assignment of frame?.challenger?.assignments || []) {
        if (assignment.order_id) orderIds.add(assignment.order_id);
      }
      const releaseTimes = [...orderIds]
        .map((orderId) => Number(orderIndex[orderId]?.created_at_s))
        .filter(Number.isFinite);
      return Math.max(Number(frame?.sim_time_s) || workbench.timeline.start_s, ...releaseTimes);
    }

    function frameForTime(simTimeS) {
      const frames = contract.frames || [];
      let selected = frames[0];
      if (frames.length && simTimeS < effectiveFrameTime(frames[0])) {
        return preDispatchFrame(simTimeS);
      }
      for (const frame of frames) {
        const frameTime = effectiveFrameTime(frame);
        if (frameTime <= simTimeS) selected = frame;
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

    // 路线也严格按时间真值绘制：
    //   - 只画「已派单·执行中」订单的路线（订单已释放 + 决策已真实触发 + 未送达）；
    //   - 绝不引用未释放订单，也不会在派单前提前画线；
    //   - baseline / difference 仅在对比模式下、针对当前执行中的订单展示。
    const MAP_ROUTE_CAP = 8;
    function baselineRouteByOrderId(orderId) {
      return (workbench.map.routes || []).find((route) => route.lane === "baseline" && route.order_id === orderId) || null;
    }
    function liveDispatchedRoutes(simTimeS = inferenceState.currentTimeS) {
      const rows = [];
      for (const order of workbench.map.anchors.orders) {
        if (orderStatusAt(order.id, simTimeS) !== "dispatched") continue;
        const route = routeForOrder(order.id);
        if (route) rows.push(route);
      }
      // 同级按派单时间排序，保留最近 MAP_ROUTE_CAP 条正在执行的路线。
      rows.sort((a, b) => (orderLifecycle[a.order_id]?.assign_at_s || 0) - (orderLifecycle[b.order_id]?.assign_at_s || 0));
      return rows.slice(-MAP_ROUTE_CAP);
    }
    // 已送达“淡线”滚动保留：保留最近 COMPLETED_TRAIL_S(30分钟) 内完成的配送轨迹，超过自动移除。
    function liveCompletedRoutes(simTimeS = inferenceState.currentTimeS) {
      const rows = [];
      for (const order of workbench.map.anchors.orders) {
        if (orderStatusAt(order.id, simTimeS) !== "completed") continue;
        const life = orderLifecycle[order.id];
        if (!life || !life.dispatched) continue; // 只保留“真派过单”的完成线
        if (simTimeS > life.complete_at_s + COMPLETED_TRAIL_S) continue; // 超过 30 分钟滚动窗口不再画
        const route = routeForOrder(order.id);
        if (route) rows.push(route);
      }
      rows.sort((a, b) => (orderLifecycle[a.order_id]?.complete_at_s || 0) - (orderLifecycle[b.order_id]?.complete_at_s || 0));
      return rows.slice(-COMPLETED_TRAIL_CAP); // 高峰期最多保留最近 16 条，防止过密
    }
    // 全天累计送达单数（单调递增，用于“已送达”核对）。
    function deliveredCountAt(simTimeS = inferenceState.currentTimeS) {
      let n = 0;
      for (const id in orderLifecycle) {
        const life = orderLifecycle[id];
        if (life && Number.isFinite(life.complete_at_s) && life.complete_at_s <= simTimeS && simTimeS >= life.created_at_s) n += 1;
      }
      return n;
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
    //   - 每个点带上 map_order_state，供着色和图例解释。
    const MAP_ORDER_CAP = 72;
    const ORDER_STATE_RANK = { dispatched: 0, waiting: 1, completed: 2 };
    function ordersForMap(frame) {
      const t = inferenceState.currentTimeS;
      const visible = [];
      for (const order of workbench.map.anchors.orders) {
        const status = orderStatusAt(order.id, t);
        if (status === "unreleased" || status === "unknown") continue;
        if (status === "completed") {
          const life = orderLifecycle[order.id];
          // 绿✓订单点与已送达淡线用同一个 30 分钟滚动窗口，保证“点和线”一起保留、一起滚动移除。
          if (life && t > life.complete_at_s + COMPLETED_TRAIL_S) continue;
        }
        visible.push({ ...order, map_order_state: status });
      }
      if (visible.length <= MAP_ORDER_CAP) {
        return visible.sort((a, b) => a.created_at_s - b.created_at_s);
      }
      // 超过上限时优先保留「执行中 > 待派单 > 已完成」，同级取最新，避免地图过载。
      const trimmed = visible
        .slice()
        .sort((a, b) => (ORDER_STATE_RANK[a.map_order_state] - ORDER_STATE_RANK[b.map_order_state]) || (b.created_at_s - a.created_at_s))
        .slice(0, MAP_ORDER_CAP);
      return trimmed.sort((a, b) => a.created_at_s - b.created_at_s);
    }

    // ordersByCourier 现由 buildAlgoModel 生成、随 setActiveModel 切换（见上），此处不再单独声明。

    // 让“停在客户处的空闲骑手”不与该客户的订单点完全重叠：按骑手 id 给一个小方向偏移（约 40m）。
    function _hashInt(s) { let h = 0; for (let i = 0; i < s.length; i += 1) { h = (h * 31 + s.charCodeAt(i)) | 0; } return Math.abs(h); }
    function nudgedPosition(pos, key) {
      if (!pos) return pos;
      const ang = (_hashInt(String(key)) % 360) * Math.PI / 180;
      return {
        lat: Number(pos.lat) + Math.cos(ang) * 0.00045,
        lng: Number(pos.lng) + Math.sin(ang) * 0.00045,
        screen_x: Number(pos.screen_x) + Math.cos(ang) * 2.6,
        screen_y: Number(pos.screen_y) + Math.sin(ang) * 2.6
      };
    }
    // 骑手轨迹（全时段一致、位置真实）：
    //   未接单 -> 停在驻点(anchor)；配送中 -> 沿路线移动(取餐段/配送段)；
    //   送完 -> 停在“最后一个客户”附近“空闲·待命”，可继续接下一单（符合现实：骑手送完还在，能再接单）。
    function riderStateAt(courierId, anchorPos, simTimeS) {
      const ids = ordersByCourier[courierId] || [];
      let current = null;
      let lastDone = null;
      let doneCount = 0;
      for (const oid of ids) {
        const life = orderLifecycle[oid];
        if (simTimeS < life.assign_at_s) break;
        if (simTimeS < life.complete_at_s) { current = oid; break; }
        lastDone = oid;
        doneCount += 1;
      }
      if (current) {
        const life = orderLifecycle[current];
        const route = routeForOrder(current);
        const poly = route ? route.polyline : null;
        const span = Math.max(1, life.complete_at_s - life.assign_at_s);
        const progress = clamp((simTimeS - life.assign_at_s) / span, 0, 1);
        const position = poly ? pointAlongPolyline(poly, progress) : anchorPos;
        const leg = poly && progress < merchantFractionForPolyline(poly) ? "pickup" : "deliver";
        return {
          position, motion: "moving", order_id: current, task_order_ids: [current], task_order_count: 1,
          merchant_label: merchantLabelForOrder(current), leg,
          phase: leg === "pickup" ? "取餐中" : "配送中", progress
        };
      }
      if (lastDone) {
        const anchor = orderAnchorById[lastDone];
        const at = (anchor && anchor.dropoff) || anchorPos;
        return { position: nudgedPosition(at, courierId), motion: "idle", phase: `空闲·待命（已完成 ${doneCount} 单）`, done_count: doneCount, last_order_id: lastDone };
      }
      return { position: anchorPos, motion: "idle", phase: "空闲·待命", done_count: 0 };
    }

    function riderPositionsForFrame(frame) {
      const simTimeS = inferenceState.currentTimeS;
      const anchors = (workbench.map.anchors.riders || []).slice(0, 18);
      const riders = anchors.map((rider) => {
        const state = riderStateAt(rider.id, rider.position, simTimeS);
        return { id: rider.id, label: riderLabelForId(rider.id), map_label: riderLabelForId(rider.id), ...state };
      }).filter((rider) => rider.position);
      // 配送中的骑手排前面，保证“正在送餐的骑手”一定优先显示（即使有渲染上限也不会被截掉）。
      riders.sort((a, b) => (a.motion === "moving" ? 0 : 1) - (b.motion === "moving" ? 0 : 1));
      return dedupeRiderPositions(riders);
    }

    // 同一骑手任一时刻只保留一个当前位置，杜绝地图上出现两个同名骑手（“分身”）。
    function dedupeRiderPositions(riders = []) {
      const seen = new Map();
      for (const rider of riders) {
        if (!seen.has(rider.id)) seen.set(rider.id, rider);
      }
      return Array.from(seen.values());
    }


    // ---- 商家（取餐点）与任务链关系辅助 ----------------------------------
    const merchantAnchorById = Object.fromEntries((workbench.map.anchors.merchants || []).map((m) => [m.id, m]));
    const orderAnchorById = Object.fromEntries((workbench.map.anchors.orders || []).map((o) => [o.id, o]));
    function merchantForOrder(orderId) {
      const order = orderAnchorById[orderId];
      if (!order) return null;
      const anchor = merchantAnchorById[order.merchant_id];
      const position = (anchor && anchor.position) || order.pickup;
      if (!position) return null;
      return { id: order.merchant_id, map_label: (anchor && anchor.map_label) || order.merchant_id, position };
    }
    function merchantLabelForOrder(orderId) {
      const merchant = merchantForOrder(orderId);
      return merchant ? merchant.map_label : "";
    }
    function merchantFractionForPolyline(polyline = []) {
      const n = (polyline || []).length;
      return n >= 3 ? 1 / (n - 1) : 0;
    }
    // 只展示与当前可见订单相关的商家（取餐点），建立“商家↔订单”的可见关系。
    function activeMerchantsForMap(orders = []) {
      const seen = new Map();
      for (const order of orders) {
        const merchant = merchantForOrder(order.id);
        if (!merchant || seen.has(merchant.id)) continue;
        seen.set(merchant.id, { ...merchant, kind: "merchant" });
      }
      return Array.from(seen.values());
    }
    // 待派单订单：下单后、派单前，用“商家⋯客户”虚线表达这单的取餐点→送达点关系。
    function waitingLinksForMap(orders = []) {
      const links = [];
      for (const order of orders) {
        if (order.map_order_state !== "waiting") continue;
        const merchant = merchantForOrder(order.id);
        if (!merchant || !order.dropoff) continue;
        links.push({
          order_id: order.id,
          order_label: order.map_label,
          renderLane: "pending-link",
          polyline: [merchant.position, order.dropoff]
        });
      }
      return links.slice(-10); // 待派连线最多展示最近 10 条，避免高峰期连线过密
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
          <aside class="page-role-card" aria-label="当前页面说明">
            <b>${escapeHtml(copy.navLabel)}</b>
            <span>${escapeHtml(copy.navHint)}</span>
            <em>全天预置数据回放</em>
          </aside>
        </div>
      `;
    }

    function hydrateLivePage() {
      bindLiveControls();
      bindLiveMapResizeHandle();
      renderRuntimeState();
    }

    function bindLiveControls() {
      const startButton = document.getElementById("start-inference");
      const pauseButton = document.getElementById("pause-inference");
      const speedSelect = document.getElementById("playback-speed");
      const playbackPaceSelect = document.getElementById("playback-pace");
      const modeSelect = document.getElementById("inference-mode");
      const progressControl = document.getElementById("inference-progress-control");
      if (!startButton || !pauseButton || !speedSelect || !playbackPaceSelect || !modeSelect) return;
      startButton.addEventListener("click", startInference);
      pauseButton.addEventListener("click", toggleInferencePause);
      speedSelect.value = String(inferenceState.speed);
      playbackPaceSelect.value = inferenceState.playbackPace;
      modeSelect.value = inferenceState.mode;
      speedSelect.addEventListener("change", () => setInferenceSpeed(Number(speedSelect.value)));
      playbackPaceSelect.addEventListener("change", () => setInferencePlaybackPace(playbackPaceSelect.value));
      modeSelect.addEventListener("change", () => setInferenceMode(modeSelect.value));
      if (progressControl) {
        progressControl.addEventListener("pointerdown", handleProgressPointerDown);
        progressControl.addEventListener("pointermove", handleProgressPointerMove);
        progressControl.addEventListener("pointerup", handleProgressPointerEnd);
        progressControl.addEventListener("pointercancel", handleProgressPointerEnd);
      }
      // 方向键拖动时间：绑到 document（只绑一次），无需进度条获得焦点，暂停/播放中都能用。
      if (!timelineKeysBound) {
        timelineKeysBound = true;
        document.addEventListener("keydown", handleProgressKeyboardSeek);
      }
      // 地图全屏：点按钮进入全屏，ESC / 再点退出（浏览器原生 ESC 触发 fullscreenchange 复原）。
      const fullscreenBtn = document.getElementById("live-map-fullscreen");
      if (fullscreenBtn) fullscreenBtn.addEventListener("click", toggleLiveMapFullscreen);
      // 全屏悬浮面板的「收起/展开」按钮（仅绑定一次）
      const fsExplainToggle = document.getElementById("fs-explain-toggle");
      if (fsExplainToggle && fsExplainToggle.dataset.bound !== "true") {
        fsExplainToggle.dataset.bound = "true";
        fsExplainToggle.addEventListener("click", () => {
          const dock = document.getElementById("live-fs-explain-dock");
          if (!dock) return;
          const collapsed = dock.getAttribute("data-collapsed") === "true";
          dock.setAttribute("data-collapsed", collapsed ? "false" : "true");
          fsExplainToggle.textContent = collapsed ? "收起 ▾" : "展开 ▴";
        });
      }
      // 全屏悬浮面板里的播放控件：复用主控的 setter，state 同步在 renderLiveRuntimeState 里做（仅绑一次）
      const fsPause = document.getElementById("fs-pause");
      if (fsPause && fsPause.dataset.bound !== "true") { fsPause.dataset.bound = "true"; fsPause.addEventListener("click", toggleInferencePause); }
      const fsSpeed = document.getElementById("fs-speed");
      if (fsSpeed && fsSpeed.dataset.bound !== "true") { fsSpeed.dataset.bound = "true"; fsSpeed.addEventListener("change", () => setInferenceSpeed(Number(fsSpeed.value))); }
      const fsPace = document.getElementById("fs-pace");
      if (fsPace && fsPace.dataset.bound !== "true") { fsPace.dataset.bound = "true"; fsPace.addEventListener("change", () => setInferencePlaybackPace(fsPace.value)); }
      if (!fullscreenBound) {
        fullscreenBound = true;
        document.addEventListener("fullscreenchange", handleLiveMapFullscreenChange);
        document.addEventListener("webkitfullscreenchange", handleLiveMapFullscreenChange);
      }
      // 点选「每条线说明」卡片 → 高亮地图上对应线段（容器常驻，用事件委托，仅绑定一次）
      const lineExplain = document.getElementById("live-line-explain");
      if (lineExplain && lineExplain.dataset.clickBound !== "true") {
        lineExplain.dataset.clickBound = "true";
        lineExplain.addEventListener("click", (event) => {
          const card = event.target.closest ? event.target.closest(".line-explain-card[data-order-id]") : null;
          if (card) highlightRoute(card.getAttribute("data-order-id"));
        });
      }
    }

    function bindLiveMapResizeHandle() {
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      if (!panel) return;
      syncLiveMapResizeHandleValue();
      for (const id of ["live-map-resize-handle", "live-map-resize-handle-top"]) {
        const handle = document.getElementById(id);
        if (!handle || handle.dataset.bound === "true") continue;
        handle.dataset.bound = "true";
        handle.addEventListener("pointerdown", handleLiveMapResizePointerDown);
        handle.addEventListener("keydown", handleLiveMapResizeKeyboard);
      }
    }

    function liveMapPanelHeightBounds() {
      const minHeight = window.matchMedia?.("(max-width: 720px)").matches ? 300 : 360;
      const viewportLimit = Math.floor((window.innerHeight || 900) * .94);
      return {
        min: minHeight,
        max: Math.max(minHeight, Math.min(1800, viewportLimit))
      };
    }

    function currentLiveMapPanelHeight() {
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      return panel ? panel.getBoundingClientRect().height : 574;
    }

    function handleLiveMapResizePointerDown(event) {
      if (event.button !== undefined && event.button !== 0) return;
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      if (!panel) return;
      liveMapResizeState.active = true;
      liveMapResizeState.pointerId = event.pointerId;
      liveMapResizeState.startY = event.clientY;
      liveMapResizeState.startHeight = panel.getBoundingClientRect().height;
      // 顶部手柄 dir=-1（向上拖=变大），底部手柄 dir=+1（向下拖=变大）
      liveMapResizeState.dir = event.currentTarget?.dataset?.resizeDir === "top" ? -1 : 1;
      panel.dataset.resizingMap = "true";
      if (event.currentTarget?.setPointerCapture) event.currentTarget.setPointerCapture(event.pointerId);
      window.addEventListener("pointermove", handleLiveMapResizePointerMove);
      window.addEventListener("pointerup", handleLiveMapResizePointerEnd);
      window.addEventListener("pointercancel", handleLiveMapResizePointerEnd);
      event.preventDefault();
    }

    function handleLiveMapResizePointerMove(event) {
      if (!liveMapResizeState.active || liveMapResizeState.pointerId !== event.pointerId) return;
      event.preventDefault();
      const dir = liveMapResizeState.dir || 1;
      setLiveMapPanelHeight(liveMapResizeState.startHeight + dir * (event.clientY - liveMapResizeState.startY));
    }

    function handleLiveMapResizePointerEnd(event) {
      if (liveMapResizeState.pointerId !== event.pointerId) return;
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      const handle = document.getElementById("live-map-resize-handle");
      if (handle?.hasPointerCapture?.(event.pointerId)) {
        handle.releasePointerCapture(event.pointerId);
      }
      if (panel) panel.dataset.resizingMap = "false";
      liveMapResizeState.active = false;
      liveMapResizeState.pointerId = null;
      window.removeEventListener("pointermove", handleLiveMapResizePointerMove);
      window.removeEventListener("pointerup", handleLiveMapResizePointerEnd);
      window.removeEventListener("pointercancel", handleLiveMapResizePointerEnd);
      invalidateLiveMapSize();
    }

    function handleLiveMapResizeKeyboard(event) {
      const bounds = liveMapPanelHeightBounds();
      const step = event.shiftKey ? 80 : 24;
      let nextHeight = null;
      if (event.key === "ArrowUp") {
        nextHeight = currentLiveMapPanelHeight() - step;
      } else if (event.key === "ArrowDown") {
        nextHeight = currentLiveMapPanelHeight() + step;
      } else if (event.key === "Home") {
        nextHeight = bounds.min;
      } else if (event.key === "End") {
        nextHeight = bounds.max;
      }
      if (nextHeight === null) return;
      event.preventDefault();
      event.stopPropagation();
      setLiveMapPanelHeight(nextHeight);
    }

    function setLiveMapPanelHeight(nextHeight) {
      const panel = document.querySelector("[data-resizable-map-panel='vertical']");
      if (!panel) return;
      const bounds = liveMapPanelHeightBounds();
      const height = clamp(Number(nextHeight) || 574, bounds.min, bounds.max);
      panel.style.setProperty("--live-map-panel-height", `${Math.round(height)}px`);
      syncLiveMapResizeHandleValue(height, bounds);
      invalidateLiveMapSize();
    }

    function syncLiveMapResizeHandleValue(height = currentLiveMapPanelHeight(), bounds = liveMapPanelHeightBounds()) {
      const handle = document.getElementById("live-map-resize-handle");
      if (!handle) return;
      handle.setAttribute("aria-valuemin", String(bounds.min));
      handle.setAttribute("aria-valuemax", String(bounds.max));
      handle.setAttribute("aria-valuenow", String(Math.round(height)));
      handle.title = `上下拖动调整地图高度，当前 ${Math.round(height)}px`;
    }

    function invalidateLiveMapSize() {
      if (liveLeafletMap) {
        window.requestAnimationFrame(() => {
          if (liveLeafletMap) liveLeafletMap.invalidateSize(false);
        });
      }
    }

    function startInference() {
      inferenceState.started = true;
      inferenceState.running = true;
      inferenceState.currentTimeS = workbench.timeline.start_s;
      inferenceState.lastTickAt = Date.now();
      scheduleInferenceTick();
      renderRuntimeState();
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
      renderRuntimeState();
    }

    function setInferenceSpeed(speed) {
      inferenceState.speed = [.5, 1, 2, 4].includes(speed) ? speed : 1;
      if (inferenceState.running) {
        inferenceState.lastTickAt = Date.now();
        scheduleInferenceTick();
      }
      renderRuntimeState();
    }

    function setInferencePlaybackPace(playbackPace) {
      inferenceState.playbackPace = Object.prototype.hasOwnProperty.call(playbackPaceLabels, playbackPace) ? playbackPace : "demo";
      if (inferenceState.running) {
        inferenceState.lastTickAt = Date.now();
        scheduleInferenceTick();
      }
      renderRuntimeState();
    }

    function setInferenceMode(mode) {
      inferenceState.mode = Object.prototype.hasOwnProperty.call(inferenceModeLabels, mode) ? mode : "current";
      renderRuntimeState();
    }

    function handleProgressPointerDown(event) {
      if (event.button !== undefined && event.button !== 0) return;
      const progressControl = event.currentTarget;
      progressDragState.active = true;
      progressDragState.pointerId = event.pointerId;
      if (progressControl?.focus) progressControl.focus({ preventScroll: true });
      if (progressControl?.setPointerCapture) progressControl.setPointerCapture(event.pointerId);
      event.preventDefault();
      seekInferenceFromProgressEvent(event);
    }

    function handleProgressPointerMove(event) {
      if (!progressDragState.active || progressDragState.pointerId !== event.pointerId) return;
      event.preventDefault();
      seekInferenceFromProgressEvent(event);
    }

    function handleProgressPointerEnd(event) {
      if (progressDragState.pointerId !== event.pointerId) return;
      if (event.currentTarget?.hasPointerCapture?.(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      progressDragState.active = false;
      progressDragState.pointerId = null;
    }

    function seekInferenceFromProgressEvent(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      if (!rect.width) return;
      const ratio = clamp((event.clientX - rect.left) / rect.width, 0, 1);
      seekInferenceTime(workbench.timeline.start_s + ratio * timelineSpanS());
    }

    // 全局方向键拖动时间（不再要求进度条获得焦点，暂停后也能用）。
    // 短按（单次按下）= 前后 1 分钟；长按（系统自动重复）= 每次 1 秒，便于精细观察。
    function handleProgressKeyboardSeek(event) {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight" && event.key !== "Home" && event.key !== "End") return;
      // 实时页 + 双屏对比页生效；不劫持表单控件（下拉/输入框）上的方向键。
      if (!document.querySelector("[data-page='live'], [data-page='compare']")) return;
      const active = document.activeElement;
      const tag = active && active.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      const stepS = event.repeat ? 1 : 60;
      let nextTimeS = null;
      if (event.key === "ArrowLeft") nextTimeS = inferenceState.currentTimeS - stepS;
      else if (event.key === "ArrowRight") nextTimeS = inferenceState.currentTimeS + stepS;
      else if (event.key === "Home") nextTimeS = workbench.timeline.start_s;
      else if (event.key === "End") nextTimeS = workbench.timeline.end_s;
      if (nextTimeS === null) return;
      event.preventDefault();
      seekInferenceTime(nextTimeS);
    }

    function seekInferenceTime(nextTimeS) {
      const snappedTimeS = Math.round(Number(nextTimeS || 0));
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

    // 两种播放都用 400ms 短 tick，让画面连续、骑手平滑移动（不再是“1 秒一大步”地跳）。
    function currentTickMs() {
      return 400;
    }

    // 演示快进的基础节奏：1x ≈ 90 仿真秒 / 真实秒（原来是 900，太快、一步跨 15 分钟）。
    // 全天 16 小时按 90x 约 10 分钟放完，再叠加“临近事件放慢”，看得清商家→骑手→客户全过程。
    const DEMO_BASE_RATE_X = 60;

    function scheduleInferenceTick() {
      clearInferenceTimer();
      inferenceState.timerId = setInterval(advanceInferenceTick, currentTickMs());
    }

    function playbackStepSeconds() {
      return inferenceState.playbackPace === "realtime" ? realtimePlaybackStepSeconds() : demoPlaybackStepSeconds();
    }

    function realtimePlaybackStepSeconds() {
      // 每 tick 推进约 speed 仿真秒（逐秒级），配合 400ms tick 让画面清晰地连续推进。
      return Math.max(0.5, inferenceState.speed);
    }

    // 演示快进：事件感知的推进步长，符合真实骑手送单节奏——
    // ① 基础步长 = 90x × 倍速 × tick 秒；② 若一步会跨过“下一个业务事件”（下单/派单/取餐/送达），
    // 就收紧到刚好落在该事件后一点，保证每个状态都被渲染、绝不一次跳过好几个状态；
    // ③ 离下一个事件很远的空档期，允许适当加速掠过（但落点留在事件前一点，能看到它到来）。
    function demoPlaybackStepSeconds() {
      const tickS = currentTickMs() / 1000;
      const speed = inferenceState.speed;
      const base = DEMO_BASE_RATE_X * speed * tickS;   // 1x：90×1×0.4 = 36 仿真秒/tick
      const floor = base * 0.25;                        // 极密集期的步长下限，避免卡成蠕动
      const t = inferenceState.currentTimeS;
      const nextEvt = nextLifecycleEventTime(t);
      if (nextEvt == null) return base;
      const gap = nextEvt - t;
      if (gap <= base) {
        // 会越过下一个事件 → 只走到事件后一点点，让这个状态变化被看见（密集期自动放慢）。
        return clamp(gap + 2, floor, base);
      }
      if (gap > 300) {
        // 空档期：加速掠过没内容的时间，但停在下一个事件前约 90 秒，能看见它临近。
        return Math.min(base * 3, gap - 90);
      }
      return base;
    }

    function advanceInferenceTick() {
      if (!inferenceState.running) return;
      const now = Date.now();
      inferenceState.lastTickAt = now;
      const simulatedStepS = playbackStepSeconds();
      setInferenceTime(inferenceState.currentTimeS + simulatedStepS, true);
    }

    function setInferenceTime(nextTimeS, fromTick = false) {
      inferenceState.currentTimeS = clamp(nextTimeS, workbench.timeline.start_s, workbench.timeline.end_s);
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        inferenceState.running = false;
        clearInferenceTimer();
      }
      renderRuntimeState(!fromTick); // 自动 tick 允许侧栏降频；用户拖动/跳转则立即全量刷新
    }

    // 按当前页面把「重新渲染运行态」派发到实时页或双屏对比页（两页共用同一 inferenceState 与播放控件）。
    function renderRuntimeState(force = true) {
      if (document.querySelector("[data-page='compare']")) renderCompareRuntimeState(force);
      else renderLiveRuntimeState(force);
    }

    function renderLiveRuntimeState(force = true) {
      const liveGrid = document.querySelector("[data-page='live']");
      if (!liveGrid) return;
      // 重活（侧栏明细/卡片/评分卡）节流：自动播放时最多每 HEAVY_RENDER_MIN_MS 重建一次；
      // 用户交互(force=true)立即刷新。地图overlay与时钟/进度条不受此限，仍每次更新保证运动连续。
      const heavy = force || (Date.now() - lastHeavyRenderAt >= HEAVY_RENDER_MIN_MS);
      if (heavy) lastHeavyRenderAt = Date.now();
      const inferenceFinished = inferenceState.started && inferenceState.currentTimeS >= workbench.timeline.end_s;
      const stateLabel = inferenceState.running ? "自动推理中" : inferenceFinished ? "推演完成" : inferenceState.started ? "已暂停" : "未开始";
      const events = releasedEvents(inferenceState.currentTimeS);
      const currentScore = scoreForTime(inferenceState.currentTimeS);
      const currentDecision = decisionForTime(inferenceState.currentTimeS);
      liveGrid.dataset.inferenceState = inferenceState.running ? "running" : inferenceState.started ? "paused" : "ready";
      setText("inference-state-label", stateLabel);
      setText("inference-clock", clockPrecise(inferenceState.currentTimeS));
      setText("inference-speed-label", `${inferenceState.speed}x`);
      setText("inference-playback-pace-label", playbackPaceLabels[inferenceState.playbackPace]);
      setText("inference-mode-label", inferenceModeLabels[inferenceState.mode]);
      // 同步全屏悬浮面板里的播放控件（值 + 暂停按钮文案），使其与主控/状态一致
      const fsSpeedSel = document.getElementById("fs-speed");
      if (fsSpeedSel) fsSpeedSel.value = String(inferenceState.speed);
      const fsPaceSel = document.getElementById("fs-pace");
      if (fsPaceSel) fsPaceSel.value = inferenceState.playbackPace;
      const fsPauseBtn = document.getElementById("fs-pause");
      if (fsPauseBtn) fsPauseBtn.textContent = inferenceState.running ? "⏸ 暂停" : (inferenceState.started ? "▶ 继续" : "▶ 开始");
      setText("fs-clock", clockPrecise(inferenceState.currentTimeS)); // 全屏悬浮面板的推演时间
      setText("inference-event-count", events.length);
      setText("live-advantage-headline", liveAdvantageHeadline(currentScore));
      setText("live-advantage-copy", liveAdvantageCopy(currentScore));
      const targetRow = document.getElementById("advantage-target-row");
      if (heavy && targetRow) targetRow.innerHTML = renderAdvantageTargetRow(currentScore);
      setText("map-runtime-hint", `${stateLabel} / ${clock(inferenceState.currentTimeS)} / ${inferenceModeLabels[inferenceState.mode]}`);
      setText("event-flow-caption", `${events.length} 个事件已自动释放`);
      setText("cumulative-metrics-caption", `${currentScore.time_label} 累计优势`);
      setText("round-summary-time", currentDecision.trigger_time_label);
      const progressPct = inferenceProgressPct();
      const progressControl = document.getElementById("inference-progress-control");
      if (progressControl) {
        progressControl.setAttribute("aria-valuenow", String(progressPct));
        progressControl.setAttribute("aria-valuetext", `${clockPrecise(inferenceState.currentTimeS)} / ${fmtNumber(progressPct, 1)}%`);
        progressControl.title = `拖动跳转到对应推演秒数；当前 ${clockPrecise(inferenceState.currentTimeS)}，${fmtNumber(progressPct, 1)}%`;
      }
      const progressBar = document.getElementById("inference-progress-bar");
      if (progressBar) progressBar.style.setProperty("--progress", `${progressPct}%`);
      // 地图 overlay 重建是全页最重的一步（高峰期 200+ 路径+marker 全量销毁重建）。
      // 与侧栏重活对齐同一 heavy 节流：自动播放时最多每 HEAVY_RENDER_MIN_MS 重建一次，
      // 让两处长任务落在同一帧、其余时间主线程空闲 → 整页/切页/拖动都更跟手。
      // 用户操作(force=true→heavy)仍立即重建。骑手位置的逐帧插值不重建（用户明确不在意其顺滑）。
      const mapStage = document.getElementById("live-map-stage");
      if (heavy && mapStage) {
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
      // —— 以下为“重活”：整块侧栏/明细/卡片重建，按 heavy 节流（自动播放时降频，肉眼无差别）——
      if (heavy) {
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
        const lineExplain = document.getElementById("live-line-explain");
        if (lineExplain) lineExplain.innerHTML = renderLiveRouteBreakdown();
        const lineExplainCaption = document.getElementById("line-explain-caption");
        if (lineExplainCaption) {
          const t = inferenceState.currentTimeS;
          const dn = liveDispatchedRoutes(t).length;
          const wn = (workbench.map.anchors.orders || []).filter((order) => orderStatusAt(order.id, t) === "waiting").length;
          const done = deliveredCountAt(t);
          const focusText = highlightedOrderId
            ? `｜已聚焦 ${(orderAnchorById[highlightedOrderId] || {}).map_label || ""}（其余淡化，再点取消）`
            : "｜点选卡片高亮对应线；双击地图上的线可反查定位到卡片";
          lineExplainCaption.textContent = `执行中 ${dn} · 待派 ${wn} · 累计送达 ${done}${focusText}`;
          const fsCap = document.getElementById("fs-explain-caption"); // 全屏悬浮面板的同款计数
          if (fsCap) fsCap.textContent = `执行中 ${dn} · 待派 ${wn} · 累计送达 ${done}`;
        }
      }
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

    function liveAdvantageHeadline(score) {
      const delta = score.deltas || {};
      const timeSaved = Number(delta.time_saved_min || 0);
      if (!inferenceState.started) {
        return "等待开始推理";
      }
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        return `全日推演完成：节省 ${fmtNumber(timeSaved, 1)} 分钟`;
      }
      if (timeSaved <= 0) {
        return "正在等待首轮有效优势";
      }
      return `已节省 ${fmtNumber(timeSaved, 1)} 分钟`;
    }

    function liveAdvantageCopy(score) {
      const delta = score.deltas || {};
      const finalDelta = workbench.metrics.final.deltas;
      const timeSaved = Number(delta.time_saved_min || 0);
      const moneySaved = Number(delta.money_saved_yuan || 0);
      const timeoutText = fmtFewer(delta.timeout_order_delta || 0, "单");
      if (!inferenceState.started) {
        return "点击开始推理后，系统会按全天时间线自动释放订单、移动骑手、重算路线，并实时累计我方相对基线的优势。";
      }
      if (timeSaved <= 0) {
        return "推理已开始，当前仍在等待首轮规划评分。优势卡片只展示已经推演到的累计结果，不提前展示全日结论。";
      }
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        return `全日回放已完成：我方比基线少 ${fmtNumber(finalDelta.time_saved_min, 1)} 分钟、少 ${fmtNumber(finalDelta.money_saved_yuan, 1)} 元成本，超时单${fmtFewer(finalDelta.timeout_order_delta, "单")}。`;
      }
      return `推理正在自动推进：当前累计少 ${fmtNumber(moneySaved, 1)} 元成本，超时单${timeoutText}，地图只展示我方动作和差异路线。`;
    }

    function renderAdvantageTargetRow(score) {
      if (!inferenceState.started) {
        return `
          <span>开始后累计验证</span>
          <span>全日结论暂不展示</span>
          <span>地图将自动推进</span>
        `;
      }
      const delta = score.deltas || {};
      if (inferenceState.currentTimeS >= workbench.timeline.end_s) {
        const finalDelta = workbench.metrics.final.deltas;
        return `
          <span>全日节省 ${fmtNumber(finalDelta.time_saved_min, 1)} 分钟</span>
          <span>成本优势 ${fmtNumber(finalDelta.money_saved_yuan, 1)} 元</span>
          <span>超时单${fmtFewer(finalDelta.timeout_order_delta, "单")}</span>
        `;
      }
      return `
        <span>当前进度 ${fmtNumber(inferenceProgressPct(), 1)}%</span>
        <span>已累计 ${fmtNumber(delta.time_saved_min || 0, 1)} 分钟</span>
        <span>成本 ${fmtNumber(delta.money_saved_yuan || 0, 1)} 元</span>
      `;
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
      if (routeId !== "compare") teardownCompare(); // 离开对比页：停对比 tick + 销毁两张对比地图
      destroyLiveMap();
      view.dataset.routeView = routeId;
      const renderers = {
        live: renderLivePage,
        compare: renderComparePage,
        decisions: renderDecisionsPage,
        memory: renderMemoryPage,
        orders: renderOrdersPage,
        riders: renderRidersPage
      };
      view.innerHTML = renderers[routeId]();
      if (routeId === "live") {
        hydrateLivePage();
      } else if (routeId === "compare") {
        hydrateComparePage();
      } else if (routeId === "decisions") {
        hydrateDecisionPage();
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
              <span class="advantage-kicker">实时累计对比栏</span>
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
              <select id="playback-speed" class="select-control" data-control="speed"><option value="0.5">0.5x</option><option value="1">1x</option><option value="2">2x</option><option value="4">4x</option></select>
              <select id="playback-pace" class="select-control" data-control="playback-pace"><option value="demo">演示快进</option><option value="realtime">逐秒播放</option></select>
              <select id="inference-mode" class="select-control" data-control="mode"><option value="current">当前算法</option><option value="compare">对比</option><option value="overlay">叠加</option></select>
              <div class="runtime-strip" data-inference-runtime="status">
                <div class="runtime-cell"><span>状态</span><b id="inference-state-label">未开始</b></div>
                <div class="runtime-cell" data-runtime="clock"><span>推演时间</span><b id="inference-clock">${escapeHtml(clockPrecise(inferenceState.currentTimeS))}</b></div>
                <div class="runtime-cell"><span>倍速</span><b id="inference-speed-label">${inferenceState.speed}x</b></div>
                <div class="runtime-cell"><span>播放方式</span><b id="inference-playback-pace-label">${escapeHtml(playbackPaceLabels[inferenceState.playbackPace])}</b></div>
                <div class="runtime-cell"><span>模式</span><b id="inference-mode-label">${escapeHtml(inferenceModeLabels[inferenceState.mode])}</b></div>
                <div class="runtime-cell"><span>释放事件</span><b id="inference-event-count">${releasedEvents(inferenceState.currentTimeS).length}</b></div>
              </div>
              <div id="inference-progress-control" class="inference-progress" role="slider" tabindex="0" aria-label="拖动跳转到对应推演秒数" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${inferenceProgressPct()}" aria-valuetext="${escapeHtml(`${clockPrecise(inferenceState.currentTimeS)} / ${fmtNumber(inferenceProgressPct(), 1)}%`)}" title="拖动进度条跳转到对应推演秒数；左右方向键：短按 ±1 分钟，长按连续 ±1 秒"><span id="inference-progress-bar" style="--progress:${inferenceProgressPct()}%"></span></div>
              </div>
              <div class="card map-panel" data-resizable-map-panel="vertical">
              <div class="card-head"><h3>实时地图层</h3><div class="card-head-tools"><span id="map-runtime-hint">商家 / 订单 / 骑手 / 路线 / 热点</span><button id="live-map-fullscreen" class="map-fullscreen-btn" type="button" title="全屏展示地图（ESC 退出）" aria-label="全屏展示地图">⛶ 全屏</button></div></div>
              <div id="live-map-resize-handle-top" class="map-resize-handle map-resize-handle-top" data-resize-dir="top" role="separator" aria-orientation="horizontal" aria-label="向上拖动放大地图" title="向上拖动放大地图、向下缩小" tabindex="0"></div>
              <div id="live-map-stage" class="real-map-stage schematic-map" data-map-layer="primary" data-real-map-provider="leaflet" data-tile-layer="cartodb-light-nolabels" data-real-map-status="loading" data-map-mode="${escapeHtml(inferenceState.mode)}" data-frame-id="${escapeHtml(currentFrame.id)}">
                ${renderLiveMapLayer(currentFrame)}
              </div>
              <div id="live-map-resize-handle" class="map-resize-handle" data-resize-dir="bottom" role="separator" aria-orientation="horizontal" aria-label="向下拖动放大地图" title="向下拖动放大地图、向上缩小" tabindex="0"></div>
              <div id="live-fs-explain-dock" class="fs-explain-dock" data-collapsed="false" aria-hidden="true">
                <div class="fs-progress-row">
                  <span id="fs-clock" class="fs-clock">${escapeHtml(clockPrecise(inferenceState.currentTimeS))}</span>
                  <div id="live-fs-progress-slot" class="fs-progress-slot"></div>
                  <span class="fs-progress-hint">拖动或 ← → 键前后调时间</span>
                </div>
                <div class="fs-explain-dock-head">
                  <b>每条线说明</b>
                  <div class="fs-dock-sep"></div>
                  <div class="fs-dock-controls">
                    <button id="fs-pause" class="fs-dock-btn" type="button" data-state="paused" title="开始 / 暂停 / 继续推演">▶ 开始</button>
                    <label class="fs-ctrl">倍速
                      <select id="fs-speed" title="播放倍速"><option value="0.5">0.5x</option><option value="1">1x</option><option value="2">2x</option><option value="4">4x</option></select>
                    </label>
                    <label class="fs-ctrl">播放
                      <select id="fs-pace" title="演示快进 / 逐秒演示"><option value="demo">演示快进</option><option value="realtime">逐秒演示</option></select>
                    </label>
                  </div>
                  <span id="fs-explain-caption" class="fs-explain-caption"></span>
                  <button id="fs-explain-toggle" class="fs-explain-toggle" type="button" title="折叠/展开此面板">收起 ▾</button>
                </div>
                <div id="live-fs-explain-slot" class="fs-explain-dock-body"></div>
              </div>
              </div>
              <div class="card line-explain-panel">
                <div class="card-head"><h3>每条线说明</h3><span id="line-explain-caption">当前时刻真实在跑的线，逐条对应地图</span></div>
                <div id="live-line-explain" class="line-explain-grid">${renderLiveRouteBreakdown()}</div>
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
      const byId = Object.fromEntries(workbench.memory.items.map((item) => [item.id, item]));
      const stats = memoryStats();
      const system = workbench.memory.system || {};
      const layers = workbench.memory.layers || [];
      const profiles = workbench.memory.profiles || [];
      const recallChain = workbench.memory.recall_chain || [];
      const writebackLoop = workbench.memory.writeback_loop || [];
      return `
        ${pageHeader("memory", "长期记忆中心", "把调度经验组织为长期记忆、画像、召回链和回写反馈，展示记忆如何让下一轮派单更强。")}
        <div class="page-grid memory-workspace hermes-memory-workspace" data-page="memory" data-memory-route="hermes-long-term" data-memory-model="global-profile-recall-feedback">
          <section id="memory-command-center" class="memory-command-center" aria-label="Hermes-style long term memory command center">
            <div class="memory-command-copy">
              <span class="memory-kicker">长期记忆视图</span>
              <h3>长期记忆中枢</h3>
              <p>这里不是日志列表、资产表或文档中心。系统把每天推理中的有效经验沉淀为全局策略记忆和画像记忆，再在新一轮规划评分前召回，最后用调度结果回写置信度。</p>
              <div class="memory-model-row">
                <span>全局记忆</span>
                <span>画像记忆</span>
                <span>召回链</span>
                <span>回写反馈</span>
              </div>
            </div>
            <div id="memory-overview" class="memory-command-metrics">
              ${renderMemoryOverview(stats, system)}
            </div>
          </section>
          <div class="memory-operating-grid">
            <section id="memory-layer-board" class="card" data-memory-surface="memory-layers">
              <div class="card-head"><h3>记忆层结构</h3><span>全局策略 / 画像记忆</span></div>
              <div class="card-body memory-layer-grid">
                ${layers.map(renderMemoryLayerCard).join("")}
              </div>
            </section>
            <aside id="memory-profile-board" class="memory-profile-board" data-memory-surface="profiles">
              <h3>画像记忆</h3>
              <p>画像不是人员档案，而是系统在历史推理中沉淀的供给、商圈和订单风险模式。</p>
              <div class="memory-profile-list">
                ${profiles.map(renderMemoryProfile).join("")}
              </div>
            </aside>
          </div>
          <div class="memory-flow-grid">
            <section id="memory-recall-chain" class="card" data-memory-surface="recall-chain">
              <div class="card-head"><h3>当前召回链路</h3><span>命中 -> 注入 -> 决策 -> 回写</span></div>
              <div class="card-body memory-flow-lane">
                ${recallChain.map((step, index) => renderMemoryRecallStep(step, byId, index)).join("")}
              </div>
            </section>
            <section id="memory-writeback-loop" class="card" data-memory-surface="writeback-loop">
              <div class="card-head"><h3>记忆形成与反馈闭环</h3><span>新沉淀 / 已整理 / 命中中 / 效果反馈</span></div>
              <div class="card-body memory-flow-lane">
                ${writebackLoop.map((step, index) => renderMemoryWritebackStep(step, byId, index)).join("")}
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
      const showAllOrderLabels = shouldShowAllOrderLabels(frame, routes);
      const merchants = activeMerchantsForMap(orders);
      const waitingLinks = waitingLinksForMap(orders);
      return `
        <div id="map-action-status" class="map-action-status" data-map-action="active">${renderMapActionStatus(frame, routes, riders, orders)}</div>
        <div class="map-mode-chip">${escapeHtml(inferenceModeLabels[inferenceState.mode])} / ${escapeHtml(frame.id)}</div>
        <div id="leaflet-live-map" class="leaflet-live-map" data-leaflet-map="live" data-tile-provider="${escapeHtml(workbench.map.tile_provider || liveTileLayer.id)}" aria-label="匿名无标签真实地图"></div>
        <div class="fallback-map-overlay" data-fallback-map="screen-coordinate" aria-hidden="true">
          ${renderMapRoutes(routes, riders, waitingLinks)}
          ${renderHotspots()}
          ${renderMapDots("merchant", merchants, "position")}
          ${renderMapDots("rider", riders, "position")}
          ${renderMapDots("order", orders.slice(0, 96), "dropoff", focusOrderIds, showAllOrderLabels)}
        </div>
        ${renderMapLegend()}
      `;
    }

    // 把「已派单·执行中」的路线拆成两段：取餐段(骑手→商家) + 配送段(商家→客户)。
    function routeRenderSegments(route) {
      const lane = route.renderLane || route.lane;
      const poly = route.polyline || [];
      if (["ours", "difference"].includes(lane) && poly.length >= 3) {
        return [
          { points: [poly[0], poly[1]], lane: "pickup", route },
          { points: poly.slice(1), lane, route }
        ];
      }
      return [{ points: poly, lane, route }];
    }

    function renderMapRoutes(routes, riders = [], waitingLinks = []) {
      const completedRows = liveCompletedRoutes();
      if (!routes.length && !waitingLinks.length && !completedRows.length) return "";
      const progressLines = activeProgressRoutes(routes);
      const segments = routes.flatMap(routeRenderSegments);
      return `
        <svg class="map-route" data-route-count="${routes.length}" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          ${completedRows.map((route) => {
            const points = (route.polyline || []).map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="completed-route" data-order-ref="${escapeHtml(route.order_label || "")}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
          ${waitingLinks.map((link) => {
            const points = (link.polyline || []).map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="pending-link" data-order-ref="${escapeHtml(link.order_label || "")}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
          ${segments.map((segment) => {
            const points = (segment.points || []).map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="${escapeHtml(segment.lane)}" data-order-ref="${escapeHtml(actionDisplayLabel("order", segment.route))}" data-rider-ref="${escapeHtml(actionDisplayLabel("rider", segment.route))}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
          ${progressLines.map((route) => {
            const points = route.progressPolyline.map((point) => `${point.screen_x},${point.screen_y}`).join(" ");
            return `<polyline class="route-line" data-lane="active-progress" data-order-ref="${escapeHtml(actionDisplayLabel("order", route))}" data-rider-ref="${escapeHtml(actionDisplayLabel("rider", route))}" points="${escapeHtml(points)}"></polyline>`;
          }).join("")}
          ${routes.filter((route) => shouldShowRouteAssignmentLabel(route) && route.order_id === highlightedOrderId).map((route) => {
            const point = routeLabelPoint(route);
            if (!point) return "";
            return `<text class="route-assignment-label" data-lane="${escapeHtml(route.renderLane || route.lane)}" x="${point.screen_x}" y="${point.screen_y}" text-anchor="middle">${escapeHtml(routeAssignmentLabel(route))}</text>`;
          }).join("")}
        </svg>
      `;
    }

    function shouldShowRouteAssignmentLabel(route) {
      const lane = route.renderLane || route.lane;
      return ["ours", "difference"].includes(lane);
    }

    function routeAssignmentLabel(route) {
      return actionPairLabel(route);
    }

    function routeLabelPoint(route) {
      const points = route.polyline || [];
      if (points.length >= 3) return interpolateMapPoint(points[1], points[2], .72);
      if (points.length >= 2) return interpolateMapPoint(points[0], points[1], .5);
      return points[0] || null;
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

    function activeMapRider(riders = []) {
      return riders.find((rider) => rider.motion === "moving") || null;
    }

    // 执行进度（绿色“已走过”线）——全局一致。
    // 关键修复：不再靠“把某条路线匹配到一个 moving 骑手对象”来决定画不画绿线，
    // 而是对【每一条正在执行的路线】直接用订单生命周期算进度：
    //   progress = (T − assign_at_s) / (complete_at_s − assign_at_s)
    // 然后沿 route.polyline 精确铺到当前插值点。这样只要是“执行中”的单，
    // 无论取餐段还是配送段，都必有一条绿色“已走过”覆盖已行驶部分，未行驶部分才露出
    // 橙(取餐)/teal(配送)。彻底消除“有的取餐段是绿的、有的却整条橙色”的不一致，
    // 也去掉了旧的 slice(0,4) 封顶（高峰期 5~8 条执行中路线里，被截掉的那几条正是“满橙线”）。
    function activeProgressRoutes(routes = [], simTimeS = inferenceState.currentTimeS) {
      return routes
        .filter((route) => !["baseline", "previous"].includes(route.renderLane || route.lane))
        .map((route) => {
          const life = orderLifecycle[route.order_id];
          if (!life || !life.dispatched || !Number.isFinite(life.assign_at_s) || !Number.isFinite(life.complete_at_s)) return null;
          const span = Math.max(1, life.complete_at_s - life.assign_at_s);
          const progress = clamp((simTimeS - life.assign_at_s) / span, 0, 1);
          if (progress <= 0.001) return null; // 刚派单、还没起步的不画绿线
          const progressPolyline = progressPolylineForRoute(route, progress);
          return progressPolyline.length >= 2 ? {...route, progressPolyline} : null;
        })
        .filter(Boolean);
    }

    // 沿折线精确取“已走过”那一段：start → 按 progress 插值出的当前点。
    // 折线按“段数”均匀参数化（3 点=2 段：0~0.5 在取餐段，0.5~1 在配送段），
    // 不再整取到商家节点、也不再依赖骑手对象的 position。
    function progressPolylineForRoute(route, progress) {
      const points = route.polyline || [];
      if (points.length < 2) return [];
      const p = clamp(Number(progress) || 0, 0, 1);
      const segCount = points.length - 1;
      const exact = p * segCount;
      const segIdx = Math.min(segCount - 1, Math.floor(exact));
      const frac = exact - segIdx;
      const out = points.slice(0, segIdx + 1);
      out.push(interpolateMapPoint(points[segIdx], points[segIdx + 1], frac));
      return out;
    }

    function orderStateCounts(orders = []) {
      const counts = { waiting: 0, dispatched: 0, completed: 0 };
      for (const order of orders) {
        const state = order.map_order_state || "waiting";
        if (state in counts) counts[state] += 1;
      }
      return counts;
    }

    function orderStateSummaryText(orders = []) {
      const counts = orderStateCounts(orders);
      return `待派单 ${counts.waiting} · 执行中 ${counts.dispatched} · 已完成 ${counts.completed}`;
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
        const merchantLabel = moving.merchant_label || merchantLabelForOrder(moving.order_id);
        const phase = moving.phase || "配送中";
        const chain = merchantLabel ? `${merchantLabel} → ${riderLabel} → ${orderLabel}` : `${riderLabel} → ${orderLabel}`;
        const extraOrders = orderLabelsForIds(moving.task_order_ids || []).filter((label) => label !== orderLabel);
        const taskChain = extraOrders.length ? `，本轮还承接 ${extraOrders.join("、")}` : "";
        return `<strong>${escapeHtml(riderLabel)} ${escapeHtml(phase)}：${escapeHtml(chain)}</strong><span>任务链进度 ${fmtNumber((moving.progress || 0) * 100, 0)}%（骑手→商家取餐→送客户）${escapeHtml(taskChain)}。当前地图：${escapeHtml(stateText)}。变化原因：${escapeHtml(reason)}</span>`;
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
          const merchantLabel = merchantLabelForOrder(route.order_id);
          const span = Math.max(1, (life.complete_at_s || t) - (life.assign_at_s || t));
          const prog = clamp((t - (life.assign_at_s || t)) / span, 0, 1);
          const phase = prog < merchantFractionForPolyline(route.polyline) ? "取餐中" : "配送中";
          const chain = merchantLabel ? `${merchantLabel} → ${riderLabel} → ${orderLabel}` : `${riderLabel} → ${orderLabel}`;
          return `<div class="list-item" data-dispatch-order="${escapeHtml(orderLabel)}"><strong>${escapeHtml(chain)}</strong><p>${escapeHtml(phase)} / 预计还需 ${fmtNumber(remainingMin, 1)} 分钟送达</p></div>`;
        })
        .join("");
      const tail = waitingCount ? `<div class="list-item"><strong>另有 ${waitingCount} 个待派单</strong><p>已释放、等待下一次派单决策，地图上以「待派单」样式显示。</p></div>` : "";
      return rows + tail;
    }

    // 底部「每条线说明」面板：把地图上当前真实在跑的每条线逐条拆开讲清楚，
    // 与地图一一对应，也承担“每条线是什么/数量对不对”的核对职责（减轻地图上标签压力）。
    function renderLiveRouteBreakdown() {
      if (!inferenceState.started) {
        return `<div class="line-explain-empty">开始推理后，这里会逐条列出地图上的每条线：<b>取餐段</b>(骑手→商家) + <b>配送段</b>(商家→客户)，以及<b>待派连线</b>(商家→客户，已下单待派)。</div>`;
      }
      const t = inferenceState.currentTimeS;
      const dispatched = liveDispatchedRoutes(t).slice().sort((a, b) => (orderLifecycle[a.order_id]?.assign_at_s || 0) - (orderLifecycle[b.order_id]?.assign_at_s || 0));
      const waiting = (workbench.map.anchors.orders || []).filter((order) => orderStatusAt(order.id, t) === "waiting");
      const cards = [];
      for (const route of dispatched) {
        const life = orderLifecycle[route.order_id] || {};
        const orderLabel = actionDisplayLabel("order", route);
        const riderLabel = actionDisplayLabel("rider", route);
        const merchantLabel = merchantLabelForOrder(route.order_id);
        const span = Math.max(1, (life.complete_at_s || t) - (life.assign_at_s || t));
        const prog = clamp((t - (life.assign_at_s || t)) / span, 0, 1);
        const atMerchant = prog >= merchantFractionForPolyline(route.polyline);
        const selected = highlightedOrderId === route.order_id ? " data-selected='1'" : "";
        cards.push(`<div class="line-explain-card" role="button" tabindex="0" title="点选高亮地图上这条线" data-order="${escapeHtml(orderLabel)}" data-order-id="${escapeHtml(route.order_id)}"${selected}>
          <div class="line-explain-head"><b>${escapeHtml(riderLabel)} → ${escapeHtml(orderLabel)}</b><span class="line-explain-badge" data-phase="${atMerchant ? "deliver" : "pickup"}">${atMerchant ? "配送中" : "取餐中"}</span></div>
          <div class="line-explain-leg"><i class="leg-swatch" data-lane="pickup"></i><span>取餐段：${escapeHtml(riderLabel)} → 商家${escapeHtml(merchantLabel)}</span><em>${atMerchant ? "已到店取餐" : "前往商家中"}</em></div>
          <div class="line-explain-leg"><i class="leg-swatch" data-lane="ours"></i><span>配送段：商家${escapeHtml(merchantLabel)} → 客户${escapeHtml(orderLabel)}</span><em>${atMerchant ? "配送中" : "待取餐后出发"}</em></div>
          <div class="line-explain-foot">整体进度 ${fmtNumber(prog * 100, 0)}%</div>
        </div>`);
      }
      // 已送达卡片：面板里只列最近 6 条（地图淡线可留更久），避免卡片过多把面板撑长。
      for (const route of liveCompletedRoutes(t).slice(-6)) {
        const life = orderLifecycle[route.order_id] || {};
        const orderLabel = actionDisplayLabel("order", route);
        const riderLabel = actionDisplayLabel("rider", route);
        const merchantLabel = merchantLabelForOrder(route.order_id);
        const selected = highlightedOrderId === route.order_id ? " data-selected='1'" : "";
        const doneAt = life.complete_at_s != null ? clock(life.complete_at_s) : "";
        cards.push(`<div class="line-explain-card" role="button" tabindex="0" title="点选高亮地图上这条线" data-done="1" data-order="${escapeHtml(orderLabel)}" data-order-id="${escapeHtml(route.order_id)}"${selected}>
          <div class="line-explain-head"><b>${escapeHtml(riderLabel)} → ${escapeHtml(orderLabel)}</b><span class="line-explain-badge" data-phase="done">已送达 ✓</span></div>
          <div class="line-explain-leg"><i class="leg-swatch" data-lane="pickup"></i><span>取餐段：${escapeHtml(riderLabel)} → 商家${escapeHtml(merchantLabel)}</span><em>已取餐</em></div>
          <div class="line-explain-leg"><i class="leg-swatch" data-lane="ours"></i><span>配送段：商家${escapeHtml(merchantLabel)} → 客户${escapeHtml(orderLabel)}</span><em>已送达</em></div>
          <div class="line-explain-foot">整体进度 100%${doneAt ? ` · ${escapeHtml(doneAt)} 送达` : ""}</div>
        </div>`);
      }
      for (const order of waiting) {
        const merchantLabel = merchantLabelForOrder(order.id);
        const selected = highlightedOrderId === order.id ? " data-selected='1'" : "";
        cards.push(`<div class="line-explain-card" role="button" tabindex="0" title="点选高亮地图上这条线" data-pending="1" data-order="${escapeHtml(order.map_label)}" data-order-id="${escapeHtml(order.id)}"${selected}>
          <div class="line-explain-head"><b>商家${escapeHtml(merchantLabel)} → 客户${escapeHtml(order.map_label)}</b><span class="line-explain-badge" data-phase="pending">待派单</span></div>
          <div class="line-explain-leg"><i class="leg-swatch" data-lane="pending-link"></i><span>待派连线：已下单，等待派单决策</span><em>暂未分配骑手</em></div>
        </div>`);
      }
      if (!cards.length) {
        return `<div class="line-explain-empty">当前没有正在执行、待派或刚送达的线。累计送达 ${deliveredCountAt(t)} 单。</div>`;
      }
      return cards.join("");
    }

    function renderHotspots() {
      // 与 Leaflet 版一致：只在生效时段画热点，休眠时段不画（备用示意图底图同样口径）。
      return workbench.map.hotspots.map((hotspot, index) => {
        const active = hotspot.start_s <= inferenceState.currentTimeS && inferenceState.currentTimeS <= hotspot.end_s;
        if (!active) return "";
        const label = mapEntityLabel("hotspot", hotspot, index);
        return `<div class="hotspot" data-active="true" data-map-ref="${escapeHtml(label)}" title="${escapeHtml(mapEntityTitle("hotspot", label, {phase: "active"}))}" style="--x:${hotspot.center.screen_x};--y:${hotspot.center.screen_y};--severity:${hotspot.severity}"></div>`;
      }).join("");
    }

    function renderMapDots(kind, items, positionKey, focusOrderIds = new Set(), showAllOrderLabels = false) {
      return items.map((item, index) => {
        const pos = item[positionKey];
        const release = kind === "order" && item.created_at_s >= inferenceState.currentTimeS - 900 ? "new" : "stable";
        const motion = kind === "rider" ? (item.motion || "snapshot") : "";
        const label = mapEntityLabel(kind, item, index);
        const orderState = kind === "order" ? (item.map_order_state || "active") : "";
        const dimmed = isDimmed(kind, item);
        const showLabel = dimmed ? false : shouldShowMapLabel(kind, item, index, label, focusOrderIds, showAllOrderLabels);
        return `<span class="map-dot" data-kind="${escapeHtml(kind)}" data-map-ref="${escapeHtml(label)}" data-map-label="${escapeHtml(label)}" data-show-label="${showLabel}" data-dim="${dimmed}" data-release="${escapeHtml(release)}" data-motion="${escapeHtml(motion)}" data-order-state="${escapeHtml(orderState)}" data-phase="${escapeHtml(item.phase || "")}" title="${escapeHtml(mapEntityTitle(kind, label, item))}" aria-label="${escapeHtml(mapEntityTitle(kind, label, item))}" style="--x:${pos.screen_x};--y:${pos.screen_y}"></span>`;
      }).join("");
    }

    function renderMapLegend() {
      const entityItems = [
        ["merchant", "商家（取餐点）"],
        ["rider", "骑手（实心=配送中 / 空心=空闲）"],
        ["hotspot", "热点"]
      ];
      // 客户订单点按生命周期着色，图例逐一解释，避免“点消失/变色看不懂”。
      const orderStateItems = [
        ["waiting", "客户单·待派单（空心橙）"],
        ["dispatched", "客户单·执行中（实心橙）"],
        ["completed", "客户单·已送达（绿 ✓）"]
      ];
      // 线条语义与实际绘制严格一致：任务链 = 取餐段(骑手→商家) + 配送段(商家→客户)。
      const routeItems = [
        ["pickup", "取餐段（骑手→商家）"],
        ["ours", "配送段（商家→客户）"],
        ["active-progress", "执行进度（骑手已走过）"],
        ["completed-route", "已送达路线（淡出）"],
        ["pending-link", "待派连线（商家→客户）"]
      ];
      if (inferenceState.mode !== "current") {
        routeItems.push(["baseline", "基线路线"]);
        routeItems.push(["difference", "差异路线（派给不同骑手）"]);
      }
      return `
        <div class="map-legend">
          ${entityItems.map(([kind, label]) => `<span class="legend-item"><i class="legend-dot" data-kind="${escapeHtml(kind)}"></i>${escapeHtml(label)}</span>`).join("")}
          ${orderStateItems.map(([state, label]) => `<span class="legend-item"><i class="legend-dot" data-kind="order" data-order-state="${escapeHtml(state)}"></i>${escapeHtml(label)}</span>`).join("")}
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

    function hasCurrentMapRoute(routes = []) {
      return routes.some((route) => ["ours", "difference"].includes(route.renderLane || route.lane));
    }

    function shouldShowAllOrderLabels(frame, routes = []) {
      // 订单编号始终可追踪：默认展示全部已释放订单的 O 编号（已完成的淡出点除外）。
      return true;
    }

    function shouldShowMapLabel(kind, item, index, label, focusOrderIds = new Set(), showAllOrderLabels = false) {
      if (kind === "rider") return true;
      if (kind === "merchant") return true; // 取餐点显示商家 M 编号，建立“商家↔订单”关系
      if (kind !== "order") return false;
      return true; // 待派单/执行中/已完成 三态都显示订单编号，方便逐单追踪与核对数量
    }

    function mapEntityTitle(kind, label, item = {}) {
      const kindLabel = {
        merchant: "商家·取餐点",
        rider: "骑手",
        order: "客户订单",
        hotspot: "热点"
      }[kind] || "实体";
      const details = [];
      // 仅对实时地图上的订单点补充生命周期信息（这些对象带有 map_order_state），
      // 不影响其他页面（订单页/骑手页小地图）复用同一 tooltip 函数时的展示。
      if (kind === "order" && item.map_order_state) {
        const life = orderLifecycle[item.id];
        details.push(`状态:${orderStatusLabel(item.map_order_state)}`);
        const merchant = merchantLabelForOrder(item.id);
        if (merchant) details.push(`商家:${merchant}`);
        if (life && life.created_at_s != null) details.push(`下单:${clock(life.created_at_s)}`);
        if (life && life.dispatched && life.courier_label) details.push(`骑手:${life.courier_label}`);
      }
      if (kind === "rider") {
        if ((item.motion === "moving" || item.motion === "idle") && item.phase) details.push(item.phase); // 取餐中 / 配送中 / 空闲·待命
        else if (item.phase) details.push(displayRiderState(item.phase));
        if (item.leg === "pickup" && item.merchant_label) details.push(`前往商家:${item.merchant_label}`);
        if (item.order_id) details.push(`当前单:${actionDisplayLabel("order", { order_id: item.order_id })}`);
        if (item.task_order_ids && item.task_order_ids.length > 1) details.push(`任务链:${orderLabelsForIds(item.task_order_ids).join(" + ")}`);
      }
      if (item.risk_level) details.push(`风险:${displayRisk(item.risk_level)}`);
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

    // 交互（缩放/拖动）结束后，用当前时刻数据重建一次图层，补上交互期间跳过的更新。
    function refreshLiveOverlayNow() {
      if (!liveLeafletMap || !liveLeafletOverlayGroup) return;
      const frame = frameForTime(inferenceState.currentTimeS);
      updateLiveLeafletOverlay(frame, mapRouteRows(frame), riderPositionsForFrame(frame), ordersForMap(frame));
    }

    function updateLiveLeafletOverlay(frame, routes, riders, orders) {
      const stage = document.getElementById("live-map-stage");
      if (!window.L || !stage || !liveLeafletMap || !liveLeafletOverlayGroup || stage.dataset.realMapStatus !== "leaflet") return false;
      if (liveMapInteracting) return true; // 缩放/拖动期间不重建图层，交互结束再统一重建，避免逐帧卡顿
      try {
        stage.dataset.leafletRouteCount = String(routes.length);
        stage.dataset.leafletMarkerCount = String(workbench.map.anchors.merchants.slice(0, 16).length + riders.length + orders.slice(0, 96).length);
        const chip = stage.querySelector(".map-mode-chip");
        if (chip) chip.textContent = `${inferenceModeLabels[inferenceState.mode]} / ${frame.id}`;
        liveLeafletOverlayGroup.clearLayers();
        renderLeafletMapLayers(liveLeafletOverlayGroup, frame, routes, riders, orders);
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
        stage.dataset.leafletMarkerCount = String(workbench.map.anchors.merchants.slice(0, 16).length + riders.length + orders.slice(0, 96).length);
        const map = window.L.map(container, {
          attributionControl: true,
          boxZoom: true,
          doubleClickZoom: false, // 双击留给“双击线条→反查底部卡片”，避免同时触发地图缩放
          keyboard: false, // 关掉 Leaflet 方向键平移：方向键专用于时间线前后 ±1 分钟，地图只靠鼠标拖动
          preferCanvas: false,
          scrollWheelZoom: true,
          zoomControl: false,
          // 缩放动画保持开启：动画期间用 GPU 的 CSS 变换平滑过渡、动画结束才重投影一次（便宜），
          // 关掉反而让矢量图层每次缩放“硬跳”→ 连续滚会闪烁。真正的缩放卡顿已由“交互期间停重建 +
          // 松手不强制重建”解决，无需靠关动画。
          zoomAnimation: true,
          markerZoomAnimation: true,
          // 缩放手感：细粒度小步 + 需要多滚才缩一级，避免太敏感难控（尤其触控板）
          zoomSnap: 0.25,             // 允许 0.25 级的分数缩放，落点更细
          zoomDelta: 0.5,             // 缩放按钮每次 ±0.5 级，更温和
          wheelPxPerZoomLevel: 160,   // 默认 60→160：需要滚更多才缩一级，降低灵敏度
          wheelDebounceTime: 80       // 合并高频滚动事件（尤其触控板），不再一碰就狂缩
        });
        liveLeafletMap = map;
        // 缩放/拖动地图期间暂停图层重建（见 updateLiveLeafletOverlay）。结束后不强制重建——
        // Leaflet 已在缩放/平移时自动把现有图层重投影/位移到正确位置，强制重建纯属浪费且造成松手卡顿。
        // 播放中下一个 heavy tick 会自然刷新；暂停时位置本就没变，无需重建。
        map.on("movestart zoomstart", () => { liveMapInteracting = true; });
        map.on("moveend zoomend", () => { liveMapInteracting = false; });
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
        renderLeafletMapLayers(liveLeafletOverlayGroup, frame, routes, riders, orders);
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

    function renderLeafletMapLayers(layerGroup, frame, routes, riders, orders) {
      const merchants = activeMerchantsForMap(orders);
      const waitingLinks = waitingLinksForMap(orders);
      renderLeafletHotspots(layerGroup);
      renderLeafletRoutes(layerGroup, routes, riders, waitingLinks);
      renderLeafletMarkers(layerGroup, "merchant", merchants, "position");
      renderLeafletMarkers(layerGroup, "rider", riders, "position");
      renderLeafletMarkers(layerGroup, "order", orders.slice(0, 96), "dropoff", focusedMapOrderIds(routes, riders), shouldShowAllOrderLabels(frame, routes));
    }

    function mapBounds() {
      if (!window.L || !workbench.map.bounds || workbench.map.bounds.length < 2) return null;
      return window.L.latLngBounds(workbench.map.bounds.map(mapPoint));
    }

    function mapPoint(point) {
      return [Number(point.lat), Number(point.lng)];
    }

    function renderLeafletHotspots(map) {
      const color = "#b7791f";
      workbench.map.hotspots.forEach((hotspot, index) => {
        const active = hotspot.start_s <= inferenceState.currentTimeS && inferenceState.currentTimeS <= hotspot.end_s;
        // 只在“生效时段”画热点：某个扰动（下雨/爆单/拥堵/缺运力）正发生时才在地图上出现对应的圈；
        // 休眠时段完全不画，避免一堆灰同心圈全天挂着干扰画面。“地图上出现一个圈”＝此刻此处正有扰动。
        if (!active) return;
        const label = mapEntityLabel("hotspot", hotspot, index);
        const radius = 230 + Number(hotspot.severity || 1) * 220;
        // ① 填充圆只做背景，interactive:false → 指针完全穿透到里面的线和点（不再“吃掉”悬浮/点击）；
        window.L.circle(mapPoint(hotspot.center), {
          radius, color, fillColor: color,
          fillOpacity: .16, opacity: .42, weight: 1, interactive: false
        }).addTo(map);
        // ② 只保留“无填充”的一圈描边环可交互（fill:false → 内部不接收指针，仅环线本身接收），
        //    悬浮热点边缘能看到热点说明，环内部不挡线/点。
        window.L.circle(mapPoint(hotspot.center), {
          radius, color, weight: 2.4, opacity: .62, fill: false
        }).bindTooltip(escapeHtml(mapEntityTitle("hotspot", label, {phase: "active"})), { sticky: true }).addTo(map);
      });
    }

    // 高亮某条线时给它的样式叠加：更粗 + 满不透明 + 描边光晕 + （点击瞬间）闪烁两下
    function emphasizeStyle(style, orderId) {
      if (!highlightedOrderId) return style;
      if (orderId === highlightedOrderId) {
        const cls = flashPending ? "route-highlighted route-flash" : "route-highlighted";
        return { ...style, weight: Number(style.weight || 4) + 3, opacity: 1, className: cls };
      }
      return { ...style, opacity: (Number(style.opacity) || .8) * 0.25 }; // 聚焦时淡化其它线
    }
    function renderLeafletRoutes(map, routes, riders = [], waitingLinks = []) {
      const progressRoutes = activeProgressRoutes(routes);
      // 聚焦模式下，非焦点线的白色描边也一起淡化，避免淡线仍被高亮白边“拽”出来。
      const haloFor = (lane, orderId) => {
        const halo = routeHaloStyle(lane);
        if (highlightedOrderId && orderId !== highlightedOrderId) halo.opacity = (Number(halo.opacity) || .9) * 0.22;
        return halo;
      };
      // 先画“已送达”淡出线（垫底），再画待派/执行中，保证进行中的线在最上层。图例已解释此淡线。
      for (const route of liveCompletedRoutes()) {
        const points = (route.polyline || []).map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        if (points.length < 2) continue;
        window.L.polyline(points, emphasizeStyle(routeStyle("completed-route"), route.order_id)).addTo(map);
        bindRouteHit(map, points, route.order_id, escapeHtml(`已送达 / 商家${merchantLabelForOrder(route.order_id)} → 骑手${actionDisplayLabel("rider", route)} → 客户${route.order_label || ""}（双击反查下方卡片）`));
      }
      for (const link of waitingLinks) {
        const points = (link.polyline || []).map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        if (points.length < 2) continue;
        window.L.polyline(points, haloFor("pending-link", link.order_id)).addTo(map);
        window.L.polyline(points, emphasizeStyle(routeStyle("pending-link"), link.order_id)).addTo(map);
        bindRouteHit(map, points, link.order_id, escapeHtml(`已下单待派单 / 商家${merchantLabelForOrder(link.order_id)} → 客户${link.order_label || ""}（等待派单决策，双击反查下方卡片）`));
      }
      for (const route of routes) {
        for (const segment of routeRenderSegments(route)) {
          const points = (segment.points || []).map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
          if (points.length < 2) continue;
          window.L.polyline(points, haloFor(segment.lane, route.order_id)).addTo(map);
          window.L.polyline(points, emphasizeStyle(routeStyle(segment.lane), route.order_id)).addTo(map);
        }
        // 整条路线只叠一条命中线（覆盖取餐段+配送段），减少路径数、悬浮/双击照常
        const routePts = (route.polyline || []).map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        bindRouteHit(map, routePts, route.order_id, escapeHtml(`${routeTooltip(route)}（双击反查下方卡片）`));
      }
      for (const route of progressRoutes) {
        const points = route.progressPolyline.map(mapPoint).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
        if (points.length < 2) continue;
        const dim = highlightedOrderId && route.order_id !== highlightedOrderId;
        window.L.polyline(points, { color: "#ffffff", weight: 13, opacity: dim ? .18 : .8, lineCap: "round", interactive: false }).addTo(map);
        const prog = routeProgressStyle();
        if (dim) prog.opacity = 0.25;
        window.L.polyline(points, prog).bindTooltip(escapeHtml(`已走过（执行进度）/ ${routeTooltip(route)}（双击反查下方卡片）`), { sticky: true }).on("dblclick", (ev) => selectRouteFromMap(route.order_id, ev)).addTo(map);
      }
      renderLeafletRouteLabels(map, routes);
    }

    function renderLeafletRouteLabels(map, routes = []) {
      // 只给「被点选高亮」的那条线显示 O→R 标签，默认不画，避免大量标签互相压盖（问题4）。
      for (const route of routes.filter((route) => shouldShowRouteAssignmentLabel(route) && route.order_id === highlightedOrderId)) {
        const point = routeLabelPoint(route);
        if (!point || !Number.isFinite(Number(point.lat)) || !Number.isFinite(Number(point.lng))) continue;
        window.L.marker(mapPoint(point), {
          icon: window.L.divIcon({
            className: "leaflet-route-assignment",
            html: `<span>${escapeHtml(routeAssignmentLabel(route))}</span>`,
            iconAnchor: [48, 10],
            iconSize: [96, 20]
          }),
          interactive: false,
          keyboard: false,
          zIndexOffset: 420
        }).addTo(map);
      }
    }

    // 线条视觉系统：每条线都配「白色描边」在灰底地图上打底，再用「颜色=角色 + 线型=语义」区分，
    // 保证既看得清、又能一眼知道含义（评委友好）。
    function routeStyle(lane) {
      const styles = {
        // 配送段：商家→客户，主色实线、最粗（骑手带餐送达）
        ours: { color: "#0f766e", weight: 6, opacity: .96, lineCap: "round" },
        // 取餐段：骑手→商家，橙色粗虚线（骑手空手去取餐）
        pickup: { color: "#ea580c", weight: 5.5, opacity: .96, dashArray: "12 8", lineCap: "round" },
        // 待派连线：商家→客户，下单待派，靛蓝点线（还没分配骑手，用点线表达“暂定”）
        "pending-link": { color: "#4f46e5", weight: 4, opacity: .95, dashArray: "2 10", lineCap: "round" },
        // 已送达：成功绿细虚线、半透明，作为“刚送达”的淡出痕迹（不用灰，灰会糊在灰底上）
        "completed-route": { color: "#16a34a", weight: 3, opacity: .5, dashArray: "5 8", lineCap: "round" },
        // 对比模式
        previous: { color: "#64748b", weight: 2.5, opacity: .45, dashArray: "3 9", lineCap: "round" },
        baseline: { color: "#dc2626", weight: 4, opacity: .7, dashArray: "8 8", lineCap: "round" },
        difference: { color: "#d97706", weight: 6, opacity: .96, lineCap: "round" }
      };
      return styles[lane] || styles.ours;
    }

    // 白色描边：不复制虚线间隔（用实线打底），比上层线更宽，形成“白边彩线”，在任何底图上都醒目。
    function routeHaloStyle(lane) {
      const style = routeStyle(lane);
      return {
        color: "#ffffff",
        weight: Number(style.weight || 4) + 6,
        opacity: lane === "previous" ? .5 : .9,
        lineCap: "round",
        interactive: false
      };
    }

    function routeProgressStyle() {
      return {
        color: "#16a34a",
        dashArray: "8 10",
        lineCap: "round",
        interactive: false,
        opacity: 1,
        weight: 7
      };
    }

    function routeTooltip(route, lane) {
      const laneLabel = {
        ours: "配送段（商家→客户）",
        pickup: "取餐段（骑手→商家）",
        "pending-link": "已下单待派单（商家→客户）",
        previous: "旧路线",
        baseline: "基线路线",
        difference: "差异路线"
      }[lane || route.renderLane || route.lane] || "路线";
      const merchant = merchantLabelForOrder(route.order_id);
      const chain = merchant ? `${merchant} → ${actionDisplayLabel("rider", route)} → ${actionDisplayLabel("order", route)}` : actionPairLabel(route);
      return `${laneLabel} / ${chain}`;
    }

    function renderLeafletMarkers(map, kind, items, positionKey, focusOrderIds = new Set(), showAllOrderLabels = false) {
      items.forEach((item, index) => {
        const pos = item[positionKey];
        if (!pos || !Number.isFinite(Number(pos.lat)) || !Number.isFinite(Number(pos.lng))) return;
        const label = mapEntityLabel(kind, item, index);
        const release = kind === "order" && item.created_at_s >= inferenceState.currentTimeS - 900 ? "new" : "stable";
        const motion = kind === "rider" ? (item.motion || "snapshot") : "";
        const orderState = kind === "order" ? (item.map_order_state || "active") : "";
        // 聚焦模式下，非焦点元素淡化并隐藏标签，让被点选的那条链一眼跳出来。
        const dimmed = isDimmed(kind, item);
        let showLabel = dimmed ? false : shouldShowMapLabel(kind, item, index, label, focusOrderIds, showAllOrderLabels);
        // 对比页精简标注：只标“执行中订单 + 移动骑手”，空闲骑手/已送达/待派/商家一律不标，
        // 让适配缩放下也不重叠；这些实体仍以圆点/方块+图例呈现，不影响看整体格局。
        if (compareLeanLabels && !dimmed) {
          showLabel = (kind === "order" && orderState === "dispatched") || (kind === "rider" && item.motion === "moving");
        }
        const focusBoost = highlightedOrderId && !dimmed ? 600 : 0;
        window.L.marker(mapPoint(pos), {
          icon: renderLeafletMarker(kind, label, release, motion, index, showLabel, orderState),
          keyboard: false,
          opacity: dimmed ? 0.32 : 1,
          zIndexOffset: (kind === "rider" ? 500 : kind === "order" ? 300 : 100) + focusBoost
        }).bindTooltip(escapeHtml(mapEntityTitle(kind, label, item)), { direction: "top", opacity: .92, sticky: true }).addTo(map);
      });
    }

    function renderLeafletMarker(kind, label, release, motion, index = 0, showLabel = null, orderState = "") {
      const visible = showLabel ?? (kind === "rider" || (kind === "order" && index < 4));
      return window.L.divIcon({
        className: "leaflet-map-pin",
        html: `<span class="leaflet-map-pin-body" data-kind="${escapeHtml(kind)}" data-release="${escapeHtml(release)}" data-motion="${escapeHtml(motion)}" data-order-state="${escapeHtml(orderState)}"></span>${visible ? `<span class="leaflet-map-pin-label">${escapeHtml(label)}</span>` : ""}`,
        iconAnchor: [8, 8],
        iconSize: [16, 16]
      });
    }

    function renderScoreCard(label, value, detail, tone, metricId = "") {
      const metricAttrs = metricId ? ` id="${escapeHtml(metricId)}" data-metric="${escapeHtml(metricId)}"` : "";
      return `<div class="score-card" data-tone="${escapeHtml(tone)}"${metricAttrs}><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`;
    }

    function renderLiveScoreCards(score) {
      const timeoutTone = score.deltas.timeout_order_delta <= 0 ? "good" : "risk";
      const profitTone = score.deltas.profit_delta_yuan >= 0 ? "good" : "risk";
      return `
        <div class="algorithm-pair" data-score-section="algorithm-cumulative">
          ${renderScoreCard("基线/弹金算法累计", `${fmtNumber(score.baseline.total_cost_yuan, 1)} 元`, `${fmtNumber(score.baseline.total_time_cost_min, 1)} 分钟 / ${score.baseline.late_orders} 超时单`, "warn", "metric-baseline-cumulative")}
          ${renderScoreCard("我们的算法累计", `${fmtNumber(score.ours.total_cost_yuan, 1)} 元`, `${fmtNumber(score.ours.total_time_cost_min, 1)} 分钟 / ${score.ours.late_orders} 超时单`, "good", "metric-ours-cumulative")}
        </div>
        <div class="delta-grid" data-score-section="advantage-deltas">
          ${renderScoreCard("时间差异", `节省 ${fmtNumber(score.deltas.time_saved_min, 1)} 分钟`, score.deltas.headline, "good", "metric-time-delta")}
          ${renderScoreCard("金钱差异", `节省 ${fmtNumber(score.deltas.money_saved_yuan, 1)} 元`, `收益 ${fmtSigned(score.deltas.revenue_delta_yuan, 1)} 元 / 利润 ${fmtSigned(score.deltas.profit_delta_yuan, 1)} 元`, profitTone, "metric-money-delta")}
          ${renderScoreCard("超时单差异", fmtFewer(score.deltas.timeout_order_delta, "单"), `风险差异 ${fmtSigned(score.deltas.timeout_risk_delta, 3)}`, timeoutTone, "metric-timeout-delta")}
          ${renderScoreCard("收益/成本差异", `${fmtSigned(score.deltas.profit_delta_yuan, 1)} 元`, `收入 ${fmtSigned(score.deltas.revenue_delta_yuan, 1)} 元 / 成本节省 ${fmtNumber(score.deltas.money_saved_yuan, 1)} 元`, profitTone, "metric-profit-delta")}
        </div>
      `;
    }

    function renderMetricChip(metricId, label, value, detail) {
      return `<div class="metric-chip" id="metric-chip-${escapeHtml(metricId)}" data-metric="${escapeHtml(metricId)}"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`;
    }

    function renderLiveCumulativeMetrics(score) {
      return [
        renderMetricChip("time-delta", "时间差异", `${fmtNumber(score.deltas.time_saved_min, 1)} 分钟`, `基线 ${fmtNumber(score.baseline.total_time_cost_min, 1)} / 我方 ${fmtNumber(score.ours.total_time_cost_min, 1)}`),
        renderMetricChip("money-delta", "金钱差异", `${fmtNumber(score.deltas.money_saved_yuan, 1)} 元`, `基线 ${fmtNumber(score.baseline.total_cost_yuan, 1)} / 我方 ${fmtNumber(score.ours.total_cost_yuan, 1)}`),
        renderMetricChip("timeout-delta", "超时单差异", fmtFewer(score.deltas.timeout_order_delta, "单"), `基线 ${score.baseline.late_orders} / 我方 ${score.ours.late_orders}`),
        renderMetricChip("profit-delta", "收益/成本差异", `${fmtSigned(score.deltas.profit_delta_yuan, 1)} 元`, `收益 ${fmtSigned(score.deltas.revenue_delta_yuan, 1)} / 成本 ${fmtNumber(score.deltas.money_saved_yuan, 1)}`)
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
      if (document.body.dataset.route !== "live" && document.body.dataset.route !== "compare") return;
      if (!document.querySelector("[data-page='live'], [data-page='compare']")) return;
      const inferenceFinished = inferenceState.started && inferenceState.currentTimeS >= workbench.timeline.end_s;
      if (inferenceFinished && !inferenceState.running) return;
      event.preventDefault();
      toggleInferencePause();
    }

    // ===================== 双屏对比页（复用实时地图管线：左基线贪心 / 右我方 AutoSolver） =====================
    // 关键：两屏都用实时页那套 renderLeafletMapLayers 渲染，只是 setActiveModel 切到不同算法模型；
    // 播放控件(开始/暂停/演示快进/逐秒/倍速/时间轴/方向键)直接复用实时页的 inferenceState + bindLiveControls。
    let compareMapB = null, compareMapO = null, compareGroupB = null, compareGroupO = null;
    let compareInteractingB = false, compareInteractingO = false;
    let compareFullscreenBound = false;
    let compareLeanLabels = false; // 对比页两屏用精简标注：只标“执行中订单+移动骑手”，避免适配缩放下标签重叠

    // 双屏全屏：把「两张图 + 图例 + 下方指标」整块 #compare-fs-wrap 一起全屏，控件也在里面。
    function toggleCompareFullscreen() {
      const el = document.getElementById("compare-fs-wrap");
      if (!el) return;
      const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
      if (fsEl) (document.exitFullscreen || document.webkitExitFullscreen || function () {}).call(document);
      else (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el);
    }
    function handleCompareFullscreenChange() {
      const el = document.getElementById("compare-fs-wrap");
      const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
      const isFs = Boolean(fsEl && el && fsEl === el);
      if (el) el.dataset.fullscreen = isFs ? "true" : "false";
      const btn = document.getElementById("compare-fullscreen");
      if (btn) btn.textContent = isFs ? "⛶ 退出全屏" : "⛶ 全屏对比";
      // 容器尺寸变化后两张 Leaflet 都要重算尺寸 + 重新 fitBounds + 重画（延时两次兼容全屏动画）。
      const settle = () => {
        [compareMapB, compareMapO].forEach((m) => {
          if (!m) return;
          m.invalidateSize(false);
          const b = mapBounds();
          if (b) m.fitBounds(b, { animate: false, padding: [16, 16] });
        });
        renderCompareRuntimeState(true);
      };
      window.setTimeout(settle, 80);
      window.setTimeout(settle, 320);
    }

    // 「已送达 / 执行中」计数直接数各算法的真实生命周期（后端真实 assign/complete 时刻），与地图上的
    // 绿✓/执行中路线完全一致——这不是模拟，只是读后端真值。避免“地图有送达、记分牌却对不上”。
    function modelCounts(model, T) {
      const life = model.orderLifecycle; let delivered = 0, active = 0;
      for (const id in life) {
        const l = life[id];
        if (!l.dispatched || !Number.isFinite(l.assign_at_s)) continue;
        if (l.complete_at_s <= T) delivered += 1;
        else if (l.assign_at_s <= T) active += 1;
      }
      return { delivered, active };
    }
    // 质量指标（均时/P95/成本/超时）与趋势曲线一律直接用后端真实全天序列，与实时页同源、前后端一致。
    function getCompareSeries() { return workbench.metrics.series || []; }

    function renderComparePage() {
      return `
        ${pageHeader("compare", "双屏对照 + 指标分化", "同一批订单、同一条时间轴：左侧最近贪心基线，右侧我方 AutoSolver，下方核心指标实时分化，一眼看出差距。")}
        <div class="page-grid compare-grid" data-page="compare" data-inference-state="${inferenceState.running ? "running" : inferenceState.started ? "paused" : "ready"}">
          <div id="compare-fs-wrap" class="compare-fs-wrap" data-fullscreen="false">
            <div class="control-dock live-control-dock" data-control-strip="compare">
              <button id="start-inference" class="primary-button" data-control="start-inference">开始推理</button>
              <button id="pause-inference" class="ghost-button" data-control="pause-resume">暂停/继续</button>
              <select id="playback-speed" class="select-control" data-control="speed"><option value="0.5">0.5x</option><option value="1">1x</option><option value="2">2x</option><option value="4">4x</option></select>
              <select id="playback-pace" class="select-control" data-control="playback-pace"><option value="demo">演示快进</option><option value="realtime">逐秒播放</option></select>
              <select id="inference-mode" class="select-control" data-control="mode"><option value="current">当前算法</option><option value="compare">对比</option><option value="overlay">叠加</option></select>
              <div class="runtime-strip" data-inference-runtime="status">
                <div class="runtime-cell"><span>状态</span><b id="inference-state-label">未开始</b></div>
                <div class="runtime-cell" data-runtime="clock"><span>推演时间</span><b id="inference-clock">${escapeHtml(clockPrecise(inferenceState.currentTimeS))}</b></div>
                <div class="runtime-cell"><span>倍速</span><b id="inference-speed-label">${inferenceState.speed}x</b></div>
                <div class="runtime-cell"><span>播放方式</span><b id="inference-playback-pace-label">${escapeHtml(playbackPaceLabels[inferenceState.playbackPace])}</b></div>
                <div class="runtime-cell"><span>释放事件</span><b id="inference-event-count">${releasedEvents(inferenceState.currentTimeS).length}</b></div>
              </div>
              <div id="inference-progress-control" class="inference-progress" role="slider" tabindex="0" aria-label="拖动跳转到对应推演秒数" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${inferenceProgressPct()}" title="拖动进度条跳转；左右方向键：短按 ±1 分钟，长按 ±1 秒"><span id="inference-progress-bar" style="--progress:${inferenceProgressPct()}%"></span></div>
              <button id="compare-fullscreen" class="map-fullscreen-btn" type="button" title="双屏全屏对比（ESC 退出）">⛶ 全屏对比</button>
            </div>
            <div class="compare-stage-row">
              <div class="compare-panel" data-algo="baseline">
                <div class="compare-panel-head">
                  <div class="compare-algo"><span class="compare-badge" data-algo="baseline">基线</span><b>最近贪心 nearest_greedy</b></div>
                  <div id="compare-mini-baseline" class="compare-mini"></div>
                </div>
                <div id="compare-map-baseline" class="compare-map" aria-label="基线算法地图"></div>
              </div>
              <div class="compare-panel" data-algo="ours">
                <div class="compare-panel-head">
                  <div class="compare-algo"><span class="compare-badge" data-algo="ours">我方</span><b>AutoSolver Agent</b></div>
                  <div id="compare-mini-ours" class="compare-mini"></div>
                </div>
                <div id="compare-map-ours" class="compare-map" aria-label="我方算法地图"></div>
              </div>
            </div>
            <div class="compare-legend-bar">${renderMapLegend()}</div>
            <div class="compare-bottom">
              <div class="compare-scoreboard-wrap">
                <div class="compare-section-title">核心指标实时对比 <span class="compare-hint">（绿色=我方更优）</span></div>
                <div id="compare-scoreboard" class="compare-scoreboard"></div>
              </div>
              <div class="compare-trend-wrap">
                <div class="compare-section-title">核心指标趋势 · 随时间分化 <span class="compare-hint">（红=基线 / 绿=我方，越低越好）</span></div>
                <div id="compare-trends" class="compare-trends"></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function hydrateComparePage() {
      inferenceState.mode = "current"; // 每屏各画单一算法（不叠加基线）
      hydrateCompareMaps();
      bindLiveControls();              // 复用实时页控件绑定：开始/暂停/演示快进/逐秒/倍速/时间轴/方向键
      const fsBtn = document.getElementById("compare-fullscreen");
      if (fsBtn) fsBtn.addEventListener("click", toggleCompareFullscreen);
      if (!compareFullscreenBound) {
        compareFullscreenBound = true;
        document.addEventListener("fullscreenchange", handleCompareFullscreenChange);
        document.addEventListener("webkitfullscreenchange", handleCompareFullscreenChange);
      }
      renderCompareRuntimeState(true);
    }

    function hydrateCompareMaps() {
      if (!window.L) return;
      const mk = (id) => {
        const map = window.L.map(id, { attributionControl: true, zoomControl: false, boxZoom: false, doubleClickZoom: false, keyboard: false, scrollWheelZoom: true, preferCanvas: false, zoomAnimation: true, markerZoomAnimation: true, zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 160, wheelDebounceTime: 80 });
        window.L.control.zoom({ position: "bottomright" }).addTo(map);
        window.L.tileLayer(liveTileLayer.url, { attribution: liveTileLayer.attribution, maxZoom: 19, subdomains: liveTileLayer.subdomains }).addTo(map);
        const bounds = mapBounds();
        if (bounds) map.fitBounds(bounds, { animate: false, padding: [16, 16] });
        else map.setView(mapPoint(workbench.map.center), 14);
        return map;
      };
      compareMapB = mk("compare-map-baseline");
      compareMapO = mk("compare-map-ours");
      compareGroupB = window.L.layerGroup().addTo(compareMapB);
      compareGroupO = window.L.layerGroup().addTo(compareMapO);
      compareMapB.on("movestart zoomstart", () => { compareInteractingB = true; });
      compareMapB.on("moveend zoomend", () => { compareInteractingB = false; });
      compareMapO.on("movestart zoomstart", () => { compareInteractingO = true; });
      compareMapO.on("moveend zoomend", () => { compareInteractingO = false; });
      // 容器刚插入时可能量到 0px：布局稳定后重算尺寸+重新 fitBounds+重画一遍，避免地图错位/缩放错。
      const settle = () => {
        [compareMapB, compareMapO].forEach((m) => {
          if (!m) return;
          m.invalidateSize(false);
          const b = mapBounds();
          if (b) m.fitBounds(b, { animate: false, padding: [16, 16] });
        });
        renderCompareRuntimeState(true);
      };
      window.setTimeout(settle, 80);
      window.setTimeout(settle, 320);
    }

    function teardownCompare() {
      if (compareMapB) { compareMapB.remove(); compareMapB = null; }
      if (compareMapO) { compareMapO.remove(); compareMapO = null; }
      compareGroupB = compareGroupO = null;
      setActiveModel(oursModel); // 复位默认模型
    }

    // 用实时地图管线渲染某一屏：切到该算法模型 → 取该模型的路线/骑手/订单 → renderLeafletMapLayers。
    function updateCompareOverlay(map, group, model, frame, interacting) {
      if (!map || !group || interacting) return;
      setActiveModel(model);
      const routes = mapRouteRows(frame);
      const riders = riderPositionsForFrame(frame);
      const orders = ordersForMap(frame);
      group.clearLayers();
      compareLeanLabels = true;  // 两屏都精简标注（只标执行中订单+移动骑手），避免适配缩放下标签挤成一团
      renderLeafletMapLayers(group, frame, routes, riders, orders);
      compareLeanLabels = false;
    }

    // 对比页的“重新渲染运行态”——由 renderRuntimeState 在对比页时派发到这里。复用实时页节流。
    function renderCompareRuntimeState(force) {
      const grid = document.querySelector("[data-page='compare']");
      if (!grid) return;
      const finished = inferenceState.started && inferenceState.currentTimeS >= workbench.timeline.end_s;
      const stateLabel = inferenceState.running ? "自动推理中" : finished ? "推演完成" : inferenceState.started ? "已暂停" : "未开始";
      grid.dataset.inferenceState = inferenceState.running ? "running" : inferenceState.started ? "paused" : "ready";
      setText("inference-state-label", stateLabel);
      setText("inference-clock", clockPrecise(inferenceState.currentTimeS));
      setText("inference-speed-label", `${inferenceState.speed}x`);
      setText("inference-playback-pace-label", playbackPaceLabels[inferenceState.playbackPace]);
      setText("inference-event-count", releasedEvents(inferenceState.currentTimeS).length);
      const pb = document.getElementById("inference-progress-bar");
      if (pb) pb.style.setProperty("--progress", `${inferenceProgressPct()}%`);
      const startBtn = document.getElementById("start-inference");
      if (startBtn) { startBtn.disabled = inferenceState.started && inferenceState.running; startBtn.textContent = inferenceState.started ? "重新开始" : "开始推理"; }
      const pauseBtn = document.getElementById("pause-inference");
      if (pauseBtn) { pauseBtn.textContent = inferenceState.running ? "暂停" : finished ? "已完成" : "继续"; pauseBtn.disabled = finished && !inferenceState.running; }
      const heavy = force || (Date.now() - lastHeavyRenderAt >= HEAVY_RENDER_MIN_MS);
      if (heavy) {
        lastHeavyRenderAt = Date.now();
        const frame = frameForTime(inferenceState.currentTimeS);
        updateCompareOverlay(compareMapB, compareGroupB, baselineModel, frame, compareInteractingB);
        updateCompareOverlay(compareMapO, compareGroupO, oursModel, frame, compareInteractingO);
        setActiveModel(oursModel); // 复位默认模型，供 pacing 等读取
        const t = inferenceState.currentTimeS;
        renderCompareScoreboard(t);
        renderCompareTrends(t);
        renderCompareMini(t);
      }
    }

    function renderCompareScoreboard(T) {
      const el = document.getElementById("compare-scoreboard"); if (!el) return;
      const _s = scoreForTime(T); const b = _s.baseline || {}, o = _s.ours || {}; // 质量指标用后端真实 series
      const bc = modelCounts(baselineModel, T), oc = modelCounts(oursModel, T);   // 计数用真实生命周期，与地图一致
      const rows = [
        { k: "已送达单", bv: bc.delivered, ov: oc.delivered, better: "high", d: 0 },
        { k: "执行中", bv: bc.active, ov: oc.active, better: "none", d: 0 },
        { k: "超时单", bv: b.late_orders, ov: o.late_orders, better: "low", d: 0 },
        { k: "平均送达(min)", bv: b.avg_eta_min, ov: o.avg_eta_min, better: "low", d: 1 },
        { k: "P95送达(min)", bv: b.p95_eta_min, ov: o.p95_eta_min, better: "low", d: 1 },
        { k: "累计成本(元)", bv: b.total_cost_yuan, ov: o.total_cost_yuan, better: "low", d: 0 }
      ];
      el.innerHTML = `<div class="cmp-row cmp-head"><span>指标</span><span>基线</span><span>我方</span><span>优势</span></div>` + rows.map((r) => {
        const bv = Number(r.bv || 0), ov = Number(r.ov || 0);
        if (r.better === "none") return `<div class="cmp-row" data-cmp="tie"><span>${escapeHtml(r.k)}</span><span class="cmp-b">${escapeHtml(fmtNumber(bv, r.d))}</span><span class="cmp-o">${escapeHtml(fmtNumber(ov, r.d))}</span><span class="cmp-gap">—</span></div>`;
        const tie = Math.abs(ov - bv) < (r.d ? 0.05 : 0.5);
        const oursBetter = r.better === "low" ? ov < bv : ov > bv;
        const cls = tie ? "tie" : (oursBetter ? "win" : "lose");
        const gapText = tie ? "持平" : `${oursBetter ? "优" : "劣"} ${fmtNumber(Math.abs(ov - bv), r.d)}`;
        return `<div class="cmp-row" data-cmp="${cls}"><span>${escapeHtml(r.k)}</span><span class="cmp-b">${escapeHtml(fmtNumber(bv, r.d))}</span><span class="cmp-o">${escapeHtml(fmtNumber(ov, r.d))}</span><span class="cmp-gap">${escapeHtml(gapText)}</span></div>`;
      }).join("");
    }

    // 要对比的核心指标（都是越低越好），做成小图矩阵，随时间逐渐展开。全部与地图同源（模型计算）。
    const COMPARE_TREND_METRICS = [
      { key: "avg_eta_min", label: "平均送达时长", unit: "min", d: 1 },
      { key: "p95_eta_min", label: "P95 送达时长", unit: "min", d: 1 },
      { key: "total_cost_yuan", label: "累计成本", unit: "元", d: 0 },
      { key: "late_orders", label: "累计超时单", unit: "单", d: 0 }
    ];
    function renderCompareTrends(T) {
      const el = document.getElementById("compare-trends"); if (!el) return;
      const series = getCompareSeries();
      if (!series.length) { el.innerHTML = ""; return; }
      const _s = scoreForTime(T); const bCur = _s.baseline || {}, oCur = _s.ours || {}; // 后端真实当前值
      el.innerHTML = COMPARE_TREND_METRICS.map((m) => compareMiniTrendCard(series, m, T, bCur, oCur)).join("");
    }
    // 单个指标小图：baseline(红)/ours(绿) 两条线；只画 time_s<=T 的部分（末端插值到 T），随播放逐渐展开。
    function compareMiniTrendCard(series, m, T, bCur, oCur) {
      const W = 100, H = 44;
      const t0 = series[0].time_s, t1 = series[series.length - 1].time_s;
      const vals = series.flatMap((p) => [Number((p.baseline || {})[m.key] || 0), Number((p.ours || {})[m.key] || 0)]);
      let ymin = Math.min.apply(null, vals), ymax = Math.max.apply(null, vals);
      if (ymax - ymin < 1e-6) ymax = ymin + 1;
      const xOf = (t) => ((clamp(t, t0, t1) - t0) / Math.max(1, t1 - t0)) * W;
      const yOf = (v) => H - ((v - ymin) / (ymax - ymin)) * (H - 8) - 4;
      const revealPath = (getter) => {
        const pts = [];
        for (let i = 0; i < series.length; i++) {
          const p = series[i];
          if (p.time_s <= T) { pts.push([xOf(p.time_s), yOf(Number(getter(p)))]); continue; }
          if (i > 0 && series[i - 1].time_s <= T) { // 末端插值到 T，使线随时间平滑生长
            const a = series[i - 1], b = p;
            const f = (T - a.time_s) / Math.max(1, b.time_s - a.time_s);
            const va = Number(getter(a)), vb = Number(getter(b));
            pts.push([xOf(T), yOf(va + (vb - va) * f)]);
          }
          break;
        }
        return pts.length < 1 ? "" : pts.map((pt, i) => `${i ? "L" : "M"}${pt[0].toFixed(1)},${pt[1].toFixed(1)}`).join(" ");
      };
      const bPath = revealPath((p) => (p.baseline || {})[m.key] || 0);
      const oPath = revealPath((p) => (p.ours || {})[m.key] || 0);
      const nowX = xOf(T).toFixed(1);
      const bv = Number((bCur || {})[m.key] || 0), ov = Number((oCur || {})[m.key] || 0);
      const gap = bv - ov, better = gap > 1e-6;
      return `<div class="cmp-mini-card">
        <div class="cmp-mini-head"><b>${escapeHtml(m.label)}</b><span class="cmp-mini-vals"><i class="cmp-b">${escapeHtml(fmtNumber(bv, m.d))}</i> / <i class="cmp-o">${escapeHtml(fmtNumber(ov, m.d))}</i>${m.unit ? " " + escapeHtml(m.unit) : ""}${better ? ` <em class="cmp-mini-gap">优 ${escapeHtml(fmtNumber(gap, m.d))}</em>` : ""}</span></div>
        <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="cmp-mini-svg">
          ${bPath ? `<path d="${bPath}" fill="none" stroke="#dc2626" stroke-width="1.4" vector-effect="non-scaling-stroke"></path>` : ""}
          ${oPath ? `<path d="${oPath}" fill="none" stroke="#0f766e" stroke-width="1.9" vector-effect="non-scaling-stroke"></path>` : ""}
          <line x1="${nowX}" y1="0" x2="${nowX}" y2="${H}" stroke="#94a3b8" stroke-width="0.7" stroke-dasharray="2 2" vector-effect="non-scaling-stroke"></line>
        </svg>
      </div>`;
    }

    function renderCompareMini(T) {
      const _s = scoreForTime(T); const b = _s.baseline || {}, o = _s.ours || {};      // 质量指标用后端 series
      const bc = modelCounts(baselineModel, T), oc = modelCounts(oursModel, T);          // 已送达用真实生命周期，与地图一致
      const mb = document.getElementById("compare-mini-baseline");
      const mo = document.getElementById("compare-mini-ours");
      if (mb) mb.innerHTML = `已送达 <b>${fmtNumber(bc.delivered, 0)}</b> · 超时 <b class="cmp-bad">${fmtNumber(Number(b.late_orders || 0), 0)}</b> · 均时 <b>${fmtNumber(Number(b.avg_eta_min || 0), 1)}</b>min`;
      if (mo) mo.innerHTML = `已送达 <b>${fmtNumber(oc.delivered, 0)}</b> · 超时 <b class="cmp-good">${fmtNumber(Number(o.late_orders || 0), 0)}</b> · 均时 <b>${fmtNumber(Number(o.avg_eta_min || 0), 1)}</b>min`;
    }

    function bootstrapDispatchWorkbench() {
      // 注入「双屏对比」导航项（仅前端新增页面，不改后端 payload）
      if (Array.isArray(workbench.routes) && !workbench.routes.some((r) => r.id === "compare")) {
        workbench.routes.push({ id: "compare", path: "#/compare", label: "双屏对比", kandbox_module: "对比验证" });
      }
      renderNav();
      renderTopbarStats();
      setRoute(routeFromHash());
      window.addEventListener("hashchange", () => setRoute(routeFromHash()));
      window.addEventListener("keydown", handleGlobalPlaybackShortcut);
      // 标签页切到后台时停掉推演定时器，别在看不见时空耗 CPU；回到前台且仍在播放则恢复。
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) clearInferenceTimer();
        else if (inferenceState.running) scheduleInferenceTick();
      });
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
      setInferencePlaybackPace,
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
