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
import os


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
        self.pending_positions: set[tuple[int,int]] = set()  # 本帧预占位置
        self.ticks = 0
        
    def collect_RNAs(self):
        """收集并统计所有不同的RNA序列"""
        rna_counts = {}
        for cell in self.cells:
            if not cell.dead:
                raw_RNA = cell.gene_RNA
                RNA = [r[0] for r in raw_RNA if r != '']  # 去除空指令
                rna_str = ''.join(RNA)
                rna_counts[rna_str] = rna_counts.get(rna_str, 0) + 1
        
        # 按数量排序，最多的在前
        sorted_rnas = sorted(rna_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 格式化输出：序号、数量、长度、RNA（截断长序列）
        lines = [f"=== 收集到 {len(sorted_rnas)} 种不同的RNA，共 {len([c for c in self.cells if not c.dead])} 个细胞 ==="]
        for i, (rna, count) in enumerate(sorted_rnas[:20], 1):  # 只显示前20种
            # 将RNA按指令分组显示，更易读
            # 将每个RNA用|分隔，每10个字符换行
            display_rna = rna if len(rna) <= 40 else rna[:37] + "..."
            lines.append(f"#{i:2d} | x{count:4d} | len={len(rna):3d} | {display_rna}")
        
        if len(sorted_rnas) > 20:
            lines.append(f"... 还有 {len(sorted_rnas) - 20} 种RNA未显示")
        
        output_rna = '\n'.join(lines)
        return output_rna

    def collect_DNAs(self) -> str | list:
        #TODO:分离非统计的DNA收集功能
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
        
        output_dna = '\n'.join(lines)
        return output_dna
    
    def save_world_state(self, filename: str) -> None:
        """保存当前世界状态到文件"""
        #创建路径
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            for cell in self.cells:
                f.write(f"({cell.x}, {cell.y})\n")
                f.write(f"{cell.gene_DNA}\n")
        # 同步保存 NTs 三维矩阵到 .npy
        nts_filename = filename.replace('.txt', '_NTs.npy')
        try:
            np.save(nts_filename, self.NTs.map)
            self.logger.info(f"World state saved to {filename}; NTs saved to {nts_filename}")
        except Exception as e:
            self.logger.error(f"Failed to save NTs to {nts_filename}: {e}")

    def read_world_state(self, filename: str) -> None:
        """从文件读取世界状态"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        self.cells.clear()
        i = 0
        while i < len(lines):
            pos_line = lines[i].strip()
            dna_line = lines[i + 1].strip()
            x, y = eval(pos_line)  # 注意：eval 有安全风险，确保文件可信
            cell = Cell.create_cell_from_DNA(dna_line, x, y, self.NTs, self)
            self.cells.append(cell)
            i += 2
        # 读取 NTs 三维矩阵（与快照同名的 *_NTs.npy）
        nts_filename = filename.replace('.txt', '_NTs.npy')
        try:
            nts_map = np.load(nts_filename)
            self.NTs = NTs.initialize_NTs(map=nts_map)
            self.logger.info(f"NTs loaded from {nts_filename} (shape={nts_map.shape})")
        except FileNotFoundError:
            # 不存在则保持当前 NTs（全零），以兼容老存档
            self.logger.warning(f"NTs file not found: {nts_filename}, using blank NTs")
            self.NTs = NTs.initialize_NTs()
        except Exception as e:
            self.logger.error(f"Failed to read NTs from {nts_filename}: {e}")
            self.NTs = NTs.initialize_NTs()
        #NOTE: 得用连接路径: os
        self.update_cells_map()
        self.logger.info(f"World state loaded from {filename}, total cells: {len(self.cells)}")

    def add_new_cells(self) -> None:
        """将新生成的细胞添加到世界中，并清理预占位"""
        for cell in self.new_cells:
            self.cells.append(cell)
        self.new_cells.clear()
        self.pending_positions.clear()
        
    def begin_frame(self) -> None:
        """开始一帧：清空预占位"""
        self.pending_positions.clear()
        
    def reserve_position(self, x: int, y: int) -> bool:
        """尝试预占 (x,y)，避免同一帧重复落子"""
        ix = int(x); iy = int(y)
        if self.cells_map[ix, iy]:
            return False
        if (ix, iy) in self.pending_positions:
            return False
        self.pending_positions.add((ix, iy))
        return True

    def cells_act(self)-> None:
        """让所有细胞执行动作"""
        self.begin_frame()
        self.update_cells_map()  # 用于当前帧占用检查
        for cell in list(self.cells):
            cell.act()
            self.check_dead(cell)
              
        # 一帧结束后统一加入新细胞，并刷新占用图
        self.add_new_cells()
        self.update_cells_map()
        
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
            output_dna = self.collect_DNAs()
            output_rna = self.collect_RNAs()
            output = f"=== 当前帧数: {self.ticks} ===\n{output_dna}\n{output_rna}"
            self.logger.info(output)

        if self.ticks % SaveConfig.autosave_interval == 0 and SaveConfig.autosave_interval > 0:
            filename = os.path.join(SaveConfig.autosave_dir,f'{SaveConfig.autosave_prefix}tick_{self.ticks}.txt')
            self.save_world_state(filename)

        if len(self.cells) == 0:
            self.logger.info("All cells are dead. Game Over.")
            return False
        
        return True
