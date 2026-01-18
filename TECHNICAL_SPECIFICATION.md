# FaunaFuck 项目技术规格文档

**版本**: 1.0  
**日期**: 2026-01-18  
**目标**: 用于指导 AI 将此 Python 项目翻译为其他编程语言

---

## 🎯 项目概述

### 核心理念
FaunaFuck 是一个**细胞自动机进化模拟器**，其中每个"细胞"都是一个执行遗传程序的虚拟生命体。系统灵感来源于 Brainfuck 编程语言和生物学的 DNA→RNA 转录过程。

### 关键特性
1. **遗传编程**: 细胞通过 DNA 序列编码行为
2. **转录机制**: DNA → RNA → 指令执行（模拟生物学中心法则）
3. **进化系统**: 繁殖 + 变异 → 种群进化
4. **环境交互**: 256 通道神经递质网格作为环境信息载体
5. **实时可视化**: Pygame 渲染细胞和环境状态

---

## 📐 系统架构

```
                    ┌─────────────────────────────────┐
                    │         main.py                 │
                    │  (主循环 + Pygame 事件处理)       │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────────────┐
                    │        world.py                 │
                    │ (世界管理器 - 协调所有系统)        │
                    └─┬────────┬─────────┬───────────┘
                      │        │         │
         ┌────────────▼──┐ ┌──▼──────┐ ┌▼──────────────┐
         │   cell.py     │ │ NTs.py  │ │ drawer.py     │
         │ (细胞生命)     │ │(环境信息)│ │ (渲染系统)     │
         └───────┬───────┘ └─────────┘ └───────────────┘
                 │
         ┌───────▼──────────────┐
         │ DNA_processing.py    │
         │ (遗传算法 + 转录)     │
         └──────────────────────┘
```

### 数据流
```
1. 初始化: Cell.initialize_cells() → 生成初始细胞群
2. 每帧循环:
   a) world.update() → 更新所有细胞状态
   b) cell.act() → 每个细胞执行 RNA 指令
   c) DNA_processing.mutate_DNA() → 繁殖时变异
   d) drawer.render_frame() → 渲染到屏幕
3. 存档: world.save_world_state() → 保存状态
```

---

## 📦 模块详细规格

---

### 1. `config.py` - 配置管理

#### 目的
集中管理所有全局配置参数，避免硬编码。

#### 数据类

##### `MapConfig` - 地图配置
```python
class MapConfig:
    width: int = 100          # 世界宽度（格子数）
    height: int = 100         # 世界高度（格子数）
    channels: int = 256       # 神经递质通道数（每个格子有 256 层信息）
    max_instructions: int = 1000  # 每帧每细胞最大执行指令数
```

**用途**: 定义模拟世界的物理尺寸和信息容量。

---

##### `DispConfig` - 显示配置
```python
class DispConfig:
    fps: int = 60           # 目标帧率
    scale: int = 4          # 渲染缩放倍数（1 格子 = scale × scale 像素）
```

**用途**: 控制渲染性能和显示效果。

---

##### `CellConfig` - 细胞配置
```python
class CellConfig:
    debug_mode: bool = False              # 调试模式（输出详细日志）
    die_mode: int = 3                     # 死亡条件模式
    gene_DNA: str = '<>!?!?><'           # 初始 DNA 序列
    original_num: int = 10                # 初始细胞数量
    pure_mode: bool = False               # 纯净模式（只生成 1 个细胞）
    skip_transcript: bool = False         # 跳过转录（直接用 RNA）
    ribosome_loop: bool = False           # RNA 执行完是否循环
    
    # 变异概率
    base_muatation_rate: float = 1e-3     # 单碱基突变率（每个碱基）
    gene_mutation_rate: float = 1e-4      # 基因片段重组率
    
    # 繁殖设置
    randomize_reproduction_direction: bool = True  # 随机选择子代位置
    
    # 亚培养（自定义初始种群）
    cell_subculture: list[tuple[str, int]] | None = None  # [(DNA, 数量), ...]
    cell_subculture_survive_rate: float = 1.0
```

**用途**: 控制细胞行为、变异率、初始条件等核心参数。

---

##### `SaveConfig` - 存档配置
```python
class SaveConfig:
    autosave_interval: int = 5000         # 自动保存间隔（tick 数）
    autosave_dir: str = "saves"           # 存档文件夹
    autosave_prefix: str = "autosave_"    # 存档文件名前缀
    
    read: bool = True                     # 是否读取存档
    read_tick: int = 450000               # 读取指定 tick 的存档（0=最新）
    read_path: str = "saves/autosave_tick_450000.txt"
```

**用途**: 管理自动保存和加载功能。

---

##### `LogConfig` - 日志配置
```python
class LogConfig:
    enable: bool = True                   # 是否启用日志
    level: str = "INFO"                   # 日志级别
    file: str = "logs/fauna.log"          # 日志文件路径
    rotate_max_bytes: int = 2_000_000     # 日志文件最大 2MB
    rotate_backup_count: int = 1          # 保留备份数
    snapshot_minutes: int = 5             # 每 5 分钟创建快照
    snapshot_backup_count: int = 2        # 快照保留数
```

**用途**: 控制日志系统行为。

---

### 2. `NTs.py` - 神经递质系统

#### 目的
管理一个 **3 维数组** `(width+1, height+1, 256)`，作为细胞的环境信息载体。每个格子有 256 个通道（类似颜色通道），细胞可以读写这些值。

#### 类: `NTs`

##### 数据结构
```python
class NTs:
    map: np.ndarray  # shape = (width+1, height+1, 256), dtype = uint8
```

**说明**:
- `map[x, y, channel]` 表示位置 `(x, y)` 的第 `channel` 通道的值（0-255）
- 类似"神经递质浓度"，细胞可以通过 `+` 增加、`-` 减少

---

##### 方法规格

###### `__init__(self)`
```python
def __init__(self):
    self.map = np.zeros((MapConfig.width + 1, MapConfig.height + 1, MapConfig.channels), dtype=np.uint8)
```

**功能**: 创建一个全零的神经递质网格。

**返回**: 无

---

###### `initialize_NTs(cls, map=None) -> NTs` (类方法)
```python
@classmethod
def initialize_NTs(cls, map=None) -> 'NTs':
    if map is not None:
        NTs_instance = NTs()
        NTs_instance.set_map(map)
        return NTs_instance
    return NTs()
```

**功能**: 工厂方法，可选择性地从已有数组初始化。

**参数**:
- `map: np.ndarray | None` - 预加载的 3D 数组（用于加载存档）

**返回**: `NTs` 实例

**用途**: 启动时创建环境，或从存档恢复。

---

###### `draw(self, screen) -> None`
```python
def draw(self, screen: pygame.surface.Surface) -> None:
    # 将 channel 0 归一化为灰度图
    normalized = (self.map[:, :, 0] != 0) * 255
    grayscale_image = np.stack([np.zeros_like(normalized), normalized, np.zeros_like(normalized)], axis=-1)
    surface = pygame.surfarray.make_surface(grayscale_image.swapaxes(0, 1))
    screen.blit(surface, (0, 0))
```

**功能**: 将第 0 通道的神经递质可视化为绿色图像。

**参数**:
- `screen: pygame.Surface` - 渲染目标

**返回**: 无

**注意**: 当前实现只显示第 0 通道。

---

### 3. `cell.py` - 细胞类

#### 目的
表示单个细胞，包含：
- **遗传信息**: DNA 序列 → 转录为 RNA → 执行指令
- **物理状态**: 位置 `(x, y)`、当前通道 `channel`
- **执行器**: 核糖体指针 `ribosome` 逐条执行 RNA

#### 类: `Cell`

##### 数据结构
```python
class Cell:
    x: float                    # X 坐标
    y: float                    # Y 坐标
    channel: int                # 当前操作的神经递质通道（0-255）
    gene_DNA: str               # DNA 序列（字符串）
    gene_RNA: List[str]         # RNA 指令列表
    ribosome: int               # 当前执行的 RNA 指令索引
    transcripted_flag: bool     # 是否已转录
    locked: bool                # 新生细胞保护锁（1 帧无敌）
    dead: bool                  # 是否死亡
    NTs: NTs                    # 引用全局神经递质
    world: World                # 引用世界对象
    logger: logging.Logger      # 日志记录器
```

---

##### 方法规格

###### `__init__(self, x, y, gene_DNA, NTs, world)`
```python
def __init__(self, x: float, y: float, gene_DNA: str, NTs: 'NTs', world: 'World'):
    self.x = x
    self.y = y
    self.channel = 0
    self.gene_DNA = gene_DNA
    self.gene_RNA = []
    self.transcripted_flag = False
    self.transcript()  # 立即转录
    self.ribosome = 0
    self.NTs = NTs
    self.world = world
    self.dead = False
```

**功能**: 创建细胞并立即转录 DNA。

**参数**:
- `x, y: float` - 初始位置
- `gene_DNA: str` - DNA 序列
- `NTs: NTs` - 神经递质引用
- `world: World` - 世界引用

**返回**: 无

---

###### `initialize_cells(cls, NTs, world) -> List[Cell]` (类方法)
```python
@classmethod
def initialize_cells(cls, NTs: 'NTs', world: 'World') -> List['Cell']:
    cells = []
    if CellConfig.cell_subculture:
        # 从亚培养列表生成
        for gene_DNA, count in CellConfig.cell_subculture:
            for _ in range(int(count * CellConfig.cell_subculture_survive_rate)):
                x = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
                y = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
                cell = Cell(x, y, gene_DNA, NTs, world)
                cells.append(cell)
    elif CellConfig.pure_mode:
        # 纯净模式：中心生成 1 个细胞
        cell = Cell(MapConfig.width // 2, MapConfig.height // 2, CellConfig.gene_DNA, NTs, world)
        cells.append(cell)
    else:
        # 正常模式：高斯分布生成
        for _ in range(CellConfig.original_num):
            x = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
            y = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
            cell = Cell(x, y, CellConfig.gene_DNA, NTs, world)
            cells.append(cell)
    return cells
```

**功能**: 工厂方法，生成初始细胞群。

**参数**:
- `NTs: NTs` - 神经递质引用
- `world: World` - 世界引用

**返回**: `List[Cell]` - 细胞列表

**用途**: 游戏开始时调用，根据配置生成种群。

---

###### `transcript(self) -> None`
```python
def transcript(self):
    from DNA_processing import transcript_DNA_to_RNA
    DNA = self.gene_DNA
    RNA = transcript_DNA_to_RNA(DNA)
    self.gene_RNA = RNA
    if CellConfig.debug_mode:
        self.logger.info(f'Cell at ({int(self.x)},{int(self.y)}) transcribed DNA to RNA: {self.gene_RNA}')
```

**功能**: 将 DNA 字符串转录为 RNA 指令列表。

**参数**: 无

**返回**: 无

**副作用**: 修改 `self.gene_RNA`

**依赖**: `DNA_processing.transcript_DNA_to_RNA()`

---

###### `move(self, direction: str) -> None`
```python
def move(self, direction: str):
    self.lock()  # 锁定当前帧
    if direction == 'd':  # 右
        new_x = (self.x + 1) % MapConfig.width
        if not self.world.cells_map[int(new_x), int(self.y)]:
            self.x = new_x
    elif direction == 'a':  # 左
        new_x = (self.x - 1) % MapConfig.width
        if not self.world.cells_map[int(new_x), int(self.y)]:
            self.x = new_x
    elif direction == 'w':  # 上
        new_y = (self.y - 1) % MapConfig.height
        if not self.world.cells_map[int(self.x), int(new_y)]:
            self.y = new_y
    elif direction == 's':  # 下
        new_y = (self.y + 1) % MapConfig.height
        if not self.world.cells_map[int(self.x), int(new_y)]:
            self.y = new_y
```

**功能**: 向指定方向移动一格（循环世界）。
-  TODO： 添加一个修改选项（循环/有边界）

**参数**:
- `direction: str` - 'd'(右), 'a'(左), 'w'(上), 's'(下)

**返回**: 无

**副作用**: 修改 `self.x` 或 `self.y`

**碰撞检测**: 通过 `world.cells_map` 布尔数组检查目标位置是否有细胞

**边界处理**: 使用模运算实现环形世界（Toroidal topology）

---

###### `change_number(self, command: str) -> None`
```python
def change_number(self, command: str) -> None:
    ch = int(self.channel) & 0xFF
    x = int(self.x)
    y = int(self.y)
    if command == '+':
        current = int(self.NTs.map[x, y, ch])
        self.NTs.map[x, y, ch] = min(255, current + 1)
    elif command == '-':
        current = int(self.NTs.map[x, y, ch])
        self.NTs.map[x, y, ch] = max(0, current - 1)
```

**功能**: 增加或减少当前位置当前通道的神经递质值。

**参数**:
- `command: str` - '+' (增加) 或 '-' (减少)

**返回**: 无

**副作用**: 修改 `NTs.map[x, y, channel]`

**范围限制**: 0-255

---

###### `reproduce(self) -> None`
```python
def reproduce(self) -> None:
    from DNA_processing import mutate_DNA
    child_DNA, mutated = mutate_DNA(self.gene_DNA)
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    if CellConfig.randomize_reproduction_direction:
        random.shuffle(directions)
    for dx, dy in directions:
        new_x = (self.x + dx) % MapConfig.width
        new_y = (self.y + dy) % MapConfig.height
        if self.world.reserve_position(int(new_x), int(new_y)):
            child_cell = Cell(new_x, new_y, child_DNA, self.NTs, world=self.world)
            child_cell.channel = self.channel
            child_cell.locked = True  # 新细胞无敌一回合
            self.world.new_cells.append(child_cell)
            break
```

**功能**: 在相邻格子生成子代细胞（带 DNA 变异）。

**参数**: 无

**返回**: 无

**副作用**: 向 `world.new_cells` 添加新细胞

**关键机制**:
1. 调用 `mutate_DNA()` 产生变异的子代 DNA
2. 尝试 4 个相邻方向（上下左右）
3. 使用 `reserve_position()` 预留位置防止同帧冲突
4. 子代继承父代的 `channel`
5. `locked = True` 给予新生细胞 1 帧无敌保护

---

###### `die(self, reason: str) -> None`
```python
def die(self, reason: str) -> None:
    if not self.locked:
        self.dead = True
    if CellConfig.debug_mode:
        self.logger.info(f'Cell at ({int(self.x)},{int(self.y)}) died. Reason: {reason}')
```

**功能**: 标记细胞死亡。

**参数**:
- `reason: str` - 死亡原因（用于日志）

**返回**: 无

**副作用**: 设置 `self.dead = True`（除非 `locked = True`）

---

###### `jump_forward(self, command: str) -> None`
```python
def jump_forward(self, command: str) -> None:
    """'[' 指令: 若当前 (x,y) 的当前 channel 值为 0 则跳转"""
    target = int(command[1:])  # '[5' → 5
    x = int(self.x)
    y = int(self.y)
    ch = int(self.channel) & 0xFF
    val = int(self.NTs.map[x, y, ch])
    if val == 0:
        self.ribosome = target
    else:
        self.move_ribosome()
```

**功能**: 条件跳转（类似 Brainfuck 的 `[`）。

**参数**:
- `command: str` - 格式 '[目标索引'，如 '[5'

**返回**: 无

**副作用**: 修改 `self.ribosome`

**逻辑**: 
- 如果当前位置当前通道值 == 0，跳转到目标索引
- 否则，正常前进（ribosome++）

---

###### `jump_backward(self, command: str) -> None`
```python
def jump_backward(self, command: str) -> None:
    "']' 指令: 若当前 (x,y) 的当前 channel 值 > 0 则跳转"
    target = int(command[1:])  # ']2' → 2
    x = int(self.x)
    y = int(self.y)
    ch = int(self.channel) & 0xFF
    val = int(self.NTs.map[x, y, ch])
    if val > 0:
        self.ribosome = target
    else:
        self.move_ribosome()
```

**功能**: 条件跳转（类似 Brainfuck 的 `]`）。

**参数**:
- `command: str` - 格式 ']目标索引'，如 ']2'

**返回**: 无

**副作用**: 修改 `self.ribosome`

**逻辑**: 
- 如果当前位置当前通道值 > 0，跳转到目标索引
- 否则，正常前进

---

###### `change_channel(self, command: str) -> None`
```python
def change_channel(self, command: str) -> None:
    if command == '>':
        self.channel = (self.channel + 1) & 0xFF
    elif command == '<':
        self.channel = (self.channel - 1) & 0xFF
```

**功能**: 切换当前操作的神经递质通道。

**参数**:
- `command: str` - '>' (通道+1) 或 '<' (通道-1)

**返回**: 无

**副作用**: 修改 `self.channel`

**范围限制**: 使用 `& 0xFF` 确保在 0-255 范围内循环

---

###### `do_RNA(self) -> None`
```python
def do_RNA(self) -> None:
    if self.ribosome >= len(self.gene_RNA):
        if CellConfig.ribosome_loop:
            self.ribosome = 0
        else:
            return
    
    command = self.gene_RNA[self.ribosome]
    
    # 执行指令
    if command in ['d', 'a', 'w', 's']:
        self.move(command)
        self.move_ribosome()
    elif command in ['+', '-']:
        self.change_number(command)
        self.move_ribosome()
    elif command == ',':
        self.reproduce()
        self.move_ribosome()
    elif command == '.':
        self.die("执行死亡指令")
        self.move_ribosome()
    elif command[0] == '[':
        self.jump_forward(command)
    elif command[0] == ']':
        self.jump_backward(command)
    elif command in ['>', '<']:
        self.change_channel(command)
        self.move_ribosome()
```

**功能**: 执行当前 `ribosome` 指向的 RNA 指令。

**参数**: 无

**返回**: 无

**副作用**: 根据指令修改细胞状态、环境、或生成新细胞

**指令集**:
| 指令 | 功能 |
|------|------|
| `d` | 右移 |
| `a` | 左移 |
| `w` | 上移 |
| `s` | 下移 |
| `+` | 增加神经递质 |
| `-` | 减少神经递质 |
| `,` | 繁殖 |
| `.` | 死亡 |
| `[n` | 值为 0 时跳转到索引 n |
| `]n` | 值 > 0 时跳转到索引 n |
| `>` | 通道 +1 |
| `<` | 通道 -1 |

---

###### `act(self) -> None`
```python
def act(self) -> None:
    if self.dead:
        return
    
    instructions_executed = 0
    while instructions_executed < MapConfig.max_instructions:
        if self.ribosome >= len(self.gene_RNA):
            break
        self.do_RNA()
        instructions_executed += 1
        if self.dead:
            break
```

**功能**: 每帧执行多条 RNA 指令（最多 `max_instructions` 条）。

**参数**: 无

**返回**: 无

**副作用**: 多次调用 `do_RNA()`

**性能限制**: 防止无限循环 DNA 占用过多 CPU

---

### 4. `world.py` - 世界管理器

#### 目的
协调所有系统：细胞生命周期、碰撞检测、存档、统计。

#### 类: `World`

##### 数据结构
```python
class World:
    width: int                              # 世界宽度
    height: int                             # 世界高度
    cells: List[Cell]                       # 当前活着的细胞列表
    cells_map: np.ndarray                   # 碰撞检测布尔数组 (width+1, height+1)
    new_cells: List[Cell]                   # 本帧新生成的细胞
    pending_positions: set[tuple[int,int]]  # 本帧预留位置集合
    NTs: NTs                                # 神经递质系统
    ticks: int                              # 当前帧数
    logger: logging.Logger                  # 日志记录器
```

---

##### 方法规格

###### `__init__(self, width: int, height: int)`
```python
def __init__(self, width: int, height: int):
    self.width = width
    self.height = height
    self.cells = []
    self.cells_map = np.zeros((width + 1, height + 1), dtype=bool)
    self.NTs = NTs.initialize_NTs()
    self.cells = Cell.initialize_cells(self.NTs, self)
    self.new_cells = []
    self.pending_positions = set()
    self.ticks = 0
```

**功能**: 初始化世界并生成初始细胞。

**参数**:
- `width, height: int` - 世界尺寸

**返回**: 无

---

###### `update(self) -> None`
```python
def update(self) -> None:
    # 1. 清空预留位置
    self.pending_positions.clear()
    
    # 2. 所有细胞执行行为
    for cell in self.cells:
        if not cell.dead:
            cell.act()
    
    # 3. 清除死细胞
    self.cells = [c for c in self.cells if not c.dead]
    
    # 4. 添加新细胞
    self.add_new_cells()
    
    # 5. 更新碰撞图
    self.update_cells_map()
    
    # 6. 帧计数器
    self.ticks += 1
    
    # 7. 自动保存
    if SaveConfig.autosave_interval > 0 and self.ticks % SaveConfig.autosave_interval == 0:
        self.save_world_state(f"{SaveConfig.autosave_dir}/{SaveConfig.autosave_prefix}tick_{self.ticks}.txt")
```

**功能**: 每帧更新循环的核心逻辑。

**参数**: 无

**返回**: 无

**执行顺序**（关键）:
1. 清空本帧预留位置
2. 所有细胞执行 `act()`
3. 移除死细胞
4. 将 `new_cells` 合并到 `cells`
5. 重建碰撞检测图
6. 自动保存检查

---

###### `reserve_position(self, x: int, y: int) -> bool`
```python
def reserve_position(self, x: int, y: int) -> bool:
    pos = (x, y)
    if pos in self.pending_positions or self.cells_map[x, y]:
        return False
    self.pending_positions.add(pos)
    return True
```

**功能**: 预留位置，防止同帧多个细胞生成在同一格子。

**参数**:
- `x, y: int` - 目标位置

**返回**: `bool` - 成功预留返回 True，否则 False

**用途**: 繁殖时调用，确保不会覆盖已有细胞

---

###### `update_cells_map(self) -> None`
```python
def update_cells_map(self) -> None:
    self.cells_map.fill(False)
    for cell in self.cells:
        if not cell.dead:
            x = int(cell.x)
            y = int(cell.y)
            self.cells_map[x, y] = True
```

**功能**: 重建碰撞检测布尔数组。

**参数**: 无

**返回**: 无

**副作用**: 更新 `self.cells_map`

**性能**: O(细胞数)，每帧调用一次

---

###### `save_world_state(self, filename: str) -> None`
```python
def save_world_state(self, filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        for cell in self.cells:
            f.write(f"({cell.x}, {cell.y})\\n")
            f.write(f"{cell.gene_DNA}\\n")
            f.write(f"{cell.ribosome}\\n")
            f.write(f"{cell.channel}\\n")
    
    # 保存神经递质矩阵
    nts_filename = filename.replace('.txt', '_NTs.npy')
    np.save(nts_filename, self.NTs.map)
```

**功能**: 保存当前世界状态到文件。

**参数**:
- `filename: str` - 存档文件路径

**返回**: 无

**存档格式**:
```
(x, y)
DNA序列
ribosome索引
channel值
(x, y)
...
```

**额外文件**: `*_NTs.npy` 保存神经递质 3D 数组

---

###### `read_world_state(self, filename: str) -> None`
```python
def read_world_state(self, filename: str) -> None:
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    self.cells.clear()
    i = 0
    while i < len(lines):
        pos_line = lines[i].strip()
        dna_line = lines[i + 1].strip()
        rbs_line = lines[i + 2].strip()
        channel_line = lines[i + 3].strip()
        x, y = eval(pos_line)
        cell = Cell.create_cell_from_DNA(dna_line, x, y, self.NTs, self, 
                                         ribosome=int(rbs_line), channel=int(channel_line))
        self.cells.append(cell)
        i += 4
    
    # 加载神经递质
    nts_filename = filename.replace('.txt', '_NTs.npy')
    nts_map = np.load(nts_filename)
    self.NTs = NTs.initialize_NTs(map=nts_map)
    self.update_cells_map()
```

**功能**: 从存档文件恢复世界状态。

**参数**:
- `filename: str` - 存档文件路径

**返回**: 无

**副作用**: 清空当前细胞，重新加载

**容错**: 兼容旧版存档格式（无 channel 行）

---

###### `collect_DNAs(self) -> str`
```python
def collect_DNAs(self) -> str:
    dna_counts = {}
    for cell in self.cells:
        if not cell.dead:
            dna_counts[cell.gene_DNA] = dna_counts.get(cell.gene_DNA, 0) + 1
    
    sorted_dnas = sorted(dna_counts.items(), key=lambda x: x[1], reverse=True)
    
    lines = [f"=== 收集到 {len(sorted_dnas)} 种不同的DNA，共 {len(self.cells)} 个细胞 ==="]
    for i, (dna, count) in enumerate(sorted_dnas, 1):
        dna_parts = [dna[j:j+2] for j in range(0, len(dna), 2)]
        dna = ' '.join(dna_parts)
        lines.append(f"#{i:2d} | x{count:4d} | len={len(dna):3d} | {dna}")
    
    return '\\n'.join(lines)
```

**功能**: 统计并格式化输出所有不同的 DNA 序列及数量。

**参数**: 无

**返回**: `str` - 格式化的统计报告

**用途**: 日志输出，观察种群基因多样性

---

### 5. `DNA_processing.py` - 遗传算法模块

#### 目的
实现 DNA 变异和转录机制。

---

#### 函数: `mutate_DNA(gene_DNA: str) -> Tuple[str, bool]`

```python
def mutate_DNA(gene_DNA: str) -> Tuple[str, bool]:
    # 1. 单碱基突变（概率 base_muatation_rate）
    if random.random() < CellConfig.base_muatation_rate:
        index = random.randrange(len(gene_DNA))
        method = random.choice([_add_base, _drop_base, _substitute_base])
        gene_DNA = method(gene_DNA, index)
    
    # 2. 基因片段重组
    segments = _break_to_segments(gene_DNA, CellConfig.gene_mutation_rate)
    if len(segments) == 1:
        return gene_DNA, False
    segments = _duplicate_segment(segments)
    segments = _shuffle_segments(segments)
    mutated_DNA = _join_segments_with_connectors(segments)
    
    return mutated_DNA, True
```

**功能**: 产生变异的子代 DNA。

**参数**:
- `gene_DNA: str` - 父代 DNA

**返回**: 
- `Tuple[str, bool]` - (子代 DNA, 是否发生变异)

**变异类型**:
1. **点突变** - 随机插入/删除/替换单个碱基
2. **片段重组** - 切割 → 复制 → 打乱 → 反转 → 重组

**算法流程**:
```
父代 DNA
  ↓ (概率 base_muatation_rate)
点突变（插入/删除/替换碱基）
  ↓
选取断点切割为片段
  ↓
随机复制一个片段 + 随机删除一个片段
  ↓
打乱片段顺序 + 随机反转某些片段
  ↓
用随机碱基连接片段
  ↓
子代 DNA
```

---

#### 函数: `transcript_DNA_to_RNA(gene_DNA: str, MODE: int) -> List[str]`

```python
def transcript_DNA_to_RNA(gene_DNA: str, MODE=2) -> List[str]:
    if MODE == 2:
        # 1. 查找转录起始标记 '<>' 和终止标记 '><'
        RNA_list = []
        i = 0
        transcript_switch = False
        while i < len(gene_DNA) - 1:
            bases = gene_DNA[i] + gene_DNA[i + 1]
            if bases == '<>':
                transcript_switch = True  # 开始转录
                i += 2
                continue
            if not transcript_switch:
                i += 2
                continue
            if bases == '><':
                break  # 终止转录
            RNA_list.append(bases)
            i += 2
        
        # 2. 双碱基转录表
        translate_dict = {
            '!!': '+', '!?': ',', '!>': 'd', '!<': 'a',
            '?!': '.', '??': '-', '?>': 'w', '?<': 's',
            '>!': '[', '>?': '}', '>>': '>', '><': 'e',
            '<!': ']', '<?': '{', '<<': '<', '<>': 'b',
        }
        translated_RNA = [translate_dict[token] for token in RNA_list if token in translate_dict]
        
        # 3. 括号匹配（为 '[' 和 ']' 添加跳转目标索引）
        RNA = _match_RNA(translated_RNA)
        
        return RNA
```

**功能**: 将 DNA 字符串转录为 RNA 指令列表。

**参数**:
- `gene_DNA: str` - DNA 序列
- `MODE: int` - 转录模式（1=旧版，2=当前版本）

**返回**: `List[str]` - RNA 指令列表

**转录规则（MODE=2）**:
| DNA（双碱基） | RNA 指令 | 功能 |
|--------------|---------|------|
| `<>` | - | **转录起始标记** |
| `><` | - | **转录终止标记** |
| `!!` | `+` | 增加神经递质 |
| `!?` | `,` | 繁殖 |
| `!>` | `d` | 右移 |
| `!<` | `a` | 左移 |
| `?!` | `.` | 死亡 |
| `??` | `-` | 减少神经递质 |
| `?>` | `w` | 上移 |
| `?<` | `s` | 下移 |
| `>!` | `[` | 条件跳转（前） |
| `<!` | `]` | 条件跳转（后） |
| `>>` | `>` | 通道+1 |
| `<<` | `<` | 通道-1 |

**关键机制**:
1. **转录区标记**: 只有 `<>` 到 `><` 之间的序列会被转录
2. **双碱基解析**: 每次读取 2 个碱基
3. **括号匹配**: 为 `[` 和 `]` 添加跳转目标索引（如 `[5` 表示跳转到索引 5）

---

#### 内部函数: `_match_RNA(translated_RNA: List[str]) -> List[str]`

```python
def _match_RNA(translated_RNA: List[str]) -> List[str]:
    stack = []
    matched_indices = set()
    
    # 第一遍：找出所有配对的括号
    for i, command in enumerate(translated_RNA):
        if command == '[':
            stack.append(i)
        elif command == ']':
            if stack:
                j = stack.pop()
                matched_indices.add(i)
                matched_indices.add(j)
    
    # 第二遍：只保留配对的括号
    result = []
    index_map = {}
    for i, command in enumerate(translated_RNA):
        if command in ['[', ']']:
            if i in matched_indices:
                index_map[i] = len(result)
                result.append(command)
        else:
            result.append(command)
    
    # 第三遍：为括号添加跳转位置
    stack = []
    for i, command in enumerate(result):
        if command == '[':
            stack.append(i)
        elif command == ']':
            if stack:
                j = stack.pop()
                result[j] = f'[{i}'  # '[5' 表示跳转到索引 5
                result[i] = f']{j}'  # ']2' 表示跳转到索引 2
    
    return result
```

**功能**: 为 RNA 中的括号指令添加跳转目标。

**参数**:
- `translated_RNA: List[str]` - 已翻译但未匹配的 RNA

**返回**: `List[str]` - 带跳转目标的 RNA

**算法**: 使用栈匹配括号，丢弃未配对的括号

**示例**:
```python
输入: ['[', 'd', 'd', ']', 'w']
输出: ['[3', 'd', 'd', ']0', 'w']
```

---

### 6. `drawer.py` - 渲染系统

#### 目的
将细胞和环境绘制到 Pygame 屏幕上。

---

#### 函数: `render_frame(screen, world) -> None`

```python
def render_frame(screen: pygame.Surface, world: World) -> None:
    # 创建基础表面（世界大小）
    base_surface = pygame.Surface((MapConfig.width, MapConfig.height))
    base_surface.fill((0, 0, 0))  # 黑色背景
    
    # 绘制神经递质（可选）
    # world.NTs.draw(base_surface)
    
    # 绘制所有细胞
    for cell in world.cells:
        if not cell.dead:
            x = int(cell.x)
            y = int(cell.y)
            base_surface.set_at((x, y), (0, 255, 0))  # 绿色像素
    
    # 缩放到窗口大小
    scaled_surface = pygame.transform.scale(base_surface, 
                                           (MapConfig.width * DispConfig.scale, 
                                            MapConfig.height * DispConfig.scale))
    screen.blit(scaled_surface, (0, 0))
```

**功能**: 渲染一帧画面。

**参数**:
- `screen: pygame.Surface` - 目标屏幕
- `world: World` - 世界对象

**返回**: 无

**渲染流程**:
1. 创建世界大小的基础表面
2. 填充黑色背景
3. 逐像素绘制细胞（绿色）
4. 缩放到窗口大小
5. blit 到屏幕

---

#### 函数: `draw_tick(screen, world) -> None`

```python
def draw_tick(screen: pygame.Surface, world: World) -> None:
    font = pygame.font.Font(None, 36)
    text = font.render(f'Tick: {world.ticks}', True, (255, 255, 255))
    screen.blit(text, (10, 10))
```

**功能**: 在左上角显示当前帧数。

**参数**:
- `screen: pygame.Surface` - 目标屏幕
- `world: World` - 世界对象

**返回**: 无

---

### 7. `main.py` - 主程序

#### 目的
初始化 Pygame，运行主循环，处理事件。

---

#### 函数: `main() -> None`

```python
def main():
    # 1. 清空旧日志
    log_file = Path(LogConfig.file)
    if log_file.exists():
        log_file.unlink()
    
    # 2. 初始化日志
    logger = setup_logging()
    
    # 3. 初始化 Pygame
    pygame.init()
    WIDTH, HEIGHT = MapConfig.width, MapConfig.height
    SCALE = DispConfig.scale
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE), 
                                     pygame.DOUBLEBUF, vsync=1)
    pygame.display.set_caption('Fauna F**k')
    
    # 4. 创建世界
    world = World(WIDTH, HEIGHT)
    
    # 5. 读取存档（可选）
    if SaveConfig.read and SaveConfig.read_path:
        try:
            world.read_world_state(SaveConfig.read_path)
        except Exception as e:
            logger.error(f"Failed to read world state: {e}")
    
    # 6. 主循环
    running = True
    clock = pygame.time.Clock()
    
    while running:
        clock.tick(DispConfig.fps)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # 更新世界
        world.update()
        
        # 渲染
        render_frame(screen, world)
        draw_tick(screen, world)
        pygame.display.flip()
        
        # 日志输出（每 100 帧）
        if world.ticks % 100 == 0:
            logger.info(f"Tick: {world.ticks}, Cells: {len(world.cells)}")
            logger.info(world.collect_DNAs())
    
    # 7. 退出时保存
    if SaveConfig.autosave_interval > 0:
        world.save_world_state(f"{SaveConfig.autosave_dir}/final_stats.txt")
    
    pygame.quit()
```

**功能**: 程序主入口。

**参数**: 无

**返回**: 无

**执行流程**:
1. 清空旧日志文件
2. 初始化日志系统
3. 初始化 Pygame 窗口
4. 创建世界并生成初始细胞
5. 可选：从存档恢复
6. 进入主循环：
   - 限制帧率
   - 处理退出事件
   - 调用 `world.update()`
   - 渲染画面
   - 定期输出统计日志
7. 退出时保存最终状态

---

### 8. `logger_setup.py` - 日志系统

#### 目的
配置旋转日志文件系统。

---

#### 函数: `setup_logging() -> logging.Logger`

```python
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("fauna")
    logger.setLevel(getattr(logging, LogConfig.level))
    
    # 创建日志文件夹
    log_dir = Path(LogConfig.file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件处理器（基于大小轮转）
    file_handler = RotatingFileHandler(
        LogConfig.file,
        maxBytes=LogConfig.rotate_max_bytes,
        backupCount=LogConfig.rotate_backup_count
    )
    
    # 快照处理器（基于时间轮转）
    snapshot_handler = TimedRotatingFileHandler(
        f"{log_dir}/snapshot.log",
        when='M',
        interval=LogConfig.snapshot_minutes,
        backupCount=LogConfig.snapshot_backup_count
    )
    
    # 格式化
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    snapshot_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(snapshot_handler)
    
    return logger
```

**功能**: 配置并返回日志记录器。

**参数**: 无

**返回**: `logging.Logger` - 配置好的日志记录器

**日志策略**:
1. **主日志**: 大小达到 2MB 时轮转，保留 1 个备份
2. **快照日志**: 每 5 分钟轮转一次，保留 2 个快照

---

## 🧬 核心算法详解

### DNA 变异算法

```python
父代 DNA: '<>!?!?><'
         ↓
1. 单碱基突变 (1e-3 概率)
   - 插入: '<>!?X!?><'
   - 删除: '<>!?><'
   - 替换: '<>??!?><'
         ↓
2. 选断点切割 (1e-4 概率/碱基)
   '<>!?' | '!?><'
         ↓
3. 复制片段 + 删除片段
   ['<>!?', '!?><', '<>!?']  // 复制第一个
   ['<>!?', '!?><']          // 删除最后一个
         ↓
4. 打乱 + 反转
   ['!?><', '<>!?']          // 打乱
   ['<>?!', '<>!?']          // 反转第一个
         ↓
5. 用随机碱基连接
   '<>?!' + '!' + '<>!?'
         ↓
子代 DNA: '<>?!!<>!?'
```

### 转录流程

```python
DNA: '<>!?!?><噪声!?'
         ↓
1. 查找转录区标记
   '<>' 开始 → '><' 结束
   提取: '!?!?'
         ↓
2. 双碱基翻译
   '!?' → ','  (繁殖)
   '!?' → ','  (繁殖)
   结果: [',', ',']
         ↓
3. 括号匹配
   (无括号，跳过)
         ↓
RNA: [',', ',']
```

---

## 🎮 使用场景示例

### 场景 1: 简单移动细胞
```python
# 配置
CellConfig.gene_DNA = '<>!>!>><'  # 转录区: !>!>
CellConfig.original_num = 1

# DNA → RNA
'!>' → 'd'  (右移)
'!>' → 'd'  (右移)

# 行为: 细胞持续向右移动
```

### 场景 2: 繁殖循环
```python
# 配置
CellConfig.gene_DNA = '<>!?><'  # 转录区: !?

# DNA → RNA
'!?' → ','  (繁殖)

# 行为: 细胞每帧尝试繁殖，快速增长
```

### 场景 3: 条件分支
```python
# 配置
CellConfig.gene_DNA = '<>>!??!<!><'  # 转录区: >!??!<

# DNA → RNA
'>!' → '['  (条件跳转前)
'??' → '-'  (减少神经递质)
'<!' → ']'  (条件跳转后)

# RNA: ['[2', '-', ']0']

# 行为: 
# - 如果当前位置神经递质 == 0，跳过 '-' 指令
# - 否则，执行 '-' 减少神经递质
# - 形成循环：不断减少直到值为 0
```

---

## 📊 性能考虑

### 关键性能瓶颈
1. **`world.update_cells_map()`**: O(细胞数)，每帧调用
2. **`cell.do_RNA()`**: 每细胞每帧执行最多 1000 条指令
3. **`drawer.render_frame()`**: 像素级绘制 + 缩放

### 优化建议
1. **空间分区**: 使用四叉树优化碰撞检测
2. **批量渲染**: 使用 `pygame.surfarray` 一次性绘制所有细胞
3. **指令限制**: 降低 `max_instructions` 避免无限循环
4. **稀疏存储**: 用字典存储非零神经递质值

---

## 🔗 模块依赖关系

```
main.py
  ├─ pygame
  ├─ logger_setup.py
  ├─ config.py
  ├─ world.py
  │   ├─ numpy
  │   ├─ cell.py
  │   │   ├─ DNA_processing.py
  │   │   │   ├─ random
  │   │   │   └─ config.py
  │   │   ├─ NTs.py
  │   │   │   ├─ numpy
  │   │   │   └─ pygame
  │   │   └─ drawer.py
  │   │       └─ pygame
  │   └─ NTs.py
  └─ drawer.py
```

---

## 🚀 实现其他语言的检查清单

### 必须实现的数据结构
- [ ] 3D uint8 数组（神经递质网格）
- [ ] 2D bool 数组（碰撞检测图）
- [ ] 动态数组/列表（细胞列表）
- [ ] 集合（预留位置）
- [ ] 字符串处理（DNA/RNA）

### 必须实现的核心功能
- [ ] 随机数生成（正态分布、均匀分布）
- [ ] 模运算环绕（Toroidal 边界）
- [ ] 文件 I/O（存档/加载）
- [ ] 图形渲染（像素级绘制 + 缩放）
- [ ] 日志系统

### 算法实现检查
- [ ] DNA 变异流水线（7 个步骤）
- [ ] DNA → RNA 转录（双碱基解析 + 括号匹配）
- [ ] RNA 指令执行引擎（12 种指令）
- [ ] 碰撞检测预留机制

### 性能目标
- [ ] 支持 1000+ 细胞 @ 60 FPS
- [ ] 每帧每细胞执行 ≥100 条指令
- [ ] 内存占用 <500MB（10000 细胞）

---

## 📝 术语表

| 术语 | 含义 |
|------|------|
| **DNA** | 细胞的遗传信息（字符串） |
| **RNA** | DNA 转录后的指令列表 |
| **ribosome** | 核糖体，当前执行的 RNA 指令索引 |
| **channel** | 神经递质通道（0-255） |
| **神经递质** | 环境信息网格，每格有 256 个通道 |
| **预留位置** | 防止同帧多个细胞生成在同一位置的机制 |
| **碰撞图** | 布尔数组，标记哪些位置有细胞 |
| **转录区** | DNA 中 `<>` 到 `><` 之间的序列 |
| **括号匹配** | 为 `[` 和 `]` 添加跳转目标索引 |

---

## 🎓 总结

FaunaFuck 是一个复杂但模块化的系统，核心概念是：

1. **遗传编程**: 细胞 = 执行遗传程序的虚拟机
2. **环境交互**: 256 通道神经递质网格 = 信息载体
3. **进化驱动**: 繁殖 + 变异 → 适应性种群

实现其他语言时，关键是：
- **保持数据流一致**: DNA → RNA → 执行
- **实现核心算法**: 变异流水线、转录规则、指令执行
- **优化性能**: 空间分区、批量操作、指令限制

---

**文档版本**: 1.0  
**最后更新**: 2026-01-18  
**作者**: GitHub Copilot  
**目标读者**: AI 代码生成系统、跨语言移植开发者
