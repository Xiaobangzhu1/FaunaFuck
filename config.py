# config.py

import math
from dataclasses import dataclass, field
from pathlib import Path

class MapConfig:
    '''地图大小'''
    
    width : int = 100
    height : int = 100
    channels : int = 256  # 神经递质通道数
    
    max_instructions : int = 1000  # 每个细胞每帧最大执行指令数
    
class DispConfig:
    '''显示设置'''
    
    fps : int = 60
    scale : int = 4  # 窗口显示放大倍数（地图与细胞等比例放大）
    
    
class CellConfig:
    '''细胞配置'''
    debug_mode : bool = False # 是否开启调试模式
    die_mode : int = 3
    gene_DNA : str = '<>!?!?><'  # 初始基因序列
    original_num : int = 10  # 初始细胞数量
    pure_mode : bool = False # 纯净模式，仅生成一个细胞
    skip_transcript : bool = False  # 跳过转录阶段，直接使用预设RNA序列
    long_gene_encourage : bool = False  # 长基因鼓励因子
    randomize_reproduction_direction : bool = True  # 繁殖时随机选择方向
    surroundings = 8
    
    ribosome_loop : bool = False  # 核糖体到达末端后循环回起点
    # 各种变异发生的概率
    
    base_muatation_rate : float = 1e-3  # 基础碱基突变概率
    gene_mutation_rate : float = 1e-4  # 基础基因突变概率

    
    
    
    
    
    replant : bool = False #
    replant_DNAs : list[str] = []
    
    cell_subculture : list[tuple[str, int]]|None = None  # 亚培养细胞列表，格式为 [(DNA序列, 数量), ...]
    cell_subculture_survive_rate : float = 1  # 亚培养细胞存活率
    
class SaveConfig:
    '''存档设置'''
    import os
    autosave_interval : int = 5000  # 自动保存间隔，单位为 tick，0 表示不自动保存
    autosave_dir : str = "saves"  # 自动保存文件夹
    autosave_prefix : str = "autosave_"  # 自动保存文件名前缀

    read = 1 # 是否读取存档
    read_tick = 0 # 读取存档的指定帧数，0 表示读取最新帧
    read_path : str =  os.path.join(autosave_dir, f"autosave_tick_{read_tick}.txt")  # 读取存档路径，空字符串表示不读取存档
    read_path = os.path.join(autosave_dir,'final_stats.txt') if read_tick == 0 else read_path

class LogConfig:
    """日志设置"""
    enable: bool = True
    level: str = "INFO"  # 建议 INFO 或 WARNING，减少磁盘写入
    file: str = "logs/fauna.log"  # 日志文件存放在 logs 文件夹
    rotate_max_bytes: int = 2_000_000  # ~2MB
    rotate_backup_count: int = 1 # 保留多少个轮转备份
    # 分钟级日志快照（基于时间的轮转）
    snapshot_minutes: int = 5           # 每隔多少分钟轮转一次
    snapshot_backup_count: int = 2    # 最多保留多少个快照（例如保留近2小时）


    
if __name__ == '__main__':
    # When run directly, print sync message and run main.
    # Avoid importing `main` at module import time to prevent circular imports
    print('Config Synchronized')
    from main import main as _main
    _main()