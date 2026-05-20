"""Agent-accessible notepad tools wrapping the Notepad module."""
from __future__ import annotations
from zero_g.core.notepad import Notepad

_notepad = Notepad()


def notepad_read(section: str | None = None) -> str:
    """Read the notepad. Optionally filter by section ('priority', 'working', 'manual').

    Args:
        section: Optional section name. If omitted, returns all.
    """
    import json
    if section == "priority":
        return _notepad.read_priority() or "Priority context is empty."
    elif section == "working":
        return json.dumps(_notepad.read_working(), indent=2, ensure_ascii=False)
    elif section == "manual":
        return json.dumps(_notepad.read_manual(), indent=2, ensure_ascii=False)
    return json.dumps(_notepad.read_all(), indent=2, ensure_ascii=False)


def notepad_write_priority(content: str) -> str:
    """Write to the Priority Context section (max 500 chars, always loaded).

    Args:
        content: The priority context to set.
    """
    return _notepad.write_priority(content)


def notepad_write_working(content: str, tags: str = "") -> str:
    """Add an entry to Working Memory (auto-pruned after 7 days).

    Args:
        content: The content to remember.
        tags: Comma-separated tags for categorization.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return _notepad.write_working(content, tag_list)


def notepad_write_manual(content: str, tags: str = "") -> str:
    """Add a permanent entry to the Manual section (never auto-pruned).

    Args:
        content: The content to remember permanently.
        tags: Comma-separated tags for categorization.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return _notepad.write_manual(content, tag_list)


def notepad_prune(days: int = 7) -> str:
    """Remove working memory entries older than N days.

    Args:
        days: Age threshold in days (default 7).
    """
    _notepad.prune_days = days
    pruned = _notepad.prune()
    return f"Pruned {pruned} entries older than {days} days."


def notepad_stats() -> str:
    """Get notepad statistics."""
    import json
    return json.dumps(_notepad.stats(), indent=2)
