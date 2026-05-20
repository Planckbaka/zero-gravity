<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# agents

## Purpose
Antigravity agent system-instruction markdown files. These define the behavioral profiles and communication styles for each subagent role. Used as reference alongside the YAML profiles in `src/zero_g/agents/profiles/`.

## Key Files
| File | Description |
|------|-------------|
| `Architect.md` | Architect subagent — planning, design, requirements specification. No code modification allowed |
| `Executor.md` | Executor subagent — code implementation and modification. Reads plans, writes production code |
| `Tester.md` | Tester subagent — test writing, verification, and walkthrough report generation. No direct code fixes |

## For AI Agents

### Working In This Directory
- Each file defines a single subagent role with strict separation of concerns
- Architect never modifies code; Executor never runs tests; Tester never fixes code
- These markdown files complement the YAML profiles in `src/zero_g/agents/profiles/`

### Common Patterns
- All subagents follow the OMC blueprint: plan → execute → verify → correct loop
- Correction loop is limited to 3 attempts before escalating to the user
