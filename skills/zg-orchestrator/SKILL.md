---
name: zg-orchestrator
description: Teaches the main agent how to orchestrate the Architect, Executor, and Tester subagents to complete complex tasks following the Oh My Claude Code (OMC) blueprint.
---

## Multi-Agent Orchestration Flow (Oh My Claude Code Blueprint)

When a complex task is requested, follow this workflow exactly:

### Step 1: Read State and Task
1. Look for the `.zg/state.json` file and read the current task status.
2. If there is an active task in progress, check if you should resume it or start a new one.

### Step 2: Planning Stage
1. Transition state to `PLANNING`. Write `current_stage: "planning"` to `.zg/state.json`.
2. Spawn the `Architect` subagent using the `invoke_subagent` tool:
   - Provide the task description and instructions to analyze the codebase and design an implementation plan.
3. Wait for the `Architect`'s response.
4. Output the resulting plan to `implementation_plan.md` in the brain artifacts directory.
5. **CRITICAL (Gradual Confirmation)**: Present the plan to the user and wait for their explicit approval before proceeding.

### Step 3: Execution Stage
1. After the user approves, transition state to `EXECUTION`. Write `current_stage: "execution"` to `.zg/state.json`.
2. Spawn the `Executor` subagent using the `invoke_subagent` tool:
   - Provide the approved `implementation_plan.md` and instruct them to write clean, complete code modifications.
3. Wait for the `Executor` to complete the changes.
4. Update `.zg/tasks.md` with progress checkboxes.

### Step 4: Verification Stage
1. Transition state to `VERIFICATION`. Write `current_stage: "verification"` to `.zg/state.json`.
2. Spawn the `Tester` subagent using the `invoke_subagent` tool:
   - Instruct them to write tests and execute validation commands (e.g. `pytest`).
3. Wait for the `Tester`'s report.
4. If validation fails:
   - Transition state to `CORRECTION` and loop back to the `Executor` subagent with the exact errors and stack trace.
   - Limit the correction loop to a maximum of 3 attempts before asking the user for help.

### Step 5: Wrap-up & Completion
1. If validation succeeds, transition state to `COMPLETED`. Write `current_stage: "completed"` to `.zg/state.json`.
2. Let the `Tester` compile the `walkthrough.md` report.
3. Clean up any temporary files.
4. Mark all tasks as completed in `.zg/tasks.md`.
