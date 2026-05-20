"""Unit tests for SkillLoader discovering, importing, and routing custom skills."""
from __future__ import annotations
from pathlib import Path
from zero_g.core.skill_loader import SkillLoader

def test_skill_loader_discovery_and_routing(tmp_path: Path):
    # Setup a mock skill folder structure in a temp directory
    skill_dir = tmp_path / "mock-skill"
    skill_dir.mkdir()
    
    skill_yaml_content = """
name: mock-skill
description: A dummy test skill.
triggers:
  - "run-dummy"
  - "dummy-trigger"
agent_profile: architect
api_layer: L1
steps:
  - "Test step A"
max_iterations: 1
"""
    (skill_dir / "skill.yaml").write_text(skill_yaml_content.strip(), encoding="utf-8")
    
    skill_handler_content = """
from zero_g.skills.base_skill import BaseSkill

class MockSkillTest(BaseSkill):
    async def execute(self, task: str, context: dict) -> str:
        return f"Hello: {task}"
"""
    (skill_dir / "handler.py").write_text(skill_handler_content.strip(), encoding="utf-8")
    
    # Instantiate loader scanning our temporary directory
    loader = SkillLoader(builtin_dir=tmp_path)
    skills = loader.discover()
    
    # Assert skill was discovered
    assert "mock-skill" in skills
    skill_instance = skills["mock-skill"]
    assert skill_instance.config.name == "mock-skill"
    assert skill_instance.config.triggers == ["run-dummy", "dummy-trigger"]
    
    # Test keyword matching / routing
    matched_a = loader.match_trigger("Please run-dummy task")
    assert matched_a is not None
    assert matched_a.config.name == "mock-skill"
    
    matched_b = loader.match_trigger("Call the DUMMY-trigger now!")
    assert matched_b is not None
    assert matched_b.config.name == "mock-skill"
    
    # Nonexistent trigger
    assert loader.match_trigger("Arbitrary query") is None
