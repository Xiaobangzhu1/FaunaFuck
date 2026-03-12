# FRONTEND_GUIDELINES - Pygame 显示规范

## 1. 窗口设置

### 1.1 窗口尺寸
```python
SCALE = 6  # DispConfig.scale 默认值
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 630
TICK_RECT = (0, 0, 600, 30)      # 左侧 tick 顶栏
MAP_RECT = (0, 30, 600, 600)     # 左侧主地图
PANEL_RECT = (600, 0, 600, 630)  # 右侧交互区
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF, vsync=1)
```

### 1.2 帧率控制
```python
clock = pygame.time.Clock()
clock.tick(DispConfig.fps)  # 默认 60 FPS
```

## 2. 渲染流程

### 2.1 双缓冲渲染架构
```
左侧 Tick 顶栏 (600x30) + 地图子表面 (600x600) → 右侧面板绘制 (600x630) → 显示
```

### 2.2 右侧交互区文本规范
- 右侧不显示 tick 信息。
- 右侧说明文案需覆盖快捷键与核心命令示例。
- 输入与消息文本需支持自动换行，避免超出面板宽度。
- 快捷键仅在输入框为空时触发；输入框有内容时按键用于编辑。
- 支持 `dna` 命令打开 DNA 转录规则浮窗。
- DNA 规则浮窗支持独立快捷键 `/` 与右侧按钮打开。
- `tick` 在左侧地图上方独立条显示，不覆盖地图内容。

### 2.2 核心渲染函数 (drawer.py)
| 函数 | 用途 |
|------|------|
| `render_frame(target, world)` | 主渲染入口，处理缩放 |
| `draw_cells(surface, cells)` | 绘制所有细胞 |
| `draw_cell_on(surface, x, y)` | 单像素绘制细胞 |
| `draw_NTs_map(surface, NTs_map)` | 绘制神经递质图层 |
| `draw_tick(surface, tick)` | 绘制帧计数器 |

## 3. 颜色规范

### 3.1 统一色系（Forest Console）
| Token | Hex | RGB | 用途 |
|------|-----|-----|------|
| `bg.base` | `#0B1210` | (11, 18, 16) | 主背景 |
| `bg.panel` | `#13201C` | (19, 32, 28) | 侧栏面板 |
| `bg.card` | `#1A2A24` | (26, 42, 36) | 浮窗/卡片 |
| `border` | `#2D4A3F` | (45, 74, 63) | 边框 |
| `text.primary` | `#E6F1EC` | (230, 241, 236) | 主文字 |
| `text.secondary` | `#A8C0B4` | (168, 192, 180) | 次级文字 |
| `accent.primary` | `#4FCB8D` | (79, 203, 141) | 主高亮 |
| `accent.hover` | `#66DDA1` | (102, 221, 161) | 强调/悬停 |
| `accent.muted` | `#2F8F68` | (47, 143, 104) | 弱高亮 |
| `state.error` | `#E25555` | (226, 85, 85) | 错误态 |
| `state.warning` | `#F2B544` | (242, 181, 68) | 警告态 |
| `state.info` | `#58A6FF` | (88, 166, 255) | 信息态 |
| `state.success` | `#4FCB8D` | (79, 203, 141) | 成功态 |

### 3.2 细胞颜色规则
- 非空 RNA 细胞按 3 档离散颜色显示：
  - 最年轻（刚生成）: `#4CC9F0`
  - `1 tick` 后: `#4361EE`
  - `2 tick+` 后: `#7209B7`
- `len(gene_RNA) == 0` 时使用 `state.error` 覆盖年龄渐变。
- 有方向细胞使用箭头叠加显示方向：`w=↑`、`a=←`、`s=↓`、`d=→`。
- 无方向（`None`）细胞仅显示底色方块。

## 3.3 控制台输入增强
- 回退指令：`undo`（回填上一条已执行命令到输入框，不改变世界状态）。
- 复制粘贴指令：`copy`、`paste`。
- 日志指令：`log5`（调出最近 5 分钟日志，导出 `logs/recent_5m.log`）。
- 快捷键：`Ctrl/Cmd + C` 复制、`Ctrl/Cmd + V` 粘贴、`Ctrl/Cmd + Z` 执行 `undo`。
- 约束：`back` 继续用于“模拟帧回退”，不与 `undo` 混用。

## 4. DNA 规则浮窗
- 类型：游戏内浮动子窗口（非模态）。
- 打开：输入 `dna` 命令，或使用快捷键 `/`，或点击右侧按钮。
- 关闭：`ESC` 或浮窗右上角关闭按钮。
- 拖动：鼠标左键按住浮窗标题栏拖动。
- 边界：浮窗需保留可关闭区域，不能完全拖出窗口。
- 尺寸：按内容自适应，超出高度时在窗口内截断显示。
- 文案来源：`docs/DNA_RULES.md`（MODE2-only）。

## 5. 坐标系统

### 5.1 逻辑坐标
- 原点 (0, 0) 在左上角
- X轴向右增加，Y轴向下增加
- 范围: [0, width) × [0, height)

### 5.2 环绕处理
```python
ix = int(x) % MapConfig.width
iy = int(y) % MapConfig.height
```

## 6. 渲染层级 (从底到顶)
1. 背景填充 (黑色)
2. NTs神经递质图层 (可选)
3. 细胞层
4. UI层 (交互面板、DNA浮窗等)

## 7. 性能优化

### 7.1 已采用优化
- `pygame.DOUBLEBUF` 双缓冲
- `vsync=1` 垂直同步
- 基础画布绘制后统一缩放

### 7.2 注意事项
- 避免在主循环中创建新Surface
- 使用 `surface.set_at()` 进行单像素操作
- NTs渲染使用 `numpy` 批量处理后转Surface

## 8. 示例代码

### 8.1 主循环
```python
while running:
    clock.tick(DispConfig.fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    if world.update(screen) is False:
        running = False

    pygame.display.flip()
```

### 8.2 细胞绘制
```python
def draw_cell_on(surface, x, y, color):
    ix = int(x) % MapConfig.width
    iy = int(y) % MapConfig.height
    surface.set_at((ix, iy), color)
```
