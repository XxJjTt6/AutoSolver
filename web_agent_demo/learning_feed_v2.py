"""会议方案 v4 · 学习轨道控制台 只读数据解析器 (learning_feed_v2)。

把 autosolver_agent 离线进化真实落盘的两个状态文件归一化成前端 schema：
  - autosolver_agent/evolution_state/evolution_memory.jsonl  (28 条事件)
  - autosolver_agent/evolution_state/strategy_registry.json  (5 个生成策略, 全 rejected)

诚实红线（见 docs/会议明确有用点_详细执行方案_v4_20260625.md §16.7/§16.21）：
  - 只读、不跑求解、不调 LLM、不写盘（write_snapshot 除外, 显式调用）。
  - 5 策略全被拒 = "质量门有判别力", 不是失败、不冒充"进化提分"。
  - 主屏权威数字用官方 654.29 / 706.197; 657.104 仅作"本地实时估算"且带 label。
  - 1×1 退化算例 (tasks<=1 或 rows<=1) 打 degenerate 标, 不进正式成本对比。
  - 真实字段直绑, 不绑代码里不存在的字段 (无 regime_hit_rate / similarity)。

本模块不依赖第三方库; 既可被 server_meeting_v2 import, 也可 `python3 web_agent_demo/learning_feed_v2.py`
直接生成断网兜底快照 docs/prebuilt/learning-trace.json。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EVO_DIR = ROOT / "autosolver_agent" / "evolution_state"
MEMORY_JSONL = EVO_DIR / "evolution_memory.jsonl"
REGISTRY_JSON = EVO_DIR / "strategy_registry.json"
SNAPSHOT_PATH = ROOT / "docs" / "prebuilt" / "learning-trace.json"

# 口径基线: 权威=官方; 本地=复跑近似(带 label, 前端不得硬编码冒充官方)。
BASELINES: dict[str, dict[str, Any]] = {
    "official_case": {"value": 654.2935, "label": "官方 · large_seed301 同名隐藏算例", "authoritative": True},
    "official_total": {"value": 706.197, "label": "官方 · 整体提交分 (10/10)", "authoritative": True},
    "local_realtime": {"value": 657.104, "label": "本地实时估算 · 非官方分", "authoritative": False},
    "greedy_local": {"value": 2097.658, "label": "本地纯贪心基线 · large_seed301", "authoritative": False},
}

# 六阶段流水线 (Stage Rail)。来源映射见每项 source。
STAGES: list[dict[str, str]] = [
    {"key": "perception", "cn": "看场景", "desc": "先判断现在是什么状况", "source": "autosolver_agent/system.py:perception"},
    {"key": "generate", "cn": "试造打法", "desc": "针对状况生成一个新策略", "source": "strategy_generated"},
    {"key": "safety", "cn": "安全检查", "desc": "AST 安全门 + 接口校验", "source": "strategy_validated"},
    {"key": "sandbox", "cn": "沙箱试跑", "desc": "隔离跑一遍看成绩", "source": "strategy_trial.elapsed_ms"},
    {"key": "judge", "cn": "质量门判决", "desc": "打不过现有最好方案就不上线", "source": "strategy_trial.decision"},
    {"key": "memory", "cn": "记下来", "desc": "结果沉淀进记忆 / 移出活跃池", "source": "strategy_registry.rollback_action"},
]

# regime 真值桶 → 人话 (禁词表: 不许翻成早/午/晚高峰、雨天)。
REGIME_CN: dict[str, str] = {
    "large": "大单量场景",
    "small": "小单量平峰",
    "low-willingness": "骑手不愿接",
    "low_willingness": "骑手不愿接",
    "scarce": "运力紧张",
}

# 拒绝原因 → 人话。
REASON_CN: dict[str, str] = {
    "quality regression": "成绩不如现有方案",
    "timeout": "试跑超时",
    "passed": "通过",
}


def regime_cn(regime: str | None) -> str:
    if not regime:
        return "未标注状况"
    return REGIME_CN.get(regime, str(regime))


def reason_cn(reason: str | None) -> str:
    if not reason:
        return "—"
    return REASON_CN.get(reason, str(reason))


def _is_degenerate(case_profile: dict[str, Any] | None) -> bool:
    """1×1 冒烟测试算例 (tasks<=1 或 rows<=1): 只用于跑通管道, 不进正式成本对比。"""
    if not isinstance(case_profile, dict):
        return False
    tasks = case_profile.get("tasks")
    rows = case_profile.get("rows")
    try:
        if tasks is not None and float(tasks) <= 1:
            return True
        if rows is not None and float(rows) <= 1:
            return True
    except (TypeError, ValueError):
        return False
    return False


def _read_memory_events(path: Path = MEMORY_JSONL) -> list[dict[str, Any]]:
    """逐行读 jsonl, 坏行跳过 (健壮性兜底 B2)。"""
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            events.append(json.loads(raw))
        except json.JSONDecodeError:
            continue  # 坏行跳过, 不让一行脏数据搞崩整条时间线
    return events


def _read_registry(path: Path = REGISTRY_JSON) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_event(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    """把一条原始事件归一化成前端事件卡所需字段 (只读真实字段)。"""
    etype = str(raw.get("event", ""))
    case = raw.get("case_profile") if isinstance(raw.get("case_profile"), dict) else {}
    regime = raw.get("target_regime") or case.get("regime")
    out: dict[str, Any] = {
        "idx": idx,
        "created_at": raw.get("created_at"),
        "event": etype,
        "strategy_id": raw.get("strategy_id"),
        "regime": regime,
        "regime_cn": regime_cn(regime),
    }
    if etype == "strategy_generated":
        out["stage"] = "generate"
        out["case"] = {
            "tasks": case.get("tasks"),
            "couriers": case.get("couriers"),
            "rows": case.get("rows"),
            "avg_willingness": case.get("avg_willingness"),
        }
        out["degenerate"] = _is_degenerate(case)
    elif etype == "strategy_validated":
        out["stage"] = "safety"
        out["syntax_passed"] = bool(raw.get("syntax_passed"))
        out["safety_passed"] = bool(raw.get("safety_passed"))
        out["interface_passed"] = bool(raw.get("interface_passed"))
        out["status"] = raw.get("status")
        out["reason"] = raw.get("reason")
    elif etype == "strategy_trial":
        degenerate = _is_degenerate(case)
        reason = raw.get("reason")
        out["stage"] = "judge" if reason == "quality regression" else "sandbox"
        out["accepted"] = bool(raw.get("accepted"))
        out["decision"] = raw.get("decision")
        out["reason"] = reason
        out["reason_cn"] = reason_cn(reason)
        out["elapsed_ms"] = raw.get("elapsed_ms")
        out["local_cost"] = raw.get("local_cost")
        out["degenerate"] = degenerate
        out["case"] = {"tasks": case.get("tasks"), "couriers": case.get("couriers"), "rows": case.get("rows")}
        # 成本对比: 只对 large 同口径 (非退化) 给数字对比; timeout 无成本; 退化算例只标注。
        if degenerate:
            out["cost_note"] = "1×1 冒烟测试算例, 非正式对比"
        elif raw.get("local_cost") is None:
            out["cost_note"] = "试跑超时, 未产出成本"
        elif regime == "large":
            local = BASELINES["local_realtime"]["value"]
            out["beat_local"] = bool(raw.get("local_cost") < local)
            out["cost_vs_local"] = f"{raw.get('local_cost'):.1f} vs 现有 {local:.1f} (本地估算)"
        else:
            out["cost_note"] = "未达标 (quality regression)"
    else:
        out["stage"] = None
    return out


def _normalize_strategy(sid: str, rec: dict[str, Any]) -> dict[str, Any]:
    case = rec.get("last_case_profile") if isinstance(rec.get("last_case_profile"), dict) else {}
    regime = rec.get("target_regime") or case.get("regime")
    last_cost = rec.get("last_cost")
    out: dict[str, Any] = {
        "strategy_id": sid,
        "target_regime": regime,
        "regime_cn": regime_cn(regime),
        "accepted": int(rec.get("accepted", 0) or 0),
        "rejected": int(rec.get("rejected", 0) or 0),
        "attempts": int(rec.get("attempts", 0) or 0),
        "status": rec.get("status"),
        "last_reason": rec.get("last_reason"),
        "last_reason_cn": reason_cn(rec.get("last_reason")),
        "last_cost": last_cost,
        "safety_passed": bool(rec.get("safety_passed")),
        "safety_reason": rec.get("safety_reason"),
        "rollback_action": rec.get("rollback_action"),
        "last_seen": rec.get("last_seen"),
        "case": {"tasks": case.get("tasks"), "couriers": case.get("couriers"), "rows": case.get("rows")},
        # file 只展示文本, 前端不尝试打开 (多数路径指向别的机器)。
        "file": rec.get("file"),
    }
    if regime == "large" and isinstance(last_cost, (int, float)):
        out["beat_local"] = bool(last_cost < BASELINES["local_realtime"]["value"])
    return out


def build_payload() -> dict[str, Any]:
    """归一化成前端 /api/meeting-v2/learning-trace 的 schema。纯只读。"""
    raw_events = _read_memory_events()
    registry = _read_registry()

    events = [_normalize_event(e, i) for i, e in enumerate(raw_events)]

    trials = [e for e in events if e["event"] == "strategy_trial"]
    stats = {
        "generated": sum(1 for e in events if e["event"] == "strategy_generated"),
        "validated": sum(1 for e in events if e["event"] == "strategy_validated"),
        "trial": len(trials),
        "accepted": sum(1 for e in trials if e.get("accepted")),
        "reject_quality": sum(1 for e in trials if e.get("reason") == "quality regression"),
        "reject_timeout": sum(1 for e in trials if e.get("reason") == "timeout"),
        "safety_all_passed": all(
            e.get("safety_passed") and e.get("interface_passed")
            for e in events if e["event"] == "strategy_validated"
        ),
    }

    strategies = [_normalize_strategy(sid, rec) for sid, rec in registry.items() if isinstance(rec, dict)]

    return {
        "schema_version": 1,
        "source": "autosolver_agent/evolution_state (真实离线进化落盘记录)",
        "honest_note": "现场零 LLM · 离线真实记录回放 · 5 策略全被拒=质量门有判别力",
        "stages": STAGES,
        "events": events,
        "stats": stats,
        "strategies": strategies,
        "baselines": BASELINES,
        "regime_cn": REGIME_CN,
    }


def write_snapshot(path: Path = SNAPSHOT_PATH) -> Path:
    """生成断网兜底快照 (唯一显式写盘动作)。"""
    payload = build_payload()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    p = build_payload()
    out = write_snapshot()
    print(f"[learning_feed_v2] 生成={p['stats']['generated']} 校验={p['stats']['validated']} "
          f"试跑={p['stats']['trial']} 采纳={p['stats']['accepted']} "
          f"(质检拦截={p['stats']['reject_quality']} 超时={p['stats']['reject_timeout']})")
    print(f"[learning_feed_v2] 策略={len(p['strategies'])} 全部 accepted=0: "
          f"{all(s['accepted'] == 0 for s in p['strategies'])}")
    print(f"[learning_feed_v2] 快照已写: {out}")
