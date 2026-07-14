"""可选功能：用 LLM（默认千问）按场景生成实验策略代码，交给 evolution 三道门验证。

诚实与安全边界（红线）：
- **默认关闭**：需同时设置 API key（DASHSCOPE_LLM_API_KEY 或 AUTOSOLVER_LLM_API_KEY）
  与 AUTOSOLVER_LLM_CODEGEN=1 才启用；不启用时策略生成走原确定性模板，行为与之前完全一致
  （保持"相同输入 → 相同输出"的确定性口径）。
- **LLM 生成的代码没有直接上场权**：与模板代码走同一条流水线——AST 静态安检（import 白名单、
  禁 while、禁危险调用）→ 限时沙箱试跑 → 质量门（优于基线才保留）；任一环节失败即拒绝、留痕、回退。
- **生成失败不阻塞主链路**：LLM 不可用/超时/输出不合规 → 自动回退到确定性模板并在
  evolution_memory 里留痕（generator_note）。
- key 只从环境变量读取，绝不写进代码/项目文件。

默认走阿里云百炼「套餐专属」Base URL + qwen3.7-plus（与 web_agent_demo/llm_strategy.py 同一套环境变量）。
"""
from __future__ import annotations

import json
import os
import re
import threading
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

_DEFAULT_BASE = "https://coding.dashscope.aliyuncs.com/v1"
_DEFAULT_MODEL = "qwen3.7-plus"
_TRUTHY = {"1", "true", "yes", "on"}

# 后台生成线程池：请求在这里跑，主求解链路只按自己的预算“等一小会”，
# 等不到就先用模板起步；迟到的结果仍会被写进缓存供后续轮次使用。
_EXECUTOR: ThreadPoolExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()


def _executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llm-codegen")
        return _EXECUTOR


def http_timeout_s() -> float:
    """单次 HTTP 调用的超时（后台线程内生效），可用 AUTOSOLVER_LLM_TIMEOUT 覆盖。"""
    try:
        return max(3.0, float(os.environ.get("AUTOSOLVER_LLM_TIMEOUT", "30")))
    except ValueError:
        return 30.0


def _cfg() -> tuple[str, str, str]:
    key = os.environ.get("DASHSCOPE_LLM_API_KEY") or os.environ.get("AUTOSOLVER_LLM_API_KEY") or ""
    base = os.environ.get("DASHSCOPE_LLM_BASE_URL", _DEFAULT_BASE)
    model = os.environ.get("DASHSCOPE_LLM_MODEL", _DEFAULT_MODEL)
    return key, base, model


def enabled() -> bool:
    """代码生成是双开关：有 key 且显式打开 AUTOSOLVER_LLM_CODEGEN 才启用。"""
    key, _, _ = _cfg()
    flag = os.environ.get("AUTOSOLVER_LLM_CODEGEN", "").strip().lower()
    return bool(key) and flag in _TRUTHY


_SYSTEM_PROMPT = (
    "你是外卖派单优化的算法工程师。你要编写一个纯 Python 策略函数，它将在受限沙箱中被限时执行，"
    "用于从候选“任务组-骑手”行里挑选一组不冲突的派单方案。"
    "只输出 Python 源代码本身：不要 markdown 代码块围栏，不要任何解释文字。"
)

_PROMPT_TEMPLATE = """【硬约束（违反任一条会被静态安检直接拒绝）】
1. 只定义一个函数，签名逐字为：def propose(candidates, all_tasks, deadline, helpers):
2. 只允许 import：collections, heapq, itertools, math, random, time（可不 import）
3. 禁止 while；禁止 eval/exec/compile/open/globals/locals/__import__；禁止 os/sys/pathlib/socket/subprocess
4. 主循环开头：time_left = helpers.get("time_left")；若其不为 None 且 time_left(deadline) <= 0.01 立即返回当前结果

【数据接口】
- candidates 每行 6 元组 (task_key:str, task_ids:序列, courier_id:str, score:float 越低越好, willingness:float(0,1] 接单概率, row_index:int)
- all_tasks: set[str] 全部任务 id
- 返回 list[tuple[str, list[str]]]：每项 (task_key, [courier_id])；同一骑手全局最多出现一次；同一任务 id 不得重复覆盖

【目标】未覆盖任务每个约 +100 分重罚：先覆盖所有任务，再最小化期望成本（如按 score / max(willingness, 0.001) 排序取舍）。

【场景】{profile_block}
针对该场景设计排序与挑选逻辑，直接给出最终代码，全函数不超过 45 行。"""


def _profile_block(target_regime: str, case_profile: dict[str, Any] | None) -> str:
    profile = case_profile or {}
    lines = [f"场景档位 regime: {target_regime or 'generic'}"]
    if profile:
        lines.append(
            "任务数 {tasks}；骑手数 {couriers}；候选行数 {rows}；平均接单意愿 {aw}；是否含合单 {hb}".format(
                tasks=profile.get("tasks", "?"),
                couriers=profile.get("couriers", "?"),
                rows=profile.get("rows", "?"),
                aw=profile.get("avg_willingness", "?"),
                hb="是" if profile.get("has_bundles") else "否",
            )
        )
    return "\n".join(lines)


def _extract_code(text: str) -> str:
    """LLM 偶尔仍会包 markdown 围栏，剥掉围栏只留代码。"""
    stripped = text.strip()
    fence = re.match(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n?```\s*$", stripped, re.S)
    if fence:
        return fence.group(1).strip() + "\n"
    return stripped + "\n"


def repair_code(code: str) -> str:
    """低成本自修复：函数没叫 propose 但恰有一个 4 参顶层函数时，重命名为 propose。

    只改 def 行、不动函数体（策略函数不会自调用）；修不了就原样返回，交给预筛拒绝。
    """
    import ast as _ast

    try:
        tree = _ast.parse(code)
    except SyntaxError:
        return code
    funcs = [node for node in tree.body if isinstance(node, _ast.FunctionDef)]
    if any(func.name == "propose" for func in funcs):
        return code
    four_arg = [func for func in funcs if len(func.args.args) == 4]
    if len(four_arg) == 1:
        return re.sub(rf"^def {re.escape(four_arg[0].name)}\(", "def propose(", code, count=1, flags=re.M)
    return code


def generate_code(
    target_regime: str,
    case_profile: dict[str, Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """请求 LLM 生成一份 propose() 策略源码（同步版）。

    返回 {status: "ok", code, model, tokens} 或可回退的 {status: "unavailable"/"error", message}。
    这里只负责“拿到代码文本”；安全与质量把关完全交给 evolution 的三道门。
    """
    key, base, model = _cfg()
    if not key:
        return {"status": "unavailable", "message": "未配置 LLM API Key，回退到确定性模板生成。"}
    if timeout_s is None:
        timeout_s = http_timeout_s()
    body = {
        "model": model,
        "enable_thinking": False,  # 关思考链：优先响应速度
        "temperature": 0,          # 代码生成求稳，不求发散
        "max_tokens": 1000,        # 45 行以内的策略函数足够；越小首包越快
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _PROMPT_TEMPLATE.format(profile_block=_profile_block(target_regime, case_profile))},
        ],
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (data["choices"][0]["message"]["content"] or "").strip()
        if not text:
            return {"status": "error", "message": "LLM 返回空内容，回退到确定性模板生成。"}
        usage = data.get("usage", {}) or {}
        return {"status": "ok", "code": repair_code(_extract_code(text)), "model": model, "tokens": usage.get("total_tokens")}
    except Exception as exc:  # noqa: BLE001 - 任何失败都优雅回退
        return {"status": "error", "message": f"LLM 调用失败：{exc}，回退到确定性模板生成。"}


def request_code_async(
    target_regime: str,
    case_profile: dict[str, Any] | None = None,
    timeout_s: float | None = None,
) -> "Future[dict[str, Any]]":
    """异步版：立即返回 Future，请求在后台线程执行。

    调用方（evolution）按自己的时间预算 result(timeout=…) 等一小会；
    等不到就先用模板起步，Future 完成后结果仍可通过缓存/热切换被复用。
    """
    return _executor().submit(generate_code, target_regime, case_profile, timeout_s)
