"""Per-mode state manager with file-locked atomic read/write.

Manages state files at .zg/state/{mode}-state.json, allowing concurrent
tracking of multiple execution modes (ralph, autopilot, team, etc.).

Port of OMC's .omc/state/{mode}-state.json pattern.
"""
from __future__ import annotations
import json
import os
import fcntl
from pathlib import Path
from datetime import datetime
from copy import deepcopy

_DEFAULT_STATE = {"active": False, "current_stage": "initialized", "iteration": 0}


class StateManager:
    """Manages per-mode state files using exclusive locks for safety."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(".zg/state")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _state_file(self, mode: str) -> Path:
        return self.base_dir / f"{mode}-state.json"

    def write(self, mode: str, state: dict) -> None:
        """Write state for a specific mode using an exclusive file lock."""
        state_file = self._state_file(mode)
        data = deepcopy(state)
        data["_updated_at"] = datetime.now().isoformat()

        with open(state_file, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def read(self, mode: str) -> dict:
        """Read state for a specific mode using a shared file lock."""
        state_file = self._state_file(mode)
        if not state_file.exists():
            return dict(_DEFAULT_STATE)

        with open(state_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                content = f.read().strip()
                if not content:
                    return dict(_DEFAULT_STATE)
                return json.loads(content)
            except json.JSONDecodeError:
                return dict(_DEFAULT_STATE)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def clear(self, mode: str) -> None:
        """Remove the state file for a specific mode."""
        state_file = self._state_file(mode)
        if state_file.exists():
            state_file.unlink()

    def is_active(self, mode: str) -> bool:
        """Check if a specific mode is active and not stale (> 24 hours)."""
        state_file = self._state_file(mode)
        if not state_file.exists():
            return False

        try:
            mtime = os.path.getmtime(state_file)
            age_hours = (datetime.now().timestamp() - mtime) / 3600.0
            if age_hours > 24.0:
                return False
            state = self.read(mode)
            return state.get("active", False)
        except Exception:
            return False

    def list_active(self) -> list[str]:
        """List all currently active mode names."""
        active = []
        for state_file in self.base_dir.glob("*-state.json"):
            mode = state_file.stem.replace("-state", "")
            if self.is_active(mode):
                active.append(mode)
        return active

    def get_status(self, mode: str | None = None) -> dict:
        """Get detailed status for a specific mode or all modes."""
        if mode:
            if not self._state_file(mode).exists():
                return {"mode": mode, "active": False}
            return {"mode": mode, **self.read(mode)}

        # Return status for all modes
        all_status = {}
        for state_file in self.base_dir.glob("*-state.json"):
            m = state_file.stem.replace("-state", "")
            all_status[m] = {"mode": m, **self.read(m)}
        return all_status

    def cleanup_stale(self) -> list[str]:
        """Clean up all stale active states (> 24h). Returns cleaned mode names."""
        cleaned = []
        for state_file in self.base_dir.glob("*-state.json"):
            mode = state_file.stem.replace("-state", "")
            state = self.read(mode)
            if state.get("active"):
                mtime = os.path.getmtime(state_file)
                age_hours = (datetime.now().timestamp() - mtime) / 3600.0
                if age_hours > 24.0:
                    state["active"] = False
                    state["_stale_cleanup"] = True
                    self.write(mode, state)
                    cleaned.append(mode)
        return cleaned
