# zero-gravity

> Multi-agent orchestration plugin for the **Google Antigravity SDK**, modeled after [Oh My Claude Code (OMC)](https://omc.vibetip.help/docs).

## What It Does

`zero-gravity` brings structured multi-agent workflows to Antigravity. When a user gives a complex coding task, it automatically coordinates three specialized subagents:

1. **Architect** — analyzes the codebase and drafts an implementation plan
2. **Executor** — implements the approved code changes
3. **Tester** — runs tests, catches failures, and feeds errors back for correction (up to 3 retries)

The whole flow is state-persisted in `.zg/state.json` so it survives interruptions and resumes gracefully.

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set API key
export GEMINI_API_KEY=your_key_here  # https://aistudio.google.com/app/api-keys

# 3. Run the test driver (interactive)
uv run python test_plugin.py

# 4. Run unit tests
PYTHONPATH=src uv run python -m pytest
```

## Install as Antigravity CLI Plugin

```bash
ln -s /path/to/zero-gravity ~/.gemini/config/plugins/zero-gravity
# Restart the Antigravity app — the plugin loads automatically
```

Then in any workspace, run `/zero-gravity:zg-setup` to bootstrap the `.zg/` state directory.

## Project Structure

```
zero-gravity/
├── plugin.json                   # Antigravity plugin manifest
├── installed_version.json        # CLI version lock file
├── pyproject.toml                # Python project config (requires Python >=3.14)
├── main.py                       # Standalone SDK demo
├── test_plugin.py                # Interactive plugin test driver
│
├── skills/                       # Antigravity-native skill definitions
│   └── zg-orchestrator/
│       ├── SKILL.md              # Skill loaded by the CLI (YAML frontmatter + instructions)
│       ├── skill.yaml            # Skill metadata for Python SkillLoader
│       └── handler.py            # Full orchestration state machine
│
├── commands/
│   └── zg-setup.md              # /zero-gravity:zg-setup command definition
│
├── agents/
│   ├── Architect.md             # Architect role system instructions
│   ├── Executor.md              # Executor role system instructions
│   └── Tester.md                # Tester role system instructions
│
├── src/zero_g/
│   ├── core/
│   │   ├── state_manager.py     # .zg/state.json with fcntl file locking
│   │   ├── agent_factory.py     # L1 Agent builder from YAML profiles
│   │   ├── tool_registry.py     # Global str→callable tool registry
│   │   ├── skill_loader.py      # Dynamic importlib skill discovery
│   │   └── json_utils.py        # LLM output JSON extraction + repair
│   ├── agents/
│   │   ├── _builtin_tools.py    # read_file, write_file, run_command, etc.
│   │   └── profiles/
│   │       ├── architect.yaml   # Architect tool allowlist + system prompt
│   │       ├── executor.yaml    # Executor tool allowlist + system prompt
│   │       └── tester.yaml      # Tester tool allowlist + system prompt
│   ├── skills/
│   │   └── base_skill.py        # BaseSkill ABC + SkillConfig dataclass
│   ├── tools/
│   │   ├── state_tools.py       # state_read / state_write / state_clear
│   │   └── task_tools.py        # task_create / task_update / task_list
│   └── commands/
│       └── zg_setup.py          # bootstrap_workspace() implementation
│
└── tests/
    ├── test_state_manager.py
    ├── test_json_utils.py
    ├── test_tool_registry.py
    ├── test_agent_factory.py
    └── test_skill_loader.py
```

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python ≥ 3.14 |
| Package manager | `uv` |
| AI runtime | `google-antigravity ≥ 0.1.0` |
| YAML parsing | `pyyaml` |
| Testing | `pytest` + `pytest-asyncio` |
