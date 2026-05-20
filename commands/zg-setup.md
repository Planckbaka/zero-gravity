# `/zero-gravity:zg-setup` Command

This command bootstraps the project workspace for the **zero-gravity** multi-agent orchestration workflow.

When the user runs this command, you must execute the following setup sequence:

1. **Create the `.zg/` configuration directory** at the root of the workspace if it doesn't already exist.
2. **Create the state tracker `.zg/state.json`** with the initial state configuration:
   ```json
   {
     "current_stage": "initialized",
     "task_id": null,
     "step_history": []
   }
   ```
3. **Create the task list `.zg/tasks.md`** representing the status tracker for the user. Initialize it with a simple checklist template.
4. **Create the workspace bootstrapper file `ANTIGRAVITY.md`** at the root of the workspace. This file acts as the project instruction template (equivalent to `CLAUDE.md`) containing:
   - Development environment details (Python, `uv`, testing).
   - Detailed instructions on how the agent should read `.zg/state.json` on session start and launch the `zg-orchestrator` skill to coordinate subagents.
   - Code style guidelines (type hints, PEP 8 rules).
   - Test execution commands.

Once these files are created, print a summary report to the user indicating that the workspace is successfully bootstrapped for the **zero-gravity** workflow.
