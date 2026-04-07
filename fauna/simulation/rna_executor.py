from __future__ import annotations

from ..config import CellConfig, MapConfig


def execute_rna(cell) -> None:
    if len(cell.gene_RNA) == 0:
        return

    try:
        for _ in range(MapConfig.max_instructions):
            command = cell.gene_RNA[cell.ribosome]

            if command in ['d', 'a', 'w', 's']:
                cell.move(command)
                cell.move_ribosome()
                return
            if command in ['+', '-']:
                cell.change_number(command)
                cell.move_ribosome()
                continue
            if command == ',':
                cell.reproduce()
                cell.move_ribosome()
                return
            if command == '.':
                cell.kill()
                cell.move_ribosome()
                return
            if command.startswith('['):
                cell.jump_forward(command)
                continue
            if command.startswith(']'):
                cell.jump_backward(command)
                continue
            if command in ['>', '<']:
                cell.change_channel(command)
                cell.move_ribosome()
                return
            if command in ['{', '}']:
                cell.move_ribosome()
                return

        raise Exception('Max instructions exceeded')
    except Exception as error:
        if CellConfig.debug_mode:
            raise error
        cell.die(f'Error: {error}')
        cell.gene_DNA = str(error)