"""可选功能：用千问(LLM)为「决策过程」页生成本轮派单的策略分析/推理，增强说服力。

诚实边界（红线）：
- **默认不启用**：项目仍是现在的启发式策略池（贪心/成本/风险/流…真跑评分），一切不变。只有前端勾选并主动请求时才调 LLM。
- LLM 只做**策略解释/生成的展示层**，**绝不篡改**真实派单结果（后端算法与地图仍是真实的）。
- **key 只从环境变量读，绝不写进代码/项目文件**；key 缺失或调用失败 → 优雅回退，明确标注"LLM 未启用/不可用"。

默认走阿里云百炼「套餐专属」Base URL + qwen3.7-plus（可用环境变量覆盖）。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

_DEFAULT_BASE = "https://coding.dashscope.aliyuncs.com/v1"
_DEFAULT_MODEL = "qwen3.7-plus"


def _cfg() -> tuple[str, str, str]:
    key = os.environ.get("DASHSCOPE_LLM_API_KEY") or os.environ.get("AUTOSOLVER_LLM_API_KEY") or ""
    base = os.environ.get("DASHSCOPE_LLM_BASE_URL", _DEFAULT_BASE)
    model = os.environ.get("DASHSCOPE_LLM_MODEL", _DEFAULT_MODEL)
    return key, base, model


def available() -> bool:
    key, _, _ = _cfg()
    return bool(key)


def _build_prompt(ctx: dict[str, Any]) -> str:
    lines = ["【本轮真实运营场景】"]
    lines.append(f"时段：{ctx.get('demand_phase', '')}；天气：{ctx.get('weather', '')}；拥堵系数：{ctx.get('congestion_level', '')}")
    lines.append(f"进入推理的订单：{ctx.get('order_count', '?')} 个；可用骑手：{ctx.get('courier_count', '?')} 名")
    if ctx.get("trigger_reason"):
        lines.append(f"触发原因：{ctx.get('trigger_reason')}")
    cands = ctx.get("candidates") or []
    if cands:
        lines.append("【候选算法 · 真实评分（分越低越优）】")
        for c in cands[:8]:
            star = " ★系统选中" if c.get("selected") else ""
            lines.append(f"- {c.get('label')}：评分{c.get('score')} 成本{c.get('cost')} 风险{c.get('risk')}{star}")
    lines.append("请据此给出本轮派单的核心策略与理由。")
    return "\n".join(lines)


def generate_strategy(payload: dict[str, Any]) -> dict[str, Any]:
    """给决策页生成本轮策略分析。返回 {status, text, model, ...}；失败/无 key 返回可回退的状态。"""
    key, base, model = _cfg()
    if not key:
        return {"status": "unavailable", "reason": "no_key",
                "message": "未配置 LLM API Key（环境变量 DASHSCOPE_LLM_API_KEY），已回退到本地启发式策略池。"}
    ctx = payload.get("context") or {}
    system = (
        "你是外卖智能调度的策略专家。基于给定的真实运营场景与候选算法评分，用简洁专业的中文给出本轮派单的"
        "核心策略与理由，务必涵盖：是否顺路合单及如何权衡、如何在时间/成本/超时风险/骑手负载之间取舍。"
        "3-5 句，直接给策略，不要客套、不要编造未提供的数字。"
    )
    body = {
        "model": model,
        "enable_thinking": False,  # 关思考链：qwen3.7-plus 推理模式要 ~20s，关掉后 ~3s，适合演示按钮
        "max_tokens": 360,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": _build_prompt(ctx)},
        ],
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (data["choices"][0]["message"]["content"] or "").strip()
        usage = data.get("usage", {}) or {}
        return {"status": "ok", "text": text, "model": model, "tokens": usage.get("total_tokens")}
    except Exception as exc:  # noqa: BLE001 - 任何失败都优雅回退
        return {"status": "error", "message": f"千问调用失败：{exc}（已回退到本地启发式策略池）"}
