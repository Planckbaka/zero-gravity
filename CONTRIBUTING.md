# Contributing to Zero-Gravity

First off, thank you for considering contributing to Zero-Gravity! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to make multi-agent orchestration better.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/Planckbaka/zero-gravity/issues)
- Open a new issue with:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Python version and OS
  - Relevant logs or error messages

### Suggesting Features

- Open an issue with the `enhancement` label
- Describe the use case and expected behavior
- Reference similar features in other tools if applicable

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass (`uv run pytest`)
6. Follow the commit message conventions below
7. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/zero-gravity.git
cd zero-gravity

# Install dependencies
uv sync

# Install in editable mode
uv pip install -e .

# Verify setup
uv run python -c "from zero_g.core.tool_registry import init_registry; init_registry(); print('OK')"
```

## Project Structure

```
src/zero_g/
├── core/           # Core orchestration engine (factories, registry, state)
├── agents/         # Agent profiles (YAML) and builtin tools
├── skills/         # Skill implementations (skill.yaml + handler.py)
├── hooks/          # Keyword routing, state cleanup
└── tools/          # Agent-accessible tools (state, task)
```

## Code Style

- **Python**: Follow PEP 8 with type hints required
- Use `from __future__ import annotations` in all modules
- All tool functions need docstrings (Antigravity SDK auto-generates tool schemas from them)
- No comments unless the WHY is non-obvious
- Keep functions focused and small

### Adding a New Agent Profile

1. Create `src/zero_g/agents/profiles/{name}.yaml`:
   ```yaml
   system_instructions: |
     You are the {Name} subagent for zero-gravity.
     {Role description and rules}
   tools:
     - read_file
     - write_file
     # ... list of registered tool names
   ```
2. Optionally add `agents/{Name}.md` with extended instructions

### Adding a New Skill

1. Create `src/zero_g/skills/{name}/skill.yaml`:
   ```yaml
   name: my-skill
   description: What the skill does
   triggers:
     - my-skill
     - trigger phrase
   agent_profile: executor        # Default agent profile
   api_layer: L2                  # L2 for multi-stage, L1 for single-shot
   steps:
     - "Step 1 description"
     - "Step 2 description"
   max_iterations: 3
   ```
2. Create `src/zero_g/skills/{name}/handler.py`:
   ```python
   from zero_g.skills.base_skill import BaseSkill
   from zero_g.core.error_handling import skill_error_handler

   class MySkill(BaseSkill):
       @skill_error_handler("my-skill")
       async def execute(self, task: str, context: dict) -> str:
           # Implementation
           ...
   ```

### Adding a New Tool

1. Add the tool function in the appropriate file under `src/zero_g/tools/` or `src/zero_g/agents/_builtin_tools.py`
2. The function needs a docstring with `Args:` section (SDK auto-generates schema)
3. Register it in `src/zero_g/core/tool_registry.py` → `init_registry()`

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_state_manager.py

# Run with verbose output
uv run pytest -v
```

### Test Guidelines

- Use `tmp_path` fixture for file operations (never write to actual project directory)
- Mock `google.antigravity` SDK imports (the SDK requires a running harness)
- Test error paths, not just happy paths
- Keep tests independent and deterministic

## Commit Messages

Format:
```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`

Examples:
```
feat(skills): add deep-interview skill with L2 conversation
fix(state): prevent race condition in per-mode state files
docs(readme): add architecture diagram and skill documentation
```

## Questions?

Feel free to open an issue with the `question` label or start a discussion.
