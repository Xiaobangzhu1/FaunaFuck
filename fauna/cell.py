from __future__ import annotations

import pygame
from typing import List, Optional, TYPE_CHECKING

from .nts import NTs
from .config import *

import random
import numpy as np
from .config import CellConfig
import logging
from .drawer import draw_cell as drawer_draw_cell
from .simulation import cell_actions, cell_factory

if TYPE_CHECKING:
    from .world import World

class Cell():
    '''管理单个细胞'''
    
    def __init__(self, x: float, y: float, gene_DNA: str, NTs: 'NTs', world: 'World'):
        self.logger = logging.getLogger("fauna.cell")
        self.x = x
        self.y = y
        self.channel = 0
        self.gene_DNA = gene_DNA
        self.gene_RNA: List[str] = []  # RNA 序列
        self.transcripted_flag = False
        self.transcript()
        
        self.ribosome = 0

        self.NTs = NTs
        self.world = world
        self.dead = False
        self.age_ticks = 0
        self.direction: Optional[str] = random.choice(['w', 'a', 's', 'd'])
        
        
    
    @classmethod
    def initialize_cells(cls, NTs : 'NTs', world: 'World') -> List['Cell']:
        '''初始化细胞'''
        return cell_factory.build_initial_cells(cls, NTs, world)
    
    @classmethod
    def create_cell_from_DNA(cls, gene_DNA: str, x: int, y: int, NTs: 'NTs', world: 'World', ribosome = 0, channel = 0) -> 'Cell':
        '''通过DNA创建细胞'''
        return cell_factory.create_cell_from_dna(cls, gene_DNA, x, y, NTs, world, ribosome, channel)
    
    def transcript(self):
        '''基因转录

        !d = a;  ?d = w ;  !?d = ?!d = s
        !+ = -;  ?+ = , ;  !?+ = ?!+ = .
        ![ = ];  ?[ = > ;  !?[ = ?![ = <
        !!/?? ： pause
        '''
        cell_factory.transcribe_cell(self)
    
    def move(self,direction: str) -> bool:
        '''细胞移动一步，撞墙或超出边界则停止移动但仍消耗移动次数
        Returns:
            bool: 是否成功移动到新位置
        '''
        return cell_actions.move(self, direction)

    def change_number(self, command: str) -> None:
        cell_actions.change_number(self, command)
    
    def reproduce(self) -> bool:
        '''细胞自我复制，找不到空位则繁殖失败但仍消耗繁殖次数
        Returns:
            bool: 是否成功繁殖
        '''
        return cell_actions.reproduce(self)
        
        
    
    def die(self, reason: str) -> None:
        cell_actions.die(self, reason)

    def kill(self) -> bool:
        return cell_actions.kill_front_cell(self)

    def jump_forward(self, command: str) -> None:
        """'[' 指令: 若当前 (x,y) 的当前 channel 值为 0 则跳转, 否则 ribosome+1"""
        cell_actions.jump_forward(self, command)
        return

    def jump_backward(self, command: str) -> None:
        "']' 指令: 若当前 (x,y) 的当前 channel 值 > 0 则跳转, 否则 ribosome+1"
        cell_actions.jump_backward(self, command)
        return
    
    def change_channel(self, command: str) -> None:
        cell_actions.change_channel(self, command)
            
    def move_ribosome(self, position: str = 'forward') -> None:
        cell_actions.move_ribosome(self, position)
    
    def do_RNA(self) -> None:
        '''执行RNA指令
        Args:
            None
        Returns:
            None
            对应RNA指令集执行相应操作
            d/a/w/s : 移动
            + : 增加所在单元格的数字
            - : 减少所在单元格的数字
            , : 自我复制
            . : 自杀
            [int : 如果所在单元格数字为0，跳转到int
            ]int : 如果所在单元格数字不为0，跳转到int
            > : 增加所在channel的值
            < : 减少所在channel的值
            p : 停止一刻
        '''
        from .simulation.rna_executor import execute_rna

        execute_rna(self)
      
    def check_death(self) -> None:
        """若**所有**相邻格都被占满则死亡"""
        cell_actions.check_death(self)
            
        
    def lock(self):
        "进入无敌状态"
        cell_actions.lock(self)
        
    def unlock(self):
        "退出无敌状态"
        cell_actions.unlock(self)
        
    def act(self) -> None:
        '''细胞行为'''
        cell_actions.act(self)
        

    def draw_cell(self, screen: pygame.surface.Surface) -> None:
        '''绘制细胞'''
        drawer_draw_cell(self.x, self.y, screen)
        
if __name__ == '__main__':
    # When run directly, print sync message and run main.
    # Avoid importing `main` at module import time to prevent circular imports
    print('Cell Synchronized')
    from main import main as _main
    _main()
