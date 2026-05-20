<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# profiles

## Purpose
YAML configuration files that define agent behavioral profiles for the Antigravity L1 Agent factory. Each profile specifies system instructions and the list of tools the agent is allowed to use.

## Key Files
| File | Description |
|------|-------------|
| `architect.yaml` | Architect profile — planning and design only; tools: read, search, list, state, task (no write/edit/run) |
| `executor.yaml` | Executor profile — code implementation; tools: read, write, edit, search, list, state, task (no run_command) |
| `tester.yaml` | Tester profile — verification and test execution; tools: read, write, search, list, run_command, state, task |

## For AI Agents

### Working In This Directory
- Profile names are loaded by `agent_factory.load_profile(name)` — the name argument is lowercased and matched to `{name}.yaml`
- Each profile has `system_instructions` (multiline YAML block scalar) and `tools` (list of tool name strings)
- Tool name strings must match names registered in `ToolRegistry` via `init_registry()`
- To add a new agent role: create a new YAML file with `system_instructions` and `tools` keys

### Common Patterns
- Tool access is strictly role-based: Architect cannot modify code, Executor cannot run tests, Tester cannot fix code
- Policies are auto-generated from the tool list in `agent_factory.create_agent()`: deny all, then allow listed tools
