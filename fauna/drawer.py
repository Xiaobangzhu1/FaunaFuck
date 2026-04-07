import pygame
import numpy as np
from typing import Iterable

from .config import MapConfig, UITheme

EMPTY_RNA_COLOR = UITheme.state_error
AGE_YOUNGEST_COLOR = (76, 201, 240)   # #4CC9F0
AGE_1TICK_COLOR = (67, 97, 238)       # #4361EE
AGE_2PLUS_COLOR = (114, 9, 183)       # #7209B7

def draw_cell_on(surface: pygame.Surface, x: int, y: int, color=(255, 255, 255)) -> None:
    ix = int(x) % MapConfig.width
    iy = int(y) % MapConfig.height
    # 单像素渲染；如需更大显示尺寸，请在 render_frame 中做整体缩放
    surface.set_at((ix, iy), color)

def _interpolate_age_color(age_ticks: int) -> tuple[int, int, int]:
    age = max(0, int(age_ticks))
    if age == 0:
        return AGE_YOUNGEST_COLOR
    if age == 1:
        return AGE_1TICK_COLOR
    return AGE_2PLUS_COLOR

def get_cell_color(cell) -> tuple[int, int, int]:
    if len(getattr(cell, 'gene_RNA', [])) == 0:
        return EMPTY_RNA_COLOR
    return _interpolate_age_color(int(getattr(cell, 'age_ticks', 0)))


def draw_cells(surface: pygame.Surface, cells: Iterable) -> None:
    for c in cells:
        if getattr(c, 'dead', False):
            continue
        draw_cell_on(surface, c.x, c.y, get_cell_color(c))


def draw_tick(surface: pygame.Surface, tick: int) -> None:
    font = pygame.font.SysFont(None, 24)
    text = font.render(f'Tick: {tick}', True, UITheme.state_info)
    surface.blit(text, (10, 10))

def draw_NTs_map(surface: pygame.Surface, NTs_map: np.ndarray) -> None:
    # 将 NTs_map 的值归一化为 0-255 灰度
    normalized = (np.minimum(255,(NTs_map != 0) * 255)).clip(0, 255).astype(np.uint8).T
    # 创建单通道红色图像
    grayscale_image = np.stack([np.zeros_like(normalized), normalized, np.zeros_like(normalized)], axis=-1)  # G通道  # shape = (H, W, 3)
    # 转换为 Surface
    surface_NTs = pygame.surfarray.make_surface(grayscale_image.swapaxes(0, 1))  # Pygame 要求 (W, H, 3)
    surface.blit(surface_NTs, (0, 0))


def render_frame(target_surface: pygame.Surface, world) -> None:
    """在基础尺寸画布上渲染整帧，然后按窗口大小缩放到目标 Surface。
    这样地图与细胞等比例放大，且不改动模拟分辨率。
    """
    base_size = (MapConfig.width, MapConfig.height)
    # 基础画布
    base = pygame.Surface(base_size)
    base.fill(UITheme.bg_base)

    # 如需绘制 NTs 图层，可在此加入（当前 world 未统一调用）
    # 例如：如果 world.NTs.map 是二维或三维矩阵，可以在此转为彩色表面后 blit 到 base

    # 绘制细胞
    draw_cells(base, world.cells)

    # 如需在此绘制 tick，可取消注释：
    # draw_tick(base, world.ticks)

    # 放大到目标窗口大小
    scaled = pygame.transform.scale(base, target_surface.get_size())
    target_surface.blit(scaled, (0, 0))

def draw_cell(x, y, screen: pygame.surface.Surface, color=(255, 255, 255), size: int = 5) -> None:
    """绘制细胞为 size×size 的实心方块，带地图环绕"""
    x = int(x)
    y = int(y)
    size = max(1, int(size))
    half = size // 2
    for dx in range(-half, half + 1):
        for dy in range(-half, half + 1):
            sx = (x + dx + MapConfig.width) % MapConfig.width
            sy = (y + dy + MapConfig.height) % MapConfig.height
            screen.set_at((sx, sy), color)

def draw_NTs(screen: pygame.surface.Surface, NT_map: np.ndarray) -> None:
    # 将 NT_map 的值归一化为 0-255 灰度
    normalized = (np.minimum(255,(NT_map != 0) * 255)).clip(0, 255).astype(np.uint8).T
    # 创建单通道红色图像
    grayscale_image = np.stack([np.zeros_like(normalized), normalized, np.zeros_like(normalized)], axis=-1)  # G通道  # shape = (H, W, 3)
    # 转换为 Surface
    surface = pygame.surfarray.make_surface(grayscale_image.swapaxes(0, 1))  # Pygame 要求 (W, H, 3)
    screen.blit(surface, (0, 0))

# 注意：上方已定义 draw_tick，用于基础画布与缩放渲染。
