<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# zero_g

## Purpose
Core Python package for the zero-gravity multi-agent orchestration framework. Implements agent factories, tool registry, state management, skill loading, and custom tools on top of the Google Antigravity SDK.

## Key Files
| File | Description |
|------|-------------|
| `__init__.py` | Package init — exports `__version__ = "0.1.0"` |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `core/` | Core orchestration modules: agent factory, tool registry, state manager, skill loader, JSON utils (see `core/AGENTS.md`) |
| `agents/` | Agent profiles (YAML) and builtin tool implementations (see `agents/AGENTS.md`) |
| `skills/` | Skill base classes (`BaseSkill`, `SkillConfig`) (see `skills/AGENTS.md`) |
| `tools/` | Custom agent-accessible tools: state and task management (see `tools/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- This is the installable Python package (`zero_g`)
- Import path: `from zero_g.core.tool_registry import registry`
- Initialize the tool registry at startup: `from zero_g.core.tool_registry import init_registry; init_registry()`
- All modules use `from __future__ import annotations` for forward-compatible type hints

### Testing Requirements
- Unit tests should mock `google.antigravity` SDK imports since the SDK requires a running harness
- Test state management with temporary directories via `tmp_path` fixture

### Common Patterns
- `ToolRegistry` is a global singleton — register tools once via `init_registry()`
- Agent profiles are YAML files loaded by `load_profile(name)` — name maps to `profiles/{name}.yaml`
- State files live in `.zg/` at the project root, not inside this package
