"""Unit tests for ToolRegistry mapping tool name strings to callable objects."""
from __future__ import annotations
from zero_g.core.tool_registry import ToolRegistry, registry, init_registry

def test_registry_register_and_get():
    reg = ToolRegistry()
    def dummy_tool(x: int) -> int:
        return x + 1
        
    reg.register("dummy_tool", dummy_tool)
    assert reg.get("dummy_tool") == dummy_tool
    assert reg.get("nonexistent") is None

def test_registry_resolve():
    reg = ToolRegistry()
    def tool_a(): pass
    def tool_b(): pass
    
    reg.register("tool_a", tool_a)
    reg.register("tool_b", tool_b)
    
    resolved = reg.resolve(["tool_a", "nonexistent", "tool_b"])
    assert resolved == [tool_a, tool_b]

def test_registry_available_names():
    reg = ToolRegistry()
    reg.register("tool_a", lambda: None)
    reg.register("tool_b", lambda: None)
    
    names = reg.available_names()
    assert "tool_a" in names
    assert "tool_b" in names
    assert len(names) == 2

def test_global_init_registry():
    # Calling global bootstrapper should populate the registry
    init_registry()
    
    # Assert some builtins are registered
    assert registry.get("read_file") is not None
    assert registry.get("run_command") is not None
    assert registry.get("state_write") is not None
    assert registry.get("task_create") is not None
