"""现场演示：LLM 按场景生成调度策略代码 → 三道门验证 → 接受/拒绝留痕。

用法（真调 LLM，需要千问 key）：
    export DASHSCOPE_LLM_API_KEY=sk-...      # 或 AUTOSOLVER_LLM_API_KEY
    export AUTOSOLVER_LLM_CODEGEN=1
    python3 tools/llm_evolution_demo.py --regime low-willingness

不配 key 也能跑：生成位自动回退到确定性模板，同样走完三道门（用于验证链路/彩排）。
可选参数：--regime {low-willingness,scarce,generic}；--tasks N；--seed N；--keep-root DIR（持久化注册表）。
"""
from __future__ import annotations

import argparse
import random
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autosolver_agent import llm_generator  # noqa: E402
from autosolver_agent.evolution import EvolutionManager  # noqa: E402


def build_case(regime: str, n_tasks: int, seed: int):
    """构造一个确定性的演示用例（固定种子，相同参数结果可复现）。"""
    rng = random.Random(seed)
    tasks = [f"T{i:04d}" for i in range(n_tasks)]
    n_couriers = max(2, n_tasks // 3) if regime == "scarce" else n_tasks * 2
    couriers = [f"C{i:03d}" for i in range(n_couriers)]
    w_low, w_high = (0.05, 0.35) if regime == "low-willingness" else (0.35, 0.95)
    candidates = []
    row_index = 0
    for task in tasks:
        for courier in rng.sample(couriers, min(len(couriers), 4)):
            candidates.append((task, (task,), courier, round(rng.uniform(4.0, 28.0), 2), round(rng.uniform(w_low, w_high), 3), row_index))
            row_index += 1
    return candidates, set(tasks), couriers


def make_scorers(candidates, all_tasks):
    known_rows = {(row[0], courier) for row in candidates for courier in [row[2]]}

    def score_fn(solution):
        covered, used, cost = set(), set(), 0.0
        by_key = {}
        for row in candidates:
            by_key.setdefault(row[0], {})[row[2]] = row
        for task_key, courier_ids in solution:
            for courier_id in courier_ids:
                row = by_key.get(task_key, {}).get(courier_id)
                if row is None:
                    return float("inf")
                cost += row[3] / max(row[4], 0.001)
                used.add(courier_id)
                covered.update(row[1])
        return cost + 100.0 * len(all_tasks - covered)

    def summarize_fn(solution, cost):
        used, covered, reasons = set(), set(), []
        for task_key, courier_ids in solution:
            for courier_id in courier_ids:
                if (task_key, courier_id) not in known_rows:
                    reasons.append(f"unknown row {task_key}/{courier_id}")
                if courier_id in used:
                    reasons.append(f"courier reused: {courier_id}")
                used.add(courier_id)
            if task_key in covered:
                reasons.append(f"task duplicated: {task_key}")
            covered.add(task_key)
        return {"valid": not reasons, "invalid_reasons": reasons}

    return score_fn, summarize_fn


def baseline_cost_of(candidates, all_tasks, score_fn):
    """基线：官方贪心风格——按 score 升序、骑手/任务不重复地捡。"""
    used, covered, solution = set(), set(), []
    for row in sorted(candidates, key=lambda r: r[3]):
        task_key, task_ids, courier_id = row[0], row[1], row[2]
        if courier_id in used or any(t in covered for t in task_ids):
            continue
        used.add(courier_id)
        covered.update(task_ids)
        solution.append((task_key, [courier_id]))
    return score_fn(solution)


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM 策略生成 × 三道门 演示")
    parser.add_argument("--regime", default="low-willingness", choices=["low-willingness", "scarce", "generic"])
    parser.add_argument("--tasks", type=int, default=18)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--keep-root", default=None, help="持久化 evolution 状态目录（默认临时目录）")
    parser.add_argument("--llm-wait", type=float, default=2.0, help="生成阶段阻塞等待 LLM 的秒数（与 Agent 主链路一致，默认 2s）")
    parser.add_argument("--swap-wait", type=float, default=6.0, help="试跑前热切换最多再等的秒数（演示迟到补挂）")
    args = parser.parse_args()

    print("=" * 72)
    print(f"LLM 代码生成开关 enabled() = {llm_generator.enabled()}"
          f"（需 API key + AUTOSOLVER_LLM_CODEGEN=1；关闭时回退确定性模板）")
    candidates, all_tasks, couriers = build_case(args.regime, args.tasks, args.seed)
    case_profile = {
        "regime": args.regime,
        "tasks": len(all_tasks),
        "couriers": len(couriers),
        "rows": len(candidates),
        "avg_willingness": round(sum(r[4] for r in candidates) / len(candidates), 4),
        "has_bundles": False,
    }
    print(f"演示场景: {case_profile}")

    root = Path(args.keep_root) if args.keep_root else Path(tempfile.mkdtemp(prefix="llm_evolution_demo_"))
    manager = EvolutionManager(root)

    print("-" * 72)
    print(f"① 生成：请求策略代码（LLM 优先，失败回退模板；阻塞等待上限 {args.llm_wait:.1f}s）...")
    tick = time.perf_counter()
    generated = manager.generate_strategy(args.regime, "llm_evolution_demo", case_profile, llm_wait_s=args.llm_wait)
    gen_ms = (time.perf_counter() - tick) * 1000.0
    registry_entry = manager._read_registry()[generated.strategy_id]
    print(f"   策略 id = {generated.strategy_id}   生成来源 = {generated.generator}   生成阶段耗时 = {gen_ms:.0f} ms")
    if generated.generator == "template" and generated.strategy_id in manager._pending_llm:
        tick = time.perf_counter()
        if manager.refresh_generated_strategy(generated, wait_s=args.swap_wait):
            registry_entry = manager._read_registry()[generated.strategy_id]
            print(f"   ↻ LLM 结果迟到 {(time.perf_counter() - tick) * 1000.0:.0f} ms 后送达，已在试跑前热切换为 LLM 代码")
        else:
            print(f"   ↻ 等待 {args.swap_wait:.1f}s 仍未送达，按模板继续（迟到结果会自动进缓存供下一轮）")
    if registry_entry.get("generator_note"):
        print(f"   备注 = {registry_entry['generator_note']}")
    code_lines = generated.path.read_text(encoding="utf-8").splitlines()
    print(f"   代码共 {len(code_lines)} 行，前 6 行：")
    for line in code_lines[:6]:
        print(f"     | {line}")

    print("-" * 72)
    print("② 三道门：AST 静态安检 → 限时沙箱试跑 → 质量门")
    safety = manager.safety_check(generated.path, generated.strategy_id)
    print(f"   门1 静态安检: {'通过' if safety.passed else '拒绝'}（{safety.reason}）")
    if not safety.passed:
        print("   已拒绝并留痕（strategy_registry.json / evolution_memory.jsonl）")
        return 1

    score_fn, summarize_fn = make_scorers(candidates, all_tasks)
    baseline = baseline_cost_of(candidates, all_tasks, score_fn)
    print(f"   基线（贪心）期望成本 = {baseline:.2f}")
    outcome = manager.run_generated_strategy(
        generated, candidates, all_tasks,
        deadline_s=0.5,
        helpers={"time_left": lambda deadline: 0.5, "fallback_greedy": lambda rows: []},
        baseline_cost=baseline,
        score_fn=score_fn,
        summarize_fn=summarize_fn,
        case_profile=case_profile,
    )
    print(f"   门2 限时沙箱: 执行 {outcome.elapsed_ms:.1f} ms，输出 {len(outcome.solution)} 条派单")
    print(f"   门3 质量门:   成本 = {outcome.local_cost if outcome.local_cost is not None else 'N/A'}"
          f" → {'接受，进入候选池 (candidate)' if outcome.accepted else f'拒绝（{outcome.reason}）'}")

    print("-" * 72)
    tick = time.perf_counter()
    second = manager.generate_strategy(args.regime, "llm_evolution_demo:repeat", case_profile, llm_wait_s=0.0)
    second_ms = (time.perf_counter() - tick) * 1000.0
    second_note = manager._read_registry()[second.strategy_id].get("generator_note", "")
    print(f"③ 同类场景再次生成：来源 = {second.generator}   耗时 = {second_ms:.0f} ms"
          f"{'（场景桶缓存命中，无需再调 LLM）' if 'cache hit' in second_note else ''}")
    print("-" * 72)
    print(f"④ 留痕：{root}/strategy_registry.json / evolution_memory.jsonl / llm_code_cache.json")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
