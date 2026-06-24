"""Teacher v4 —— 策略护栏 + 停滞复盘。

- playbook(): 读 teacher_playbook_v4.md（嵌入 system prompt，可缓存）。
- checklist(regime): 该 regime 的护栏与"当前别再踩的坑"（结合 memory 的 try_error）。
- should_review(history): 停滞检测（最近 N 轮无 improved）。
- review(client, ...): 触发一次反思（可用 deepseek-reasoner），产 next_candidates 注入下一轮 header。
"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PLAYBOOK = _ROOT / "autosolver_llm_v4" / "teacher_playbook_v4.md"


class Teacher:
    def __init__(self, memory=None, playbook_path: Path | None = None) -> None:
        self.memory = memory
        self.playbook_path = Path(playbook_path or _PLAYBOOK)
        self._cache: str | None = None

    def playbook(self) -> str:
        if self._cache is None:
            self._cache = self.playbook_path.read_text(encoding="utf-8") if self.playbook_path.exists() else ""
        return self._cache

    def checklist(self, regime: str) -> str:
        lines = [
            "## Teacher 护栏（必须遵守）",
            "- 只能写 propose(candidates, all_tasks, deadline, helpers)，返回 list[tuple[str, list[str]]]。",
            "- 尽量覆盖 all_tasks（未覆盖重罚）；不得重复用 courier、不得重复覆盖 task。",
            "- 白名单 import；禁 while；用 helpers['time_left'](deadline) 做 anytime 截断。",
            f"- 当前场景 regime = {regime}；按 playbook 对应方向提一个小改进假设。",
        ]
        if self.memory is not None:
            hits = self.memory.search(f"{regime} fail regression", sections=["try_error"], k=3)
            if hits:
                lines.append("- 已知坑（别再犯）：")
                for h in hits:
                    lines.append(f"  · {h['meta'].get('title', '')}")
        return "\n".join(lines)

    @staticmethod
    def should_review(history: list[dict], window: int = 3) -> bool:
        recent = history[-window:]
        if len(recent) < window:
            return False
        return all(h.get("outcome") not in ("improved", "accepted") for h in recent)

    def review(self, client, history: list[dict], regime: str) -> str:
        """停滞复盘：让模型总结已饱和方向 + 提 next_candidates。失败则返回静态提示。"""
        recent = history[-5:]
        summary = "\n".join(
            f"- R{h.get('round')}: {h.get('outcome')} cost={h.get('candidate_cost')} 假设={h.get('hypothesis','')[:80]}"
            for h in recent
        )
        prompt = [
            {"role": "system", "content": "你是调度策略复盘教练。只输出简洁中文复盘，给出 1) 已饱和/无效方向 2) 接下来值得试的 2 个新方向。"},
            {"role": "user", "content": f"regime={regime}，最近几轮：\n{summary}\n请复盘。"},
        ]
        try:
            return client.complete(prompt, max_tokens=600)
        except Exception as exc:
            return f"(复盘不可用: {exc}) 建议换方向：①对未接风险任务多派；②按 willingness 重排尾段。"
