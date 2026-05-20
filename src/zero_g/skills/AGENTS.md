<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-20 | Updated: 2026-05-20 -->

# skills

## Purpose
Skill framework providing the abstract base class and configuration parsing for structured multi-agent workflows. Concrete skill implementations live elsewhere (e.g., project root `skills/` directory).

## Key Files
| File | Description |
|------|-------------|
| `__init__.py` | Package init |
| `base_skill.py` | `SkillConfig` dataclass (parsed from `skill.yaml`) and `BaseSkill` ABC with `execute()` and `build_prompt()` |

## For AI Agents

### Working In This Directory
- `SkillConfig.from_yaml(path)` parses `skill.yaml` with field filtering for safety
- `SkillConfig.api_layer` defaults to `"L1"` but supports `"L2"` for multi-stage Conversation-based skills
- `BaseSkill.execute(task, context)` is the main entry point — must be implemented by subclasses
- `BaseSkill.build_prompt(task, context)` generates a formatted prompt from config steps

### Common Patterns
- Skills declare triggers (keywords) that `SkillLoader.match_trigger()` matches against user input
- Each skill has an `agent_profile` referencing a YAML profile name in `agents/profiles/`
