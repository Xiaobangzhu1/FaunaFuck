# 系统设计：细胞行为（Cell Behavior）

## 1. 文档目的

定义细胞在模拟中的行为规则与状态变化条件。  
本文件不定义 UI 视觉规范，不定义实施任务分解。

## 2. 范围

- DNA→RNA 规则入口
- RNA 指令执行行为
- 移动、繁殖、死亡、通道读写

## 3. 相关对象 / 变量

- `Cell.gene_DNA`
- `Cell.gene_RNA`
- `Cell.ribosome`
- `Cell.channel`
- `Cell.dead / locked / age_ticks / direction`
- `CellConfig.death_neighbor_threshold`
- `CellConfig.reproduction_fail_rate`
- `MapConfig.width/height/channels/max_instructions`

## 4. 系统规则

- 触发条件：细胞在每帧执行行为，或收到命令改变参数。
- 处理规则：
  - DNA 按 MODE2 转录为 RNA（映射表见 `docs/DNA_RULES.md`）。
  - RNA 指令驱动移动、繁殖、自杀、条件跳转、channel 切换。
  - 复制（繁殖）指令每次执行都有概率失败（由 `CellConfig.reproduction_fail_rate` 定义）；失败时该指令直接结束，不生成子代。
  - 繁殖默认优先尝试父细胞当前朝向方向生成子代。
  - 若优先方向不可用，再尝试其他可用位置。
  - 死亡判定除 `.` 指令外，还受邻域计数阈值控制。
- 状态变化：
  - 执行移动后更新位置；`direction` 记录移动方向。
  - 满足死亡条件时置为死亡。
  - 年龄与核糖体位置按帧推进。
- 输出反馈：
  - 位置、数量、颜色、日志变化。
- 例外情况：
  - 越界移动失败但消耗指令。
  - 概率失败的复制指令不生成子代并跳过，不抛出异常。
  - 无可用空位时繁殖失败但消耗指令。
  - 邻域定义历史曾调整，若与其他文档冲突统一标 `待确认`。

## 5. 输入 / 输出

- 玩家输入：
  - `spawn`、`set CellConfig.*` 等影响细胞行为参数
- 系统输入：
  - DNA、当前状态、配置阈值、NTs 数值
- 系统输出：
  - 新细胞状态、可能新增子代或死亡事件
- 可视化反馈：
  - 细胞位置与颜色变化
  - 面板/日志中的行为结果

## 6. 关键流程

1. 细胞解锁并进入本帧执行。  
2. 执行死亡前检查（邻域阈值）。  
3. 按 RNA 指令推进行为。  
4. 执行行为后再次死亡检查。  
5. 写回世界状态与可视化结果。  

## 7. 待确认问题

- 死亡邻域在历史阶段经历过“对角四格/正交四格”变更，最终规范需统一单一来源。
- `direction` 仅作为行为记录还是后续功能输入，目前未完全锁定。
- 繁殖时“优先方向不可用后”的后续尝试顺序（固定顺序/随机顺序）待确认。

## 8. 与其他文档的关系

- 转录映射细节见 `docs/DNA_RULES.md`。
- 实体字段定义见 `docs/system-entities-and-state.md`。
- 运行控制节奏见 `docs/system-core-loop.md`。
