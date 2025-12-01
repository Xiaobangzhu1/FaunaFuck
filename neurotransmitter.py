# neurotransmitter.py
'''葡萄糖管理'''
import pygame
import random
from config import *

import numpy as np

class Neurotransmitters():
    '''管理神经递质'''
    
    def __init__(self):
        self.map = np.zeros((MapConfig.width + 1, MapConfig.height + 1), dtype=np.uint8)
        
        
    @classmethod
    def initialize_glutoses(self) -> 'Neurotransmitters':
        '''初始化葡萄糖'''
        neurotransmitters = Neurotransmitters()
        neurotransmitters.map = np.zeros((MapConfig.width + 1, MapConfig.height + 1), dtype=np.uint8)
        return neurotransmitters


    def spawn(self, loss_energies: int) -> None:
        print(f'Spawning {loss_energies} glutoses')
        xs = np.random.normal(loc=MapConfig.width / 2, scale=MapConfig.width / 8, size=loss_energies)
        ys = np.random.normal(loc=MapConfig.height / 2, scale=MapConfig.height / 8, size=loss_energies)
        xs = np.clip(xs, 0, MapConfig.width - 1)
        ys = np.clip(ys, 0, MapConfig.height - 1)
        xs = xs.astype(np.uint8)
        ys = ys.astype(np.uint8)
        
        
        np.add.at(self.map, (ys, xs), 1)
        
    def draw(self, screen: pygame.surface.Surface) -> None:
        '''绘制神经递质'''
        # 将 glutose_map 的值归一化为 0-255 灰度
        normalized = (np.minimum(255,(self.map != 0) * 255)).clip(0, 255).astype(np.uint8).T
        # 创建单通道红色图像
        grayscale_image = np.stack([np.zeros_like(normalized), normalized, np.zeros_like(normalized)], axis=-1)  # G通道  # shape = (H, W, 3)
        # 转换为 Surface
        surface = pygame.surfarray.make_surface(grayscale_image.swapaxes(0, 1))  # Pygame 要求 (W, H, 3)

        screen.blit(surface, (0, 0))