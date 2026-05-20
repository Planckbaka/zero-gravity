# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-20

### Added

**Core Infrastructure**
- `ToolRegistry` — global singleton mapping string tool names to Python callables with `init_registry()` (#1)
- `AgentFactory` — L1 Agent factory that creates Antigravity Agent instances from YAML profiles (#2)
- `ConversationFactory` — L2 Conversation factory for multi-stage skills with model selection support (#3)
- `StateManager` — per-mode file-locked state persistence (`.zg/state/{mode}-state.json`) with 24h expiry (#4)
- `SkillLoader` — dynamic skill discovery with unique module names and trigger keyword matching (#5)
- `JSON Utils` — robust JSON extraction from LLM output (markdown fences, trailing commas, surrounding text) (#6)
- `Error Handling` — `skill_error_handler` decorator that guarantees state cleanup on skill crash (#7)

**Agent Profiles**
- `architect.yaml` — planning and design (read-only tools, no code modification)
- `executor.yaml` — code implementation (write/edit tools, no test execution)
- `tester.yaml` — test writing and verification (run_command, no code fixes)
- `planner.yaml` — task decomposition for team coordination
- `critic.yaml` — critical multi-perspective review of plans and designs

**Skills**
- `autopilot` — L2 Conversation full pipeline: plan → confirm → execute → verify → correct → complete (#8)
- `ralph` — L2 Conversation loop: implement → review → fix until APPROVE (max 10 iterations) (#9)
- `team` — L1 Agent parallel execution with file partition coordination and `asyncio.gather` (#10)

**Hooks**
- `keyword_router` — magic keyword detection with priority conflict resolution (#11)
- `stale_state_cleanup` — SIGINT handler for graceful shutdown, 24h stale state auto-cleanup (#12)

**Tools (14 registered)**
- Workspace: `read_file`, `write_file`, `edit_file`, `run_command`, `search_files`, `list_directory`
- State: `state_read`, `state_write`, `state_clear`, `state_list_active`, `state_get_status`
- Task: `task_create`, `task_update`, `task_list`

**Documentation**
- Hierarchical AGENTS.md across all directories
- PRD.md — product requirements document
- DEVELOPMENT_GUIDE.md — architecture guide and OMC concept mapping

### Inspired By
- [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) — primary blueprint for multi-agent orchestration patterns
- [oh-my-opencode](https://github.com/nicekid1/oh-my-opencode) — agent orchestration for OpenCode
- [claude-hud](https://github.com/nicekid1/claude-hud) — HUD display system
- [Superpowers](https://github.com/Nase0012/super-powers) — enhanced AI agent capabilities
- [everything-claude-code](https://github.com/nicekid1/everything-claude-code) — comprehensive Claude Code configuration
- [Ouroboros](https://github.com/nicekid1/ouroboros) — self-referential loop patterns
