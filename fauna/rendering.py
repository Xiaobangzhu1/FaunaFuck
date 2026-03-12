from __future__ import annotations

import pygame

from .config import UITheme
from .drawer import draw_tick as drawer_draw_tick, render_frame


def render_world(screen: pygame.surface.Surface, world) -> None:
    screen.fill(UITheme.bg_base)
    render_frame(screen, world)


def draw_tick(world) -> None:
    drawer_draw_tick(world.screen, world.ticks)
