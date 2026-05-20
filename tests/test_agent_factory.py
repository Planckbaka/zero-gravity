"""Unit tests for load_profile and create_agent factories."""
from __future__ import annotations
import pytest
from google.antigravity import Agent
from zero_g.core.agent_factory import load_profile, create_agent
from zero_g.core.tool_registry import init_registry

def test_load_profile_success():
    profile = load_profile("architect")
    assert "system_instructions" in profile
    assert "tools" in profile
    assert "read_file" in profile["tools"]

def test_load_profile_nonexistent():
    with pytest.raises(ValueError):
        load_profile("nonexistent_profile_xyz")

def test_create_agent_success():
    # Pre-populate registry
    init_registry()
    
    agent = create_agent("architect")
    assert isinstance(agent, Agent)
    
    # Assert system instructions are injected correctly
    instructions = agent._config.system_instructions
    assert "Architect subagent" in instructions
    
    # Assert tools are resolved
    tool_names = [t.__name__ for t in agent._config.tools]
    assert "read_file" in tool_names
    assert "state_read" in tool_names
