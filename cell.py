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
        self.transcript()
        
        self.ribosome = 0

        self.NTs = NTs
        self.world = world
        self.dead = False
        
        self.transcripted_flag = False
        
    
    @classmethod
    def initialize_cells(cls, NTs : 'NTs', world: 'World') -> List['Cell']:
        '''初始化细胞'''
        cells = []
        num = CellConfig.original_num
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
        A T C G
        
        AA = d; AT = a; AC = w; AG = s
        TA = +; TT = -; TC = ,; TG = .
        CA = [; CT = ]; CC = >; CG = <
        GA = start/pause; GT = stop; GC = rep
        
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
        
        def _first_clean_RNA(translated_RNA: List[str]) -> List[str]:
            '''清理.（死亡）之后的RNA序列'''
            cleaned_RNA = []
            for command in translated_RNA:
                cleaned_RNA.append(command)
                if command == '.':
                    break
            return cleaned_RNA
        
        def _match_RNA(translated_RNA: List[str]) -> List[str]:
            '''为括号添加跳转位置'''
            stack = []
            matched_RNA = translated_RNA.copy()
            for i, command in enumerate(translated_RNA):
                if command == '[':
                    stack.append(i)
                elif command == ']':
                    if len(stack) == 0:
                        continue
                    j = stack.pop()
                    matched_RNA[j] = f'[{i}'
                    matched_RNA[i] = f']{j}'
            return matched_RNA
        
        def _second_clean_RNA(matched_RNA: List[str]) -> List[str]:
            '''清理RNA序列，去除无效的[]指令和无效命令'''
            valid_commands = {'d', 'a', 'w', 's', '+', '-', ',', '.', 'p'}
            cleaned_RNA = []
            for command in matched_RNA:
                if command.startswith('[') or command.startswith(']'):
                    if command[1:].isdigit():
                        cleaned_RNA.append(command)
                elif command in valid_commands:
                    cleaned_RNA.append(command)
            return cleaned_RNA
        
        def _process(DNA: str) -> List[str]:
            cutted_DNA = _cut_DNAs(DNA)
            translated_RNA = _translate_cutted_DNA(cutted_DNA)
            first_cleaned_RNA = _first_clean_RNA(translated_RNA)
            matched_RNA = _match_RNA(first_cleaned_RNA)
            cleaned_RNA = _second_clean_RNA(matched_RNA)
            return cleaned_RNA
        
        DNA = self.gene_DNA
        RNA = _process(DNA)
        self.gene_RNA = RNA
    
    def move(self,direction: str):
        '''细胞移动一步'''
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
            self.NTs.map[x, y, ch] = min(255, self.NTs.map[x, y, ch] + 1)
        elif command == '-':
            ch = int(self.channel) & 0xFF
            x = int(self.x)
            y = int(self.y)
            self.NTs.map[x, y, ch] = max(0, self.NTs.map[x, y, ch] - 1)
    
    def reproduce(self) -> None:
        '''细胞自我复制'''
        from DNA_mutation_rules import mutate_DNA
        child_DNA, mutated = mutate_DNA(self.gene_DNA)
        if mutated:
            self.logger.info(f'Cell mutated during reproduction. New DNA: {child_DNA}')
        x = self.x
        y = self.y
        # 尝试在附近生成新细胞
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(directions)
        for dx, dy in directions:
            new_x = x + dx
            new_y = y + dy
            new_x = (new_x + MapConfig.width) % MapConfig.width
            new_y = (new_y + MapConfig.height) % MapConfig.height
            if not self.world.cells_map[int(new_x), int(new_y)]:
                # 位置空闲，生成新细胞
                child_cell = Cell(new_x, new_y, child_DNA, self.NTs, world=self.world)
                self.world.new_cells.append(child_cell)  # 取消注释并根据需要修改
                break  # 成功复制后退出
        return
        
        
    
    def die(self, reason: str) -> None:
        self.dead = True

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
            self.die(f'Error: {e}')
            self.gene_DNA = str(e)
      
    def check_death(self) -> None:
        """若**所有**相邻格都被占满则死亡"""
        if not hasattr(self, 'world') or self.world is None:
            return
        needed = CellConfig.die_mode
        offsets = [(1,0),(-1,0),(0,1),(0,-1), (1,1),(1,-1),(-1,1),(-1,-1)]
        x0, y0 = int(self.x), int(self.y)
        cnt = 0
        for dx, dy in offsets:
            nx = (x0 + dx) % MapConfig.width
            ny = (y0 + dy) % MapConfig.height
            if self.world.cells_map[nx, ny]:
                cnt += 1
        if cnt >= needed:
            self.die('Overcrowded death.')
            
        
    def act(self) -> None:
        '''细胞行为'''
        # 转录
        if CellConfig.debug_mode:
            self.logger.debug(f'Transcripting cell at ({self.x}, {self.y})')
        self.transcript()

        if CellConfig.debug_mode:
            self.logger.debug(f'Executing RNA for cell at ({self.x}, {self.y})')
        # 移动
        self.do_RNA()
        
        if CellConfig.debug_mode:
            self.logger.debug(f'Checking death for cell at ({self.x}, {self.y})')
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