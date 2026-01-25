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

    def set_map(self, new_map) -> None:
        """设置神经递质分布地图。
        接受任意可转为 numpy 数组的输入，并尽量兼容旧存档的形状/类型。
        期望形状为 (width+1, height+1, channels)，dtype 为 uint8。
        """
        arr = np.asarray(new_map)
        expected_shape = (MapConfig.width + 1, MapConfig.height + 1, MapConfig.channels)

        # 若为二维，扩展为多通道（复制同一通道）
        if arr.ndim == 2:
            arr = np.expand_dims(arr, axis=2)
            if MapConfig.channels > 1:
                arr = np.repeat(arr, MapConfig.channels, axis=2)

        # 若通道数不一致但宽高一致，则截断/填充到期望通道数
        if arr.ndim == 3 and (arr.shape[0], arr.shape[1]) == expected_shape[:2] and arr.shape[2] != expected_shape[2]:
            out = np.zeros(expected_shape, dtype=np.uint8)
            min_c = min(arr.shape[2], expected_shape[2])
            out[:, :, :min_c] = arr[:, :, :min_c].astype(np.uint8)
            arr = out

        # 若整体形状仍不匹配，则做裁剪/零填充
        if arr.shape != expected_shape:
            out = np.zeros(expected_shape, dtype=np.uint8)
            min_w = min(arr.shape[0], expected_shape[0]) if arr.ndim >= 1 else 0
            min_h = min(arr.shape[1], expected_shape[1]) if arr.ndim >= 2 else 0
            min_c = min(arr.shape[2], expected_shape[2]) if arr.ndim >= 3 else 0
            out[:min_w, :min_h, :min_c] = arr[:min_w, :min_h, :min_c].astype(np.uint8)
            arr = out

        # 最终确保类型
        self.map = arr.astype(np.uint8, copy=False)
        
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