"""Skill loader module for dynamically discovering, importing, and routing skills."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Type
from zero_g.skills.base_skill import BaseSkill


class SkillLoader:
    def __init__(self, builtin_dir: Path, user_dir: Path | None = None):
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self._skills: dict[str, BaseSkill] = {}
        self._trigger_map: dict[str, str] = {}

    def discover(self) -> dict[str, BaseSkill]:
        dirs_to_scan = []
        if self.builtin_dir and self.builtin_dir.exists():
            dirs_to_scan.append(self.builtin_dir)
        if self.user_dir and self.user_dir.exists():
            dirs_to_scan.append(self.user_dir)

        for base_dir in dirs_to_scan:
            for skill_path in sorted(base_dir.iterdir()):
                if skill_path.is_dir() and (skill_path / "skill.yaml").exists() and (skill_path / "handler.py").exists():
                    try:
                        handler_cls = self._import_handler(skill_path)
                        skill = handler_cls(skill_path)
                        self._skills[skill.config.name] = skill
                        for trigger in skill.config.triggers:
                            self._trigger_map[trigger.lower()] = skill.config.name
                    except Exception as e:
                        # Log error or raise in test environments
                        print(f"Error loading skill at {skill_path}: {e}")
                        
        return self._skills

    def match_trigger(self, user_input: str) -> BaseSkill | None:
        text = user_input.lower()
        for keyword, skill_name in self._trigger_map.items():
            if keyword in text:
                return self._skills.get(skill_name)
        return None

    def _import_handler(self, skill_path: Path) -> Type[BaseSkill]:
        # Use a unique module name based on skill directory name to avoid import conflicts
        unique_name = f"zero_g.skills.{skill_path.name}.handler"
        spec = importlib.util.spec_from_file_location(
            unique_name, skill_path / "handler.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {skill_path / 'handler.py'}")
            
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                return attr
        raise ImportError(f"No BaseSkill subclass found in {skill_path / 'handler.py'}")
