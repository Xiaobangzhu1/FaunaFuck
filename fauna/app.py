from __future__ import annotations

import os
from pathlib import Path

import pygame

from .config import DispConfig, LogConfig, MapConfig, RandomConfig, SaveConfig, UITheme, set_global_seed
from .control_panel import ControlPanel
from .logging_setup import setup_logging
from .world import World

TICK_BAR_HEIGHT = 30


def run() -> None:
    set_global_seed(RandomConfig.seed)

    log_file = Path(LogConfig.file)
    if log_file.exists():
        log_file.unlink()

    setup_logging()
    pygame.init()
    tick_font = pygame.font.SysFont('Consolas', 18)

    def _draw_tick_bar(target: pygame.Surface, world_obj: World, tick_rect: pygame.Rect) -> None:
        pygame.draw.rect(target, UITheme.bg_card, tick_rect)
        pygame.draw.line(target, UITheme.border, (tick_rect.left, tick_rect.bottom - 1), (tick_rect.right, tick_rect.bottom - 1), 1)
        tick_label = tick_font.render(f'Tick: {world_obj.ticks}', True, UITheme.state_info)
        target.blit(tick_label, (tick_rect.x + 10, tick_rect.y + 5))

    def _build_layout() -> tuple[int, int, pygame.Rect, pygame.Rect, pygame.Rect]:
        scale = max(1, int(DispConfig.scale))
        map_width = max(1, int(MapConfig.width) * scale)
        map_height = max(1, int(MapConfig.height) * scale)
        panel_width = map_width
        window_width = map_width + panel_width
        window_height = map_height + TICK_BAR_HEIGHT
        tick_rect = pygame.Rect(0, 0, map_width, TICK_BAR_HEIGHT)
        map_rect = pygame.Rect(0, TICK_BAR_HEIGHT, map_width, map_height)
        panel_rect = pygame.Rect(map_width, 0, panel_width, window_height)
        return window_width, window_height, tick_rect, map_rect, panel_rect

    def _create_screen(width: int, height: int) -> pygame.Surface:
        flags = pygame.DOUBLEBUF
        try:
            return pygame.display.set_mode((width, height), flags, vsync=1)
        except TypeError:
            return pygame.display.set_mode((width, height), flags)

    window_width, window_height, tick_rect, map_rect, panel_rect = _build_layout()
    screen = _create_screen(window_width, window_height)
    pygame.display.set_caption('Fauna F**k')

    SaveConfig.read = 0
    SaveConfig.read_path = ''
    world = World(MapConfig.width, MapConfig.height, start_empty=True)
    world.logger.info('Sandbox mode started: empty world, save read disabled.')
    panel = ControlPanel()
    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(DispConfig.fps)
        recreate_display = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if panel.handle_event(event, world):
                recreate_display = True

        if recreate_display:
            window_width, window_height, tick_rect, map_rect, panel_rect = _build_layout()
            screen = _create_screen(window_width, window_height)

        screen.fill(UITheme.bg_base)
        if world.update(screen.subsurface(map_rect), simulate=not world.paused, draw_tick_on_map=False) is False:
            running = False
        _draw_tick_bar(screen, world, tick_rect)

        panel.render(screen, world, panel_rect)
        pygame.display.flip()

    filename = os.path.join(SaveConfig.autosave_dir, 'final_stats.txt')
    world.save_world_state(filename)
