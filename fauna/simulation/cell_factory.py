from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, List

from ..config import CellConfig, MapConfig
from ..dna_processing import transcript_DNA_to_RNA

if TYPE_CHECKING:
    from ..nts import NTs
    from ..cell import Cell
    from ..world import World


def build_initial_cells(cell_cls: type['Cell'], nts: 'NTs', world: 'World') -> List['Cell']:
    cells: List['Cell'] = []
    num = CellConfig.original_num
    if CellConfig.cell_subculture:
        for gene_dna, count in CellConfig.cell_subculture:
            count = int(count * CellConfig.cell_subculture_survive_rate)
            for _ in range(count):
                cells.append(_build_random_cell(cell_cls, nts, world, gene_dna))
        return cells
    if CellConfig.pure_mode:
        x = MapConfig.width // 2
        y = MapConfig.height // 2
        cells.append(cell_cls(x, y, _pick_initial_gene_dna(), nts, world=world))
        return cells
    for _ in range(num):
        cells.append(_build_random_cell(cell_cls, nts, world, _pick_initial_gene_dna()))
    return cells


def create_cell_from_dna(
    cell_cls: type['Cell'],
    gene_dna: str,
    x: int,
    y: int,
    nts: 'NTs',
    world: 'World',
    ribosome: int = 0,
    channel: int = 0,
) -> 'Cell':
    cell = cell_cls(x, y, gene_dna, nts, world=world)
    cell.ribosome = ribosome
    cell.channel = channel
    return cell


def transcribe_cell(cell: 'Cell') -> None:
    dna = cell.gene_DNA
    cell.gene_RNA = transcript_DNA_to_RNA(dna)
    if CellConfig.debug_mode:
        logger = logging.getLogger("fauna.cell")
        logger.info(
            "Cell at (%s,%s) transcribed DNA to RNA: %s",
            int(cell.x),
            int(cell.y),
            cell.gene_RNA,
        )


def _build_random_cell(cell_cls: type['Cell'], nts: 'NTs', world: 'World', gene_dna: str) -> 'Cell':
    rawx = random.normalvariate(MapConfig.width / 2, MapConfig.width / 8)
    x = min(max(0, int(rawx)), MapConfig.width)
    rawy = random.normalvariate(MapConfig.height / 2, MapConfig.height / 8)
    y = min(max(0, int(rawy)), MapConfig.height)
    cell = cell_cls(x, y, gene_dna, nts, world=world)
    if getattr(cell, 'direction', None) not in {'w', 'a', 's', 'd'}:
        cell.direction = random.choice(['w', 'a', 's', 'd'])
    return cell


def _pick_initial_gene_dna() -> str:
    choices = list(getattr(CellConfig, 'gene_DNA_choices', []) or [])
    if choices:
        return random.choice(choices)
    return str(CellConfig.gene_DNA)