"""LLM 客户端 v4 —— 默认 DeepSeek（OpenAI 兼容），纯 stdlib（urllib），含 FakeModelClient。

设计要点：
- DeepSeek API 与 OpenAI 完全兼容（POST /chat/completions）。
- key 优先读环境变量 DEEPSEEK_API_KEY，回退读 .secrets/deepseek_key（gitignore）。
- complete() 失败做指数退避重试；上层可在彻底失败时回退 FakeModelClient。
- deepseek-reasoner 会返回 reasoning_content，complete_with_reasoning() 单独暴露。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# provider 配置；切换只改一处。base_url/模型名以官方文档为准。
PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "endpoint": "/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
        "key_file": ".secrets/deepseek_key",
        "model": "deepseek-chat",          # V3：工具循环/策略生成主力
        "reason_model": "deepseek-reasoner",  # R1：反思步按需
    },
    "openai": {
        "base_url": "https://api.openai.com",
        "endpoint": "/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "key_file": ".secrets/openai_key",
        "model": "gpt-4o-mini",
        "reason_model": "o3-mini",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "endpoint": "/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "key_file": ".secrets/openrouter_key",
        "model": "deepseek/deepseek-chat",
        "reason_model": "deepseek/deepseek-r1",
    },
}


class LLMError(RuntimeError):
    pass


def _resolve_key(cfg: dict, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit.strip()
    env = os.environ.get(cfg["key_env"])
    if env:
        return env.strip()
    key_file = _ROOT / cfg["key_file"]
    if key_file.exists():
        text = key_file.read_text(encoding="utf-8").strip()
        if text:
            return text
    return None


class LLMClient:
    """OpenAI 兼容 chat 客户端（默认 DeepSeek）。"""

    def __init__(
        self,
        provider: str = "deepseek",
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 8000,
        timeout: int = 120,
        max_retries: int = 4,
    ) -> None:
        if provider not in PROVIDERS:
            raise LLMError(f"unknown provider: {provider}")
        self.provider = provider
        self.cfg = PROVIDERS[provider]
        self.model = model or self.cfg["model"]
        self.reason_model = self.cfg.get("reason_model", self.model)
        self.api_key = _resolve_key(self.cfg, api_key)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.url = self.cfg["base_url"].rstrip("/") + self.cfg["endpoint"]
        # 统计，便于前端/日志展示
        self.calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    def _post(self, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:  # noqa: PERF203
                body = ""
                try:
                    body = exc.read().decode("utf-8", "replace")[:500]
                except Exception:
                    pass
                last_err = LLMError(f"HTTP {exc.code}: {body}")
                if exc.code in (429, 500, 502, 503, 504):
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise last_err
            except (urllib.error.URLError, TimeoutError) as exc:
                last_err = LLMError(f"network error: {exc}")
                time.sleep(min(2 ** attempt, 30))
                continue
        raise last_err or LLMError("unknown LLM error")

    def _build_payload(self, messages, max_tokens, model, temperature) -> dict:
        return {
            "model": model or self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }

    def _account(self, resp: dict) -> None:
        self.calls += 1
        usage = resp.get("usage") or {}
        self.total_prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
        self.total_completion_tokens += int(usage.get("completion_tokens", 0) or 0)

    def complete(self, messages, max_tokens=None, model=None, temperature=None) -> str:
        if not self.has_key:
            raise LLMError(
                f"no api key for provider={self.provider} "
                f"(set ${self.cfg['key_env']} or write {self.cfg['key_file']})"
            )
        resp = self._post(self._build_payload(messages, max_tokens, model, temperature))
        self._account(resp)
        choices = resp.get("choices") or []
        if not choices:
            raise LLMError(f"empty choices: {json.dumps(resp)[:300]}")
        return choices[0]["message"].get("content") or ""

    def complete_with_reasoning(self, messages, max_tokens=None, temperature=None):
        """用 reason_model（如 deepseek-reasoner）；返回 (content, reasoning_content)。"""
        if not self.has_key:
            raise LLMError("no api key")
        resp = self._post(self._build_payload(messages, max_tokens, self.reason_model, temperature))
        self._account(resp)
        msg = (resp.get("choices") or [{}])[0].get("message", {})
        return msg.get("content") or "", msg.get("reasoning_content") or ""

    def usage_summary(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "calls": self.calls,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
        }


class FakeModelClient:
    """离线/无 key 回放客户端：按队列依次吐出预置的 assistant 文本。

    每次 complete() 弹出队首；队列耗尽抛错（提示脚本不足）。
    用于单测与现场断网演示，能完整驱动 harness 的 intent/tool/final 协议。
    """

    def __init__(self, scripted_outputs, provider: str = "fake"):
        self.queue = list(scripted_outputs)
        self.provider = provider
        self.model = "fake-model"
        self.reason_model = "fake-model"
        self.calls = 0
        self.seen_messages = []

    @property
    def has_key(self) -> bool:
        return True

    def complete(self, messages, max_tokens=None, model=None, temperature=None) -> str:
        self.calls += 1
        self.seen_messages.append(messages)
        if not self.queue:
            raise LLMError("FakeModelClient queue exhausted (脚本不足以驱动这一轮)")
        return self.queue.pop(0)

    def complete_with_reasoning(self, messages, max_tokens=None, temperature=None):
        return self.complete(messages), "(fake reasoning)"

    def usage_summary(self) -> dict:
        return {"provider": "fake", "model": "fake-model", "calls": self.calls}


def make_client(provider: str = "deepseek", **kwargs):
    if provider == "fake":
        scripts = kwargs.get("scripted_outputs", [])
        return FakeModelClient(scripts)
    return LLMClient(provider=provider, **{k: v for k, v in kwargs.items() if k != "scripted_outputs"})
