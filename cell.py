import pygame
from typing import List

from config import *

import random
import numpy as np

from glutose import Glutoses

class Cell():
    '''管理单个细胞'''
    
    def __init__(self, x: float, y: float, gene_DNA: str):
        self.x = x
        self.y = y
        self.gene_DNA = gene_DNA
        
        self.energy = CellConfig.original_energy
        self.age = 0
        self.ribosome = 0

        self.glutoses = np.zeros((MapConfig.height, MapConfig.width), dtype=np.uint16)
        self.dead = False
        
        self.transcriptflag = False
    
    @classmethod
    def initialize_cells(self) -> List['Cell']:
        '''初始化细胞'''
        cells = []
        num = CellConfig.original_num
        for _ in range(num):
            # 初始化细胞的坐标
            rawx = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
            x = min(max(0, int(rawx)), MapConfig.width)
            rawy = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
            y = min(max(0, int(rawy)), MapConfig.height)
            
            # 默认基因序列
            gene_DNA = CellConfig.gene_DNA
            cell = Cell(x, y, gene_DNA)
            cells.append(cell)
        return cells
        
    def transcript(self):
        '''基因转录
        基因有：>  ^  + , [ { !
        如果出现多个!,删除偶数个
        'd'  转录为 'd'
        ‘!d' 转录为 'a'
        'w'  转录为 'w'
        '!w' 转录为 's'
        ’+'  转录为 '+'
        '!+‘ 转录为 '-'
        ','  转录为 ','
        '!,' 转录为 '.'
        将所有括号与终止符'!!'相配对。
        '['  转录为 '[int'，如果所在格子葡萄糖数量小于等于[阈值，跳转到int。其中int为相应'!!'的位置
            相应地，'!!'转录为 ']int'，如果所在格子葡萄糖数量大于[阈值，跳转到int，其中int为相应'['的位置
            
        '!['  转录为 ']int'，如果所在格子葡萄糖数量大于[阈值，跳转到int。其中int为相应'!!'的位置
            相应地，'!!'转录为 '[int'，如果所在格子葡萄糖数量小于等于[阈值，跳转到int，其中int为相应'!]'的位置
            
        '{'  转录为 '{int'，如果自身能量小于等于{阈值，跳转到int。其中int为相应'!!'的位置
            相应地，'!!'转录为 '}int'，如果自身能量大于{阈值，跳转到int，其中int为相应'['的位置
            
        '!{'  转录为 '}int'，如果自身能量大于{阈值，跳转到int。其中int为相应'!!'的位置
            相应地，'!!'转录为 '{int'，如果自身能量小于等于{阈值，跳转到int，其中int为相应'['的位置
        '''
        if self.transcriptflag is True:
            return 
        
        self.gene_RNA = ['d', '-', '{0',']0']
        return
        s = self.gene_DNA
        out : List[str] = []
        
        stack_sq : List[int] = []
        stack_br : List[int]=  []  
        
        i, n = 0, len(s)
        while i < n:
            if s[i] == '!' and i + 1 < n:
                s[i] = '_'
                if s[i + 1] == '[':
                    s[i + 1] = ']' 
                elif s[i + 1] == '{':
                    s[i + 1] = '}'
                elif s[i + 1] == 'd':
                    s[i + 1] = 'a'
                elif s[i + 1] == 'w':
                    s[i + 1] = 's'
                elif s[i + 1] == '+':
                    s[i + 1] = '-'
                elif s[i + 1] == ',':
                    s[i + 1] = '.'
                elif s[i + 1] == '!':
                    s[i + 1] = '_'
            i += 1
        
        
        
        self.gene_RNA = ['d', '-', '}0', '{0']
        
        if self.transcriptflag is True:
            return 
        self.gene_RNA = []
        
        
        for base in self.gene_DNA:
            if base == 'd':
                self.gene_RNA.append('d')
            elif base == 'a':
                self.gene_RNA.append('a')
            elif base == 'w':
                self.gene_RNA.append('w')
            elif base == 's':
                self.gene_RNA.append('s')
            elif base == '+':
                self.gene_RNA.append('+')
            elif base == '-':
                self.gene_RNA.append('-')
            elif base.isdigit():
                self.gene_RNA.append(0)
            else:
                pass
                
        self.transcriptflag = True
        return 
    
    def step(self,direction: str):
        '''细胞移动一步'''
        if direction == 'd':
            self.x += 1
            if self.x > MapConfig.width:
                self.x -= MapConfig.width
        elif direction == 'a':
            self.x -= 1
            if self.x < 0:
                self.x += MapConfig.width
        elif direction == 'w':
            self.y -= 1
            if self.y < 0:
                self.y += MapConfig.height
        elif direction == 's':
            self.y += 1
            if self.y > MapConfig.height:
                self.y -= MapConfig.height
        self.energy -= 1
    
    def move(self) -> None:
        '''细胞移动'''
        try:
            command : str = self.gene_RNA[self.ribosome]
            print(command)
            '''command是细胞的指令。
            'd', 'a', 'w', 's' 分别表示向右、左、上、下移动一步
            '-' 将当前位置的葡萄糖数量减少
            '+' 将当前位置的葡萄糖数量增加
            ',' 繁殖
            '.' 死亡
            '[int' 如果所在格子葡萄糖数量小于等于[阈值，跳转到第 int 条指令
            ']int' 如果所在格子葡萄糖数量大于[阈值，跳转到第 int 条指令
            '{int' 如果自身能量小于等于{阈值，跳转到第 int 条指令
            '}int' 如果自身能量大于{阈值，跳转到第 int 条指令
            '''

            if command in ['d', 'a', 'w', 's']:
                self.step(command)
                return
            elif command == '-':
                # 吃
                if self.glutoses.map[self.x, self.y] >= CellConfig.minus_glutose:
                    self.glutoses.map[self.x, self.y] -= CellConfig.minus_glutose
                    self.energy += CellConfig.minus_glutose * CellConfig.energy_per_glutose
                return
            elif command == '+':
                # 吐
                self.glutoses.map[self.x, self.y] += CellConfig.plus_glutose
                self.energy -= CellConfig.plus_glutose * CellConfig.energy_per_glutose
                print(f'Map : {np.shape(self.glutoses.map)}')
                return
            elif command == ',':
                return
            
            elif command == '.':
                self.die()
                return
                
            elif command.startswith('['):
                target = int(command[1:])
                if self.glutoses.map[self.x, self.y] == 0:
                    self.ribosome = target
                else:
                    self.ribosome += 1
                self.move()
                return
            elif command.startswith(']'):
                target = int(command[1:])
                if self.glutoses.map[self.x, self.y] > 0:
                    self.ribosome = target
                else:
                    self.ribosome += 1
                self.move()
                return
            
            elif command.startswith('{'):
                target = int(command[1:])
                if self.energy > CellConfig.criticalpoint:
                    self.ribosome = target
                else:
                    self.ribosome += 1
                self.move()
                return
            elif command.startswith('}'):
                target = int(command[1:])
                if self.energy <= CellConfig.criticalpoint:
                    self.ribosome = target
                else:
                    self.ribosome += 1
                self.move()
                return
                
        except Exception as e:
            self.die()
            print(f'Cell at ({self.x},{self.y}) died due to error: {e}.')
            self.gene_DNA = str(e)
      
    def update_status(self):
        '''在每次移动后更新细胞的状态'''
        self.age += 1
        self.ribosome += 1
        if self.energy <= 0 : 
            self.die()
            
        
    def act(self) -> int:
        '''细胞行为'''
        energy_tic = self.energy
        # 转录
        self.transcript()

        # 移动
        self.move()

        # 更新状态
        self.update_status()
        
        energy_tac = self.energy
        self.loss_energy = energy_tic - energy_tac
    
    def die(self):
        '''细胞死亡'''
        self.dead = True
    
    def draw(self, screen: pygame.surface.Surface) -> None:
        '''绘制细胞'''
        pygame.draw.rect(screen, (0, 0, 255), (int(self.x), int(self.y),1,1),1)