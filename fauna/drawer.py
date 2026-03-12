import pygame
import numpy as np
from typing import Iterable

from .config import MapConfig, UITheme

EMPTY_RNA_COLOR = UITheme.state_error
AGE_YOUNGEST_COLOR = (76, 201, 240)   # #4CC9F0
AGE_1TICK_COLOR = (67, 97, 238)       # #4361EE
AGE_2PLUS_COLOR = (114, 9, 183)       # #7209B7
DIRECTION_KEYS = {'w', 'a', 's', 'd'}
DIRECTION_ARROW_MAP = {
    'w': '↑',
    'a': '←',
    's': '↓',
    'd': '→',
}

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


def draw_cells(surface: pygame.Surface, cells: Iterable, skip_directional: bool = False) -> None:
    for c in cells:
        if getattr(c, 'dead', False):
            continue
        if skip_directional and getattr(c, 'direction', None) in DIRECTION_KEYS:
            continue
        draw_cell_on(surface, c.x, c.y, get_cell_color(c))


def _overlay_arrow_color(fill_color: tuple[int, int, int]) -> tuple[int, int, int]:
    # 按亮度自动选择深/浅箭头色，保证在细胞底色上可读。
    luminance = 0.299 * fill_color[0] + 0.587 * fill_color[1] + 0.114 * fill_color[2]
    return UITheme.bg_base if luminance > 160 else UITheme.text_primary


def draw_direction_arrows(surface: pygame.Surface, cells: Iterable, grid_size: tuple[int, int]) -> None:
    grid_w, grid_h = grid_size
    if grid_w <= 0 or grid_h <= 0:
        return
    scale_x = surface.get_width() / float(grid_w)
    scale_y = surface.get_height() / float(grid_h)
    font_cache: dict[int, pygame.font.Font] = {}

    for cell in cells:
        if getattr(cell, 'dead', False):
            continue
        direction = getattr(cell, 'direction', None)
        if direction not in DIRECTION_KEYS:
            continue
        cell_x = int(cell.x)
        cell_y = int(cell.y)
        left = int(cell_x * scale_x)
        top = int(cell_y * scale_y)
        right = int((cell_x + 1) * scale_x)
        bottom = int((cell_y + 1) * scale_y)
        if right <= left:
            right = left + 1
        if bottom <= top:
            bottom = top + 1
        block_w = max(1, right - left)
        block_h = max(1, bottom - top)
        font_size = max(8, int(min(block_w, block_h) * 0.9))
        font = font_cache.get(font_size)
        if font is None:
            font = pygame.font.SysFont('Consolas', font_size)
            font_cache[font_size] = font
        arrow = DIRECTION_ARROW_MAP.get(direction, '')
        if not arrow:
            continue
        arrow_surface = font.render(arrow, True, _overlay_arrow_color(get_cell_color(cell)))
        arrow_x = left + (block_w - arrow_surface.get_width()) // 2
        arrow_y = top + (block_h - arrow_surface.get_height()) // 2
        surface.blit(arrow_surface, (arrow_x, arrow_y))


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
    draw_cells(base, world.cells, skip_directional=False)

    # 如需在此绘制 tick，可取消注释：
    # draw_tick(base, world.ticks)

    # 放大到目标窗口大小
    scaled = pygame.transform.scale(base, target_surface.get_size())
    target_surface.blit(scaled, (0, 0))
    draw_direction_arrows(target_surface, world.cells, base_size)

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
