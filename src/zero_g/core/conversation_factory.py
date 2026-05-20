"""L2 Conversation factory for multi-stage skills.

Creates Conversation instances that maintain dialogue history across
multiple stages (Ralph, Autopilot, Plan, Deep-Interview).

System instructions and model selection are configured at the
LocalConnectionStrategy level, not on Conversation itself.
"""
from __future__ import annotations
import contextlib
from google.antigravity.connections.local import LocalConnectionStrategy
from google.antigravity.conversation.conversation import Conversation
from google.antigravity.tools.tool_runner import ToolRunner
from google.antigravity.types import GeminiConfig
from zero_g.core.tool_registry import registry
from zero_g.core.agent_factory import load_profile
from zero_g.core.model_router import get_gemini_config


def create_conversation(
    profile: str,
    extra_tools: list | None = None,
    model_name: str | None = None,
    tier: str | None = None,
) -> contextlib.AbstractAsyncContextManager[Conversation]:
    """Create an L2 Conversation instance for multi-stage skills.

    Args:
        profile: Agent profile name (maps to profiles/{name}.yaml).
        extra_tools: Additional callable tools beyond profile defaults.
        model_name: Optional explicit Gemini model name (overrides profile tier).
        tier: Optional model tier ("high", "medium", "low").

    Returns:
        An async context manager yielding a Conversation instance.
    """
    config = load_profile(profile)
    profile_tier = config.get("model_tier")

    # Resolve tool names to callables
    profile_tool_names = config.get("tools", [])
    resolved_tools = registry.resolve(profile_tool_names)
    if extra_tools:
        resolved_tools.extend(extra_tools)

    # Register tools with ToolRunner
    tool_runner = ToolRunner()
    for tool in resolved_tools:
        tool_runner.register(tool)

    # Configure Gemini model selection via model_router
    gemini_config = get_gemini_config(
        agent_role=profile if not model_name and not tier else None,
        tier=tier or profile_tier,
        model_name=model_name,
    )

    # Build connection strategy with system instructions and tools
    strategy = LocalConnectionStrategy(
        tool_runner=tool_runner,
        gemini_config=gemini_config,
        system_instructions=config.get("system_instructions", ""),
    )

    return Conversation.create(strategy)
