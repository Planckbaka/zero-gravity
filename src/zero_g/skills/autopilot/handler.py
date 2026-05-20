"""Autopilot skill: autonomous full pipeline from idea to working code.

Uses L2 Conversation to maintain context across planning, execution,
verification, and correction stages.
"""
from __future__ import annotations
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.conversation_factory import create_conversation
from zero_g.core.state_manager import StateManager
from zero_g.core.error_handling import skill_error_handler
from zero_g.tools import task_tools


class AutopilotSkill(BaseSkill):
    @skill_error_handler("autopilot")
    async def execute(self, task: str, context: dict) -> str:
        sm = StateManager()
        max_correction = self.config.max_iterations

        # Initialize state
        sm.write("autopilot", {
            "active": True,
            "current_stage": "planning",
            "task": task,
            "iteration": 0,
        })
        task_tools.task_create("Autopilot", task)

        # Stage 1: Planning — use Architect profile via L2 Conversation
        async with create_conversation("architect") as conv:
            await conv.send(
                f"Analyze the following task and create an implementation plan.\n\n"
                f"Task: {task}\n\n"
                f"Create a file called implementation_plan.md with:\n"
                f"1. Goal Description\n"
                f"2. Proposed changes grouped by file\n"
                f"3. Step-by-step verification plan\n"
                f"4. Any open questions"
            )
            plan_result = ""
            async for step in conv.receive_steps():
                if step.is_complete_response:
                    plan_result = step.content

        sm.write("autopilot", {"active": True, "current_stage": "awaiting_approval", "iteration": 0})

        # Gradual confirmation: return plan to user for approval
        # In a real runtime, the orchestrator pauses here and waits for user input.
        # For now, we proceed and let the orchestrator handle the pause.
        context["plan"] = plan_result
        context["stage"] = "awaiting_approval"
        return plan_result

    async def execute_stage(self, stage: str, task: str, context: dict) -> str:
        """Execute a specific stage after user approval.

        Called by the orchestrator after gradual confirmation.
        """
        sm = StateManager()
        max_correction = self.config.max_iterations

        if stage == "execution":
            sm.write("autopilot", {"active": True, "current_stage": "execution", "iteration": 0})

            # Stage 2: Execution — use Executor profile
            async with create_conversation("executor") as conv:
                await conv.send(
                    f"Implement the following plan.\n\n"
                    f"Plan: {context.get('plan', '')}\n\n"
                    f"Write clean, production-ready code. Use write_file and edit_file tools."
                )
                exec_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        exec_result = step.content

            task_tools.task_update("Autopilot", "completed")
            sm.write("autopilot", {"active": True, "current_stage": "verification", "iteration": 0})
            return exec_result

        elif stage == "verification":
            # Stage 3: Verification — use Tester profile
            sm.write("autopilot", {"active": True, "current_stage": "verification", "iteration": 0})

            async with create_conversation("tester") as conv:
                await conv.send(
                    f"Write tests and run verification for the following task.\n\n"
                    f"Task: {task}\n\n"
                    f"Run pytest and report results. If tests fail, report exact errors and tracebacks."
                )
                test_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        test_result = step.content

            # Check if tests passed
            if "passed" in test_result.lower() or "ok" in test_result.lower():
                sm.write("autopilot", {"active": False, "current_stage": "completed", "iteration": 0})
                return f"Autopilot completed successfully.\n\n{test_result}"

            # Tests failed — enter correction loop
            return await self._correction_loop(task, context, test_result, max_correction)

        return "Unknown stage"

    async def _correction_loop(self, task: str, context: dict, error_report: str, max_attempts: int) -> str:
        sm = StateManager()

        for attempt in range(1, max_attempts + 1):
            sm.write("autopilot", {"active": True, "current_stage": "correction", "iteration": attempt})

            # Executor fixes based on error report
            async with create_conversation("executor") as conv:
                await conv.send(
                    f"Fix the following errors found during testing.\n\n"
                    f"Task: {task}\n\n"
                    f"Error report:\n{error_report}\n\n"
                    f"Fix the issues and ensure tests pass."
                )
                fix_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        fix_result = step.content

            # Re-verify
            async with create_conversation("tester") as conv:
                await conv.send(
                    f"Re-run tests after corrections for: {task}\n\n"
                    f"Run pytest and report results."
                )
                test_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        test_result = step.content

            if "passed" in test_result.lower() or "ok" in test_result.lower():
                sm.write("autopilot", {"active": False, "current_stage": "completed", "iteration": attempt})
                return f"Autopilot completed after {attempt} correction(s).\n\n{test_result}"

            error_report = test_result

        sm.write("autopilot", {"active": False, "current_stage": "failed", "iteration": max_attempts})
        return f"Autopilot failed after {max_attempts} correction attempts.\n\nLast errors:\n{error_report}"
