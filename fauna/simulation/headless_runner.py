from __future__ import annotations

import pygame

from ..config import DispConfig, MapConfig, RandomConfig, set_global_seed
from ..world import World


def run_headless(max_ticks: int) -> dict[int, int]:
    set_global_seed(RandomConfig.seed)
    pygame.init()
    scale = max(1, int(DispConfig.scale))
    width = int(MapConfig.width)
    height = int(MapConfig.height)
    screen = pygame.Surface((width * scale, height * scale))
    world = World(width, height)
    counts: dict[int, int] = {}
    while world.ticks < max_ticks:
        if world.update(screen) is False:
            break
        if world.ticks % 100 == 0:
            counts[world.ticks] = len(world.cells)
    pygame.quit()
    return counts
