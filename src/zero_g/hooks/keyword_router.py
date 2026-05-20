"""Keyword router: detects magic keywords in user input and routes to skills.

Port of OMC's keyword-detector hook. Sanitizes the prompt (removes code blocks,
URLs, file paths) before matching to avoid false positives.

Conflict resolution priority: cancel > ralph > autopilot > ultrawork > team.
Disabled inside team workers to prevent infinite spawning.
"""
from __future__ import annotations
import re
from zero_g.core.skill_loader import SkillLoader
from zero_g.core.state_manager import StateManager
from pathlib import Path

# Keyword → skill mapping with priority ordering (highest priority first)
_KEYWORD_SKILLS: list[tuple[str, str]] = [
    ("cancelomc", "cancel"),
    ("stopomc", "cancel"),
    ("ralph", "ralph"),
    ("don't stop", "ralph"),
    ("must complete", "ralph"),
    ("autopilot", "autopilot"),
    ("build me", "autopilot"),
    ("i want a", "autopilot"),
    ("ultrawork", "ultrawork"),
    ("ulw", "ultrawork"),
    ("team", "team"),
    ("ralplan", "ralplan"),
    ("deep interview", "deep_interview"),
]


def sanitize_prompt(text: str) -> str:
    """Remove code blocks, URLs, and file paths to prevent false keyword matches."""
    # Remove code blocks
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove file paths (common patterns)
    text = re.sub(r"[\w./\-]+\.\w{1,4}", "", text)
    return text.lower()


def detect_keyword(user_input: str, is_team_worker: bool = False) -> str | None:
    """Detect the highest-priority magic keyword in user input.

    Args:
        user_input: The raw user prompt text.
        is_team_worker: If True, disable keyword detection to prevent
                        infinite skill spawning inside team workers.

    Returns:
        The matched skill name, or None if no keyword found.
    """
    if is_team_worker:
        return None

    sanitized = sanitize_prompt(user_input)

    for keyword, skill_name in _KEYWORD_SKILLS:
        if keyword in sanitized:
            return skill_name

    return None


def route_to_skill(
    user_input: str,
    skill_loader: SkillLoader,
    is_team_worker: bool = False,
) -> tuple[str | None, object | None]:
    """Detect keyword and resolve to a loaded skill instance.

    Returns:
        (keyword, skill) tuple. Both None if no match or skill not loaded.
    """
    skill_name = detect_keyword(user_input, is_team_worker)
    if skill_name is None:
        return None, None

    skill = skill_loader.match_trigger(skill_name)
    return skill_name, skill
