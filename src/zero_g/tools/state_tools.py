"""Agent-accessible state tools wrapping the per-mode StateManager."""
from __future__ import annotations
import json
from zero_g.core.state_manager import StateManager

_manager = StateManager()


def state_read(mode: str) -> str:
    """Read the state for a specific execution mode.

    Args:
        mode: The mode name (e.g. 'ralph', 'autopilot', 'team').
    """
    state = _manager.read(mode)
    return json.dumps(state, indent=2, ensure_ascii=False)


def state_write(mode: str, **kwargs) -> str:
    """Write or update state for a specific execution mode.

    Args:
        mode: The mode name (e.g. 'ralph', 'autopilot', 'team').
        **kwargs: State fields to set (active, current_stage, iteration, etc.).
    """
    current = _manager.read(mode)
    current.update(kwargs)
    _manager.write(mode, current)
    return f"Successfully updated {mode} state."


def state_clear(mode: str) -> str:
    """Remove the state file for a specific mode.

    Args:
        mode: The mode name to clear.
    """
    _manager.clear(mode)
    return f"Successfully cleared {mode} state."


def state_list_active() -> str:
    """List all currently active execution modes."""
    active = _manager.list_active()
    if not active:
        return "No active modes."
    return json.dumps(active)


def state_get_status(mode: str | None = None) -> str:
    """Get detailed status for a mode or all modes.

    Args:
        mode: Optional mode name. If omitted, returns all modes' status.
    """
    status = _manager.get_status(mode)
    return json.dumps(status, indent=2, ensure_ascii=False)
