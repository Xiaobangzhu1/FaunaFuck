from __future__ import annotations

import pygame
from typing import List, Optional, TYPE_CHECKING

from NTs import NTs
from config import *

import random
import numpy as np
from config import CellConfig
import logging
from drawer import draw_cell as drawer_draw_cell

#TODO：优化细胞类的速度
    #TODO：减少属性访问次数
    #TODO：减少方法调用次数
    #TODO：减少转录次数
if TYPE_CHECKING:
    from world import World

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
        
        
    
    @classmethod
    def initialize_cells(cls, NTs : 'NTs', world: 'World') -> List['Cell']:
        '''初始化细胞'''
        cells = []
        num = CellConfig.original_num
        if CellConfig.cell_subculture:
            for gene_DNA, count in CellConfig.cell_subculture:
                count = int(count * CellConfig.cell_subculture_survive_rate)
                for _ in range(count):
                    rawx = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
                    x = min(max(0, int(rawx)), MapConfig.width)
                    rawy = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
                    y = min(max(0, int(rawy)), MapConfig.height) 
                    cell = Cell(x, y, gene_DNA, NTs, world=world)
                    cells.append(cell)
            return cells
        if CellConfig.pure_mode:
            num = 1
            x = MapConfig.width // 2
            y = MapConfig.height // 2
            gene_DNA = CellConfig.gene_DNA
            cell = Cell(x, y, gene_DNA, NTs, world=world)
            cells.append(cell)
            return cells
        else:
            for _ in range(num):
                # 初始化细胞的坐标
                rawx = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
                x = min(max(0, int(rawx)), MapConfig.width)
                rawy = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
                y = min(max(0, int(rawy)), MapConfig.height) 
                # 默认基因序列
                gene_DNA = CellConfig.gene_DNA
                cell = Cell(x, y, gene_DNA, NTs, world=world)
                cells.append(cell)
            return cells
    
    def transcript(self):
        '''基因转录

        !d = a;  ?d = w ;  !?d = ?!d = s
        !+ = -;  ?+ = , ;  !?+ = ?!+ = .
        ![ = ];  ?[ = > ;  !?[ = ?![ = <
        !!/?? ： pause
        '''

        def _cut_DNAs(DNA : str) -> List[str]:
            '''将基因序列切割为片段'''
            s = DNA
            tokens = []
            base_set = ['d', '+', '[']
            stop_set = ['??']
            duo_set = ['!d', '?d', '!+','?+','![', '?[', '!!', '??']
            tri_set = ['!?d', '?!d', '!?+', '?!+', '!?[', '?![']
            fraction = []
            i = 0
            while i < len(DNA):
                if i + 2 <= len(s) and s[i:i+2] in stop_set:
                    break
                # 三字符
                if i + 3 <= len(s) and s[i:i+3] in tri_set:
                    tokens.append(s[i:i+3])
                    i += 3
                    continue
                # 两字符
                if i + 2 <= len(s) and s[i:i+2] in duo_set:
                    tokens.append(s[i:i+2])
                    i += 2
                    continue
                # 单字符
                if s[i] in base_set:
                    tokens.append(s[i])
                    i += 1
                    continue
                # 噪声跳过
                i += 1

            return tokens
                
        def _translate_cutted_DNA(cutted_DNA: List[str]) -> List[str]:
            '''将切割后的DNA转录为RNA'''
            translate_dict = {
                'd' : 'd', '!d' : 'a', '?d' : 'w', '!?d' : 's', '?!d' : 's',
                '+' : '+', '!+' : '-', '?+' : ',', '!?+' : '.', '?!+' : '.',
                '[' : '[', '![' : ']', '?[' : '>', '!?[' : '<', '?![' : '<',
                '!!' : 'p'
            }
            translated_RNA = [translate_dict[token] for token in cutted_DNA if token in translate_dict]
            return translated_RNA

        def _match_RNA(translated_RNA: List[str]) -> List[str]:
            '''为括号添加跳转位置，丢弃没有配对的括号'''
            stack = []
            matched_indices = set()  # 记录成功配对的索引
            
            # 第一遍：找出所有配对的括号
            for i, command in enumerate(translated_RNA):
                if command == '[':
                    stack.append(i)
                elif command == ']':
                    if len(stack) > 0:
                        j = stack.pop()
                        matched_indices.add(i)
                        matched_indices.add(j)
            
            # 第二遍：构建结果，只保留配对的括号和非括号命令
            result = []
            index_map = {}  # 旧索引到新索引的映射
            
            for i, command in enumerate(translated_RNA):
                if command in ['[', ']']:
                    if i in matched_indices:
                        index_map[i] = len(result)
                        result.append(command)
                else:
                    result.append(command)
            
            # 第三遍：为配对的括号添加跳转位置
            stack = []
            for i, command in enumerate(result):
                if command == '[':
                    stack.append(i)
                elif command == ']':
                    if len(stack) > 0:
                        j = stack.pop()
                        result[j] = f'[{i}'
                        result[i] = f']{j}'
            
            return result

        def _process(DNA: str) -> List[str]:
            RNA = _cut_DNAs(DNA)
            RNA = _translate_cutted_DNA(RNA)
            RNA = _match_RNA(RNA)

            return RNA
            
        if self.transcripted_flag:
            return
        DNA = self.gene_DNA
        RNA = _process(DNA)
        self.gene_RNA = RNA
        if CellConfig.debug_mode:
            self.logger.info(f'Cell at ({int(self.x)},{int(self.y)}) transcribed DNA to RNA: {self.gene_RNA}')
    
    def move(self,direction: str):
        '''细胞移动一步'''
        self.lock()
        if direction == 'd' :
            x = int(self.x)
            new_x = self.x + 1
            new_x = (new_x + MapConfig.width) % MapConfig.width
            if not self.world.cells_map[int(new_x), int(self.y)]:
                self.x = new_x
        elif direction == 'a':
            x = int(self.x)
            new_x = self.x - 1
            new_x = (new_x + MapConfig.width) % MapConfig.width
            if not self.world.cells_map[int(new_x), int(self.y)]:
                self.x = new_x
        elif direction == 'w':
            new_y = self.y - 1
            new_y = (new_y + MapConfig.height) % MapConfig.height
            if not self.world.cells_map[int(self.x), int(new_y)]:
                self.y = new_y
        elif direction == 's':
            new_y = self.y + 1
            new_y = (new_y + MapConfig.height) % MapConfig.height
            if not self.world.cells_map[int(self.x), int(new_y)]:
                self.y = new_y

    def change_number(self, command: str) -> None:
        if command == '+':
            ch = int(self.channel) & 0xFF
            x = int(self.x)
            y = int(self.y)
            current = int(self.NTs.map[x, y, ch])
            self.NTs.map[x, y, ch] = min(255, current + 1)
        elif command == '-':
            ch = int(self.channel) & 0xFF
            x = int(self.x)
            y = int(self.y)
            current = int(self.NTs.map[x, y, ch])
            self.NTs.map[x, y, ch] = max(0, current - 1)
    
    def reproduce(self) -> None:
        '''细胞自我复制'''
        from DNA_mutation_rules import mutate_DNA
        child_DNA, mutated = mutate_DNA(self.gene_DNA)
        x = self.x
        y = self.y
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        if CellConfig.randomize_reproduction_direction:
            random.shuffle(directions)
        for dx, dy in directions:
            new_x = (x + dx + MapConfig.width) % MapConfig.width
            new_y = (y + dy + MapConfig.height) % MapConfig.height
            # 同帧预占位，避免重复落子
            if self.world.reserve_position(int(new_x), int(new_y)):
                child_cell = Cell(new_x, new_y, child_DNA, self.NTs, world=self.world)
                child_cell.channel = self.channel
                child_cell.locked = True  # 新细胞无敌一回合
                if mutated :
                    child_cell.transcripted_flag = False
                else:
                    child_cell.transcripted_flag = True
                    child_cell.gene_RNA = self.gene_RNA.copy()
                self.world.new_cells.append(child_cell)
                break
        return
        
        
    
    def die(self, reason: str) -> None:
        if not self.locked:
            self.dead = True
        if CellConfig.debug_mode:
            self.logger.info(f'Cell at ({int(self.x)},{int(self.y)}) died. Reason: {reason}')

    def jump_forward(self, command: str) -> None:
        """'[' 指令: 若当前 (x,y) 的当前 channel 值为 0 则跳转, 否则 ribosome+1"""
        target = int(command[1:])
        x = int(self.x)
        y = int(self.y)
        ch = int(self.channel) & 0xFF
        val = int(self.NTs.map[x, y, ch])
        if val == 0:
            self.ribosome = target
        else:
            self.ribosome += 1
        return

    def jump_backward(self, command: str) -> None:
        "']' 指令: 若当前 (x,y) 的当前 channel 值 > 0 则跳转, 否则 ribosome+1"
        target = int(command[1:])
        x = int(self.x)
        y = int(self.y)
        ch = int(self.channel) & 0xFF
        val = int(self.NTs.map[x, y, ch])
        if val > 0:
            self.ribosome = target
        else:
            self.ribosome += 1
        return
    
    def change_channel(self, command: str) -> None:
        if command == '>':
            self.channel = (self.channel + 1) % MapConfig.channels
        elif command == '<':
            self.channel = (self.channel - 1) % MapConfig.channels
            
    def move_ribosome(self) -> None:
        self.ribosome += 1
        if self.ribosome >= len(self.gene_RNA):
            if CellConfig.ribosome_loop:
                self.ribosome = 0
    
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
        if len(self.gene_RNA) == 0:
            return

        try:
            for _ in range(MapConfig.max_instructions):  # 防止无限循环
                command : str = self.gene_RNA[self.ribosome]
            
                if command in ['d', 'a', 'w', 's']:
                    self.move(command)
                    self.move_ribosome()
                    return
                elif command in ['+', '-']:
                    self.change_number(command)
                    self.move_ribosome()
                    return
                elif command == ',':
                    self.reproduce()
                    self.move_ribosome()
                    return
                elif command == '.':
                    self.die('Executed death command.')
                    self.move_ribosome()
                    return
                    
                elif command.startswith('['):
                    self.jump_forward(command)

                elif command.startswith(']'):
                    self.jump_backward(command)
                    
                elif command in ['>', '<']:
                    self.change_channel(command)
                    
                elif command == 'p':
                    self.move_ribosome()
                    return
                    
            raise Exception('Max instructions exceeded')
                
        except Exception as e:
            if CellConfig.debug_mode:
                raise e
            self.die(f'Error: {e}')
            self.gene_DNA = str(e)
      
    def check_death(self) -> None:
        """若**所有**相邻格都被占满则死亡"""
        if not hasattr(self, 'world') or self.world is None:
            return
        needed = CellConfig.die_mode
        if CellConfig.surroundings == 24:
            surroundings = [(-2,-2),(-2,-1),(-2,0),(-2,1),(-2,2),
                            (-1,-2),(-1,-1),(-1,0),(-1,1),(-1,2),
                            (0 ,-2),(0 ,-1),       (0 ,1),(0 ,2),
                            (1 ,-2),(1 ,-1),(1 ,0),(1 ,1),(1 ,2),
                            (2 ,-2),(2 ,-1),(2 ,0),(2 ,1),(2 ,2)]
        elif CellConfig.surroundings == 4:  
            surroundings = [(-1,0),(1,0),(0,-1),(0,1)]
        else: 
            surroundings = [(-1,0),(1,0),(0,-1),(0,1),
                            (-1,-1),(-1,1),(1,-1),(1,1)]
        x0, y0 = int(self.x), int(self.y)
        cnt = 0
        for dx, dy in surroundings:
            nx = (x0 + dx) % MapConfig.width
            ny = (y0 + dy) % MapConfig.height
            if self.world.cells_map[nx, ny]:
                cnt += 1
        if cnt >= needed:
            self.die('Overcrowded death.')
            
        
    def lock(self):
        "进入无敌状态"
        self.locked = True
        
    def unlock(self):
        "退出无敌状态"
        self.locked = False
        
    def act(self) -> None:
        '''细胞行为'''
        # 转录
        self.unlock()
        self.check_death()
        if self.dead:
            return
        self.do_RNA()
        self.check_death()
        
    

    def draw_cell(self, screen: pygame.surface.Surface) -> None:
        '''绘制细胞'''
        drawer_draw_cell(self.x, self.y, screen)
        
if __name__ == '__main__':
    # When run directly, print sync message and run main.
    # Avoid importing `main` at module import time to prevent circular imports
    print('Cell Synchronized')
    from main import main as _main
    _main()