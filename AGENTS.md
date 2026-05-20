<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# zero-gravity

## Purpose
Multi-agent orchestration plugin for Google Antigravity SDK, modeled after Oh My Claude Code (OMC). Provides structured workflows (autopilot, ralph, team) with state persistence, dual API strategy (L1 Agent / L2 Conversation), and a tool registry for agent coordination.

## Key Files
| File | Description |
|------|-------------|
| `pyproject.toml` | Project metadata — Python >=3.14, depends on `google-antigravity>=0.1.0` |
| `plugin.json` | Antigravity plugin manifest (name, version, author) |
| `main.py` | Standalone demo: creates an L1 Agent with a custom `greeting_tool` and runs a chat loop |
| `PRD.md` | Product requirements document — defines zg-setup, gradual confirmation flow, state persistence |
| `DEVELOPMENT_GUIDE.md` | Architecture guide: dual API strategy, OMC-to-Antigravity concept mapping, module designs |
| `README.md` | Project readme (currently empty) |
| `.python-version` | Python version pin for `uv` |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `src/` | Source code container (see `src/AGENTS.md`) |
| `agents/` | Antigravity agent system-instruction markdown files (see `agents/AGENTS.md`) |
| `commands/` | CLI command definitions for the Antigravity plugin (see `commands/AGENTS.md`) |
| `skills/` | User-facing skill definitions loaded at runtime (see `skills/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Use `uv` for dependency management (`uv run`, `uv add`)
- Run tests with `uv run pytest`
- The project follows PEP 8 with type hints required
- Agent profiles are defined as YAML in `src/zero_g/agents/profiles/`
- Tools are registered via `ToolRegistry` singleton at startup via `init_registry()`

### Testing Requirements
- Run `uv run pytest` from the project root
- Tests are not yet created; expected location is `tests/` at root level

### Common Patterns
- Dual API strategy: L1 `Agent` for parallel workers, L2 `Conversation` for multi-stage skills
- All tool functions use docstrings for Antigravity SDK auto-schema generation
- State persistence uses file-locked JSON in `.zg/` directory

## Dependencies

### External
- `google-antigravity>=0.1.0` — Antigravity SDK (Agent, LocalAgentConfig, policies)
- `pyyaml` (transitive) — YAML profile parsing

<!-- MANUAL: Custom project notes can be added below -->
