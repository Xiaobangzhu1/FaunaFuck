# TEMPLATE - automation-script

## Global Rules
- [GLOBAL] 文档优先：先更新 `PRD` / 系统文档 / `IPP`，再编码。
- [GLOBAL] `.md` 文件修改可直接执行；非 `.md` 改动遵循确认触发词。
- [GLOBAL] 触发词：仅 `【确认】`、`【直接】` 生效。

## Type Focus
- 关注参数校验、幂等性、失败重试与输出稳定性。
- 明确脚本副作用范围与失败回滚策略。

## Agent Output Contract
- 必须同步更新：`AGENTS.md` 与 `.github/copilot-instructions.md`。
- 若规则冲突，先提问用户，不自动覆盖。
