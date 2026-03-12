from __future__ import annotations

import os

import numpy as np

from .nts import NTs


def _normalize_direction(raw: str | None) -> str | None:
    if raw is None:
        return None
    direction = str(raw).strip()
    if direction in {'w', 'a', 's', 'd'}:
        return direction
    return None


def _build_cell(world, x, y, dna_line: str, rbs_line: str, channel_line: str, age: int, direction: str | None):
    cell = world.cell_cls.create_cell_from_DNA(
        dna_line,
        x,
        y,
        world.NTs,
        world,
        ribosome=int(rbs_line),
        channel=int(channel_line),
    )
    cell.age_ticks = int(age)
    cell.direction = _normalize_direction(direction)
    return cell


def save_world_state(world, filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as handle:
        for cell in world.cells:
            handle.write(f'({cell.x}, {cell.y})\n')
            handle.write(f'{cell.gene_DNA}\n')
            handle.write(f'{cell.ribosome}\n')
            handle.write(f'{cell.channel}\n')
            handle.write(f"{getattr(cell, 'direction', None)}\n")
            handle.write(f"{int(getattr(cell, 'age_ticks', 0))}\n")
    nts_filename = filename.replace('.txt', '_NTs.npy')
    try:
        np.save(nts_filename, world.NTs.map)
        world.logger.info('World state saved to %s; NTs saved to %s', filename, nts_filename)
    except Exception as error:
        world.logger.error('Failed to save NTs to %s: %s', nts_filename, error)


def read_world_state(world, filename: str) -> None:
    with open(filename, 'r') as handle:
        lines = handle.readlines()

    world.cells.clear()
    index = 0
    try:
        while index < len(lines):
            pos_line = lines[index].strip()
            dna_line = lines[index + 1].strip()
            rbs_line = lines[index + 2].strip()
            channel_line = lines[index + 3].strip()
            direction_line = lines[index + 4].strip()
            age_line = lines[index + 5].strip()
            x, y = eval(pos_line)
            cell = _build_cell(
                world=world,
                x=x,
                y=y,
                dna_line=dna_line,
                rbs_line=rbs_line,
                channel_line=channel_line,
                age=int(age_line),
                direction=direction_line,
            )
            world.cells.append(cell)
            index += 6
    except Exception:
        world.cells.clear()
        index = 0
        try:
            while index < len(lines):
                pos_line = lines[index].strip()
                dna_line = lines[index + 1].strip()
                rbs_line = lines[index + 2].strip()
                channel_line = lines[index + 3].strip()
                age_line = lines[index + 4].strip()
                x, y = eval(pos_line)
                cell = _build_cell(
                    world=world,
                    x=x,
                    y=y,
                    dna_line=dna_line,
                    rbs_line=rbs_line,
                    channel_line=channel_line,
                    age=int(age_line),
                    direction=None,
                )
                world.cells.append(cell)
                index += 5
        except Exception:
            world.cells.clear()
            index = 0
            try:
                while index < len(lines):
                    pos_line = lines[index].strip()
                    dna_line = lines[index + 1].strip()
                    rbs_line = lines[index + 2].strip()
                    x, y = eval(pos_line)
                    cell = _build_cell(
                        world=world,
                        x=x,
                        y=y,
                        dna_line=dna_line,
                        rbs_line=rbs_line,
                        channel_line='0',
                        age=0,
                        direction=None,
                    )
                    world.cells.append(cell)
                    index += 3
            except Exception as error:
                world.logger.error('Error reading world state from %s at line %s: %s', filename, index, error)
                raise error

    nts_filename = filename.replace('.txt', '_NTs.npy')
    try:
        nts_map = np.load(nts_filename)
        world.NTs = NTs.initialize_NTs(map=nts_map)
        world.logger.info('NTs loaded from %s (shape=%s)', nts_filename, nts_map.shape)
    except FileNotFoundError:
        world.logger.warning('NTs file not found: %s, using blank NTs', nts_filename)
        world.NTs = NTs.initialize_NTs()
    except Exception as error:
        world.logger.error('Failed to read NTs from %s: %s', nts_filename, error)
        world.NTs = NTs.initialize_NTs()
    world.update_cells_map()
    world.logger.info('World state loaded from %s, total cells: %s', filename, len(world.cells))
