"""Tool registry module mapping string tool names to Python callables."""
from __future__ import annotations
from typing import Callable


class ToolRegistry:
    """Global tool registry: string name -> Python callable."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def resolve(self, names: list[str]) -> list[Callable]:
        """Resolve a list of string tool names to their corresponding callable objects, skipping unregistered ones."""
        resolved = []
        for name in names:
            tool = self._tools.get(name)
            if tool:
                resolved.append(tool)
        return resolved

    def available_names(self) -> list[str]:
        return list(self._tools.keys())


# Global singleton instance
registry = ToolRegistry()


def init_registry():
    """Initialize registry and register all builtin, state, and task tools."""
    from zero_g.agents._builtin_tools import (
        read_file, write_file, edit_file, run_command, search_files, list_directory,
    )
    from zero_g.tools import state_tools, task_tools

    # Builtin workspace utilities
    for func in [read_file, write_file, edit_file, run_command, search_files, list_directory]:
        registry.register(func.__name__, func)

    # State tools
    for func in [state_tools.state_write, state_tools.state_read, state_tools.state_clear,
                 state_tools.state_list_active, state_tools.state_get_status]:
        registry.register(func.__name__, func)

    # Task tools
    for func in [task_tools.task_create, task_tools.task_update, task_tools.task_list]:
        registry.register(func.__name__, func)

