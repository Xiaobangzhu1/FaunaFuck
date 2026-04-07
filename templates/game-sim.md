# TEMPLATE - game-sim

## Global Rules
- [GLOBAL] 文档优先：先更新 `PRD` / 系统文档 / `IPP`，再编码。
- [GLOBAL] `.md` 文件修改可直接执行；非 `.md` 改动遵循确认触发词。
- [GLOBAL] 触发词：仅 `【确认】`、`【直接】` 生效。

## Type Focus
- 关注主循环稳定性、输入响应与渲染可观察性。
- 关键改动需提供最小可复现验证（帧控制、状态变化、日志反馈）。

## Agent Output Contract
- 必须同步更新：`AGENTS.md` 与 `.github/copilot-instructions.md`。
- 若规则冲突，先提问用户，不自动覆盖。
