"""ZgOrchestratorSkill handler implementing the Oh My Claude Code multi-agent workflow."""
from __future__ import annotations
import os
import re
from pathlib import Path
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.state_manager import StateManager
from zero_g.core.agent_factory import create_agent
from zero_g.tools.task_tools import task_create, task_update, task_list
from zero_g.tools.state_tools import state_read, state_write, state_clear

class ZgOrchestratorSkill(BaseSkill):
    async def execute(self, task: str, context: dict) -> str:
        manager = StateManager()
        state = manager.read()

        # Read state
        stage = state.get("current_stage", "initialized")
        task_id = state.get("task_id")
        step_history = state.get("step_history", [])
        correction_attempts = state.get("correction_attempts", 0)

        # Brain artifacts directory path
        artifacts_dir = context.get("artifacts_dir") or "/Users/akiwayne/.gemini/antigravity/brain/a08b299e-412c-43c8-b387-06bdb109b518"

        if stage == "initialized" or not task_id:
            # Starting fresh
            task_id = "task_" + Path(".").resolve().name
            state = {
                "current_stage": "planning",
                "task_id": task_id,
                "step_history": ["Session started"],
                "correction_attempts": 0,
                "original_task": task,
            }
            manager.write(state)
            
            # Setup initial tasks
            task_clear_fn = lambda: Path(".zg/tasks.md").unlink(missing_ok=True)
            try:
                task_clear_fn()
            except Exception:
                pass
                
            task_create("Read state and task status", "Read existing task state or initialize.")
            task_create("Architect drafts implementation plan", "Architect subagent designs modifications.")
            task_create("Await user confirmation of plan", "User reviews and confirms the drafted plan.")
            task_create("Executor implements code changes", "Executor writes code changes to workspace.")
            task_create("Tester validates and compiles walkthrough", "Tester validates with tests and outputs report.")
            
            task_update("Read state and task status", "completed")
            task_update("Architect drafts implementation plan", "in_progress")
            
            stage = "planning"

        if stage == "planning":
            # Planning Stage
            print("[zero-gravity] Spawning Architect subagent...")
            architect_prompt = (
                f"You are the Architect. Analyze the codebase and design a comprehensive implementation plan for the following task:\n\n"
                f"Task Description: {task}\n\n"
                f"Write a highly-detailed implementation plan with clear goals, proposed file changes, self-assessment, and a verification plan."
            )
            
            async with create_agent("architect") as architect:
                response = await architect.chat(architect_prompt)
                architect_reply = await response.text()

            # Save the plan to implementation_plan.md in the workspace root and the brain artifacts directory
            workspace_plan_path = Path("implementation_plan.md")
            workspace_plan_path.write_text(architect_reply, encoding="utf-8")
            
            # Also save to brain artifacts dir
            if artifacts_dir:
                artifacts_plan_path = Path(artifacts_dir) / "implementation_plan.md"
                try:
                    artifacts_plan_path.parent.mkdir(parents=True, exist_ok=True)
                    artifacts_plan_path.write_text(architect_reply, encoding="utf-8")
                except Exception as e:
                    print(f"Failed to write implementation plan to artifacts directory: {e}")

            # Transition to awaiting_confirmation
            state = manager.read()
            state["current_stage"] = "awaiting_confirmation"
            state["step_history"].append("Architect drafted implementation plan")
            manager.write(state)
            
            task_update("Architect drafts implementation plan", "completed")
            task_update("Await user confirmation of plan", "in_progress")
            
            return (
                "### 📋 Architectural Implementation Plan Drafted\n\n"
                "I have successfully spawned the **Architect** subagent. "
                "The designed implementation plan has been written to the workspace root as [implementation_plan.md](file:///Users/akiwayne/Documents/Project2026/python-tutorial/zero-gravity/implementation_plan.md).\n\n"
                "Please review the plan carefully. If you approve, **reply with 'approve'** or 'continue' to start the implementation."
            )

        if stage == "awaiting_confirmation":
            # Awaiting user confirmation
            # Check if user input indicates approval
            user_input = task.lower().strip()
            if "approve" in user_input or "continue" in user_input or user_input == "yes" or user_input == "y":
                state = manager.read()
                state["current_stage"] = "execution"
                state["step_history"].append("User approved implementation plan")
                manager.write(state)
                
                task_update("Await user confirmation of plan", "completed")
                task_update("Executor implements code changes", "in_progress")
                stage = "execution"
            else:
                return (
                    "### ⚠️ Waiting for Plan Approval\n\n"
                    "The plan in `implementation_plan.md` is currently awaiting your approval. "
                    "To proceed, please reply with **'approve'**."
                )

        if stage == "execution" or stage == "correction":
            # Execution Stage
            print("[zero-gravity] Spawning Executor subagent...")
            
            # Read implementation plan
            workspace_plan_path = Path("implementation_plan.md")
            if not workspace_plan_path.exists():
                return "Error: implementation_plan.md not found in workspace."
            plan_content = workspace_plan_path.read_text(encoding="utf-8")
            
            original_task = state.get("original_task", task)
            
            executor_prompt = (
                f"You are the Executor. You must read the approved implementation plan below and make all the code modifications/creations described in it.\n\n"
                f"--- APPROVED PLAN ---\n"
                f"{plan_content}\n\n"
                f"--- ORIGINAL TASK ---\n"
                f"{original_task}\n\n"
                f"Please implement the files and write high-quality, production-ready code. Remember to preserve existing comments/docstrings."
            )
            
            if stage == "correction":
                # Add previous test failure information to prompt
                last_error = state.get("last_error", "No detailed error captured.")
                executor_prompt += (
                    f"\n\n⚠️ ATTENTION: The previous verification failed with the following errors. "
                    f"Please correct the implementation to fix these issues:\n\n"
                    f"--- VERIFICATION ERRORS ---\n"
                    f"{last_error}"
                )

            async with create_agent("executor") as executor:
                response = await executor.chat(executor_prompt)
                executor_reply = await response.text()

            # Transition to verification
            state = manager.read()
            state["current_stage"] = "verification"
            state["step_history"].append(f"Executor completed code implementation (Correction attempt {correction_attempts})")
            manager.write(state)
            
            task_update("Executor implements code changes", "completed")
            task_update("Tester validates and compiles walkthrough", "in_progress")
            stage = "verification"

        if stage == "verification":
            # Verification Stage
            print("[zero-gravity] Spawning Tester subagent...")
            
            original_task = state.get("original_task", task)
            
            tester_prompt = (
                f"You are the Tester. Analyze the modifications made in the codebase, write unit/integration tests as specified in the plan, and run tests (e.g. using `run_command` with `pytest`).\n\n"
                f"If there are any failing tests or linters, extract the traceback/error and report it clearly. "
                f"If everything passes, compile a robust walkthrough.md containing details of what was tested, code changes, and test results.\n\n"
                f"Task context:\n{original_task}"
            )
            
            async with create_agent("tester") as tester:
                response = await tester.chat(tester_prompt)
                tester_reply = await response.text()

            # Analyze the tester reply to see if there are failures
            has_failures = False
            # Check for standard test failure patterns
            failure_keywords = ["failed", "error", "exception", "traceback", "assertionerror", "failing"]
            lower_reply = tester_reply.lower()
            
            # Simple heuristic or check if the tester explicitly reported a failure
            if any(kw in lower_reply for kw in failure_keywords) and ("failing" in lower_reply or "traceback" in lower_reply or "failed" in lower_reply):
                has_failures = True

            if has_failures:
                # Test failure: increment correction attempts
                state = manager.read()
                attempts = state.get("correction_attempts", 0) + 1
                state["correction_attempts"] = attempts
                state["last_error"] = tester_reply
                
                if attempts >= 3:
                    state["current_stage"] = "failed"
                    manager.write(state)
                    task_update("Tester validates and compiles walkthrough", "pending")
                    return (
                        f"### ❌ Orchestration Failed\n\n"
                        f"The Tester subagent reported test failures after {attempts} attempts. "
                        f"Please review the logs and resolve the issues manually.\n\n"
                        f"--- TESTER REPORT ---\n\n{tester_reply}"
                    )
                else:
                    state["current_stage"] = "correction"
                    manager.write(state)
                    task_update("Executor implements code changes", "in_progress")
                    task_update("Tester validates and compiles walkthrough", "pending")
                    print(f"[zero-gravity] Verification failed. Attempt {attempts} of 3. Retrying execution correction...")
                    # We can recursively execute to start correction immediately
                    return await self.execute(task, context)
            else:
                # Verification Succeeded!
                # Save walkthrough.md to workspace root and brain artifacts dir
                workspace_walkthrough_path = Path("walkthrough.md")
                workspace_walkthrough_path.write_text(tester_reply, encoding="utf-8")
                
                if artifacts_dir:
                    artifacts_walkthrough_path = Path(artifacts_dir) / "walkthrough.md"
                    try:
                        artifacts_walkthrough_path.parent.mkdir(parents=True, exist_ok=True)
                        artifacts_walkthrough_path.write_text(tester_reply, encoding="utf-8")
                    except Exception as e:
                        print(f"Failed to write walkthrough to artifacts directory: {e}")

                state = manager.read()
                state["current_stage"] = "completed"
                state["step_history"].append("Tester validated implementation successfully")
                manager.write(state)
                
                task_update("Tester validates and compiles walkthrough", "completed")
                
                return (
                    f"### 🎉 Orchestration Successfully Completed!\n\n"
                    f"All subagents have completed their tasks. The implementation has been verified and fully validated.\n\n"
                    f"Please review [walkthrough.md](file:///Users/akiwayne/Documents/Project2026/python-tutorial/zero-gravity/walkthrough.md) for the completion report."
                )

        return f"Unknown orchestrator stage: {stage}"
