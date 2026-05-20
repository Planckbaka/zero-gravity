# Zero-G 开发指南 — OMC 理念移植到 Google Antigravity SDK

> 将 oh-my-claudecode (OMC) 的核心理念移植到 Google Antigravity 生态的架构设计与实现指南。
>
> **版本**: v2 (经 Architect APPROVE + Critic REVISE → 修订后共识版)
> **审核日期**: 2026-05-20

## 0. Architect/Critic 共识修订记录

| 问题 | 严重性 | 修订内容 |
|------|--------|---------|
| `LocalAgentConfig` 无 `model` 参数 | CRITICAL | 引入双 API 策略：L2 Conversation + GeminiConfig 用于多阶段 skill，L1 Agent 用于并行 worker |
| YAML 工具名字符串无法传给 `tools=` | CRITICAL | 新增 ToolRegistry 工具注册表，自动解析字符串→Python callable |
| Team skill `json.loads()` 无错误处理 | CRITICAL | 新增 `extract_json()` 函数，处理 markdown fence、前后缀文本、malformed JSON |
| Team skill task ID 不匹配 | CRITICAL | 解析 `task_create()` 返回的实际 task_id |
| Skill loader 模块名冲突 | MAJOR | 使用唯一模块名 `f"zero_g.skills.{name}.handler"` |
| Team 无 inter-agent 通信 | MAJOR | 新增文件锁 + 分区策略 + 共享状态协调 |
| 无错误处理策略 | MAJOR | 全局新增错误处理模式章节 |
| 无 graceful shutdown | MAJOR | 新增 stale state 清理 + SIGINT 处理 |

## 1. 背景与动机

### 什么是 OMC

oh-my-claudecode 是 Claude Code CLI 的多 agent 编排层，提供：
- **Skills**：可复用的结构化工作流（autopilot、team、ralph、deep-interview 等）
- **Agents**：专业化的 subagent（executor、architect、critic、planner 等）
- **Hooks**：事件驱动的拦截系统（关键词检测、工具调用拦截、模式强制）
- **State**：模式状态持久化（ralph 循环、team 协调、interview 进度）
- **Consensus**：Planner → Architect → Critic 三方共识规划

### 为什么移植到 Antigravity

Google Antigravity 是 Google 的 agent-first 开发平台（2025 年末发布），提供 Python SDK，支持：
- `Agent` 类（L1 高层入口，管理完整生命周期）
- `Conversation` 类（L2 有状态会话 + 历史记录 + 步骤追踪）
- Custom Tools（Python 函数注册为 agent 可调用工具）
- MCP Integration（`McpStdioServer` 原生支持）
- Hooks & Policies（`deny()`, `allow()`, `ask_user()`, `enforce()`）
- Triggers（`every(N, handler)` 后台定时任务）
- Streaming（实时响应流 + thoughts + tool_calls）
- Multimodal（图片、视频、音频、文档）

OMC 的理念是通用的——不绑定 Claude Code 的实现细节。Antigravity SDK 提供了足够的基础设施来重建同样的编排能力。

## 2. 核心架构决策：双 API 策略

> **这是 v2 最重要的修订。** Architect 和 Critic 一致指出：Antigravity SDK 的 L1 `Agent` 类设计用于单次有状态会话，不适合多阶段 skill 中反复创建销毁 Agent 实例的模式。

### L1 vs L2 选择规则

| 使用场景 | API 层 | 原因 |
|----------|--------|------|
| 多阶段顺序 skill（Ralph、Autopilot、Plan、Deep-Interview） | **L2 Conversation** | 需要保持对话历史、上下文连贯性、模型切换 |
| 并行 worker（Team 的 worker） | **L1 Agent** | 独立任务、无需跨 worker 上下文、简单创建销毁 |
| 交互式主循环 | **L1 Agent** | 匹配 SDK 官方推荐的 interactive 用法 |
| 单次快速查询（Explorer） | **L1 Agent** | 无状态、一次性、轻量 |

### 为什么不能用纯 L1

```
Ralph skill 每个迭代：
  创建 executor Agent → 执行 → 销毁
  创建 architect Agent → 审核 → 销毁
  重复 10 次 = 20 个 Agent 实例

问题：
1. 每次 async with Agent(config) 初始化新的 runtime 连接（昂贵）
2. 无对话历史 — architect 只看到 executor 的文本摘要，不是完整推理链
3. 上下文通过手动文本拼接传递，信息损失严重
```

### 为什么不能用纯 L2

```
Team skill 并行 worker：
  worker-1: Agent + Conversation
  worker-2: Agent + Conversation  
  worker-3: Agent + Conversation

问题：
1. Conversation 不支持并行 chat（单线程状态机）
2. 共享 Connection 的并发安全性未知
3. 每个 worker 需要独立的对话历史
```

### 模型选择机制

`LocalAgentConfig` 没有 `model` 参数。模型选择通过 L2 的 `GeminiConfig` 实现：

```python
from google.antigravity.types import GeminiConfig

# L2 路径：每个 Conversation 可指定不同模型
gemini_config_pro = GeminiConfig(
    api_key="...",
    # model 参数需在实现时验证是否支持
    # 如果不支持，则通过 system_instructions 长度/复杂度间接控制
)
```

如果 `GeminiConfig` 也不支持 model 参数（需安装后验证），则：
- **方案 A**：所有 agent 使用同一模型，通过 system_instructions 的复杂度间接控制推理深度
- **方案 B**：为不同模型配置不同的 API key / project（如果有多个 Gemini 项目）
- **方案 C**：等待 SDK 后续版本支持 model 参数

## 3. OMC → Antigravity SDK 概念映射

| OMC 概念 | Antigravity SDK 等价 | 说明 |
|----------|---------------------|------|
| Hooks (PreToolUse 等) | `policies` 系统 (`deny`, `allow`, `ask_user`, `enforce`) | 工具调用的拦截与授权 |
| 关键词检测 (keyword-detector) | `Agent.chat()` 前置处理 + 自定义路由 | 检测用户输入中的关键词，路由到 skill |
| MCP Tools | `McpStdioServer` | 原生 MCP 支持 |
| Skills (SKILL.md) | Custom Tools + YAML config + handler.py | 可复用工作流定义 |
| Agent 类型 (executor, architect...) | 不同配置的 Agent/Conversation | 不同 system_instructions + tools + model |
| State 管理 (state_write/read) | Custom Tool + JSON 文件持久化 | 模式状态（ralph/team/interview） |
| Team (多 Agent 协调) | L1 Agent 并行 + 共享文件状态 + 文件锁 | 并行 agent 工作池 |
| Conversation 连续性 | L2 Conversation + history | 多阶段 skill 的上下文保持 |
| Notepad / Wiki | Custom Tools (file-based) | 持久化知识库 |

## 4. 推荐项目结构

```
zero-g/
├── pyproject.toml
├── README.md
├── src/
│   └── zero_g/
│       ├── __init__.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent_factory.py      # L1 Agent 工厂（并行 worker 用）
│       │   ├── conversation_factory.py # L2 Conversation 工厂（多阶段 skill 用）
│       │   ├── tool_registry.py       # 工具注册表：字符串名 → Python callable
│       │   ├── skill_loader.py        # Skill 发现与加载（唯一模块名）
│       │   ├── state_manager.py       # 模式状态持久化（含文件锁）
│       │   ├── json_utils.py          # LLM 输出 JSON 提取
│       │   └── config.py              # 全局配置
│       │
│       ├── agents/                    # Agent 角色定义
│       │   ├── __init__.py
│       │   ├── profiles/              # YAML 角色配置
│       │   │   ├── executor.yaml
│       │   │   ├── architect.yaml
│       │   │   ├── critic.yaml
│       │   │   ├── planner.yaml
│       │   │   └── explorer.yaml
│       │   └── _builtin_tools.py      # 内置工具函数集合
│       │
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── base_skill.py          # Skill 基类（区分 L1/L2）
│       │   ├── autopilot/
│       │   │   ├── skill.yaml
│       │   │   └── handler.py         # 使用 L2 Conversation
│       │   ├── ralph/
│       │   │   ├── skill.yaml
│       │   │   └── handler.py         # 使用 L2 Conversation
│       │   ├── team/
│       │   │   ├── skill.yaml
│       │   │   ├── handler.py         # 使用 L1 Agent 并行
│       │   │   └── coordinator.py     # 文件锁 + 分区策略
│       │   ├── deep_interview/
│       │   │   ├── skill.yaml
│       │   │   └── handler.py         # 使用 L2 Conversation
│       │   └── plan/
│       │       ├── skill.yaml
│       │       └── handler.py         # 使用 L2 Conversation
│       │
│       ├── hooks/
│       │   ├── __init__.py
│       │   ├── keyword_router.py
│       │   ├── mode_enforcer.py
│       │   └── stale_state_cleanup.py # SIGINT/stale state 处理
│       │
│       └── tools/                     # Custom Tools（注册给 Agent）
│           ├── __init__.py
│           ├── state_tools.py
│           ├── wiki_tools.py
│           ├── task_tools.py          # 修复 task ID 逻辑
│           ├── notepad_tools.py
│           └── memory_tools.py
│
├── skills/                            # 用户自定义 skill（热加载）
│   └── README.md
│
├── tests/
│   ├── test_agent_factory.py
│   ├── test_conversation_factory.py
│   ├── test_tool_registry.py
│   ├── test_skill_loader.py
│   ├── test_json_utils.py
│   └── test_state_manager.py
│
└── examples/
    ├── basic_usage.py
    ├── autopilot_demo.py
    └── team_demo.py
```

## 5. 核心模块设计

### 5.1 工具注册表（新增 — 解决 CRITICAL #2）

```python
# src/zero_g/core/tool_registry.py
"""将字符串工具名映射到 Python callable 对象。"""
from __future__ import annotations
from typing import Callable


class ToolRegistry:
    """全局工具注册表：字符串名 → Python callable。"""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def resolve(self, names: list[str]) -> list[Callable]:
        """将字符串列表解析为 callable 列表，跳过未注册的。"""
        resolved = []
        for name in names:
            tool = self._tools.get(name)
            if tool:
                resolved.append(tool)
        return resolved

    def available_names(self) -> list[str]:
        return list(self._tools.keys())


# 全局单例
registry = ToolRegistry()


def init_registry():
    """注册所有内置工具。在应用启动时调用一次。"""
    from zero_g.tools import (
        state_tools, task_tools, wiki_tools, notepad_tools, memory_tools,
    )
    from zero_g.agents._builtin_tools import (
        read_file, write_file, edit_file, run_command, search_files, list_directory,
    )

    # 内置文件操作
    for func in [read_file, write_file, edit_file, run_command, search_files, list_directory]:
        registry.register(func.__name__, func)

    # 状态工具
    for func in [state_tools.state_write, state_tools.state_read, state_tools.state_clear]:
        registry.register(func.__name__, func)

    # 任务工具
    for func in [task_tools.task_create, task_tools.task_update, task_tools.task_list]:
        registry.register(func.__name__, func)

    # Wiki / Notepad / Memory
    # ... 同理注册
```

### 5.2 Agent 工厂 — L1（并行 worker 用）

```python
# src/zero_g/core/agent_factory.py
"""L1 Agent 工厂：用于 Team 的并行 worker 和单次快速查询。"""
from __future__ import annotations
import yaml
from pathlib import Path
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.hooks.policy import deny, allow
from zero_g.core.tool_registry import registry

_PROFILES_DIR = Path(__file__).parent.parent / "agents" / "profiles"


def load_profile(name: str) -> dict:
    profile_path = _PROFILES_DIR / f"{name}.yaml"
    if not profile_path.exists():
        raise ValueError(f"Unknown agent profile: {name}")
    return yaml.safe_load(profile_path.read_text())


def create_agent(
    profile: str,
    extra_tools: list | None = None,
) -> Agent:
    """
    创建 L1 Agent 实例。用于并行 worker 和单次查询。

    注意：L1 Agent 不支持模型选择。所有实例使用 SDK 默认模型。
    如需模型切换，使用 conversation_factory.py 的 L2 路径。
    """
    config = load_profile(profile)

    # 从注册表解析工具名字符串 → Python callable
    profile_tool_names = config.get("tools", [])
    resolved_tools = registry.resolve(profile_tool_names)
    if extra_tools:
        resolved_tools.extend(extra_tools)

    # 构建 policies：deny all → allow registered tools
    policies = [deny("*")]
    for name in profile_tool_names:
        if registry.get(name):
            policies.append(allow(name))
    # 也放行 extra_tools
    if extra_tools:
        for tool in extra_tools:
            policies.append(allow(tool.__name__))

    agent_config = LocalAgentConfig(
        system_instructions=config["system_instructions"],
        tools=resolved_tools,
        capabilities=CapabilitiesConfig() if config.get("allow_write") else None,
        policies=policies,
    )

    return Agent(agent_config)
```

### 5.3 Conversation 工厂 — L2（多阶段 skill 用）（新增）

```python
# src/zero_g/core/conversation_factory.py
"""L2 Conversation 工厂：用于多阶段 skill（Ralph、Autopilot、Plan、Deep-Interview）。

优势：
- 保持对话历史（conversation.history）
- 支持角色切换（通过新的 system_instructions）
- 上下文连续性（无需手动拼接文本）
"""
from __future__ import annotations
from google.antigravity.connections.local import LocalConnectionStrategy
from google.antigravity.conversation.conversation import Conversation
from google.antigravity.tools.tool_runner import ToolRunner
from google.antigravity.types import GeminiConfig
from zero_g.core.tool_registry import registry
from zero_g.core.agent_factory import load_profile


def create_conversation(
    profile: str,
    extra_tools: list | None = None,
) -> Conversation:
    """
    创建 L2 Conversation 实例。用于多阶段 skill。

    每个 Conversation 维护独立的对话历史。
    同一 skill 的不同阶段可以共享同一个 Conversation（上下文连续），
    或创建新的 Conversation（角色切换）。
    """
    config = load_profile(profile)

    # 解析工具
    profile_tool_names = config.get("tools", [])
    resolved_tools = registry.resolve(profile_tool_names)
    if extra_tools:
        resolved_tools.extend(extra_tools)

    # 注册工具到 ToolRunner
    tool_runner = ToolRunner()
    for tool in resolved_tools:
        tool_runner.register(tool)

    strategy = LocalConnectionStrategy(
        tool_runner=tool_runner,
        gemini_config=GeminiConfig(
            # model 选择需在安装 SDK 后验证 GeminiConfig 是否支持 model 参数
            # 如果不支持，所有 conversation 使用同一模型
        ),
    )

    # 使用 Conversation.create 并设置 system_instructions
    conversation = Conversation.create_with_instructions(
        strategy,
        system_instructions=config["system_instructions"],
    )
    return conversation
```

### 5.4 JSON 提取工具（新增 — 解决 CRITICAL #3）

```python
# src/zero_g/core/json_utils.py
"""从 LLM 输出中提取 JSON。处理 markdown fence、前后缀文本、malformed JSON。"""
from __future__ import annotations
import json
import re


def extract_json(text: str) -> list | dict:
    """
    从 LLM 输出文本中提取 JSON。

    处理以下情况：
    1. 纯 JSON（直接 json.loads）
    2. Markdown code fence 包裹的 JSON (```json ... ```)
    3. JSON 前后有解释文本
    4. 数组/对象的尾部逗号

    Raises:
        ValueError: 无法提取有效 JSON
    """
    # 策略 1：直接解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 策略 2：提取 markdown code fence
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 策略 3：查找第一个 [ 或 { 到最后一个 ] 或 }
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1]
            # 修复尾部逗号
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from LLM output: {text[:200]}...")


def extract_json_with_retry(extract_fn, text: str, max_retries: int = 2) -> list | dict:
    """带重试的 JSON 提取。重试时通过 extract_fn 让 LLM 重新生成。"""
    for attempt in range(max_retries + 1):
        try:
            return extract_json(text)
        except ValueError:
            if attempt < max_retries:
                text = extract_fn("Your previous output was not valid JSON. Output ONLY valid JSON, no other text.")
            else:
                raise
```

### 5.5 Skill 基类（修订 — 区分 L1/L2）

```python
# src/zero_g/skills/base_skill.py
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
    api_layer: str = "L1"  # "L1" (Agent) or "L2" (Conversation) — 新增
    steps: list[str] = field(default_factory=list)
    max_iterations: int = 1
    extra_tools: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "SkillConfig":
        data = yaml.safe_load(path.read_text())
        # 容错：忽略 YAML 中不在 dataclass 里的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class BaseSkill(ABC):
    def __init__(self, skill_dir: Path):
        self.config = SkillConfig.from_yaml(skill_dir / "skill.yaml")
        self.skill_dir = skill_dir

    @abstractmethod
    async def execute(self, task: str, context: dict) -> str:
        ...

    def build_prompt(self, task: str, context: dict) -> str:
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.config.steps))
        return f"Task: {task}\n\nContext: {context}\n\nSteps:\n{steps_text}"
```

### 5.6 状态管理（修订 — 含 cleanup）

```python
# src/zero_g/core/state_manager.py
from __future__ import annotations
import json
import fcntl
from pathlib import Path
from datetime import datetime
from copy import deepcopy


class StateManager:
    """模式状态持久化，支持文件锁防止并发冲突。"""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(".zero-g/state")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, mode: str, state: dict) -> None:
        state_file = self.base_dir / f"{mode}-state.json"
        # 深拷贝避免修改调用方的 dict
        data = deepcopy(state)
        data["_updated_at"] = datetime.now().isoformat()
        with open(state_file, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # 排他锁
            json.dump(data, f, indent=2, ensure_ascii=False)
            fcntl.flock(f, fcntl.LOCK_UN)

    def read(self, mode: str) -> dict | None:
        state_file = self.base_dir / f"{mode}-state.json"
        if not state_file.exists():
            return None
        with open(state_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)  # 共享锁
            content = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)
        return json.loads(content)

    def clear(self, mode: str) -> None:
        state_file = self.base_dir / f"{mode}-state.json"
        if state_file.exists():
            state_file.unlink()

    def is_active(self, mode: str) -> bool:
        """快速检查：文件存在 + active=true。"""
        state_file = self.base_dir / f"{mode}-state.json"
        if not state_file.exists():
            return False
        # 仅在文件修改时间 < 24h 时认为是活跃的（防止 stale state）
        import os
        age_hours = (datetime.now().timestamp() - os.path.getmtime(state_file)) / 3600
        if age_hours > 24:
            return False
        state = self.read(mode)
        return state is not None and state.get("active", False)

    def cleanup_stale(self) -> list[str]:
        """清理所有超过 24h 的 active state。返回清理的 mode 列表。"""
        cleaned = []
        for state_file in self.base_dir.glob("*-state.json"):
            mode = state_file.stem.replace("-state", "")
            if self.is_active(mode):
                # is_active 已经检查了 24h 限制
                continue
            state = self.read(mode)
            if state and state.get("active"):
                state["active"] = False
                state["_stale_cleanup"] = True
                self.write(mode, state)
                cleaned.append(mode)
        return cleaned
```

### 5.7 Skill Loader（修订 — 唯一模块名）

```python
# src/zero_g/core/skill_loader.py
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Type
from zero_g.skills.base_skill import BaseSkill, SkillConfig


class SkillLoader:
    def __init__(self, builtin_dir: Path, user_dir: Path | None = None):
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self._skills: dict[str, BaseSkill] = {}
        self._trigger_map: dict[str, str] = {}

    def discover(self) -> dict[str, BaseSkill]:
        dirs_to_scan = [self.builtin_dir]
        if self.user_dir and self.user_dir.exists():
            dirs_to_scan.append(self.user_dir)

        for base_dir in dirs_to_scan:
            for skill_path in sorted(base_dir.iterdir()):
                if skill_path.is_dir() and (skill_path / "skill.yaml").exists():
                    handler_cls = self._import_handler(skill_path)
                    skill = handler_cls(skill_path)
                    self._skills[skill.config.name] = skill
                    for trigger in skill.config.triggers:
                        self._trigger_map[trigger.lower()] = skill.config.name
        return self._skills

    def match_trigger(self, user_input: str) -> BaseSkill | None:
        text = user_input.lower()
        for keyword, skill_name in self._trigger_map.items():
            if keyword in text:
                return self._skills.get(skill_name)
        return None

    def _import_handler(self, skill_path: Path) -> Type[BaseSkill]:
        # 使用唯一模块名，避免 sys.modules 冲突
        unique_name = f"zero_g.skills.{skill_path.name}.handler"
        spec = importlib.util.spec_from_file_location(
            unique_name, skill_path / "handler.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                return attr
        raise ImportError(f"No BaseSkill subclass found in {skill_path / 'handler.py'}")
```

### 5.8 任务工具（修订 — 修复 task ID）

```python
# src/zero_g/tools/task_tools.py
import json
from pathlib import Path
from datetime import datetime


class TaskManager:
    def __init__(self, team_name: str, base_dir: Path | None = None):
        self.tasks_dir = (base_dir or Path(".zero-g/tasks")) / team_name
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _next_id(self) -> str:
        """基于现有最大 ID 递增，而非文件计数。"""
        existing_ids = []
        for f in self.tasks_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                existing_ids.append(int(data.get("id", 0)))
            except (json.JSONDecodeError, ValueError):
                pass
        return str(max(existing_ids, default=0) + 1)

    def create(self, subject: str, description: str, owner: str = "") -> dict:
        task_id = self._next_id()
        task = {
            "id": task_id,
            "subject": subject,
            "description": description,
            "owner": owner,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        (self.tasks_dir / f"{task_id}.json").write_text(json.dumps(task, indent=2))
        return task  # 返回 dict 而非 JSON string，方便调用方解析

    def update(self, task_id: str, status: str | None = None, owner: str | None = None) -> dict:
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            raise FileNotFoundError(f"Task {task_id} not found")
        task = json.loads(task_file.read_text())
        if status:
            task["status"] = status
        if owner:
            task["owner"] = owner
        task_file.write_text(json.dumps(task, indent=2))
        return task

    def list_tasks(self) -> list[dict]:
        tasks = []
        for f in sorted(self.tasks_dir.glob("*.json")):
            try:
                tasks.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
        return tasks


_managers: dict[str, TaskManager] = {}

def _get(name: str) -> TaskManager:
    if name not in _managers:
        _managers[name] = TaskManager(name)
    return _managers[name]

def task_create(team_name: str, subject: str, description: str, owner: str = "") -> str:
    """Create a task. Returns JSON with task_id."""
    task = _get(team_name).create(subject, description, owner)
    return json.dumps(task)

def task_update(team_name: str, task_id: str, status: str | None = None, owner: str | None = None) -> str:
    """Update a task's status or owner."""
    task = _get(team_name).update(task_id, status, owner)
    return json.dumps(task)

def task_list(team_name: str) -> str:
    """List all tasks in a team."""
    return json.dumps(_get(team_name).list_tasks())
```

## 6. Skill 实现示例（修订版）

### 6.1 Ralph — 使用 L2 Conversation

```python
# src/zero_g/skills/ralph/handler.py
from __future__ import annotations
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.conversation_factory import create_conversation
from zero_g.core.state_manager import StateManager
from zero_g.core.json_utils import extract_json


class RalphSkill(BaseSkill):
    async def execute(self, task: str, context: dict) -> str:
        state = StateManager()
        state.write("ralph", {"active": True, "task": task, "iteration": 0,
                               "max_iterations": self.config.max_iterations})

        # 使用 L2 Conversation 保持上下文连续性
        conv = create_conversation(self.config.agent_profile)

        async with conv:
            # 初始请求
            await conv.send(
                f"Task: {task}\n\n"
                f"Implement this task. Write all necessary code.\n"
                f"After implementation, describe what you did and verify it works."
            )

            for iteration in range(self.config.max_iterations):
                state.write("ralph", {"active": True, "task": task,
                                       "iteration": iteration + 1})

                # 收集 executor 的响应
                impl_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        impl_result = step.content

                # 角色切换：在同一 Conversation 中发送 review 请求
                await conv.send(
                    f"--- ARCHITECT REVIEW ---\n"
                    f"Review the above implementation for: {task}\n"
                    f"Verdict: APPROVE or REVISE with specific feedback."
                )

                review_result = ""
                async for step in conv.receive_steps():
                    if step.is_complete_response:
                        review_result = step.content

                if "APPROVE" in review_result.upper():
                    state.write("ralph", {"active": False, "status": "completed",
                                           "iteration": iteration + 1})
                    return f"Completed after {iteration + 1} iterations.\n{impl_result}"

                # REVIEW 反馈已自动进入 Conversation history
                # 下一轮 executor 会看到完整历史（包括 reviewer 的反馈）
                await conv.send(
                    f"--- FIX BASED ON REVIEW ---\n"
                    f"Address the review feedback above. Fix the issues and re-verify."
                )

            state.write("ralph", {"active": False, "status": "max_iterations_reached"})
            return f"Max iterations ({self.config.max_iterations}) reached."
```

### 6.2 Team — 使用 L1 Agent 并行 + 协调器

```python
# src/zero_g/skills/team/coordinator.py
"""Team 协调器：文件锁 + 分区策略。"""
from __future__ import annotations
import fcntl
from pathlib import Path


class TeamCoordinator:
    """协调并行 worker 的文件访问。"""

    def __init__(self, team_name: str, base_dir: Path | None = None):
        self.coord_dir = (base_dir or Path(".zero-g/coord")) / team_name
        self.coord_dir.mkdir(parents=True, exist_ok=True)

    def claim_partition(self, worker_id: str, files: list[str]) -> bool:
        """Worker 声明文件分区。如果文件已被其他 worker 声明，返回 False。"""
        lock_file = self.coord_dir / "partitions.json"
        with open(lock_file, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            content = f.read()
            partitions = json.loads(content) if content else {}
            # 检查冲突
            for claimed_file in files:
                current_owner = partitions.get(claimed_file)
                if current_owner and current_owner != worker_id:
                    fcntl.flock(f, fcntl.LOCK_UN)
                    return False
            # 声明所有权
            for file in files:
                partitions[file] = worker_id
            f.seek(0)
            f.truncate()
            json.dump(partitions, f)
            fcntl.flock(f, fcntl.LOCK_UN)
        return True

    def release_partition(self, worker_id: str) -> None:
        """Worker 完成后释放文件分区。"""
        lock_file = self.coord_dir / "partitions.json"
        if not lock_file.exists():
            return
        with open(lock_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            partitions = json.loads(f.read())
            partitions = {k: v for k, v in partitions.items() if v != worker_id}
            f.seek(0)
            f.truncate()
            json.dump(partitions, f)
            fcntl.flock(f, fcntl.LOCK_UN)
```

```python
# src/zero_g/skills/team/handler.py
from __future__ import annotations
import asyncio
import json
from zero_g.skills.base_skill import BaseSkill
from zero_g.core.agent_factory import create_agent
from zero_g.core.json_utils import extract_json
from zero_g.skills.team.coordinator import TeamCoordinator
from zero_g.tools.task_tools import TaskManager


class TeamSkill(BaseSkill):
    async def execute(self, task: str, context: dict) -> str:
        team_name = context.get("team_name", "default-team")
        worker_count = min(context.get("workers", 3), 10)  # 并发上限

        # Phase 1: 分解任务
        planner = create_agent("planner")
        async with planner:
            decompose_response = await planner.chat(
                f"Decompose this task into {worker_count} independent subtasks "
                f"with NON-OVERLAPPING file scopes:\n{task}\n\n"
                f"Output ONLY a JSON array, no other text:\n"
                f'[{{"subject": "...", "description": "...", "files": ["path1.py"]}}]'
            )
            raw_text = await decompose_response.text()

        # 使用 extract_json 安全解析
        subtasks = extract_json(raw_text)
        if not isinstance(subtasks, list):
            return f"Failed to decompose task: planner did not return a list."

        # Phase 2: 创建任务并分配分区
        task_mgr = TaskManager(team_name)
        coord = TeamCoordinator(team_name)
        work_items = []
        for i, sub in enumerate(subtasks[:worker_count]):
            task = task_mgr.create(sub["subject"], sub["description"], f"worker-{i+1}")
            assigned_files = sub.get("files", [])
            coord.claim_partition(f"worker-{i+1}", assigned_files)
            work_items.append({"worker_id": i+1, "task": task, "subtask": sub})

        # Phase 3: 并行执行（L1 Agent — 无需上下文连续性）
        async def run_worker(worker_id: int, task: dict, subtask: dict):
            executor = create_agent("executor")
            async with executor:
                response = await executor.chat(
                    f"You are worker-{worker_id} in team '{team_name}'.\n"
                    f"Subtask: {subtask['subject']}\n{subtask['description']}\n"
                    f"Only modify these files: {subtask.get('files', [])}\n"
                    f"Implement this independently."
                )
                result = await response.text()
                task_mgr.update(str(task["id"]), status="completed")
                coord.release_partition(f"worker-{worker_id}")
                return result

        results = await asyncio.gather(*[
            run_worker(w["worker_id"], w["task"], w["subtask"])
            for w in work_items
        ], return_exceptions=True)

        # Phase 4: 汇总
        output_parts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output_parts.append(f"Worker {i+1} FAILED: {result}")
            else:
                output_parts.append(f"Worker {i+1} completed:\n{result}")

        return f"Team '{team_name}' finished {len(results)} tasks:\n" + "\n---\n".join(output_parts)
```

## 7. 错误处理策略（新增）

```python
# src/zero_g/core/error_handling.py
"""全局错误处理模式。"""
from __future__ import annotations
import functools
import logging
from zero_g.core.state_manager import StateManager

logger = logging.getLogger("zero_g")


def skill_error_handler(skill_name: str):
    """装饰器：捕获 skill 执行异常，确保 state 被清理。"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Skill '{skill_name}' failed: {e}", exc_info=True)
                # 清理活跃 state，防止 stale lock
                StateManager().write(skill_name.replace("-", "_"), {
                    "active": False,
                    "error": str(e),
                })
                return f"Skill '{skill_name}' failed: {e}"
        return wrapper
    return decorator


# 用法：
# class RalphSkill(BaseSkill):
#     @skill_error_handler("ralph")
#     async def execute(self, task, context):
#         ...
```

## 8. 开发路线图（修订）

| Phase | 内容 | 预计 | 关键交付物 |
|-------|------|------|-----------|
| **0** | 项目初始化 | 1 天 | pyproject.toml, CI, 目录结构 |
| **1** | Core: ToolRegistry + AgentFactory + ConversationFactory | 1 周 | 可创建 L1/L2 agent，带正确的工具解析 |
| **2** | Core: SkillLoader (唯一模块名) + JSON utils | 3 天 | 可加载多个 skill 无冲突 |
| **3** | Core: StateManager (文件锁) + error handling | 3 天 | 状态持久化 + 异常清理 |
| **4** | Tools: state_tools + task_tools (修复 ID) | 3 天 | 任务 CRUD 正确工作 |
| **5** | Skill: Autopilot (L2 Conversation) | 1 周 | 第一个端到端多阶段 skill |
| **6** | Skill: Ralph (L2 Conversation + 循环验证) | 1 周 | 持久循环 + architect 审核 |
| **7** | Skill: Team (L1 Agent + Coordinator) | 2 周 | 并行 worker + 文件分区 |
| **8** | Skill: Deep-Interview + Plan | 2 周 | 需求澄清 + 共识规划 |
| **9** | Hooks: keyword router + stale cleanup | 3 天 | 关键词路由 + stale state 清理 |
| **10** | 用户自定义 skill 热加载 | 3 天 | skills/ 目录扫描 |
| **11** | 文档 + 示例 + PyPI 发布 | 1 周 | README + 3 个 demo + pip install |

## 9. 与 OMC 的关键差异

| 方面 | OMC (Claude Code) | Zero-G (Antigravity) |
|------|-------------------|----------------------|
| 语言 | JavaScript/TypeScript | Python |
| 多阶段 skill | 多个 Agent 实例 | L2 Conversation（单实例状态保持） |
| 并行 worker | Agent tool 后台运行 | L1 Agent + asyncio.gather |
| Agent 通信 | SendMessage (DM) | 共享文件状态 + 文件锁 |
| Agent 隔离 | worktree 隔离 | 文件分区（coordinator） |
| 模型选择 | claude-opus/sonnet/haiku | 待验证 GeminiConfig model 参数 |
| Skill 定义 | SKILL.md (markdown) | skill.yaml + handler.py (结构化) |
| Hook 机制 | settings.json hooks | SDK policies |
| MCP | 原生 | 原生 (McpStdioServer) |
| 错误处理 | 分散 | 统一 skill_error_handler 装饰器 |
| Stale state | 无处理 | 24h 过期 + SIGINT 清理 |

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `GeminiConfig` 不支持 model 参数 | 高 | 高 | 方案 A：单模型 + system_instructions 复杂度控制；方案 B：等待 SDK 更新 |
| SDK API 在 preview 阶段频繁变动 | 中 | 高 | 锁定 SDK 版本，抽象层隔离 API 变化 |
| Team 并行 worker 的 Gemini API 限流 | 中 | 中 | worker_count 上限 10 + 指数退避重试 |
| 文件锁在 NFS/网络文件系统不可靠 | 低 | 中 | 添加 lock timeout + stale lock 检测 |
| 用户自定义 skill 的安全性（无沙箱） | 中 | 中 | 文档警告 + 可选 whitelist 模式 |

## 11. 命名建议

**推荐：`zero-g`**

`pip install zero-g` — 简短，和 Antigravity 主题完美契合，npm/PyPI 命名空间冲突概率低。

---

## 参考资料

- [Google Antigravity SDK Python (GitHub)](https://github.com/google-antigravity/antigravity-sdk-python)
- [Google Antigravity Official Site](https://antigravity.google/)
- [Build with Google Antigravity — Google Developers Blog](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/)
- [Getting Started Codelab](https://codelabs.developers.google.com/getting-started-google-antigravity)
- [Antigravity Official Docs](https://antigravity.google/docs/home)
- [oh-my-claudecode (GitHub)](https://github.com/Yeachan-Heo/oh-my-claudecode)
- [Antigravity Skills 配置](https://www.cnblogs.com/hujunwei/p/19681886)
- [Spec-Driven ADK Agent Development](https://codelabs.developers.google.com/sdd-adk-antigravity?hl=zh-cn)
