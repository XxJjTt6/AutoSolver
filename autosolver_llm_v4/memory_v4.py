"""三层 memory v4。

A 单轮  : llm_runs/<run_id>/round_NNN/dialog.jsonl + llm_runs/<run_id>/events.jsonl（前端回放）
B 数据集级: llm_memory/runs/<dataset_fp>/episodes.jsonl + strategy_index.json
C 全局  : llm_memory/notes/{lesson,try_error,key_decision}_*.md + llm_memory/MEMORY.md（BM25 可检索）

注：B 层与 autosolver_agent/evolution_state/ 的 evolution_memory.jsonl + strategy_registry.json
桥接（由 evolution_runner_v4 用 EvolutionManager 同步），此处保留独立 episodes 便于前端读取。
llm_runs/ 与 llm_memory/ 均已 gitignore。
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TOKEN = re.compile(r"[a-z0-9_]+")


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _tok(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


class MemoryV4:
    def __init__(self, run_id: str, dataset_fp: str,
                 runs_root: Path | None = None, mem_root: Path | None = None) -> None:
        self.run_id = run_id
        self.dataset_fp = dataset_fp
        self.runs_root = Path(runs_root or (_ROOT / "llm_runs"))
        self.mem_root = Path(mem_root or (_ROOT / "llm_memory"))
        self.run_dir = self.runs_root / run_id
        self.ds_dir = self.mem_root / "runs" / dataset_fp
        self.notes_dir = self.mem_root / "notes"
        for d in (self.run_dir, self.ds_dir, self.notes_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.events_path = self.run_dir / "events.jsonl"
        self.episodes_path = self.ds_dir / "episodes.jsonl"
        self.index_path = self.ds_dir / "strategy_index.json"

    # ---------- A 层 ----------
    def log_dialog(self, round_idx: int, role: str, content: str) -> None:
        rd = self.run_dir / f"round_{round_idx:03d}"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "dialog.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "role": role, "content": content}, ensure_ascii=False) + "\n")

    def log_event(self, event: dict) -> None:
        """供前端 /api/v4/llm/stream 回放的事件流。"""
        with self.events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), **event}, ensure_ascii=False) + "\n")

    def read_events(self) -> list[dict]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # ---------- B 层 ----------
    def write_episode(self, episode: dict) -> None:
        with self.episodes_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "run_id": self.run_id, **episode}, ensure_ascii=False) + "\n")

    def episodes(self) -> list[dict]:
        if not self.episodes_path.exists():
            return []
        return [json.loads(line) for line in self.episodes_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def update_index(self, strategy_id: str, patch: dict) -> None:
        index = {}
        if self.index_path.exists():
            index = json.loads(self.index_path.read_text(encoding="utf-8") or "{}")
        cur = index.get(strategy_id, {})
        cur.update(patch)
        cur["last_seen"] = _now()
        index[strategy_id] = cur
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    # ---------- C 层 ----------
    def write_note(self, section: str, title: str, body: str, tags: list[str] | None = None) -> Path:
        assert section in {"lesson", "try_error", "key_decision", "preference"}
        existing = sorted(self.notes_dir.glob(f"{section}_*.md"))
        path = self.notes_dir / f"{section}_{len(existing) + 1:03d}.md"
        front = {
            "section": section, "title": title, "run_id": self.run_id,
            "dataset_fp": self.dataset_fp, "tags": tags or [], "ts": _now(),
        }
        path.write_text(
            "---\n" + json.dumps(front, ensure_ascii=False) + "\n---\n" + body.strip() + "\n",
            encoding="utf-8",
        )
        self.rebuild_index()
        return path

    def _all_notes(self) -> list[dict]:
        notes = []
        for path in sorted(self.notes_dir.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            meta = {}
            body = raw
            if raw.startswith("---\n"):
                _, front, body = raw.split("---\n", 2)
                try:
                    meta = json.loads(front)
                except Exception:
                    meta = {}
            notes.append({"path": str(path.relative_to(self.mem_root)), "meta": meta, "body": body.strip()})
        return notes

    def search(self, query: str, sections: list[str] | None = None, k: int = 5) -> list[dict]:
        """轻量 BM25：词频 + 文档长度归一 + 标签命中加权。不引向量库。"""
        notes = self._all_notes()
        if sections:
            notes = [n for n in notes if n["meta"].get("section") in sections]
        if not notes:
            return []
        q_tokens = _tok(query)
        if not q_tokens:
            return []
        docs = [_tok(n["body"] + " " + n["meta"].get("title", "")) for n in notes]
        N = len(docs)
        avgdl = sum(len(d) for d in docs) / N
        df = Counter()
        for d in docs:
            for term in set(d):
                df[term] += 1
        k1, b = 1.5, 0.75
        scored = []
        q_tags = set(query.lower().split())
        for note, d in zip(notes, docs):
            tf = Counter(d)
            s = 0.0
            for term in q_tokens:
                if term not in tf:
                    continue
                idf = math.log(1 + (N - df[term] + 0.5) / (df[term] + 0.5))
                s += idf * (tf[term] * (k1 + 1)) / (tf[term] + k1 * (1 - b + b * len(d) / avgdl))
            tag_hit = len(q_tags & {t.lower() for t in note["meta"].get("tags", [])})
            s += 1.3 * tag_hit
            if s > 0:
                scored.append({**note, "score": round(s, 4)})
        scored.sort(key=lambda x: -x["score"])
        return scored[:k]

    def rebuild_index(self) -> None:
        """重建 llm_memory/MEMORY.md（每节 top 项的一行索引）。"""
        notes = self._all_notes()
        buckets: dict[str, list[dict]] = {}
        for n in notes:
            buckets.setdefault(n["meta"].get("section", "other"), []).append(n)
        lines = ["# LLM Memory Index", "", f"_rebuilt {_now()}_", ""]
        for section in ("key_decision", "lesson", "try_error", "preference"):
            items = buckets.get(section, [])
            if not items:
                continue
            lines.append(f"## {section} ({len(items)})")
            for n in items[-5:]:
                lines.append(f"- [{n['meta'].get('title', '(untitled)')}]({n['path']})")
            lines.append("")
        (self.mem_root / "MEMORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
