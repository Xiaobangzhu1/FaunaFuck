# world.py
'''管理游戏世界'''

import pygame
from typing import List, Optional, Tuple, Union

from cell import Cell
from glutose import Glutoses

from config import *


class World:
    """创建和管理游戏中的所有实体和系统"""
    def __init__(self, width : int, height : int):
        # 基础状态
        self.width = width
        self.height = height
         
        self.cells : List[Cell] = []
        self.glutoses : Glutoses
        
        # 初始化细胞
        self.cells = Cell.initialize_cells()
        self.glutoses = Glutoses.initialize_glutoses()
        
        self.ticks = 0
        
    def act(self)-> int:
        prints = []
        loss_glutoses = 0
        for cell in self.cells:
            cell.glutoses = self.glutoses
            glutoses_tic = cell.glutoses.map.sum()
            
            cell.act()
        
            glutoses_tac = cell.glutoses.map.sum()
            loss_glutose = glutoses_tic - glutoses_tac
            print(f'Cell at ({cell.x},{cell.y}) ate {loss_glutose} glutoses')
            loss_glutoses += loss_glutose
            self.glutoses = cell.glutoses
         
            
            cell.draw(self.screen)
            
            self.check_dead(cell)
            prints.append(f'Cell at ({cell.x},{cell.y}) with energy {cell.energy} and age {cell.age}')
            # 删除被吃掉的葡萄糖

               
        print('\n'.join(prints))
        if loss_glutoses > 0:
            self.glutoses.spawn(loss_glutoses)
            
    def check_dead(self, cell) -> None:
        '''检查细胞是否死亡'''
        if cell.dead is True:
            
            # 从细胞列表中移除
            self.cells.remove(cell)

                
    def draw_glutoses(self) -> None:
        '''绘制葡萄糖'''
        self.glutoses.draw(self.screen)
        
        
    def draw_tick(self) -> None:
        """绘制当前帧数"""
        font = pygame.font.SysFont(None, 24)
        text = font.render(f'Tick: {self.ticks}', True, (0, 0, 0))
        self.screen.blit(text, (10, 10))
        self.ticks += 1
            
    def update(self, screen: pygame.surface.Surface) -> bool:
        """更新一帧世界"""
        self.screen = screen
        self.screen.fill((0, 0, 0))  # 清屏
        
        self.act()
        
        self.draw_glutoses()
        self.draw_tick()
        
        if len(self.cells) == 0:
            print("All cells are dead. Game Over.")
            return False
        
        return True
    
    def collect_gene(self) -> List[str]:
        collected_genes = []
        for cell in self.cells:
            if cell.gene_DNA not in collected_genes:
                collected_genes.append(cell.gene_DNA)
        return collected_genes