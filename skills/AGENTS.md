<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# skills

## Purpose
User-facing skill definitions loaded at runtime by `SkillLoader`. Each skill is a self-contained directory with a `SKILL.md` (or `skill.yaml` + `handler.py`) defining a structured multi-agent workflow.

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `zg-orchestrator/` | Main orchestration skill — teaches the agent the Architect → Executor → Tester flow with gradual confirmation (see `zg-orchestrator/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Skills are discovered by `SkillLoader.discover()` which scans for `skill.yaml` + `handler.py` pairs
- The `SKILL.md` format is for Antigravity-native skill definitions (markdown-based)
- Skills in this directory are user-extensible — new skills can be added without modifying core code
