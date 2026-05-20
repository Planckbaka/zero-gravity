<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# tools

## Purpose
Custom agent-accessible tool implementations for state and task management. These tools are registered into the `ToolRegistry` and exposed to Antigravity agents via the tool schema auto-generation from docstrings.

## Key Files
| File | Description |
|------|-------------|
| `state_tools.py` | State management tools: `state_read()`, `state_write(stage, task_id?, step_history?)`, `state_clear()` — wraps `StateManager` for agent access |
| `task_tools.py` | Task checklist tools: `task_create(subject, description?)`, `task_update(subject, status)`, `task_list()` — manages `.zg/tasks.md` as a markdown checkbox list |

## For AI Agents

### Working In This Directory
- `state_tools` wraps `StateManager` — agents read/write the orchestrator state without knowing about file locks
- `task_tools` manages a human-readable `.zg/tasks.md` with markdown checkbox syntax: `- [ ]`, `- [x]`, `- [/]`
- `task_update` supports statuses: `completed`, `in_progress`, `pending`
- All tool functions return strings (success messages or JSON/checkbox content)

### Testing Requirements
- Use `tmp_path` fixture and patch `TASKS_FILE` for task_tools tests
- Mock `StateManager` for state_tools tests

### Common Patterns
- Tools follow the Antigravity convention: docstrings become tool descriptions, type hints become parameter schemas
- State and task tools are registered in `init_registry()` alongside builtin workspace tools
