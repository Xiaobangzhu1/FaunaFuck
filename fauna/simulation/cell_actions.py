from __future__ import annotations

import random

from ..config import CellConfig, MapConfig
from ..dna_processing import mutate_DNA
from .rna_executor import execute_rna


def move(cell, direction: str) -> bool:
    cell.lock()
    if direction == 'd':
        new_x = int(cell.x + 1)
        if new_x >= MapConfig.width:
            return False
        if not cell.world.cells_map[new_x, int(cell.y)]:
            cell.x = new_x
            cell.direction = 'd'
            return True
        return False
    if direction == 'a':
        new_x = int(cell.x - 1)
        if new_x < 0:
            return False
        if not cell.world.cells_map[new_x, int(cell.y)]:
            cell.x = new_x
            cell.direction = 'a'
            return True
        return False
    if direction == 'w':
        new_y = int(cell.y - 1)
        if new_y < 0:
            return False
        if not cell.world.cells_map[int(cell.x), new_y]:
            cell.y = new_y
            cell.direction = 'w'
            return True
        return False
    if direction == 's':
        new_y = int(cell.y + 1)
        if new_y >= MapConfig.height:
            return False
        if not cell.world.cells_map[int(cell.x), new_y]:
            cell.y = new_y
            cell.direction = 's'
            return True
        return False
    return False


def change_number(cell, command: str) -> None:
    channel = int(cell.channel) & 0xFF
    x = int(cell.x)
    y = int(cell.y)
    current = int(cell.NTs.map[x, y, channel])
    if command == '+':
        cell.NTs.map[x, y, channel] = min(255, current + 1)
    elif command == '-':
        cell.NTs.map[x, y, channel] = max(0, current - 1)


def reproduce(cell) -> bool:
    fail_rate = float(getattr(CellConfig, 'reproduction_fail_rate', 0.0))
    fail_rate = min(1.0, max(0.0, fail_rate))
    if fail_rate > 0.0 and random.random() < fail_rate:
        return False

    child_dna, _ = mutate_DNA(cell.gene_DNA)
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    preferred_map = {'d': (1, 0), 'a': (-1, 0), 's': (0, 1), 'w': (0, -1)}
    preferred = preferred_map.get(getattr(cell, 'direction', None))
    ordered: list[tuple[int, int]] = []
    if preferred is not None and preferred in directions:
        ordered.append(preferred)
        directions.remove(preferred)
    if CellConfig.randomize_reproduction_direction:
        random.shuffle(directions)
    ordered.extend(directions)
    for dx, dy in ordered:
        new_x = int(cell.x + dx)
        new_y = int(cell.y + dy)
        if new_x < 0 or new_x >= MapConfig.width or new_y < 0 or new_y >= MapConfig.height:
            continue
        if cell.world.reserve_position(new_x, new_y):
            child_cell = cell.__class__(new_x, new_y, child_dna, cell.NTs, world=cell.world)
            child_cell.channel = cell.channel
            child_cell.locked = True
            cell.world.new_cells.append(child_cell)
            return True
    return False


def die(cell, reason: str) -> None:
    if not cell.locked:
        cell.dead = True
    if CellConfig.debug_mode:
        cell.logger.info('Cell at (%s,%s) died. Reason: %s', int(cell.x), int(cell.y), reason)


def jump_forward(cell, command: str) -> None:
    target = int(command[1:])
    x = int(cell.x)
    y = int(cell.y)
    channel = int(cell.channel) & 0xFF
    value = int(cell.NTs.map[x, y, channel])
    if value == 0:
        cell.ribosome = target
    else:
        cell.move_ribosome()


def jump_backward(cell, command: str) -> None:
    target = int(command[1:])
    x = int(cell.x)
    y = int(cell.y)
    channel = int(cell.channel) & 0xFF
    value = int(cell.NTs.map[x, y, channel])
    if value > 0:
        cell.ribosome = target
    else:
        cell.move_ribosome()


def change_channel(cell, command: str) -> None:
    if command == '>':
        cell.channel = (cell.channel + 1) % MapConfig.channels
    elif command == '<':
        cell.channel = (cell.channel - 1) % MapConfig.channels


def move_ribosome(cell, position: str = 'forward') -> None:
    if position == 'forward':
        cell.ribosome += 1
    elif position == 'backward':
        cell.ribosome -= 1
    if CellConfig.ribosome_loop:
        if cell.ribosome >= len(cell.gene_RNA):
            cell.ribosome = 0
        elif cell.ribosome < 0:
            cell.ribosome = len(cell.gene_RNA) - 1


def check_death(cell) -> None:
    if not hasattr(cell, 'world') or cell.world is None:
        return
    needed = CellConfig.death_neighbor_threshold
    # Death neighborhood is fixed to orthogonal 4-neighbors:
    # up, down, left, right.
    surroundings = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    x0, y0 = int(cell.x), int(cell.y)
    count = 0
    for dx, dy in surroundings:
        nx = (x0 + dx) % MapConfig.width
        ny = (y0 + dy) % MapConfig.height
        if cell.world.cells_map[nx, ny]:
            count += 1
    if count >= needed:
        cell.die('Overcrowded death.')


def lock(cell) -> None:
    cell.locked = True


def unlock(cell) -> None:
    cell.locked = False


def act(cell) -> None:
    cell.unlock()
    cell.check_death()
    if cell.dead:
        return
    execute_rna(cell)
    cell.check_death()
