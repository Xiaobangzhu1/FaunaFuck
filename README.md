# FaunaFuck

FaunaFuck 是一个类 Brainfuck 的细胞自动机模拟器。项目通过 DNA -> RNA 转录驱动细胞行为，在一个可交互生态箱里观察复制、死亡、状态变化与运行日志。

## 项目特点

- 空生态箱启动，运行时用右侧控制面板投放细胞。
- 支持 `spawn`、`set`、`pause`、`step`、`back`、`save`、`load`、`log5` 等命令。
- 支持 DNA 规则弹窗、历史命令选择/复制、输入框光标编辑。
- 提供无头回归能力，便于验证固定随机种子下的行为基线。

## 快速开始

### 1. 准备环境

仓库内的 [`requirements.txt`](requirements.txt) 是导出的 Conda 环境清单。若你已经有可用 Python 环境，至少需要保证 `pygame` 与 `numpy` 可用；运行测试时还需要 `pytest`。

### 2. 启动图形界面

```bash
PYTHONPATH=. python3 -m fauna.cli
```

或直接使用仓库自带入口脚本：

```bash
./cli
```

启动后会打开一个左侧地图、右侧控制面板的窗口。默认从空生态箱开始，右侧输入框可直接执行命令。

### 3. 运行测试

```bash
PYTHONPATH=. pytest -q
```

如果在无显示环境执行，可使用：

```bash
SDL_VIDEODRIVER=dummy PYTHONPATH=. pytest -q
```

## 常用命令

在右侧控制面板输入：

- `help`: 查看命令帮助。
- `spawn`: 按默认配置在中心生成一个细胞。
- `spawn dna=<>!?!?>< x=10 y=10 count=3 channel=1`: 按参数批量生成细胞。
- `set CellConfig.reproduction_fail_rate=0.25`: 运行时修改配置。
- `pause` / `resume` / `toggle`: 控制暂停与继续。
- `step` / `back`: 暂停状态下前进或回退一帧。
- `save saves/manual.txt` / `load saves/manual.txt`: 存档与读档。
- `dna`: 打开 DNA 转录规则弹窗。
- `log5`: 导出最近 5 分钟日志摘要。

常用快捷键：

- `Space` / `F5`: 切换暂停。
- `F6` / `Right`: 暂停时前进一步。
- `F7` / `Left`: 暂停时后退一步。
- `F8`: 重置为空生态箱。
- `/`: 打开 DNA 规则弹窗。
- `Tab`: 显示或隐藏控制面板。

## 目录概览

- [`fauna/`](fauna): 核心运行代码。
- [`tests/`](tests): 回归与交互测试。
- [`tools/`](tools): 日志分析、动画生成等辅助脚本。
- [`docs/`](docs): PRD、系统设计、实施计划与进度记录。
- [`STRUCTURE.md`](STRUCTURE.md): 更完整的仓库结构说明。

## 文档入口

- [`docs/README.md`](docs/README.md): 文档索引与阅读顺序。
- [`docs/PRD.md`](docs/PRD.md): 高层目标、范围、验收标准。
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md): 实施任务与完成情况。
- [`docs/system-core-loop.md`](docs/system-core-loop.md): 运行控制与命令闭环。
- [`docs/system-cell-behavior.md`](docs/system-cell-behavior.md): 细胞行为规则。
- [`docs/DNA_RULES.md`](docs/DNA_RULES.md): DNA -> RNA 转录映射。

## 运行产物

- `logs/`: 运行日志与最近 5 分钟日志摘要。
- `saves/`: 自动存档、手动存档与最终统计输出。
