# world.py
'''管理游戏世界'''

import pygame
from typing import List, Optional, Tuple, Union
import logging

from NTs import NTs
from cell import Cell
import numpy as np
from config import *
from drawer import draw_tick as drawer_draw_tick, render_frame


class World:
    """创建和管理游戏中的所有实体和系统"""
    def __init__(self, width : int, height : int):
        self.logger = logging.getLogger("fauna.world")
        # 基础状态
        self.width = width
        self.height = height
         
        self.cells : List[Cell] = []
        self.cells_map = np.zeros((self.width + 1, self.height + 1), dtype=bool)
        
        # 初始化细胞
        self.NTs = NTs.initialize_NTs()
        self.cells = Cell.initialize_cells(self.NTs, self)
        self.new_cells = []  # 用于存储新生成的细胞
        self.ticks = 0
        
    def collect_RNAs(self):
        """收集并统计所有不同的RNA序列"""
        rna_counts = {}
        for cell in self.cells:
            if not cell.dead:
                rna_str = ''.join(cell.gene_RNA)
                rna_counts[rna_str] = rna_counts.get(rna_str, 0) + 1
        
        # 按数量排序，最多的在前
        sorted_rnas = sorted(rna_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 格式化输出：序号、数量、长度、RNA（截断长序列）
        lines = [f"=== 收集到 {len(sorted_rnas)} 种不同的RNA，共 {len([c for c in self.cells if not c.dead])} 个细胞 ==="]
        for i, (rna, count) in enumerate(sorted_rnas[:20], 1):  # 只显示前20种
            # 将RNA按指令分组显示，更易读
            display_rna = rna if len(rna) <= 40 else rna[:37] + "..."
            lines.append(f"#{i:2d} | x{count:4d} | len={len(rna):3d} | {display_rna}")
        
        if len(sorted_rnas) > 20:
            lines.append(f"... 还有 {len(sorted_rnas) - 20} 种RNA未显示")
        
        output = '\n'.join(lines)
        self.logger.info(f"\n{output}")

    def collect_DNAs(self):
        """收集并统计所有不同的DNA序列"""
        dna_counts = {}
        for cell in self.cells:
            if not cell.dead:
                dna_counts[cell.gene_DNA] = dna_counts.get(cell.gene_DNA, 0) + 1
        
        # 按数量排序，最多的在前
        sorted_dnas = sorted(dna_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 格式化输出：序号、数量、长度、DNA（截断长序列）
        lines = [f"=== 收集到 {len(sorted_dnas)} 种不同的DNA，共 {len([c for c in self.cells if not c.dead])} 个细胞 ==="]
        for i, (dna, count) in enumerate(sorted_dnas[:20], 1):  # 只显示前20种
            display_dna = dna if len(dna) <= 40 else dna[:37] + "..."
            lines.append(f"#{i:2d} | x{count:4d} | len={len(dna):3d} | {display_dna}")
        
        if len(sorted_dnas) > 20:
            lines.append(f"... 还有 {len(sorted_dnas) - 20} 种DNA未显示")
        
        output = '\n'.join(lines)
        self.logger.info(f"\n{output}")

    def add_new_cells(self) -> None:
        """将新生成的细胞添加到世界中"""
        for cell in self.new_cells:
            self.cells.append(cell)
        self.new_cells.clear()  # 清空新细胞列表

    def cells_act(self)-> None:
        """让所有细胞执行动作"""
        prints = []
        self.update_cells_map()  # 先更新地图
        self.add_new_cells()  # 添加新细胞
        for cell in self.cells:
            cell.act()
            self.check_dead(cell)
              
    def check_dead(self, cell) -> None:
        '''检查细胞是否死亡'''
        if cell.dead is True:           
            # 从细胞列表中移除
            self.cells.remove(cell)
            
    def update_cells_map(self) -> None:
        """更新细胞位置映射"""
        self.cells_map = np.zeros((self.width + 1, self.height + 1), dtype=bool)
        for cell in self.cells:
            if cell.dead:
                continue
            x = int(cell.x)
            y = int(cell.y)
            self.cells_map[x, y] = True
                
        
    def draw_tick(self) -> None:
        """绘制当前帧数"""
        drawer_draw_tick(self.screen, self.ticks)
        self.ticks += 1
            
    def update(self, screen: pygame.surface.Surface) -> bool:
        """更新一帧世界"""
        self.screen = screen
        self.screen.fill((0, 0, 0))  # 清屏
        self.cells_act()
        # 统一通过 drawer 渲染（地图与细胞等比例缩放）
        render_frame(self.screen, self)

        self.draw_tick()

        if self.ticks % 100 == 0:
            self.collect_RNAs()
            self.collect_DNAs()
        if len(self.cells) == 0:
            self.logger.info("All cells are dead. Game Over.")
            return False
        
        return True
    