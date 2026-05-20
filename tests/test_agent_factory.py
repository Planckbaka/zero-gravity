"""Unit tests for load_profile and create_agent factories."""
from __future__ import annotations
import pytest
from google.antigravity import LocalAgentConfig
from zero_g.core.agent_factory import load_profile, create_agent
from zero_g.core.tool_registry import init_registry

def test_load_profile_success():
    profile = load_profile("architect")
    assert "system_instructions" in profile
    assert "tools" in profile
    assert "state_read" in profile["tools"]

def test_load_profile_nonexistent():
    with pytest.raises(ValueError):
        load_profile("nonexistent_profile_xyz")

def test_create_agent_success():
    # Pre-populate registry
    init_registry()
    
    config = create_agent("architect")
    assert isinstance(config, LocalAgentConfig)
    
    # Assert system instructions are injected correctly
    instructions = config.system_instructions
    assert "Architect subagent" in instructions
    
    # Assert custom tools are resolved
    tool_names = [t.__name__ for t in config.tools]
    assert "state_read" in tool_names
