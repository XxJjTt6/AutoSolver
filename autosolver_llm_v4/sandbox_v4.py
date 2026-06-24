"""沙箱安全门 v4 —— 在受限边界内执行 LLM 生成的 propose()。

镜像并增强 autosolver_agent/evolution.py:15-17,94 的安全门：
- 白名单 import；禁 eval/exec/open/__import__/compile/globals/locals；禁 os/sys/... 属性调用。
- 新增：禁 while 循环（防无界）、强制 deadline 在函数体被引用、强制签名与返回类型。
正式 solver.py / evolution.py 零改动；这里只对“字符串代码”做静态检查 + 受限执行。
"""
from __future__ import annotations

import ast
import inspect
import time
from typing import Any, Callable

# 镜像 evolution.py:15-17（保持与现有安全门一致）
ALLOWED_IMPORTS = {"collections", "heapq", "itertools", "math", "random", "time"}
BLOCKED_CALLS = {"compile", "eval", "exec", "globals", "locals", "open", "__import__"}
BLOCKED_ATTR_ROOTS = {"os", "pathlib", "socket", "subprocess", "sys"}

REQUIRED_SIGNATURE = ["candidates", "all_tasks", "deadline", "helpers"]


def _unsafe_reason(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.While):  # 增强：禁 while（防无界循环）
            return "unsafe loop: while (用 for + deadline 检查替代)"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue
            names = [alias.name.split(".", 1)[0] for alias in getattr(node, "names", [])]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".", 1)[0])
            for name in names:
                if name not in ALLOWED_IMPORTS:
                    return f"unsafe import: {name}"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BLOCKED_CALLS:
                return f"unsafe call: {func.id}"
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in BLOCKED_ATTR_ROOTS
            ):
                return f"unsafe attribute call: {func.value.id}.{func.attr}"
    return None


def safety_check_code(code: str) -> tuple[bool, str]:
    """返回 (passed, reason)。只静态检查，不执行。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"syntax error: {exc.msg} (line {exc.lineno})"
    reason = _unsafe_reason(tree)
    if reason:
        return False, reason
    # 必须定义 propose
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if "propose" not in funcs:
        return False, "missing function: propose"
    propose_node = funcs["propose"]
    params = [a.arg for a in propose_node.args.args]
    if params != REQUIRED_SIGNATURE:
        return False, f"invalid propose signature: {params} (must be {REQUIRED_SIGNATURE})"
    # 增强：propose 体内必须引用 deadline（鼓励 anytime 截断；防写死死循环风险）
    body_src = ast.dump(propose_node)
    if "'deadline'" not in body_src and "deadline" not in {
        getattr(n, "id", None) for n in ast.walk(propose_node) if isinstance(n, ast.Name)
    }:
        return False, "propose body must reference 'deadline' (anytime budget check)"
    return True, "passed"


def _load_propose(code: str) -> Callable:
    namespace: dict[str, Any] = {}
    compiled = compile(code, "<llm_strategy_v4>", "exec")  # 已过 safety_check_code
    exec(compiled, namespace)  # noqa: S102 — 沙箱内受控执行，已静态门控
    propose = namespace.get("propose")
    if not callable(propose):
        raise ValueError("propose not callable after load")
    sig = list(inspect.signature(propose).parameters)
    if sig != REQUIRED_SIGNATURE:
        raise ValueError(f"runtime signature mismatch: {sig}")
    return propose


def _looks_like_solution(solution: Any) -> bool:
    if not isinstance(solution, list):
        return False
    for item in solution:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        task_key, couriers = item
        if not isinstance(task_key, str) or not isinstance(couriers, list):
            return False
        if not all(isinstance(c, str) for c in couriers):
            return False
    return True


def run_propose(code: str, candidates, all_tasks, time_budget_s: float = 5.0, helpers=None) -> dict:
    """安全门 + 受限执行；返回 {ok, reason, solution, elapsed_ms}。"""
    passed, reason = safety_check_code(code)
    if not passed:
        return {"ok": False, "reason": reason, "solution": None, "elapsed_ms": 0.0}
    try:
        propose = _load_propose(code)
    except Exception as exc:
        return {"ok": False, "reason": f"load error: {exc}", "solution": None, "elapsed_ms": 0.0}
    if helpers is None:
        helpers = {"time_left": lambda d: d - time.monotonic(), "now": time.monotonic}
    deadline = time.monotonic() + max(0.05, time_budget_s)
    started = time.monotonic()
    try:
        solution = propose(candidates, all_tasks, deadline, helpers)
    except Exception as exc:
        return {"ok": False, "reason": f"exception: {exc}", "solution": None,
                "elapsed_ms": round((time.monotonic() - started) * 1000, 3)}
    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    if time.monotonic() > deadline + 0.1:
        return {"ok": False, "reason": "timeout", "solution": None, "elapsed_ms": elapsed_ms}
    if not _looks_like_solution(solution):
        return {"ok": False, "reason": "invalid output format (need list[tuple[str, list[str]]])",
                "solution": None, "elapsed_ms": elapsed_ms}
    return {"ok": True, "reason": "ran", "solution": solution, "elapsed_ms": elapsed_ms}
