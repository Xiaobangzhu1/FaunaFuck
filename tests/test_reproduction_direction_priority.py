import types

from fauna.config import CellConfig, MapConfig
from fauna.simulation import cell_actions


class DummyWorld:
    def __init__(self):
        self.new_cells = []
        self.calls = []

    def reserve_position(self, x: int, y: int) -> bool:
        self.calls.append((x, y))
        return False


class DummyCell:
    def __init__(self, x: int, y: int, gene_DNA: str, NTs, world):
        self.x = x
        self.y = y
        self.gene_DNA = gene_DNA
        self.NTs = NTs
        self.world = world
        self.channel = 0
        self.direction = None
        self.locked = False


def test_reproduce_prefers_facing_direction(monkeypatch):
    monkeypatch.setattr(MapConfig, "width", 20)
    monkeypatch.setattr(MapConfig, "height", 20)
    monkeypatch.setattr(CellConfig, "randomize_reproduction_direction", False)
    monkeypatch.setattr(CellConfig, "reproduction_fail_rate", 0.0)
    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))

    world = DummyWorld()
    origin = DummyCell(5, 5, "<>!?!?><", NTs=types.SimpleNamespace(), world=world)
    origin.direction = "d"

    def reserve(x: int, y: int) -> bool:
        world.calls.append((x, y))
        return (x, y) == (6, 5)

    world.reserve_position = reserve

    ok = cell_actions.reproduce(origin)
    assert ok is True
    assert world.calls[0] == (6, 5)
    assert len(world.new_cells) == 1
    assert (world.new_cells[0].x, world.new_cells[0].y) == (6, 5)


def test_reproduce_falls_back_when_facing_direction_blocked(monkeypatch):
    monkeypatch.setattr(MapConfig, "width", 20)
    monkeypatch.setattr(MapConfig, "height", 20)
    monkeypatch.setattr(CellConfig, "randomize_reproduction_direction", False)
    monkeypatch.setattr(CellConfig, "reproduction_fail_rate", 0.0)
    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))

    world = DummyWorld()
    origin = DummyCell(5, 5, "<>!?!?><", NTs=types.SimpleNamespace(), world=world)
    origin.direction = "d"

    def reserve(x: int, y: int) -> bool:
        world.calls.append((x, y))
        if (x, y) == (6, 5):
            return False
        return (x, y) == (4, 5)

    world.reserve_position = reserve

    ok = cell_actions.reproduce(origin)
    assert ok is True
    assert world.calls[0] == (6, 5)
    assert world.calls[1] == (4, 5)
    assert len(world.new_cells) == 1
    assert (world.new_cells[0].x, world.new_cells[0].y) == (4, 5)


def test_reproduce_can_fail_by_probability_and_skip_attempt(monkeypatch):
    monkeypatch.setattr(MapConfig, "width", 20)
    monkeypatch.setattr(MapConfig, "height", 20)
    monkeypatch.setattr(CellConfig, "reproduction_fail_rate", 1.0)
    monkeypatch.setattr(CellConfig, "randomize_reproduction_direction", False)
    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))
    monkeypatch.setattr(cell_actions.random, "random", lambda: 0.0)

    world = DummyWorld()
    origin = DummyCell(5, 5, "<>!?!?><", NTs=types.SimpleNamespace(), world=world)
    origin.direction = "d"

    ok = cell_actions.reproduce(origin)
    assert ok is False
    assert world.calls == []
    assert world.new_cells == []
