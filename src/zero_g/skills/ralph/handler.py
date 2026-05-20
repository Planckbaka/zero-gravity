"""Ralph skill: self-referential loop until verification is complete.

The signature OMC pattern. Uses L2 Conversation to maintain full context
across executor-architect review cycles, so each iteration sees the complete
reasoning chain including prior feedback.
"""
from __future__ import annotations
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.conversation_factory import create_conversation
from zero_g.core.state_manager import StateManager
from zero_g.core.error_handling import skill_error_handler
from zero_g.tools import task_tools


class RalphSkill(BaseSkill):
    @skill_error_handler("ralph")
    async def execute(self, task: str, context: dict) -> str:
        sm = StateManager()
        max_iterations = self.config.max_iterations

        sm.write("ralph", {
            "active": True,
            "task": task,
            "iteration": 0,
            "max_iterations": max_iterations,
        })
        task_tools.task_create("Ralph", task)

        # Single L2 Conversation for the entire loop — context carries across iterations
        async with create_conversation("executor") as conv:
            # Initial implementation request
            await conv.send(
                f"Task: {task}\n\n"
                f"Implement this task. Write all necessary code.\n"
                f"After implementation, describe what you did and verify it works."
            )

            impl_result = ""
            async for step in conv.receive_steps():
                if step.is_complete_response:
                    impl_result = step.content

            for iteration in range(1, max_iterations + 1):
                sm.write("ralph", {
                    "active": True,
                    "task": task,
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                })

                # Role switch: Architect review within the same conversation
                await conv.send(
                    f"--- ARCHITECT REVIEW ---\n"
                    f"Review the above implementation for: {task}\n"
                    f"Check for correctness, edge cases, and code quality.\n"
                    f"Verdict: APPROVE or REVISE with specific feedback."
                )

                review_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        review_result = step.content

                if "APPROVE" in review_result.upper():
                    sm.write("ralph", {
                        "active": False,
                        "status": "completed",
                        "iteration": iteration,
                    })
                    task_tools.task_update("Ralph", "completed")
                    return (
                        f"Ralph completed after {iteration} iteration(s).\n\n"
                        f"Implementation:\n{impl_result}\n\n"
                        f"Review:\n{review_result}"
                    )

                # REVISE — feedback is already in conversation history
                await conv.send(
                    f"--- FIX BASED ON REVIEW ---\n"
                    f"Address the review feedback above. Fix the issues and re-verify."
                )

                impl_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        impl_result = step.content

            # Max iterations reached
            sm.write("ralph", {
                "active": False,
                "status": "max_iterations_reached",
                "iteration": max_iterations,
            })
            return f"Ralph reached max iterations ({max_iterations}) without approval.\n\nLast implementation:\n{impl_result}"
