# Product Requirements Document (PRD) — zero-gravity

## 1. 产品定义与定位

`zero-gravity`（简称 ZG）是一个专门为 **Google Antigravity CLI** 设计的多智能体编排开发插件。它以 oh-my-claudecode (OMC) 为蓝图，将团队协作、渐进式规划、自动化执行与测试修复的开发模式移植到 Antigravity SDK 中。

该产品由两部分组成：
1. **上层交互层 (CLI Plugin Wrapper)**：定义 `/zero-gravity:zg-setup` 和 `/zero-gravity:zg-run` 命令，充当用户在 Antigravity 终端中调用的入口。
2. **底层核心计算层 (zero_g Python Library)**：在 `src/zero_g` 下实现基于 Antigravity SDK L1/L2 的核心逻辑（状态管理、双 API 策略、工具注册表和多智能体协调引擎）。

---

## 2. 核心功能需求

### 2.1 引导与初始化 (`zg-setup`)
* **需求**：用户输入 `/zero-gravity:zg-setup` 时，必须自动化初始化开发上下文。
* **交付物**：
  * 创建 `.zg/` 状态控制目录。
  * 自动写入 `.zg/state.json`（状态机追踪）和 `.zg/tasks.md`（人类可读进度）。
  * 在项目根目录注入 `ANTIGRAVITY.md` 指引文件，包含项目规范、测试运行指令，使 Agent 在后续会话中能自动理解环境。

### 2.2 渐进确认编排流 (Gradual Confirmation Flow)
* **阶段一：规划 (Planning)**：
  * 主 Agent 启动 L2 Conversation 切换至 `Architect` 角色，分析需求，生成 `implementation_plan.md`。
  * **必须暂停**，将计划展示给用户，由用户进行确认或反馈。
* **阶段二：执行 (Execution)**：
  * 得到用户同意后，状态机转移至 `execution`。
  * 唤醒 `Executor` 子智能体进行精准代码修改，遵从 `ANTIGRAVITY.md` 的代码质量标准。
* **阶段三：验证 (Verification & Correction)**：
  * 转移至 `verification` 状态。
  * 唤醒 `Tester` 子智能体自动运行测试套件（如 `pytest`），检测编译和语法错误。
  * 若测试失败，自动进入 `correction` 状态，循环调用 `Executor` 修复，上限 3 次，若依然失败则暂停向用户报告。
* **阶段四：收尾 (Completion)**：
  * 验证成功后，由 `Tester` 自动编写 `walkthrough.md` 变更报告，更新 `.zg/tasks.md` 状态为 100% 完成，结束会话。

### 2.3 状态持久化与断点续传 (State & Recovery)
* **需求**：防止大模型上下文 Compact（压缩）或会话中断导致任务丢失。
* **持久化策略**：
  * `state.json` 用于程序内部读取（包括 `current_stage`、`active_subagent`、`iteration_count` 等）。
  * `tasks.md` 实时渲染为 Markdown 复选框，便于用户一目了然。
* **Stale Cleanup**：自动检测超过 24 小时的活跃状态并将其设为非活跃状态，防止状态死锁。

---

## 3. 技术设计准则与 API 取舍

### 3.1 双 API 策略 (Dual API Strategy)
* **L2 Conversation**：用于多阶段顺序 Skill。因为需要保持对话上下文的连贯性，并且能频繁在同一个会话中切换 system instructions。
* **L1 Agent**：用于独立的并行子任务以及 CLI 的交互主循环。

### 3.2 错误隔离与文件锁
* 并发执行（例如在 Team 模式下的多 Workers）时，必须通过 `TeamCoordinator` 使用文件锁限制 Worker 只能修改各自的分区文件，避免竞争冒险 (Race Conditions)。
* 采用 `skill_error_handler` 装饰器统一捕获运行时异常，确保即使脚本中途崩溃，也必须将 `.zg/state.json` 的 `active` 设为 `false`，从而释放状态锁。

---

## 4. 交付计划与里程碑

* **Milestone 1**: 核心架构层实现（`ToolRegistry` + `AgentFactory` + `ConversationFactory` + `json_utils`）并通过单元测试验证。
* **Milestone 2**: 状态持久化与 CLI 插件绑定（`/zero-gravity:zg-setup` 命令与 `StateManager` 文件锁功能联调）。
* **Milestone 3**: 单 Agent 顺序编排 Skill 实现（`Autopilot` & `Ralph` 工作流交付）。
* **Milestone 4**: 多 Agent 并行 Team 协作模式集成测试与验收。
