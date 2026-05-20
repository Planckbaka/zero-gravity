"""L1 Agent factory module for zero_g.

Uses SDK AgentConfig with:
- CapabilitiesConfig(enabled_tools=...) for SDK builtin tools
- tools=[...] for ZG-specific custom Python tools
- model_router for per-role Gemini model selection

Profile YAML schema:
  builtin_tools: [VIEW_FILE, LIST_DIR, ...]   # SDK BuiltinTools enum names
  tools: [edit_file, state_read, ...]          # ZG custom tool names from ToolRegistry
  model_tier: high | medium | low              # Model routing tier
"""
from __future__ import annotations
import yaml
from pathlib import Path
from google.antigravity import LocalAgentConfig
from google.antigravity.types import BuiltinTools, CapabilitiesConfig
from google.antigravity.hooks import policy
from zero_g.core.tool_registry import registry
from zero_g.core.model_router import get_gemini_config

_PROFILES_DIR = Path(__file__).parent.parent / "agents" / "profiles"


def load_profile(name: str) -> dict:
    """Load agent profile config from YAML file."""
    profile_path = _PROFILES_DIR / f"{name.lower()}.yaml"
    if not profile_path.exists():
        raise ValueError(f"Unknown agent profile: {name}")
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_builtin_tools(names: list[str]) -> list[BuiltinTools]:
    """Resolve string names to BuiltinTools enum values."""
    resolved = []
    for name in names:
        try:
            resolved.append(BuiltinTools(name))
        except ValueError:
            pass  # Skip unknown builtin tool names
    return resolved


def create_agent(
    profile: str,
    extra_tools: list | None = None,
) -> LocalAgentConfig:
    """Create an SDK AgentConfig from a YAML profile.

    Returns an AgentConfig (not an Agent instance) so the caller can
    further customize hooks, triggers, or MCP servers before creating
    the actual Agent.

    Args:
        profile: Agent profile name (maps to profiles/{name}.yaml).
        extra_tools: Additional callable tools beyond profile defaults.

    Returns:
        An AgentConfig ready to pass to Agent(config).
    """
    config = load_profile(profile)

    # 1. Resolve SDK builtin tools → CapabilitiesConfig
    builtin_names = config.get("builtin_tools", [])
    enabled_builtins = _resolve_builtin_tools(builtin_names)
    capabilities = CapabilitiesConfig(
        enable_subagents=True,
        enabled_tools=enabled_builtins if enabled_builtins else None,
    )

    # 2. Resolve ZG custom tools → callable list
    custom_tool_names = config.get("tools", [])
    resolved_custom = registry.resolve(custom_tool_names)
    if extra_tools:
        resolved_custom.extend(extra_tools)

    # 3. Build policies: deny all, then allow specific tools
    policies = [policy.deny("*")]
    for name in builtin_names:
        policies.append(policy.allow(name))
    for name in custom_tool_names:
        if registry.get(name):
            policies.append(policy.allow(name))
    if extra_tools:
        for tool in extra_tools:
            policies.append(policy.allow(tool.__name__))

    # Restrict file tools to workspace
    workspace_root = str(Path(".").resolve())
    policies.extend(policy.workspace_only([workspace_root]))

    if "run_command" in builtin_names:
        policies.extend(policy.confirm_run_command())

    # 4. Model routing via profile tier
    gemini_config = get_gemini_config(agent_role=profile)

    return LocalAgentConfig(
        system_instructions=config.get("system_instructions", ""),
        capabilities=capabilities,
        tools=resolved_custom,
        policies=policies,
        gemini_config=gemini_config,
    )
