"""Stale state cleanup and graceful shutdown handling.

Port of OMC's stale state management:
- Auto-cleanup of states older than 24 hours
- SIGINT handler for graceful shutdown
- Deactivates all active modes on interruption
"""
from __future__ import annotations
import signal
import logging
from zero_g.core.state_manager import StateManager

logger = logging.getLogger("zero_g")


def cleanup_stale_states(base_dir=None) -> list[str]:
    """Clean up all state files that have been active for more than 24 hours.

    Returns list of cleaned mode names.
    """
    sm = StateManager(base_dir=base_dir)
    cleaned = sm.cleanup_stale()
    if cleaned:
        logger.info(f"Cleaned up stale states: {cleaned}")
    return cleaned


def deactivate_all_modes(base_dir=None) -> list[str]:
    """Force-deactivate all currently active modes.

    Used for graceful shutdown on SIGINT.
    """
    sm = StateManager(base_dir=base_dir)
    active = sm.list_active()
    for mode in active:
        state = sm.read(mode)
        state["active"] = False
        state["_shutdown_cleanup"] = True
        sm.write(mode, state)
    if active:
        logger.info(f"Deactivated modes on shutdown: {active}")
    return active


def setup_signal_handler(base_dir=None):
    """Register SIGINT handler for graceful state cleanup.

    On Ctrl+C, deactivates all active modes before exit.
    """
    def handler(signum, frame):
        logger.info("SIGINT received, cleaning up active states...")
        deactivated = deactivate_all_modes(base_dir)
        print(f"\nGraceful shutdown. Deactivated: {deactivated}")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handler)
