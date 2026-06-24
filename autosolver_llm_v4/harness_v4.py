"""harness v4 —— 单轮 run_round 工具循环（对标 MTASA fool/harness/runner.py）。

强制 <intent>；draft 后必须 smoke 再 final（smoke gate）；解析文本协议工具调用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_INTENT = re.compile(r"<intent>(.*?)</intent>", re.DOTALL | re.IGNORECASE)
_TOOL = re.compile(r'<tool\s+name="([a-z_]+)"\s*>(.*?)</tool>', re.DOTALL | re.IGNORECASE)
_TOOL_SELF = re.compile(r'<tool\s+name="([a-z_]+)"\s*/>', re.IGNORECASE)
_CODE = re.compile(r"<code>(.*?)</code>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)
_QUERY = re.compile(r"<query>(.*?)</query>", re.DOTALL | re.IGNORECASE)
_FINAL = re.compile(r"<final>(.*?)</final>", re.DOTALL | re.IGNORECASE)
_HYP = re.compile(r"<hypothesis>(.*?)</hypothesis>", re.DOTALL | re.IGNORECASE)
_SUMMARY = re.compile(r"<summary>(.*?)</summary>", re.DOTALL | re.IGNORECASE)


@dataclass
class RoundResult:
    ok: bool
    code: str | None
    summary: str
    hypothesis: str
    steps: int
    smoke: dict | None


def extract_intent(raw: str) -> str:
    m = _INTENT.search(raw)
    return m.group(1).strip() if m else ""


def extract_code(raw: str) -> str | None:
    """从任意位置抓 propose 代码（<code> 或 ```python 围栏），用于容错隐式 draft。"""
    cm = _CODE.search(raw)
    if cm and "def propose" in cm.group(1):
        return cm.group(1).strip()
    for fm in _FENCE.finditer(raw):
        if "def propose" in fm.group(1):
            return fm.group(1).strip()
    return None


def parse_output(raw: str):
    """返回 (kind, payload)，kind ∈ {tool, final, malformed}。final 优先于 tool。"""
    fm = _FINAL.search(raw)
    if fm:
        inner = fm.group(1)
        return "final", {
            "hypothesis": (_HYP.search(inner).group(1).strip() if _HYP.search(inner) else ""),
            "summary": (_SUMMARY.search(inner).group(1).strip() if _SUMMARY.search(inner) else inner.strip()[:300]),
        }
    tm = _TOOL.search(raw)
    if tm:
        name, inner = tm.group(1).lower(), tm.group(2)
        args: dict = {}
        if name == "draft_strategy":
            cm = _CODE.search(inner) or _FENCE.search(inner)
            args["code"] = (cm.group(1).strip() if cm else inner.strip())
        elif name == "memory_search":
            qm = _QUERY.search(inner)
            args["query"] = (qm.group(1).strip() if qm else inner.strip())
        return "tool", {"name": name, "args": args}
    sm = _TOOL_SELF.search(raw)
    if sm:
        return "tool", {"name": sm.group(1).lower(), "args": {}}
    return "malformed", {}


def _short(args: dict) -> str:
    if not args:
        return ""
    if "code" in args:
        return f"code({len(args['code'])}b)"
    return ", ".join(f"{k}={str(v)[:40]}" for k, v in args.items())


def run_round(client, ctx, system_prompt, round_header, registry, memory, round_idx,
              max_steps=14, max_tokens=8000, emit=None) -> RoundResult:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": round_header},
    ]
    if memory:
        memory.log_dialog(round_idx, "system", system_prompt)
        memory.log_dialog(round_idx, "user", round_header)
    if emit:
        emit({"type": "round_start", "round": round_idx, "regime": ctx.regime,
              "baseline_cost": round(ctx.baseline_cost, 2)})

    pending_smoke = False
    hypothesis = ""
    steps = 0
    malformed = 0
    while steps < max_steps:
        raw = client.complete(messages, max_tokens=max_tokens)
        messages.append({"role": "assistant", "content": raw})
        if memory:
            memory.log_dialog(round_idx, "assistant", raw)
        steps += 1

        intent = extract_intent(raw)
        kind, payload = parse_output(raw)
        code_block = extract_code(raw)

        if kind in ("tool", "final") and not intent:
            messages.append({"role": "user", "content": "缺少 <intent>。请先 <intent>…</intent> 说明做什么/为什么，再给一个动作。"})
            continue
        if intent and emit:
            emit({"type": "intent", "round": round_idx, "text": intent})

        if kind == "tool":
            name = payload["name"]
            args = payload.get("args", {})
            res = registry.run(name, ctx, args)
            if emit:
                ev = {"type": "tool", "round": round_idx, "name": name, "args": _short(args),
                      "ok": res["ok"], "result": res["content"][:500]}
                emit(ev)
                if name == "draft_strategy" and res.get("patch") and emit:
                    emit({"type": "patch", "round": round_idx, "code": res["patch"]})
                if name == "smoke_test_strategy" and ctx.smoke_result is not None:
                    emit({"type": "smoke", "round": round_idx, **ctx.smoke_result})
            tag = "OK" if res["ok"] else "FAIL"
            messages.append({"role": "user", "content": f"[tool:{name}] {tag}\n{res['content']}"})
            if name == "draft_strategy" and res["ok"]:
                pending_smoke = True
            if name == "smoke_test_strategy" and res["ok"]:
                pending_smoke = False
            continue

        if kind == "final":
            if not ctx.draft_code:
                if code_block:  # 容错：final 里直接带了代码，记为草稿再要求 smoke
                    res = registry.run("draft_strategy", ctx, {"code": code_block})
                    if emit and res.get("patch"):
                        emit({"type": "patch", "round": round_idx, "code": res["patch"]})
                    pending_smoke = True
                    messages.append({"role": "user", "content": "已把你 final 里的代码记为草稿；final 前必须先 smoke_test_strategy。请发 smoke。"})
                    continue
                messages.append({"role": "user", "content": "还没 draft 任何策略，不能 final。先 draft_strategy。"})
                continue
            if pending_smoke:
                messages.append({"role": "user", "content": "draft 之后必须先 smoke_test_strategy 再 final。"})
                continue
            hypothesis = payload.get("hypothesis", "")
            return RoundResult(True, ctx.draft_code, payload.get("summary", ""), hypothesis, steps, ctx.smoke_result)

        # 容错：模型直接贴了 def propose 代码（未用规范 tool 标签）→ 自动当 draft_strategy
        if code_block and code_block != (ctx.draft_code or ""):
            res = registry.run("draft_strategy", ctx, {"code": code_block})
            if emit:
                emit({"type": "tool", "round": round_idx, "name": "draft_strategy",
                      "args": f"code({len(code_block)}b)", "ok": res["ok"], "result": res["content"][:500]})
                if res.get("patch"):
                    emit({"type": "patch", "round": round_idx, "code": res["patch"]})
            messages.append({"role": "user", "content": f"[tool:draft_strategy] OK（已自动捕获你的代码）\n{res['content']}"})
            if res["ok"]:
                pending_smoke = True
            continue

        malformed += 1
        messages.append({"role": "user", "content": (
            "输出格式不对。每步必须是：<intent>…</intent> 紧跟单个 <tool name=\"…\">…</tool> 或 <final>…</final>。"
            "写代码用 <tool name=\"draft_strategy\"><code>…</code></tool>。"
        )})
        if malformed >= 5:
            break

    return RoundResult(False, ctx.draft_code, "max_steps/malformed reached", hypothesis, steps, ctx.smoke_result)
