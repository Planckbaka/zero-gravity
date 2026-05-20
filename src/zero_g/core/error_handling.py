"""Global error handling patterns for skill execution safety."""
from __future__ import annotations
import functools
import logging
from zero_g.core.state_manager import StateManager

logger = logging.getLogger("zero_g")


def skill_error_handler(mode: str):
    """Decorator that catches skill execution exceptions and guarantees state cleanup.

    When a skill crashes, the decorator writes an error state to prevent stale locks
    that would block subsequent runs.

    Usage:
        @skill_error_handler("ralph")
        async def execute(self, task, context):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Skill '{mode}' failed: {e}", exc_info=True)
                StateManager().write(mode, {
                    "active": False,
                    "error": str(e),
                    "current_stage": "failed",
                })
                return f"Skill '{mode}' failed: {e}"
        return wrapper
    return decorator
