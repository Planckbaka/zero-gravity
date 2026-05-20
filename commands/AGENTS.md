<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# commands

## Purpose
CLI command definitions for the Antigravity plugin. Each markdown file defines a `/zero-gravity:<name>` command that users invoke from the Antigravity terminal.

## Key Files
| File | Description |
|------|-------------|
| `zg-setup.md` | `/zero-gravity:zg-setup` — bootstraps the workspace: creates `.zg/` state directory, `ANTIGRAVITY.md` instructions, and initializes state/task files |

## For AI Agents

### Working In This Directory
- Command files are markdown instructions that the main agent reads and executes
- Each command must produce a summary report to the user upon completion
