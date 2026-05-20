<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# agents

## Purpose
Agent role definitions: YAML profile configurations for Antigravity L1 Agent creation, and builtin workspace tool implementations (file I/O, shell commands, search).

## Key Files
| File | Description |
|------|-------------|
| `__init__.py` | Package init |
| `_builtin_tools.py` | Six workspace tools: `read_file`, `write_file`, `edit_file`, `run_command`, `search_files`, `list_directory` |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `profiles/` | YAML agent profile configs defining system instructions and tool lists per role (see `profiles/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Builtin tools use Antigravity SDK auto-schema: function docstrings and type hints generate tool definitions
- `run_command` has a 120-second timeout and requires `policy.confirm_run_command()` approval
- `edit_file` does exact string replacement (first match only)
- `search_files` tries glob matching first, falls back to text content search

### Testing Requirements
- Mock `subprocess.run` for `run_command` tests
- Use `tmp_path` fixture for file operation tests

### Common Patterns
- All builtin tools are registered into `ToolRegistry` via `init_registry()`
- Profile YAML files list tool names as strings, resolved by the registry at agent creation time
