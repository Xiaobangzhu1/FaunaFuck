# config.py

import math
from dataclasses import dataclass, field
from pathlib import Path

class MapConfig:
    '''地图大小'''
    
    width : int = 200
    height : int = 200
    channels : int = 256  # 神经递质通道数
    
    max_instructions : int = 1000  # 每个细胞每帧最大执行指令数
    
class DispConfig:
    '''显示设置'''
    
    fps : int = 60
    scale : int = 4  # 窗口显示放大倍数（地图与细胞等比例放大）
    
    
class CellConfig:
    '''细胞配置'''
    debug_mode : bool = False  # 是否开启调试模式
    die_mode : int = 4 # 4:上下左右四个细胞
                       # 8:上下左右四个细胞加上四个对角线细胞
    gene_DNA : str = '?+'  # 初始基因序列
    original_num : int = 1  # 初始细胞数量
    pure_mode : bool = True  # 纯净模式，仅生成一个细胞
    skip_transcript : bool = False  # 跳过转录阶段，直接使用预设RNA序列
    mutation_rate : float = 0.000000 # 突变率

class LogConfig:
    """日志设置"""
    enable: bool = True
    level: str = "DEBUG"  # 可选: DEBUG/INFO/WARNING/ERROR
    file: str = "logs/fauna.log"  # 日志文件存放在 logs 文件夹
    rotate_max_bytes: int = 2_000_000  # ~2MB
    rotate_backup_count: int = 4
    # 分钟级日志快照（基于时间的轮转）
    snapshot_minutes: int = 1           # 每隔多少分钟轮转一次
    snapshot_backup_count: int = 120    # 最多保留多少个快照（例如保留近2小时）


    
if __name__ == '__main__':
    # When run directly, print sync message and run main.
    # Avoid importing `main` at module import time to prevent circular imports
    print('Config Synchronized')
    from main import main as _main
    _main()