"""Model routing: per-role model selection with GeminiConfig.

Maps agent roles to appropriate Gemini models and thinking levels,
porting OMC's tier-based model routing to the Antigravity SDK.

Tier mapping (OMC → Gemini):
- HIGH (opus)  → gemini-2.5-pro with ThinkingLevel.HIGH
- MEDIUM (sonnet) → gemini-2.5-flash with ThinkingLevel.MEDIUM
- LOW (haiku)  → gemini-2.5-flash with ThinkingLevel.LOW
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from google.antigravity.types import GeminiConfig, ModelConfig, ModelEntry


class ThinkingLevel:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModelTier:
    model_name: str
    thinking_level: str


# Tier definitions
TIERS = {
    "high": ModelTier("gemini-2.5-pro", ThinkingLevel.HIGH),
    "medium": ModelTier("gemini-2.5-flash", ThinkingLevel.MEDIUM),
    "low": ModelTier("gemini-2.5-flash", ThinkingLevel.LOW),
}

# Default tier per agent role
AGENT_DEFAULT_TIERS: dict[str, str] = {
    "architect": "high",
    "critic": "high",
    "planner": "high",
    "executor": "medium",
    "tester": "medium",
    "debugger": "medium",
    "explorer": "low",
    "verifier": "medium",
    "qa_tester": "medium",
    "writer": "low",
}


def get_gemini_config(
    agent_role: str | None = None,
    tier: str | None = None,
    model_name: str | None = None,
    thinking_level: str | None = None,
) -> GeminiConfig:
    """Build a GeminiConfig with model selection.

    Priority: explicit model_name > explicit tier > agent_role default > medium.
    """
    if model_name:
        resolved_model = model_name
        resolved_thinking = thinking_level or ThinkingLevel.MEDIUM
    elif tier:
        t = TIERS.get(tier, TIERS["medium"])
        resolved_model = t.model_name
        resolved_thinking = thinking_level or t.thinking_level
    elif agent_role:
        tier_name = AGENT_DEFAULT_TIERS.get(agent_role, "medium")
        t = TIERS[tier_name]
        resolved_model = t.model_name
        resolved_thinking = t.thinking_level
    else:
        t = TIERS["medium"]
        resolved_model = t.model_name
        resolved_thinking = t.thinking_level

    return GeminiConfig(
        models=ModelConfig(
            default=ModelEntry(name=resolved_model)
        )
    )
