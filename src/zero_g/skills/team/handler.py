"""Team skill: parallel L1 Agent execution with file partition coordination.

Uses asyncio.gather to run multiple independent workers concurrently.
Each worker is an L1 Agent with exclusive file access enforced by
the TeamCoordinator.
"""
from __future__ import annotations
import asyncio
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.agent_factory import create_agent
from zero_g.core.json_utils import extract_json
from zero_g.core.state_manager import StateManager
from zero_g.core.error_handling import skill_error_handler
from zero_g.skills.team.coordinator import TeamCoordinator
from zero_g.tools import task_tools
from google.antigravity import Agent


class TeamSkill(BaseSkill):
    @skill_error_handler("team")
    async def execute(self, task: str, context: dict) -> str:
        sm = StateManager()
        team_name = context.get("team_name", "default-team")
        worker_count = min(context.get("workers", 3), 10)

        sm.write("team", {
            "active": True,
            "task": task,
            "team_name": team_name,
            "worker_count": worker_count,
            "current_stage": "decomposition",
        })

        # Phase 1: Decompose task using Planner
        planner_config = create_agent("planner")
        async with Agent(planner_config) as planner:
            decompose_response = await planner.chat(
                f"Decompose this task into {worker_count} independent subtasks "
                f"with NON-OVERLAPPING file scopes:\n{task}\n\n"
                f"Output ONLY a JSON array, no other text:\n"
                f'[{{"subject": "...", "description": "...", "files": ["path1.py"]}}]'
            )
            raw_text = await decompose_response.text()

        subtasks = extract_json(raw_text)
        if not isinstance(subtasks, list):
            sm.write("team", {"active": False, "current_stage": "failed"})
            return "Failed to decompose task: planner did not return a list."

        # Phase 2: Assign partitions and create tasks
        coord = TeamCoordinator(team_name)
        work_items = []
        for i, sub in enumerate(subtasks[:worker_count]):
            worker_id = f"worker-{i + 1}"
            assigned_files = sub.get("files", [])
            claimed = coord.claim_partition(worker_id, assigned_files)
            if not claimed:
                sm.write("team", {"active": False, "current_stage": "failed"})
                return f"File partition conflict for worker-{i + 1}. Some files are already claimed."

            task_tools.task_create(
                sub.get("subject", f"Subtask {i + 1}"),
                sub.get("description", ""),
            )
            work_items.append({
                "worker_id": i + 1,
                "subtask": sub,
            })

        sm.write("team", {
            "active": True,
            "current_stage": "execution",
            "worker_count": len(work_items),
        })

        # Phase 3: Parallel execution with L1 Agents
        async def run_worker(worker_id: int, subtask: dict) -> str:
            executor_config = create_agent("executor")
            try:
                async with Agent(executor_config) as executor:
                    response = await executor.chat(
                        f"You are worker-{worker_id} in team '{team_name}'.\n"
                        f"Subtask: {subtask['subject']}\n{subtask.get('description', '')}\n"
                        f"Only modify these files: {subtask.get('files', [])}\n"
                        f"Implement this independently."
                    )
                    result = await response.text()
                task_tools.task_update(subtask["subject"], "completed")
                return result
            except Exception as e:
                task_tools.task_update(subtask["subject"], "failed")
                return f"FAILED: {e}"
            finally:
                coord.release_partition(f"worker-{worker_id}")

        results = await asyncio.gather(*[
            run_worker(w["worker_id"], w["subtask"])
            for w in work_items
        ], return_exceptions=True)

        # Phase 4: Aggregate results
        output_parts = []
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output_parts.append(f"Worker {i + 1} FAILED: {result}")
            else:
                success_count += 1
                output_parts.append(f"Worker {i + 1} completed:\n{result}")

        sm.write("team", {
            "active": False,
            "current_stage": "completed",
            "success_count": success_count,
            "total_workers": len(work_items),
        })
        coord.clear()

        return (
            f"Team '{team_name}' finished {success_count}/{len(work_items)} tasks:\n"
            + "\n---\n".join(output_parts)
        )
