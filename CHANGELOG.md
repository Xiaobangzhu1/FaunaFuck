# Agent_Seed Changelog

## 1.1.0 - 2026-03-22
- 新增模板库目录 `templates/`，首版覆盖：
  - `game-sim`
  - `backend-service`
  - `automation-script`
  - `data-pipeline`
- 新增示例目录 `examples/`，提供 game-sim 产物示例。
- 固化优先级：`!用户命令 > SEED > AGENTS > 普通用户命令 > PRD/IPP`。
- 固化回流机制：
  - 本地 `AGENTS.md` 每次变更都要产生回流提案
  - 仅 `[GLOBAL]` 标记条目可回流到 `Agent_Seed`
- 增加版本字段：`seed_version`、`agents_version`、`last_synced_at`。

## 1.0.0 - 2026-03-22
- 初始化 `SEED.md`。
- 定义跨项目 AGENT 生成基础流程与冲突提问协议。
