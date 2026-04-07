# SEED - Agent Bootstrap Spec

## 1. Metadata

- seed_name: `Fauna SEED`
- seed_version: `1.1.0`
- agents_version: `1.1.0`
- last_synced_at: `2026-03-22`
- project_type: `生态箱模拟 / 游戏化交互（Pygame）`
- supported_project_types: `game-sim`, `backend-service`, `automation-script`, `data-pipeline`
- source_repo: `https://github.com/Xiaobangzhu1/Agent_Seed`
- target_project: `FaunaFuck`
- target_repo: `https://github.com/Xiaobangzhu1/FaunaFuck`
- language: `中文为主`

## 2. Project Direction (High-Level)

- 核心方向：DNA -> RNA 驱动的细胞自动机模拟，强调“可观察、可干预、可复现”。
- 交互形态：游戏式生态箱界面（地图 + 侧栏控制），运行中支持命令输入与反馈。
- 目标能力：
  - 细胞投放、运行控制、规则调整、日志反馈
  - 支持存档/读档与关键行为回归验证
  - 文档主权清晰：PRD 高层、系统文档规则、IPP 任务

## 2.1 Multi-Project Type Catalog (for AGENT Generation)

- `game-sim`（游戏/模拟类）
  - 关注：主循环、交互输入、渲染反馈、性能与回归可观察性
- `backend-service`（后端服务类）
  - 关注：接口契约、配置/环境隔离、错误处理、日志与可观测性
- `automation-script`（脚本/工具类）
  - 关注：参数输入、幂等性、失败重试、输出结果稳定性
- `data-pipeline`（数据流程类）
  - 关注：数据模式、处理阶段、质量校验、回滚与审计日志

当项目类型不在上述列表内时：
- 新智能体必须先提问确认类型边界，再生成 AGENT。

## 3. AGENT Core Rules (Must Preserve)

- 流程规则：
  - 默认先更新 `docs/PRD.md` + `docs/IMPLEMENTATION_PLAN.md`，待用户 `【确认】` 再编码。
  - 若用户输入严格包含 `【直接】`，可在更新文档后直接实现。
- 同步规则：
  - `AGENTS.md` 与 `.github/copilot-instructions.md` 必须同步。
  - `SEED.md` 与 `AGENTS.md` 必须按版本同步。
  - 若 `SEED` / `AGENTS` 版本或规则冲突，必须先询问用户，禁止自动覆盖。
  - 本地 `AGENTS.md` 每次变更都应立即形成“回流提案”。
  - 回流仅接受人工标记 `[GLOBAL]` 的条目；未标记条目视为项目私有规则。
- 工程规则：
  - 改代码前先改文档；偏离 PRD/IPP 必须记录原因。
  - 完成后更新 `docs/progress.txt`（时间、任务、问题、解决）。
  - Git 提交信息使用中文。

## 4. How A New Agent Should Generate AGENT

拿到本 `SEED.md` 后，按以下流程自动生成目标项目的 `AGENTS.md`：

1. 先询问项目类型（必须）
- 标准问题：`当前项目属于哪一类？game-sim / backend-service / automation-script / data-pipeline / 其他`
- 若用户回答“其他”，继续追问 1-2 个边界问题后再归类。

2. 读取项目上下文
- 识别项目类型、主要语言、入口文件、文档结构。
- 优先读取：`docs/PRD.md`、`docs/IMPLEMENTATION_PLAN.md`、系统设计文档、现有 `AGENTS.md`（若存在）。

3. 生成 AGENT 草案（最小可执行）
- 固定保留本 SEED 的核心规则（流程、同步、冲突处理）。
- 结合已确认的项目类型，插入对应类型的重点约束模板。
- 将项目专属规则写入“补充约定”。
- 明确触发词语义（`【确认】` / `【直接】`）。

4. 校验与去冲突
- 对比 `AGENTS.md`、`.github/copilot-instructions.md`、`SEED.md`。
- 若规则冲突：标记冲突点并提问用户，不自动合并。

5. 输出与落盘
- 更新 `AGENTS.md`。
- 同步更新 `.github/copilot-instructions.md`。
- 若结构变化，更新 `STRUCTURE.md`。
- 若本地 `AGENTS.md` 有变化，产出一次“回流提案”清单（仅列 `[GLOBAL]` 条目）。

## 5. Unknown Handling Protocol (Ask-First)

新智能体遇到以下情况必须先提问：

- 需求存在多种实现路径且影响较大（架构、数据格式、兼容策略）。
- 文档间规则冲突（PRD / 系统文档 / IPP / AGENTS / SEED）。
- 用户输入不满足触发词规则但要求直接改代码。
- 仓库写权限、远端地址、发布策略不明确。

提问格式要求：

- 用最少问题获得决策信息（1-3 个）。
- 问题必须可执行、可二选一或给清晰选项。
- 用户未确认前，不执行高风险或不可逆操作。

## 6. Version Sync Policy

- 建议在 `SEED.md` 与 `AGENTS.md` 都维护以下字段：
  - `seed_version`
  - `agents_version`
  - `last_synced_at`
- 同步触发条件：
  - 任一规则变更
  - 流程触发词变更
  - 文档主权边界变更
- 冲突策略：
  - 先记录冲突，再询问用户。
  - 用户未明确前，保持现状，不覆盖文件。

## 7. Minimal AGENT Template Output (for New Agent)

新智能体可基于下述骨架生成 `AGENTS.md`：

```md
## 总原则
- 文档先行（PRD + IPP），确认后编码；`【直接】`例外。

## 文件与同步要求
- AGENTS 与 copilot-instructions 双向同步。
- SEED 与 AGENTS 按版本同步；冲突先询问用户。

## 指令与触发词
- 仅 `【确认】`、`【直接】` 生效。

## 实现约束
- 代码与文档一致；偏离需记录。
- 完成后更新 progress。
```

## 8. Notes

- 本 SEED 作为“跨项目可复用的智能体启动规范”。
- 若目标项目无现成文档，先通过问答补齐最小 PRD/IPP 再实现。
- 模板库目录：`templates/`（按项目类型）与 `examples/`（示例输出）。
