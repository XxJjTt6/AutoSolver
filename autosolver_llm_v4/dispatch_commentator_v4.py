"""tick 级 LLM 调度解说 Critic（§6.6①）—— 真 DeepSeek，只解说不决策。

输入某些代表性 tick 的场景画像 + 指标，产一句中文解说 + 风险提示。
离线生成一次并缓存到 autosolver_dynamic_v4/demo/commentary_<scenario>.json，前端回放（断网可用）。
决策永远由确定性求解器做；本模块只解释，绝不改派单。

CLI: python3 -m autosolver_llm_v4.dispatch_commentator_v4 --scenario weekday_peaks
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from autosolver_dynamic_v4 import scenario_builder_v4 as sb  # noqa: E402
from autosolver_llm_v4 import llm_client_v4  # noqa: E402

DEMO = _ROOT / "autosolver_dynamic_v4" / "demo"

_SYS = (
    "你是即时配送调度解说员。根据给定时刻的场景画像和指标，用一句简洁中文解释"
    "‘当前为什么这么派 + 有什么风险’。只解说，不决策。30~50字，不要客套。"
)


def _pick_ticks(steps, k=6):
    """选代表性 tick：含拥堵窗 + 均匀采样。"""
    picks = set()
    for s in steps:
        if s.get("speed_factor", 1) < 1.0:
            picks.add(s["tick"])
    n = len(steps)
    for i in range(k):
        picks.add(steps[min(n - 1, int(i * n / k))]["tick"])
    return sorted(picks)


def _prompt_for(step, scenario_label, scenario):
    g = step["lanes"]["greedy"]["metrics"]
    w = step["lanes"]["warm"]["metrics"]
    hhmm = sb.display_time(step["clock_min"], scenario)
    phase = sb.phase_label(step["clock_min"], scenario)
    shock = "（突发拥堵，骑手速度下降）" if step.get("speed_factor", 1) < 1 else ""
    return (
        f"场景：{scenario_label}；当前 {hhmm} 属{phase}{shock}；已到订单 {w['arrived']}/40；"
        f"AutoSolver每单期望成本 {w['total_cost']} vs 贪心 {g['total_cost']}（更低更好）；"
        f"准时率 {int(w['on_time_rate']*100)}%；场景识别命中率 {int(w['regime_hit_rate']*100)}%。"
        "请用一句话解说当前为什么这么派+风险提示。"
    )


def generate(scenario="weekday_peaks", provider="deepseek", client=None):
    trace_path = DEMO / f"large_seed301_{scenario}.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    label = trace.get("summary", {}).get("scenario_label", scenario)
    steps = trace["steps"]
    sc = sb.SCENARIOS[scenario]
    client = client or llm_client_v4.make_client(provider)
    out = {}
    for tk in _pick_ticks(steps):
        step = steps[tk]
        try:
            msg = client.complete(
                [{"role": "system", "content": _SYS},
                 {"role": "user", "content": _prompt_for(step, label, sc)}],
                max_tokens=120, temperature=0.5,
            ).strip().replace("\n", " ")
        except Exception as exc:
            msg = f"（解说生成失败:{exc}）"
        out[str(tk)] = {"clock_min": step["clock_min"],
                        "hhmm": sb.display_time(step["clock_min"], sc),
                        "phase": sb.phase_label(step["clock_min"], sc), "text": msg}
    return {"scenario": scenario, "label": label, "by_tick": out,
            "note": "真 DeepSeek 离线生成，现场缓存回放；只解说不决策。"}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="weekday_peaks")
    p.add_argument("--provider", default="deepseek")
    a = p.parse_args(argv)
    res = generate(a.scenario, a.provider)
    out = DEMO / f"commentary_{a.scenario}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out} ({len(res['by_tick'])} comments)")
    for tk, c in res["by_tick"].items():
        print(f"  tick{tk} {c['clock_min']//60:02d}:{c['clock_min']%60:02d}  {c['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
