"""L1 Agent factory module for zero_g."""
from __future__ import annotations
import yaml
from pathlib import Path
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.hooks import policy
from zero_g.core.tool_registry import registry

_PROFILES_DIR = Path(__file__).parent.parent / "agents" / "profiles"


def load_profile(name: str) -> dict:
    """Load agent profile config from YAML file."""
    profile_path = _PROFILES_DIR / f"{name.lower()}.yaml"
    if not profile_path.exists():
        raise ValueError(f"Unknown agent profile: {name}")
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_agent(
    profile: str,
    extra_tools: list | None = None,
) -> Agent:
    """
    Create a standard L1 Agent instance based on a YAML profile configuration.
    """
    config = load_profile(profile)

    # Resolve tool name strings to callables from the registry
    profile_tool_names = config.get("tools", [])
    resolved_tools = registry.resolve(profile_tool_names)
    if extra_tools:
        resolved_tools.extend(extra_tools)

    # Build policy list: default to deny all, allow only registered tools
    policies = [policy.deny("*")]
    for name in profile_tool_names:
        if registry.get(name):
            policies.append(policy.allow(name))
    if extra_tools:
        for tool in extra_tools:
            policies.append(policy.allow(tool.__name__))

    # Restrict file tools to the current workspace directory
    workspace_root = str(Path(".").resolve())
    policies.extend(policy.workspace_only([workspace_root]))

    # Confirm run_command if it is present
    if "run_command" in profile_tool_names:
        policies.extend(policy.confirm_run_command())

    # Capabilities configuration
    capabilities = CapabilitiesConfig()

    agent_config = LocalAgentConfig(
        system_instructions=config["system_instructions"],
        tools=resolved_tools,
        capabilities=capabilities,
        policies=policies,
    )

    return Agent(agent_config)

