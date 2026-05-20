import asyncio
from google.antigravity import Agent
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy

# 1. Define a custom tool for the plugin/skill.
# The SDK automatically uses the function docstring and type hints to generate tool schemas.
def greeting_tool(name: str) -> str:
    """Say hello to a user.

    Args:
        name: The name of the user.
    """
    return f"Hello, {name}! Welcome to the Antigravity plugin ecosystem."

async def main():
    print("Initializing Antigravity Agent Config...")
    
    # 2. Configure the local agent.
    # We pass policies=[policy.allow_all()] to approve our custom tool execution.
    config = LocalAgentConfig(
        system_instructions="You are a helpful assistant. Use the greeting_tool when asked to welcome someone.",
        tools=[greeting_tool],
        policies=[policy.allow_all()]
    )
    
    print("Starting agent session...")
    try:
        async with Agent(config) as agent:
            print("Agent started successfully!")
            
            # 3. Test a chat request to verify the custom tool is active and callable.
            print("Sending message: 'Greet akiwayne'")
            response = await agent.chat("Greet akiwayne")
            text = await response.text()
            print(f"\nAgent response:\n{text}")
    except Exception as e:
        print(f"Error during agent session: {e}")
        print("\nNote: Developing plugins locally may require a running Antigravity harness/IDE or active API configuration.")

if __name__ == "__main__":
    asyncio.run(main())
