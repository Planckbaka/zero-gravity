"""Base classes and configuration parsing for zero-gravity skills."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class SkillConfig:
    name: str
    description: str
    triggers: list[str]
    agent_profile: str
    api_layer: str = "L1"  # "L1" (Agent) or "L2" (Conversation)
    steps: list[str] = field(default_factory=list)
    max_iterations: int = 1
    extra_tools: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> SkillConfig:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Handle field filtering for safety and compatibility
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class BaseSkill(ABC):
    def __init__(self, skill_dir: Path):
        self.config = SkillConfig.from_yaml(skill_dir / "skill.yaml")
        self.skill_dir = skill_dir

    @abstractmethod
    async def execute(self, task: str, context: dict) -> str:
        pass

    def build_prompt(self, task: str, context: dict) -> str:
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.config.steps))
        return f"Task: {task}\n\nContext: {context}\n\nSteps:\n{steps_text}"
