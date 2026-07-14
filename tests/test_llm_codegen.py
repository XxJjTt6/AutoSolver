"""LLM 策略代码生成（llm_generator + evolution 接线）的行为契约测试。

关键契约：
1. 默认（无环境变量）完全关闭——生成走确定性模板，行为与接入前一致；
2. LLM 返回合规代码 → 写盘的是 LLM 代码、registry 标 generator=llm，且仍要过三道门；
3. LLM 返回危险/不合规代码 → 预筛拦下，自动回退模板并留痕（generator_note）；
4. LLM 调用失败 → 自动回退模板并留痕，不阻塞主链路。
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autosolver_agent import llm_generator
from autosolver_agent.evolution import EvolutionManager

GOOD_CODE = '''from __future__ import annotations


def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    used_couriers = set()
    covered_tasks = set()
    result = []
    rows = sorted(candidates, key=lambda row: (row[3] / max(row[4], 0.001), row[3]))
    for task_key, task_ids, courier_id, _score, _willingness, _row_index in rows:
        if time_left is not None and time_left(deadline) <= 0.01:
            break
        if courier_id in used_couriers:
            continue
        if any(task_id in covered_tasks for task_id in task_ids):
            continue
        used_couriers.add(courier_id)
        covered_tasks.update(task_ids)
        result.append((task_key, [courier_id]))
    return result
'''

UNSAFE_CODE = '''import os


def propose(candidates, all_tasks, deadline, helpers):
    os.system("echo pwned")
    return []
'''

CASE_PROFILE = {
    "regime": "low-willingness",
    "tasks": 3,
    "couriers": 5,
    "rows": 12,
    "avg_willingness": 0.21,
    "has_bundles": False,
}


class LlmGeneratorSwitchTest(unittest.TestCase):
    def test_disabled_without_any_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(llm_generator.enabled())

    def test_disabled_with_key_but_no_flag(self):
        with mock.patch.dict(os.environ, {"DASHSCOPE_LLM_API_KEY": "k"}, clear=True):
            self.assertFalse(llm_generator.enabled())

    def test_enabled_with_key_and_flag(self):
        env = {"DASHSCOPE_LLM_API_KEY": "k", "AUTOSOLVER_LLM_CODEGEN": "1"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertTrue(llm_generator.enabled())

    def test_generate_code_without_key_is_unavailable(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            result = llm_generator.generate_code("scarce", CASE_PROFILE)
        self.assertEqual(result["status"], "unavailable")

    def test_extract_code_strips_markdown_fence(self):
        fenced = "```python\ndef propose(candidates, all_tasks, deadline, helpers):\n    return []\n```"
        self.assertNotIn("```", llm_generator._extract_code(fenced))


class EvolutionLlmCodegenTest(unittest.TestCase):
    def _registry(self, root: Path) -> dict:
        return json.loads((root / "strategy_registry.json").read_text(encoding="utf-8"))

    def test_default_off_uses_template(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=True):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("low-willingness", "probe", CASE_PROFILE)
            self.assertEqual(generated.generator, "template")
            self.assertIn("Auto-generated experimental strategy", generated.path.read_text(encoding="utf-8"))
            self.assertEqual(self._registry(Path(tmp))[generated.strategy_id]["generator"], "template")

    def test_llm_good_code_is_used_and_passes_gates(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "generate_code", return_value={"status": "ok", "code": GOOD_CODE, "model": "qwen-test"}):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("low-willingness", "probe", CASE_PROFILE)
            self.assertEqual(generated.generator, "llm")
            self.assertEqual(generated.path.read_text(encoding="utf-8"), GOOD_CODE)
            entry = self._registry(Path(tmp))[generated.strategy_id]
            self.assertEqual(entry["generator"], "llm")
            self.assertIn("qwen-test", entry["generator_note"])

            safety = manager.safety_check(generated.path)
            self.assertTrue(safety.passed, safety.reason)

            outcome = manager.run_generated_strategy(
                generated,
                candidates=[("T0000", ("T0000",), "C000", 1.0, 0.9, 0)],
                all_tasks={"T0000"},
                deadline_s=0.2,
                helpers={"fallback_greedy": lambda rows: [("T0000", ["C000"])]},
                baseline_cost=10.0,
                score_fn=lambda solution: 1.0,
                summarize_fn=lambda solution, cost: {"valid": True, "invalid_reasons": []},
                case_profile=CASE_PROFILE,
            )
            self.assertTrue(outcome.accepted, outcome.reason)

    def test_llm_unsafe_code_falls_back_to_template(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "generate_code", return_value={"status": "ok", "code": UNSAFE_CODE, "model": "qwen-test"}):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("scarce", "probe", CASE_PROFILE)
            self.assertEqual(generated.generator, "template")
            entry = self._registry(Path(tmp))[generated.strategy_id]
            self.assertIn("pre-rejected", entry["generator_note"])
            self.assertIn("unsafe import: os", entry["generator_note"])
            # 回退后的模板仍然可用
            self.assertTrue(manager.safety_check(generated.path).passed)

    def test_llm_error_falls_back_to_template(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "generate_code", return_value={"status": "error", "message": "LLM 调用失败：timeout"}):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("scarce", "probe", CASE_PROFILE)
            self.assertEqual(generated.generator, "template")
            self.assertIn("timeout", self._registry(Path(tmp))[generated.strategy_id]["generator_note"])

    def test_pre_screen_rejects_bad_signature_and_missing_propose(self):
        screen = EvolutionManager._pre_screen_generated_code
        self.assertIsNone(screen(GOOD_CODE))
        self.assertEqual(screen("def propose(a, b):\n    return []\n"), "invalid propose signature")
        self.assertEqual(screen("x = 1\n"), "missing propose")
        self.assertIn("while", screen("def propose(candidates, all_tasks, deadline, helpers):\n    while True:\n        pass\n"))


class LlmLatencyPipelineTest(unittest.TestCase):
    """10 秒预算下的低延迟链路：缓存命中 / 异步 pending / 试跑前热切换 / 迟到入缓存。"""

    def _registry(self, root: Path) -> dict:
        return json.loads((root / "strategy_registry.json").read_text(encoding="utf-8"))

    def test_cache_hit_returns_llm_code_without_calling_api(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "request_code_async", side_effect=AssertionError("cache hit 不应发起新请求")):
            manager = EvolutionManager(Path(tmp))
            key = manager._llm_bucket_key("low-willingness", manager._compact_case_profile(CASE_PROFILE))
            manager._llm_cache_store(key, GOOD_CODE, "qwen-cached")
            generated = manager.generate_strategy("low-willingness", "probe", CASE_PROFILE, llm_wait_s=0.0)
            self.assertEqual(generated.generator, "llm")
            self.assertEqual(generated.path.read_text(encoding="utf-8"), GOOD_CODE)
            self.assertIn("cache hit", self._registry(Path(tmp))[generated.strategy_id]["generator_note"])

    def test_pending_starts_with_template_then_hot_swaps(self):
        from concurrent.futures import Future

        future = Future()
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "request_code_async", return_value=future):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("scarce", "probe", CASE_PROFILE, llm_wait_s=0.0)
            # 等待预算为 0：立即用模板起步，请求挂在 pending
            self.assertEqual(generated.generator, "template")
            self.assertIn("pending", self._registry(Path(tmp))[generated.strategy_id]["generator_note"])
            self.assertFalse(manager.refresh_generated_strategy(generated))  # 结果未到，不切换

            future.set_result({"status": "ok", "code": GOOD_CODE, "model": "qwen-late"})
            self.assertTrue(manager.refresh_generated_strategy(generated))  # 结果到了，热切换
            self.assertEqual(generated.path.read_text(encoding="utf-8"), GOOD_CODE)
            entry = self._registry(Path(tmp))[generated.strategy_id]
            self.assertEqual(entry["generator"], "llm")
            self.assertIn("hot-swapped", entry["generator_note"])
            # 热切换的代码同样要过安全门
            self.assertTrue(manager.safety_check(generated.path).passed)
            # 迟到结果已写入场景桶缓存：下一轮同类场景 0 毫秒命中
            second = manager.generate_strategy("scarce", "probe", CASE_PROFILE, llm_wait_s=0.0)
            self.assertEqual(second.generator, "llm")
            self.assertIn("cache hit", self._registry(Path(tmp))[second.strategy_id]["generator_note"])

    def test_late_failure_keeps_template_and_records_note(self):
        from concurrent.futures import Future

        future = Future()
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "request_code_async", return_value=future):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("scarce", "probe", CASE_PROFILE, llm_wait_s=0.0)
            future.set_result({"status": "error", "message": "LLM 调用失败：timeout"})
            self.assertFalse(manager.refresh_generated_strategy(generated))
            entry = self._registry(Path(tmp))[generated.strategy_id]
            self.assertEqual(entry["generator"], "template")
            self.assertIn("late failure", entry["generator_note"])
            self.assertTrue(manager.safety_check(generated.path).passed)

    def test_sync_wait_uses_result_when_fast(self):
        from concurrent.futures import Future

        future = Future()
        future.set_result({"status": "ok", "code": GOOD_CODE, "model": "qwen-fast"})
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(llm_generator, "enabled", return_value=True), \
                mock.patch.object(llm_generator, "request_code_async", return_value=future):
            manager = EvolutionManager(Path(tmp))
            generated = manager.generate_strategy("scarce", "probe", CASE_PROFILE, llm_wait_s=1.0)
            self.assertEqual(generated.generator, "llm")
            self.assertEqual(generated.path.read_text(encoding="utf-8"), GOOD_CODE)

    def test_repair_code_renames_single_four_arg_function(self):
        broken = "def choose_plan(candidates, all_tasks, deadline, helpers):\n    return []\n"
        fixed = llm_generator.repair_code(broken)
        self.assertIn("def propose(candidates, all_tasks, deadline, helpers):", fixed)
        self.assertIsNone(EvolutionManager._pre_screen_generated_code(fixed))


if __name__ == "__main__":
    unittest.main()
