<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# core

## Purpose
Core orchestration modules providing the foundational building blocks: agent creation, tool registration, state persistence, skill discovery, and LLM output parsing.

## Key Files
| File | Description |
|------|-------------|
| `__init__.py` | Package init |
| `agent_factory.py` | L1 Agent factory — creates Antigravity `Agent` instances from YAML profiles with resolved tools and policies |
| `tool_registry.py` | `ToolRegistry` singleton mapping string tool names to Python callables; `init_registry()` registers all builtin/state/task tools |
| `state_manager.py` | `StateManager` — file-locked atomic read/write to `.zg/state.json` with stale-state cleanup (24h expiry) |
| `skill_loader.py` | `SkillLoader` — discovers and loads skill directories (requires `skill.yaml` + `handler.py`), builds trigger keyword map |
| `json_utils.py` | `extract_json()` — robust JSON extraction from LLM text output (handles markdown fences, trailing commas, surrounding text) |

## For AI Agents

### Working In This Directory
- `tool_registry.py` contains the global `registry` singleton — call `init_registry()` once at app startup
- `agent_factory.py` uses `fcntl` file locks — POSIX only (Linux/macOS); not compatible with Windows
- `json_utils.py` is defensive by design: it tries multiple extraction strategies before raising `ValueError`
- `skill_loader.py` uses unique module names (`zero_g.skills.{name}.handler`) to avoid import conflicts

### Testing Requirements
- Mock `google.antigravity` imports for `agent_factory` tests
- Use `tmp_path` for `state_manager` tests (isolated `.zg/` directories)
- Test `json_utils.extract_json` with various malformed inputs

### Common Patterns
- All modules use `from __future__ import annotations` for PEP 604 union syntax
- File locking pattern: acquire `LOCK_EX` for writes, `LOCK_SH` for reads, always release in `finally` block
- State default: `{"current_stage": "initialized", "task_id": null, "step_history": []}`
