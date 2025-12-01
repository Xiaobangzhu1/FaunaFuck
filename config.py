# config.py

import math
from dataclasses import dataclass, field
from pathlib import Path

class MapConfig:
    '''地图大小'''
    
    width : int = 80
    height : int = 80
    
class DispConfig:
    '''显示设置'''
    
    fps : int = 60
    
    
class CellConfig:
    '''细胞配置'''
    criticalpoint : int = 20  # 低于该能量会触发特殊行为
    gene_DNA : str = 'd-0'  # 初始基因序列
    original_energy : int = 1000
    original_num : int = 1

    energy_per_glutose : int = 1  # 每个葡萄糖提供的能量
    minus_glutose : int = 1  # 每次被吃掉的葡萄糖数量
    plus_glutose : int = 1  # 每次被吐出的葡萄糖数量
    
    dead_cells : int = 5  # 死亡细胞转化为的葡萄糖数量
    
if __name__ == '__main__':
    # When run directly, print sync message and run main.
    # Avoid importing `main` at module import time to prevent circular imports
    print('Config Synchronized')
    from main import main as _main
    _main()