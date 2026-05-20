"""
Test driver for the zero-gravity plugin.

Loads skills from the local 'skills/' directory and runs an interactive loop.

Usage:
    export GEMINI_API_KEY=your_key_here
    uv run python test_plugin.py
"""
import asyncio
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from pathlib import Path

# Path to the skills directory (contains zg-orchestrator/SKILL.md)
SKILLS_DIR = Path(__file__).parent / "skills"

async def main():
    print("🚀 Starting zero-gravity plugin test harness...")
    print(f"   Loading skills from: {SKILLS_DIR}")
    print()

    config = LocalAgentConfig(
        system_instructions=(
            "You are the zero-gravity orchestrator agent. "
            "You have specialized skills loaded that teach you how to coordinate "
            "multi-agent workflows. When the user asks you to orchestrate a task, "
            "follow the zg-orchestrator skill instructions precisely."
        ),
        skills_paths=[str(SKILLS_DIR)],
        policies=[policy.allow_all()],
    )

    async with Agent(config) as agent:
        print("✅ Agent started successfully. Skills loaded.")
        print("   Try: 'What skills do you have?'")
        print("   Try: 'Orchestrate: add a hello_world function to main.py'")
        print()

        # Run a quick smoke test first
        smoke = await agent.chat("List your available skills and what they do.")
        print("--- Skill Discovery Smoke Test ---")
        print(await smoke.text())
        print()

        # Start the interactive loop for manual testing
        await agent.run_interactive_loop()


if __name__ == "__main__":
    asyncio.run(main())
