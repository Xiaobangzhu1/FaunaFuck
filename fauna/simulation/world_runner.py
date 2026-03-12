from __future__ import annotations

import os

import numpy as np

from ..config import SaveConfig
from ..world_persistence import save_world_state
from .world_stats import build_tick_summary


def begin_frame(world) -> None:
    world.pending_positions.clear()


def reserve_position(world, x: int, y: int) -> bool:
    ix = int(x)
    iy = int(y)
    if world.cells_map[ix, iy]:
        return False
    if (ix, iy) in world.pending_positions:
        return False
    world.pending_positions.add((ix, iy))
    return True


def add_new_cells(world) -> None:
    for cell in world.new_cells:
        world.cells.append(cell)
    world.new_cells.clear()
    world.pending_positions.clear()


def check_dead(world, cell) -> None:
    if cell.dead is True:
        world.cells.remove(cell)


def update_cells_map(world) -> None:
    world.cells_map = np.zeros((world.width + 1, world.height + 1), dtype=bool)
    for cell in world.cells:
        if cell.dead:
            continue
        x = int(cell.x)
        y = int(cell.y)
        world.cells_map[x, y] = True


def cells_act(world) -> None:
    begin_frame(world)
    update_cells_map(world)
    for cell in list(world.cells):
        if not cell.dead:
            cell.age_ticks = int(getattr(cell, 'age_ticks', 0)) + 1
        cell.act()
        check_dead(world, cell)
    add_new_cells(world)
    update_cells_map(world)


def log_periodic_summary(world) -> None:
    if world.ticks % 100 == 0:
        world.logger.info(build_tick_summary(world))


def autosave_if_needed(world) -> None:
    if world.ticks % SaveConfig.autosave_interval == 0 and SaveConfig.autosave_interval > 0:
        filename = os.path.join(SaveConfig.autosave_dir, f'{SaveConfig.autosave_prefix}tick_{world.ticks}.txt')
        save_world_state(world, filename)


def should_stop(world) -> bool:
    if getattr(world, 'allow_empty_world', False):
        return False
    if len(world.cells) == 0:
        world.logger.info('All cells are dead. Game Over.')
        return True
    return False
