# neurotransmitter.py
'''葡萄糖管理'''
import pygame
import random
from config import *

import numpy as np

class NTs():
    '''管理神经递质'''
    
    def __init__(self):
        self.map = np.zeros((MapConfig.width + 1, MapConfig.height + 1, MapConfig.channels), dtype=np.uint8)

        
    @classmethod
    def initialize_NTs(cls, map = None) -> 'NTs':
        '''初始化神经递质'''
        if map is not None:
            NTs_instance = NTs()
            NTs_instance.set_map(map)
            return NTs_instance
        NTs_instance = NTs()
        return NTs_instance
        
    def draw(self, screen: pygame.surface.Surface) -> None:
        '''绘制神经递质'''
        NTs_map = self.map
        
        def _draw_NTs(screen: pygame.surface.Surface, NT_map: np.ndarray) -> None:
            # 将 NT_map 的值归一化为 0-255 灰度
            normalized = (np.minimum(255,(NT_map != 0) * 255)).clip(0, 255).astype(np.uint8).T
            # 创建单通道红色图像
            grayscale_image = np.stack([np.zeros_like(normalized), normalized, np.zeros_like(normalized)], axis=-1)  # G通道  # shape = (H, W, 3)
            # 转换为 Surface
            surface = pygame.surfarray.make_surface(grayscale_image.swapaxes(0, 1))  # Pygame 要求 (W, H, 3)
            screen.blit(surface, (0, 0))
            
        _draw_NTs(screen, NTs_map)