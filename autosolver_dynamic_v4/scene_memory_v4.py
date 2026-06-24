"""场景识别记忆：从离线学到的策略库（registry）按 regime 召回 propose() 代码。

warm 泳道 enabled=True（带记忆）；cold 泳道 enabled=False（无记忆）。
读 autosolver_agent/evolution_state/strategy_registry.json + generated_strategies/*.py。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class SceneMemory:
    """召回离线学到的策略。优先读 committed strategy_pack（durable，免受 evolution_state 重置影响），
    再叠加 live registry（如有）。"""

    def __init__(self, state_root: Path | None = None, pack_root: Path | None = None,
                 enabled: bool = True) -> None:
        self.enabled = enabled
        self.root = Path(state_root or (_ROOT / "autosolver_agent" / "evolution_state"))
        self.registry_path = self.root / "strategy_registry.json"
        self.pack_root = Path(pack_root) if pack_root else (_ROOT / "autosolver_llm_v4" / "strategy_pack_v4")
        self._cache: dict | None = None

    def _load(self) -> dict:
        if not self.enabled:
            return {}
        by_regime: dict[str, list] = {}
        # 1) committed strategy pack（durable，真实 DeepSeek 学到的策略）
        manifest = self.pack_root / "manifest.json"
        if manifest.exists():
            try:
                meta = json.loads(manifest.read_text(encoding="utf-8"))
                for regime, items in (meta.get("strategies") or {}).items():
                    for it in items:
                        f = self.pack_root / it["file"]
                        if f.exists():
                            by_regime.setdefault(regime, []).append(
                                (it["sid"], float(it.get("cost", 1e18)), f.read_text(encoding="utf-8")))
            except Exception:
                pass
        # 2) live registry（次要；evolution_state 可能被 git 重置，仅作补充）
        if not self.registry_path.exists():
            for r in by_regime:
                by_regime[r].sort(key=lambda x: x[1])
            return by_regime
        try:
            registry = json.loads(self.registry_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            registry = {}
        seen = {sid for items in by_regime.values() for sid, _, _ in items}
        for sid, item in registry.items():
            if sid in seen:
                continue
            if item.get("status") not in {"candidate", "trusted", "promoted"}:
                continue
            if int(item.get("accepted", 0) or 0) <= 0:
                continue
            regime = item.get("target_regime") or "generic"
            f = item.get("file")
            code = None
            if f and Path(f).exists():
                try:
                    code = Path(f).read_text(encoding="utf-8")
                except Exception:
                    code = None
            if code:
                by_regime.setdefault(regime, []).append(
                    (sid, float(item.get("last_cost") or 1e18), code)
                )
        for r in by_regime:
            by_regime[r].sort(key=lambda x: x[1])
        return by_regime

    def recall(self, regime: str, k: int = 2) -> list[tuple[str, str]]:
        if not self.enabled:
            return []
        if self._cache is None:
            self._cache = self._load()
        return [(sid, code) for sid, _, code in self._cache.get(regime, [])[:k]]

    def known_regimes(self) -> list[str]:
        if self._cache is None:
            self._cache = self._load()
        return sorted(self._cache.keys())
