# TEMPLATE - data-pipeline

## Global Rules
- [GLOBAL] 文档优先：先更新 `PRD` / 系统文档 / `IPP`，再编码。
- [GLOBAL] `.md` 文件修改可直接执行；非 `.md` 改动遵循确认触发词。
- [GLOBAL] 触发词：仅 `【确认】`、`【直接】` 生效。

## Type Focus
- 关注数据模式、处理阶段边界、质量校验与审计日志。
- 变更应说明兼容策略与回填/回滚方案。

## Agent Output Contract
- 必须同步更新：`AGENTS.md` 与 `.github/copilot-instructions.md`。
- 若规则冲突，先提问用户，不自动覆盖。
