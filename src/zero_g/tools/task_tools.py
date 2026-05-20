"""Task tools module for zero_g, providing mechanisms to manipulate the human-readable .zg/tasks.md checklist."""
from __future__ import annotations
import re
from pathlib import Path

TASKS_FILE = Path(".zg/tasks.md")


def get_tasks_path() -> Path:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("# zero-gravity Task checklist\n\n", encoding="utf-8")
    return TASKS_FILE


def task_create(subject: str, description: str = "") -> str:
    """Create a new task in .zg/tasks.md.

    Args:
        subject: The title of the task.
        description: Brief details of the task.
    """
    path = get_tasks_path()
    content = path.read_text(encoding="utf-8")

    desc_suffix = f": {description}" if description else ""
    task_line = f"- [ ] {subject}{desc_suffix}\n"

    # Append to the end of file
    if not content.endswith("\n"):
        content += "\n"
    content += task_line
    path.write_text(content, encoding="utf-8")

    return f"Successfully created task: {subject}"


def task_update(subject: str, status: str) -> str:
    """Update an existing task in .zg/tasks.md.

    Args:
        subject: The exact title/subject of the task to update.
        status: The new status ('completed' or 'pending' or 'in_progress').
    """
    path = get_tasks_path()
    content = path.read_text(encoding="utf-8")

    # Map status to Markdown checkboxes: completed -> [x], pending -> [ ], in_progress -> [/]
    if status == "completed":
        marker = "[x]"
    elif status == "in_progress":
        marker = "[/]"
    else:
        marker = "[ ]"

    # Find the line starting with - [ ] or - [x] or - [/] followed by subject
    pattern = rf"- \[[ xX/]\] ({re.escape(subject)})(.*)"

    def replace_fn(match: re.Match) -> str:
        return f"- {marker} {match.group(1)}{match.group(2)}"

    new_content, count = re.subn(pattern, replace_fn, content)
    if count == 0:
        # Fallback: if not exact, try case-insensitive or partial match
        pattern_lazy = rf"- \[[ xX/]\] .*?{re.escape(subject)}.*"
        new_content, count = re.subn(pattern_lazy, lambda m: m.group(0).replace(m.group(0)[:5], f"- {marker}"), content)

    path.write_text(new_content, encoding="utf-8")

    if count > 0:
        return f"Successfully updated task '{subject}' to status: {status}"
    return f"Task '{subject}' not found in tasks.md"


def task_list() -> str:
    """List all tasks and their checkbox status from .zg/tasks.md."""
    path = get_tasks_path()
    content = path.read_text(encoding="utf-8")

    lines = content.splitlines()
    tasks = []
    for line in lines:
        if line.strip().startswith("- ["):
            tasks.append(line.strip())

    if not tasks:
        return "No tasks found in tasks.md."
    return "\n".join(tasks)
