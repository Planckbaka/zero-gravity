<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# zg-orchestrator

## Purpose
Main orchestration skill that teaches the agent how to coordinate the Architect, Executor, and Tester subagents following the OMC blueprint. Implements the gradual confirmation flow with state machine transitions.

## Key Files
| File | Description |
|------|-------------|
| `SKILL.md` | Skill definition — 5-step orchestration workflow: read state → plan (Architect) → execute (Executor) → verify (Tester) → wrap-up |

## For AI Agents

### Working In This Directory
- This is the primary skill invoked for complex tasks
- The flow enforces user approval at the planning stage before execution begins
- State transitions: `initialized` → `planning` → `execution` → `verification` → `completed` (or `correction` → `execution` loop, max 3 attempts)
- On verification failure, the Tester reports errors back to the orchestrator which routes to the Executor for correction

### Common Patterns
- State is tracked in `.zg/state.json` via `state_tools`
- Task progress is visible in `.zg/tasks.md` via `task_tools`
- The correction loop has a hard limit of 3 iterations before escalating to the user
