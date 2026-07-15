from __future__ import annotations

import ast
import datetime as dt
import importlib.util
import inspect
import json
import threading
import time
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from autosolver_agent import llm_generator

_LLM_CACHE_LOCK = threading.Lock()


ALLOWED_IMPORTS = {"collections", "heapq", "itertools", "math", "random", "time"}
BLOCKED_CALLS = {"compile", "eval", "exec", "globals", "locals", "open", "__import__"}
BLOCKED_ATTR_ROOTS = {"os", "pathlib", "socket", "subprocess", "sys"}


@dataclass(frozen=True)
class GeneratedStrategy:
    strategy_id: str
    path: Path
    target_regime: str
    source: str
    generator: str = "template"


@dataclass(frozen=True)
class SafetyResult:
    strategy_id: str
    path: Path
    passed: bool
    reason: str
    status: str


@dataclass(frozen=True)
class TrialOutcome:
    strategy_id: str
    status: str
    decision: str
    reason: str
    accepted: bool
    elapsed_ms: float
    solution: list[tuple[str, list[str]]]
    local_cost: float | None


class EvolutionManager:
    """Manages generated strategy experiments without mutating solver.py."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.generated_dir = self.root / "generated_strategies"
        self.memory_path = self.root / "evolution_memory.jsonl"
        self.registry_path = self.root / "strategy_registry.json"
        self.llm_cache_path = self.root / "llm_code_cache.json"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
        # 尚未等到结果的 LLM 生成请求：strategy_id -> (future, cache_key)，试跑前可热切换
        self._pending_llm: dict[str, tuple[Future, str]] = {}

    def generate_strategy(
        self,
        target_regime: str,
        source: str,
        case_profile: dict[str, Any] | None = None,
        llm_wait_s: float | None = None,
    ) -> GeneratedStrategy:
        """生成实验策略。LLM 链路按 10 秒预算设计成三级降级：

        ① 场景桶缓存命中 → 0 毫秒拿到历史 LLM 代码；
        ② 未命中 → 后台线程异步请求，只阻塞等待 llm_wait_s（默认 2 秒）；
        ③ 等不到 → 先用确定性模板起步，Future 继续在后台跑，
           试跑前可 refresh_generated_strategy() 热切换，迟到结果也会写入缓存供下一轮使用。
        """
        strategy_id = self._next_strategy_id(target_regime)
        path = self.generated_dir / f"{strategy_id}.py"
        code: str | None = None
        generator = "template"
        generator_note: str | None = None
        if llm_generator.enabled():
            compact_profile = self._compact_case_profile(case_profile)
            cache_key = self._llm_bucket_key(target_regime, compact_profile)
            cached = self._llm_cache_get(cache_key)
            if cached is not None:
                code = str(cached["code"])
                generator = "llm"
                generator_note = f"cache hit [{cache_key}]; model={cached.get('model') or 'llm'}"
            else:
                future = llm_generator.request_code_async(target_regime, compact_profile)
                future.add_done_callback(lambda fut, key=cache_key: self._llm_cache_store_from_future(key, fut))
                wait_s = 2.0 if llm_wait_s is None else max(0.0, float(llm_wait_s))
                result: dict[str, Any] | None = None
                if wait_s > 0:
                    try:
                        result = future.result(timeout=wait_s)
                    except FutureTimeoutError:
                        result = None
                if result is None:
                    generator_note = f"llm pending after {wait_s:.1f}s wait; started with template (hot-swap before trial)"
                    self._pending_llm[strategy_id] = (future, cache_key)
                elif result.get("status") == "ok":
                    candidate_code = str(result.get("code") or "")
                    pre_reason = self._pre_screen_generated_code(candidate_code)
                    if pre_reason is None:
                        code = candidate_code
                        generator = "llm"
                        generator_note = f"model={result.get('model') or 'llm'}"
                    else:
                        generator_note = f"llm code pre-rejected: {pre_reason}; fallback to template"
                else:
                    generator_note = str(result.get("message") or "llm unavailable; fallback to template")
        path.write_text(code if code is not None else self._strategy_template(strategy_id, target_regime), encoding="utf-8")
        strategy = GeneratedStrategy(strategy_id, path, target_regime, source, generator)
        registry_patch = {
            "status": "draft",
            "target_regime": target_regime,
            "source": source,
            "generator": generator,
            "file": str(path),
            "attempts": 0,
            "accepted": 0,
            "rejected": 0,
        }
        if generator_note is not None:
            registry_patch["generator_note"] = generator_note
        if case_profile is not None:
            registry_patch["origin_case_profile"] = self._compact_case_profile(case_profile)
        self._update_registry(strategy_id, registry_patch)
        memory_event = {
            "event": "strategy_generated",
            "strategy_id": strategy_id,
            "target_regime": target_regime,
            "source": source,
            "generator": generator,
            "file": str(path),
            "case_profile": self._compact_case_profile(case_profile),
        }
        if generator_note is not None:
            memory_event["generator_note"] = generator_note
        self._append_memory(memory_event)
        return strategy

    @classmethod
    def _pre_screen_generated_code(cls, code: str) -> str | None:
        """LLM 产出的代码先做一次与安全门同源的预筛：不合格就地回退模板，不浪费本轮实验。"""
        if not code.strip():
            return "empty code"
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return f"syntax error: {exc.msg}"
        reason = cls._unsafe_reason(tree)
        if reason:
            return reason
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "propose":
                params = [arg.arg for arg in node.args.args]
                if params != ["candidates", "all_tasks", "deadline", "helpers"]:
                    return "invalid propose signature"
                return None
        return "missing propose"

    def refresh_generated_strategy(self, strategy: GeneratedStrategy, wait_s: float = 0.0) -> bool:
        """LLM 结果迟到的热切换：结果已到且合格 → 盘上模板换成 LLM 代码。

        只在试跑之前调用；换入的代码随后仍会在 run_generated_strategy 里
        重新过完整三道门（静态安检→限时沙箱→质量门），没有任何直通豁免。
        """
        pending = self._pending_llm.get(strategy.strategy_id)
        if pending is None:
            return False
        future, cache_key = pending
        result: dict[str, Any] | None = None
        if future.done() or wait_s > 0:
            try:
                result = future.result(timeout=max(0.001, wait_s))
            except FutureTimeoutError:
                result = None
        if result is None:
            return False  # 还没到，留在 pending 里，迟到结果会经缓存服务后续轮次
        self._pending_llm.pop(strategy.strategy_id, None)
        if result.get("status") != "ok":
            self._update_registry(strategy.strategy_id, {"generator_note": f"llm late failure: {result.get('message') or 'unknown'}; kept template"})
            return False
        code = str(result.get("code") or "")
        pre_reason = self._pre_screen_generated_code(code)
        if pre_reason is not None:
            self._update_registry(strategy.strategy_id, {"generator_note": f"llm code pre-rejected: {pre_reason}; kept template"})
            return False
        strategy.path.write_text(code, encoding="utf-8")
        self._llm_cache_store(cache_key, code, str(result.get("model") or "llm"))
        self._update_registry(strategy.strategy_id, {"generator": "llm", "generator_note": f"hot-swapped before trial; model={result.get('model') or 'llm'}"})
        self._append_memory(
            {
                "event": "strategy_upgraded",
                "strategy_id": strategy.strategy_id,
                "generator": "llm",
                "note": "llm code arrived late and was hot-swapped before the sandbox trial",
            }
        )
        return True

    # ---------- LLM 场景桶缓存：同类场景不再重复调用，命中即 0 毫秒 ----------

    @staticmethod
    def _llm_bucket_key(target_regime: str, compact_profile: dict[str, Any] | None) -> str:
        profile = compact_profile or {}
        tasks = int(profile.get("tasks", 0) or 0)
        couriers = int(profile.get("couriers", 0) or 0)
        if tasks <= 8:
            size = "tiny"
        elif tasks <= 15:
            size = "small"
        elif tasks < 40:
            size = "medium"
        else:
            size = "large"
        supply = "scarce" if 0 < couriers <= tasks else "ample"
        willingness = round(float(profile.get("avg_willingness", 0.0) or 0.0), 1)
        bundles = "bundles" if profile.get("has_bundles") else "plain"
        return f"{target_regime}|{size}|{supply}|aw{willingness}|{bundles}"

    def _llm_cache_read(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.llm_cache_path.read_text(encoding="utf-8") or "{}")
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _llm_cache_get(self, cache_key: str) -> dict[str, Any] | None:
        item = self._llm_cache_read().get(cache_key)
        if not item:
            return None
        if self._pre_screen_generated_code(str(item.get("code") or "")) is not None:
            return None
        return item

    def _llm_cache_store(self, cache_key: str, code: str, model: str) -> None:
        if self._pre_screen_generated_code(code) is not None:
            return
        with _LLM_CACHE_LOCK:
            data = self._llm_cache_read()
            data[cache_key] = {
                "code": code,
                "model": model,
                "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
            self.llm_cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _llm_cache_store_from_future(self, cache_key: str, future: Future) -> None:
        """Future 完成回调（含迟到完成）：好代码进缓存，服务后续轮次；失败静默。"""
        try:
            result = future.result(timeout=0.001)
        except Exception:  # noqa: BLE001 - 回调线程里任何失败都不应外抛
            return
        if isinstance(result, dict) and result.get("status") == "ok":
            self._llm_cache_store(cache_key, str(result.get("code") or ""), str(result.get("model") or "llm"))

    def safety_check(self, path: Path, strategy_id: str | None = None) -> SafetyResult:
        path = Path(path)
        strategy_id = strategy_id or path.stem
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            reason = self._unsafe_reason(tree)
            if reason:
                return self._record_safety(strategy_id, path, False, reason, "rejected")
            module = self._load_module(path, strategy_id)
            propose = getattr(module, "propose", None)
            if not callable(propose):
                return self._record_safety(strategy_id, path, False, "missing propose", "rejected")
            params = list(inspect.signature(propose).parameters)
            if params != ["candidates", "all_tasks", "deadline", "helpers"]:
                return self._record_safety(strategy_id, path, False, "invalid propose signature", "rejected")
        except SyntaxError as exc:
            return self._record_safety(strategy_id, path, False, f"syntax error: {exc.msg}", "rejected")
        except Exception as exc:
            return self._record_safety(strategy_id, path, False, f"load error: {exc}", "rejected")
        return self._record_safety(strategy_id, path, True, "passed", "sandboxed")

    def run_generated_strategy(
        self,
        strategy: GeneratedStrategy,
        candidates: list,
        all_tasks: set[str],
        deadline_s: float,
        helpers: dict[str, Any],
        baseline_cost: float,
        score_fn: Callable[[list[tuple[str, list[str]]]], float],
        summarize_fn: Callable[[list[tuple[str, list[str]]], float], dict[str, Any]],
        case_profile: dict[str, Any] | None = None,
    ) -> TrialOutcome:
        started = time.monotonic()
        try:
            safety = self.safety_check(strategy.path, strategy.strategy_id)
            if not safety.passed:
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", safety.reason, case_profile)
            module = self._load_module(strategy.path, strategy.strategy_id)
            local_deadline = time.monotonic() + max(0.01, deadline_s)
            solution = module.propose(candidates, all_tasks, local_deadline, helpers)
            if time.monotonic() > local_deadline + 0.02:
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", "timeout", case_profile)
            if not self._looks_like_solution(solution):
                return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", "invalid output format", case_profile)
            cost = float(score_fn(solution))
            summary = summarize_fn(solution, cost)
            if not summary.get("valid"):
                reason = "; ".join(summary.get("invalid_reasons") or ["invalid solution"])
                return self._record_trial(strategy.strategy_id, solution, cost, started, False, "reject", reason, case_profile)
            if cost <= baseline_cost - 1e-9:
                return self._record_trial(
                    strategy.strategy_id,
                    solution,
                    cost,
                    started,
                    True,
                    "accept",
                    "improved or matched baseline",
                    case_profile,
                )
            return self._record_trial(strategy.strategy_id, solution, cost, started, False, "reject", "quality regression", case_profile)
        except Exception as exc:
            return self._record_trial(strategy.strategy_id, [], None, started, False, "reject", f"exception: {exc}", case_profile)

    def trusted_strategies(self, regime: str, case_profile: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        registry = self._read_registry()
        trusted = []
        for strategy_id, item in registry.items():
            if item.get("target_regime") == regime and item.get("status") in {"candidate", "trusted", "promoted"}:
                similarity = self._profile_similarity(case_profile, item.get("last_case_profile") or item.get("origin_case_profile"))
                trusted.append({"strategy_id": strategy_id, "similarity": similarity, **item})
        if case_profile is None:
            return sorted(trusted, key=lambda item: (-int(item.get("accepted", 0)), item["strategy_id"]))
        return sorted(trusted, key=lambda item: (-float(item.get("similarity", 0.0)), -int(item.get("accepted", 0)), item["strategy_id"]))

    def _record_safety(self, strategy_id: str, path: Path, passed: bool, reason: str, status: str) -> SafetyResult:
        patch = {"status": status, "safety_passed": passed, "safety_reason": reason}
        if not passed:
            patch["rollback_action"] = "removed_from_active_pool"
        self._update_registry(strategy_id, patch)
        self._append_memory(
            {
                "event": "strategy_validated",
                "strategy_id": strategy_id,
                "syntax_passed": not reason.startswith("syntax error"),
                "safety_passed": passed,
                "interface_passed": passed,
                "status": status,
                "reason": reason,
            }
        )
        return SafetyResult(strategy_id, path, passed, reason, status)

    def _record_trial(
        self,
        strategy_id: str,
        solution: list[tuple[str, list[str]]],
        cost: float | None,
        started: float,
        accepted: bool,
        decision: str,
        reason: str,
        case_profile: dict[str, Any] | None = None,
    ) -> TrialOutcome:
        elapsed_ms = round((time.monotonic() - started) * 1000.0, 3)
        status = "candidate" if accepted else "rejected"
        registry = self._read_registry().get(strategy_id, {})
        attempts = int(registry.get("attempts", 0)) + 1
        accepted_count = int(registry.get("accepted", 0)) + (1 if accepted else 0)
        rejected_count = int(registry.get("rejected", 0)) + (0 if accepted else 1)
        registry_patch = {
            "status": status,
            "attempts": attempts,
            "accepted": accepted_count,
            "rejected": rejected_count,
            "last_decision": decision,
            "last_reason": reason,
            "last_cost": cost,
            "rollback_action": None if accepted else "removed_from_active_pool",
        }
        compact_profile = self._compact_case_profile(case_profile)
        if compact_profile is not None:
            registry_patch["last_case_profile"] = compact_profile
            history = list(registry.get("case_profile_history", []))
            history.append({"accepted": accepted, "decision": decision, **compact_profile})
            registry_patch["case_profile_history"] = history[-8:]
        self._update_registry(strategy_id, registry_patch)
        self._append_memory(
            {
                "event": "strategy_trial",
                "strategy_id": strategy_id,
                "status": status,
                "accepted": accepted,
                "decision": decision,
                "reason": reason,
                "elapsed_ms": elapsed_ms,
                "local_cost": cost,
                "case_profile": compact_profile,
            }
        )
        return TrialOutcome(strategy_id, status, decision, reason, accepted, elapsed_ms, solution, cost)

    def _append_memory(self, event: dict[str, Any]) -> None:
        event = {"created_at": dt.datetime.now().isoformat(timespec="seconds"), **event}
        with self.memory_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _read_registry(self) -> dict[str, dict[str, Any]]:
        if not self.registry_path.exists():
            return {}
        return json.loads(self.registry_path.read_text(encoding="utf-8") or "{}")

    def _update_registry(self, strategy_id: str, patch: dict[str, Any]) -> None:
        registry = self._read_registry()
        current = registry.get(strategy_id, {})
        current.update({key: value for key, value in patch.items() if value is not None})
        current["last_seen"] = dt.datetime.now().isoformat(timespec="seconds")
        registry[strategy_id] = current
        self.registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _compact_case_profile(case_profile: dict[str, Any] | None) -> dict[str, Any] | None:
        if case_profile is None:
            return None
        return {
            "regime": str(case_profile.get("regime", "")),
            "tasks": int(case_profile.get("tasks", 0) or 0),
            "couriers": int(case_profile.get("couriers", 0) or 0),
            "rows": int(case_profile.get("rows", 0) or 0),
            "avg_willingness": round(float(case_profile.get("avg_willingness", 0.0) or 0.0), 6),
            "has_bundles": bool(case_profile.get("has_bundles", False)),
        }

    @classmethod
    def _profile_similarity(cls, current: dict[str, Any] | None, stored: dict[str, Any] | None) -> float:
        current_profile = cls._compact_case_profile(current)
        stored_profile = cls._compact_case_profile(stored)
        if current_profile is None or stored_profile is None:
            return 0.0
        score = 0.0
        if current_profile["regime"] == stored_profile["regime"]:
            score += 4.0
        if current_profile["has_bundles"] == stored_profile["has_bundles"]:
            score += 1.0
        score += cls._ratio_similarity(current_profile["tasks"], stored_profile["tasks"])
        score += cls._ratio_similarity(current_profile["couriers"], stored_profile["couriers"])
        score += cls._ratio_similarity(current_profile["rows"], stored_profile["rows"])
        score += max(0.0, 1.0 - abs(current_profile["avg_willingness"] - stored_profile["avg_willingness"]))
        return round(score, 6)

    @staticmethod
    def _ratio_similarity(left: int, right: int) -> float:
        if left <= 0 or right <= 0:
            return 0.0
        return min(left, right) / max(left, right)

    def _next_strategy_id(self, target_regime: str) -> str:
        safe = "".join(ch if ch.isalnum() else "_" for ch in target_regime).strip("_") or "generic"
        existing = sorted(self.generated_dir.glob(f"gen_{safe}_v*.py"))
        return f"gen_{safe}_v{len(existing) + 1:03d}"

    @staticmethod
    def _strategy_template(strategy_id: str, target_regime: str) -> str:
        normalized = "".join(ch if ch.isalnum() else "_" for ch in target_regime).strip("_") or "generic"
        if target_regime == "low-willingness":
            ranker = "(len(row[1]), -row[4], row[3] / max(row[4], 0.001), row[3])"
            note = "low_willingness"
        elif target_regime == "scarce":
            ranker = "(-len(row[1]), row[3] / max(len(row[1]), 1), -row[4], row[3])"
            note = "scarce"
        else:
            ranker = "(len(row[1]), row[3] / max(row[4], 0.001), row[3])"
            note = normalized
        return f'''# Auto-generated experimental strategy: {strategy_id}\n# target_regime: {note}\nfrom __future__ import annotations\n\n\ndef propose(candidates, all_tasks, deadline, helpers):\n    """Return a regime-aware experimental candidate for sandbox evaluation."""\n    time_left = helpers.get("time_left")\n    used_couriers = set()\n    covered_tasks = set()\n    result = []\n    rows = sorted(candidates, key=lambda row: {ranker})\n    for task_key, task_ids, courier_id, _score, _willingness, _row_index in rows:\n        if time_left is not None and time_left(deadline) <= 0.01:\n            break\n        if courier_id in used_couriers:\n            continue\n        if any(task_id in covered_tasks for task_id in task_ids):\n            continue\n        used_couriers.add(courier_id)\n        covered_tasks.update(task_ids)\n        result.append((task_key, [courier_id]))\n        if covered_tasks >= set(all_tasks):\n            break\n    return result\n'''

    @staticmethod
    def _unsafe_reason(tree: ast.AST) -> str | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                return "unsafe loop: while"
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
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in BLOCKED_ATTR_ROOTS:
                    return f"unsafe attribute call: {func.value.id}.{func.attr}"
        return None

    @staticmethod
    def _load_module(path: Path, strategy_id: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(f"autosolver_generated_{strategy_id}", str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generated strategy {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _looks_like_solution(solution: Any) -> bool:
        if not isinstance(solution, list):
            return False
        for item in solution:
            if not isinstance(item, tuple) or len(item) != 2:
                return False
            task_key, couriers = item
            if not isinstance(task_key, str) or not isinstance(couriers, list) or not all(isinstance(c, str) for c in couriers):
                return False
        return True
