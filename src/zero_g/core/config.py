"""Centralized configuration with layered overrides.

Load order (later overrides earlier):
1. Hardcoded defaults
2. User config (~/.config/zero-g/config.json)
3. Project config (.zg/config.json)
4. Environment variables (ZERO_G_* prefix)
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from copy import deepcopy

_DEFAULTS = {
    "state_dir": ".zg/state",
    "tasks_file": ".zg/tasks.md",
    "coord_dir": ".zg/coord",
    "stale_timeout_hours": 24,
    "max_team_workers": 10,
    "max_correction_attempts": 3,
    "max_ralph_iterations": 10,
    "default_model_tier": "medium",
    "verification_freshness_seconds": 300,
    "notepad_max_priority_chars": 500,
    "notepad_prune_days": 7,
    "context_budget_chars": 12000,
    "mcp_servers": [],
}

_USER_CONFIG_PATH = Path.home() / ".config" / "zero-g" / "config.json"
_PROJECT_CONFIG_PATH = Path(".zg/config.json")


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively."""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _load_json_file(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _load_env_overrides() -> dict:
    """Load ZERO_G_* environment variables as config overrides."""
    env_map = {}
    prefix = "ZERO_G_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            # Try to parse as JSON for complex values, fall back to string
            try:
                env_map[config_key] = json.loads(value)
            except json.JSONDecodeError:
                env_map[config_key] = value
    return env_map


class ZGConfig:
    """Layered configuration with dot-notation access."""

    def __init__(self, project_root: Path | None = None):
        self._data = dict(_DEFAULTS)

        # Layer 2: User config
        user_cfg = _load_json_file(_USER_CONFIG_PATH)
        if user_cfg:
            self._data = _deep_merge(self._data, user_cfg)

        # Layer 3: Project config
        project_path = (project_root or Path.cwd()) / ".zg" / "config.json"
        project_cfg = _load_json_file(project_path)
        if project_cfg:
            self._data = _deep_merge(self._data, project_cfg)

        # Layer 4: Environment variables
        env_cfg = _load_env_overrides()
        if env_cfg:
            self._data = _deep_merge(self._data, env_cfg)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key: str):
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def as_dict(self) -> dict:
        return dict(self._data)

    def save_project_config(self, project_root: Path | None = None) -> None:
        """Persist current config as project-level config."""
        path = (project_root or Path.cwd()) / ".zg" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")


# Global singleton
_config: ZGConfig | None = None


def get_config() -> ZGConfig:
    global _config
    if _config is None:
        _config = ZGConfig()
    return _config


def reset_config() -> None:
    global _config
    _config = None
