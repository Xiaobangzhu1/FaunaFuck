import numpy as np

from fauna.config import CellConfig, MapConfig
from fauna.simulation import cell_actions


class DummyWorld:
    def __init__(self, width: int, height: int):
        self.cells_map = np.zeros((width, height), dtype=bool)


class DummyCell:
    def __init__(self, x: int, y: int, world: DummyWorld):
        self.x = x
        self.y = y
        self.world = world
        self.dead = False
        self.locked = False

    def die(self, reason: str) -> None:
        cell_actions.die(self, reason)


def test_death_uses_orthogonal_neighbors_and_threshold(monkeypatch):
    monkeypatch.setattr(MapConfig, "width", 5)
    monkeypatch.setattr(MapConfig, "height", 5)
    monkeypatch.setattr(CellConfig, "death_neighbor_threshold", 3)

    world = DummyWorld(5, 5)
    cell = DummyCell(2, 2, world)

    # Three orthogonal neighbors should trigger death when threshold == 3.
    world.cells_map[2, 1] = True
    world.cells_map[2, 3] = True
    world.cells_map[1, 2] = True

    cell_actions.check_death(cell)
    assert cell.dead is True


def test_diagonal_neighbors_do_not_count_for_death(monkeypatch):
    monkeypatch.setattr(MapConfig, "width", 5)
    monkeypatch.setattr(MapConfig, "height", 5)
    monkeypatch.setattr(CellConfig, "death_neighbor_threshold", 1)

    world = DummyWorld(5, 5)
    cell = DummyCell(2, 2, world)

    # Diagonal neighbors should not count toward orthogonal-only death rule.
    world.cells_map[1, 1] = True
    world.cells_map[3, 1] = True
    world.cells_map[1, 3] = True
    world.cells_map[3, 3] = True

    cell_actions.check_death(cell)
    assert cell.dead is False
