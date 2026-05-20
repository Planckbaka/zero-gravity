"""Persistent working memory (notepad) for cross-session knowledge.

Port of OMC's notepad system. Three sections:
- Priority Context: always loaded, max 500 chars, never auto-pruned
- Working Memory: timestamped entries, auto-pruned after 7 days
- Manual: permanent entries, never auto-pruned

Storage: .zg/notepad.json
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class NotepadEntry:
    content: str
    timestamp: float
    tags: list[str] = field(default_factory=list)


class Notepad:
    """Persistent working memory with three sections."""

    def __init__(self, path: Path | None = None, prune_days: int = 7, max_priority_chars: int = 500):
        self.path = path or Path(".zg/notepad.json")
        self.prune_days = prune_days
        self.max_priority_chars = max_priority_chars
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"priority": "", "working": [], "manual": []}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Priority Context ---

    def read_priority(self) -> str:
        return self._data.get("priority", "")

    def write_priority(self, content: str) -> str:
        if len(content) > self.max_priority_chars:
            content = content[:self.max_priority_chars - 3] + "..."
        self._data["priority"] = content
        self._save()
        return f"Priority context updated ({len(content)} chars)."

    # --- Working Memory ---

    def read_working(self) -> list[dict]:
        return self._data.get("working", [])

    def write_working(self, content: str, tags: list[str] | None = None) -> str:
        entry = {
            "content": content,
            "timestamp": time.time(),
            "tags": tags or [],
        }
        self._data.setdefault("working", []).append(entry)
        self._save()
        return f"Working memory entry added."

    # --- Manual ---

    def read_manual(self) -> list[dict]:
        return self._data.get("manual", [])

    def write_manual(self, content: str, tags: list[str] | None = None) -> str:
        entry = {
            "content": content,
            "timestamp": time.time(),
            "tags": tags or [],
        }
        self._data.setdefault("manual", []).append(entry)
        self._save()
        return f"Manual entry added (permanent)."

    # --- Read All ---

    def read_all(self) -> dict:
        return dict(self._data)

    # --- Pruning ---

    def prune(self) -> int:
        """Remove working memory entries older than prune_days. Returns count pruned."""
        cutoff = time.time() - (self.prune_days * 86400)
        working = self._data.get("working", [])
        before = len(working)
        self._data["working"] = [e for e in working if e.get("timestamp", 0) >= cutoff]
        pruned = before - len(self._data["working"])
        if pruned > 0:
            self._save()
        return pruned

    def stats(self) -> dict:
        working = self._data.get("working", [])
        manual = self._data.get("manual", [])
        priority = self._data.get("priority", "")
        oldest = min((e["timestamp"] for e in working), default=0)
        return {
            "priority_chars": len(priority),
            "working_entries": len(working),
            "manual_entries": len(manual),
            "oldest_working_age_days": (time.time() - oldest) / 86400 if oldest else 0,
        }
