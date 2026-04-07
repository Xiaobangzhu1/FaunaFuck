# 架构示例：SEED 驱动的三层治理架构

## 1. 目标

给出一个可直接复用的架构设计案例，解决以下问题：
- 如何在不同项目中复用同一套协作规则
- 如何避免“全局规则”和“项目私有规则”相互污染
- 如何让新智能体拿到 `SEED` 后稳定生成 `AGENTS`

## 2. 三层架构

### Layer A - 治理层（Global Governance）
- 载体：`SEED.md`（位于 `Agent_Seed` 仓库）
- 职责：
  - 定义跨项目统一规则（触发词、优先级、同步策略、冲突策略）
  - 定义项目类型目录与模板选择入口
  - 定义回流规则（仅 `[GLOBAL]` 可回流）
- 输出：
  - 模板库 `templates/*.md`
  - 示例 `examples/*.md`

### Layer B - 项目协作层（Project Collaboration）
- 载体：`AGENTS.md` + `.github/copilot-instructions.md`
- 职责：
  - 将治理层规则实例化到当前项目
  - 添加项目私有协作约束（不回流）
  - 保持双文件逐条同步
- 输出：
  - 当前项目的执行规则与触发词语义

### Layer C - 产品实现层（Product Delivery）
- 载体：`docs/PRD.md`、`docs/system-*.md`、`docs/IMPLEMENTATION_PLAN.md`
- 职责：
  - 定义产品目标、系统规则、任务分解与验收
  - 承接项目协作层规则，落到具体实现
- 输出：
  - 可执行的开发与验证闭环

## 3. 数据流与控制流

1. 下行同步（SEED -> 项目）
- 输入：`SEED.md + templates/<project-type>.md`
- 过程：
  - 先询问项目类型
  - 生成/更新 `AGENTS.md` 与 `.github/copilot-instructions.md`
  - 写入 `seed_version / last_synced_at`
- 输出：项目可执行协作规则

2. 上行回流（项目 -> SEED）
- 输入：本地 `AGENTS.md` 变更
- 过程：
  - 每次变更即时产出回流提案
  - 仅提取 `[GLOBAL]` 条目
  - 提交到 `Agent_Seed`
- 输出：治理层增量优化

## 4. 冲突处理

固定优先级：
`带 ! 的用户命令 > SEED > AGENTS > 不带 ! 的用户命令 > PRD/IPP`

冲突处理协议：
- `SEED` 与 `AGENTS` 冲突：先提问用户，不自动覆盖
- `AGENTS` 与项目文档冲突：先标记 `待确认`
- 未标记 `[GLOBAL]` 的项目规则：不得回流到 `SEED`

## 5. 设计收益（为什么有效）

- 规则主权清晰：全局规则与项目规则不混杂
- 演进可控：通过 `[GLOBAL]` 控制回流范围
- 可复制：新项目只需“问类型 -> 套模板 -> 同步双文件”
- 可审计：版本字段与提案链路可追溯

## 6. 验收清单（可直接执行）

- [ ] 新项目可通过一次“项目类型问答”生成 `AGENTS.md` 与 `.github/copilot-instructions.md`
- [ ] 两文件规则逐条一致
- [ ] 当本地 `AGENTS.md` 变更时，能产出回流提案
- [ ] 回流提案仅包含 `[GLOBAL]` 条目
- [ ] 出现 `SEED`/`AGENTS` 冲突时，系统先提问而非覆盖
