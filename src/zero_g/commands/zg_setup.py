"""Command module to bootstrap the zero-gravity workspace environment."""
from __future__ import annotations
import json
from pathlib import Path

def bootstrap_workspace() -> str:
    """Bootstrap the workspace by creating state, task checklist, and guide files.

    Returns:
        A report summarizing the bootstrap operations.
    """
    report = []
    
    # 1. Create .zg directory
    zg_dir = Path(".zg")
    zg_dir.mkdir(parents=True, exist_ok=True)
    report.append("Created directory: .zg/")

    # 2. Create state.json
    state_file = zg_dir / "state.json"
    if not state_file.exists():
        initial_state = {
            "current_stage": "initialized",
            "task_id": None,
            "step_history": [],
            "correction_attempts": 0
        }
        state_file.write_text(json.dumps(initial_state, indent=2, ensure_ascii=False), encoding="utf-8")
        report.append("Initialized state file: .zg/state.json")
    else:
        report.append("Skipped state file (already exists): .zg/state.json")

    # 3. Create tasks.md
    tasks_file = zg_dir / "tasks.md"
    if not tasks_file.exists():
        tasks_template = "# zero-gravity Task checklist\n\n- [ ] Initialize workspace\n"
        tasks_file.write_text(tasks_template, encoding="utf-8")
        report.append("Initialized task list: .zg/tasks.md")
    else:
        report.append("Skipped task list (already exists): .zg/tasks.md")

    # 4. Create ANTIGRAVITY.md at workspace root
    guide_file = Path("ANTIGRAVITY.md")
    guide_content = """# Antigravity Workspace Guidelines — zero-gravity

This workspace is configured with the `zero-gravity` multi-agent orchestrator plugin.

## Setup & Running
- Python version: >=3.14 (managed via `uv`)
- Dependencies: Installed via `uv sync` or `uv pip`
- Verification commands: `pytest`

## Multi-Agent Workflow State
The multi-agent orchestration stage is tracked in `.zg/state.json`.
The human-readable checklists and progress are kept in `.zg/tasks.md`.

## Active Agent Coordination
To orchestrate subagents (Architect, Executor, Tester) for a complex task, the main agent reads `.zg/state.json` and runs the `zg-orchestrator` skill.

## Coding Standards & Guidelines
- Code Style: Strictly adhere to PEP 8, use clear variable names, and provide complete type hints.
- Documentation: Maintain all existing comments, docstrings, and headers unless explicitly asked otherwise.
- Error Handling: Use explicit try-except blocks with clean logged tracebacks instead of generic silences.
"""
    guide_file.write_text(guide_content.strip() + "\n", encoding="utf-8")
    report.append("Created guide template: ANTIGRAVITY.md")

    return "### 🚀 Workspace Successfully Bootstrapped!\n\n" + "\n".join(f"- {line}" for line in report)

if __name__ == "__main__":
    print(bootstrap_workspace())
