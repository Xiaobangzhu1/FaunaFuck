# 文档索引（PRD / 系统设计 / IPP）

## 1. 文档树

- `README.md`：仓库入口（项目简介、启动方式、测试方式、文档入口）
- `docs/PRD.md`：高层需求（做什么/为什么/成功标准）
- `docs/system-core-loop.md`：核心循环设计
- `docs/system-entities-and-state.md`：实体与状态设计
- `docs/system-cell-behavior.md`：细胞行为设计
- `docs/system-visualization-and-debug.md`：可视化与调试设计
- `docs/system-rules-and-edge-cases.md`：规则冲突与边界情况
- `docs/DNA_RULES.md`：DNA 转录规则（MODE2）
- `docs/IMPLEMENTATION_PLAN.md`：实施计划（任务顺序/依赖/验证）
- `docs/archives/prd-history.md`：历史目标与收尾事项归档
- `docs/FRONTEND_GUIDELINES.md`：前端渲染规范（与系统文档冲突处需标 `待确认`）
- `docs/architecture-example-seed-driven-governance.md`：SEED 驱动三层治理架构示例
- `docs/progress.txt`：进度记录
- `docs/lessons.md`：报错原因与解决方案

## 2. 阅读顺序建议

1. `docs/PRD.md`（理解项目定位与成功标准）
2. `README.md`（查看仓库入口、运行方式与文档导航）
3. 系统设计文档（按主题阅读）
4. `docs/DNA_RULES.md`（转录映射细节）
5. `docs/IMPLEMENTATION_PLAN.md`（看实现顺序与验证）
6. `docs/archives/prd-history.md`（只看历史背景时再读）

## 3. 边界说明

- `PRD`：定义高层目标与成功标准，不展开细节规则。
- `系统设计文档`：定义规则细节、状态、输入输出、边界与冲突项。
- `IPP`：定义任务拆解、实现顺序、依赖与验证，不重新解释规则。

## 4. 规则主权

- 规则细节主权：系统设计文档。
- 高层目标主权：PRD。
- 任务执行主权：IPP。
- 若冲突：先标记 `待确认`，不得直接实现。
