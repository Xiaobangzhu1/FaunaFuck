from fauna.simulation import cell_actions
from fauna.simulation import cell_factory
from fauna.simulation.rna_executor import execute_rna
from fauna.control_panel import ControlPanel
from fauna.config import CellConfig


class _DummyWorld:
    def __init__(self):
        self.new_cells = []
        self.cells = []
        self.pending_positions = set()

    def reserve_position(self, x, y):
        key = (int(x), int(y))
        if key in self.pending_positions:
            return False
        self.pending_positions.add(key)
        return True

class _DummyCell:
    def __init__(self, x=1, y=1, gene_dna: str = "<>!!><", nts=None, world=None, direction=None):
        self.x = x
        self.y = y
        self.gene_DNA = gene_dna
        self.gene_RNA = ["d", ","]
        self.ribosome = 3
        self.channel = 0
        self.direction = direction
        self.NTs = object() if nts is None else nts
        self.world = _DummyWorld() if world is None else world
        self.dead = False
        self.locked = False
        self.transcript_called = 0

    def transcript(self):
        self.transcript_called += 1
        self.gene_RNA = ["w"]

    def kill(self):
        return cell_actions.kill_front_cell(self)

    def move_ribosome(self):
        self.ribosome += 1

    def die(self, reason):
        self.dead = True

def test_reproduce_mutation_syncs_parent_and_child(monkeypatch):
    parent = _DummyCell(gene_dna="<>!!><", direction="w")
    parent.world.cells = [parent]

    def _fake_mutate_dna(_):
        return "<>?!><", True

    monkeypatch.setattr(cell_actions, "mutate_DNA", _fake_mutate_dna)

    ok = cell_actions.reproduce(parent)

    assert ok is True
    assert parent.gene_DNA == "<>?!><"
    assert parent.transcript_called == 1
    assert parent.ribosome == 0
    assert len(parent.world.new_cells) == 1
    assert parent.world.new_cells[0].gene_DNA == "<>?!><"
    assert parent.world.new_cells[0].direction == "w"


def test_reproduce_without_mutation_keeps_parent_dna(monkeypatch):
    parent = _DummyCell(gene_dna="<>!!><", direction="a")
    parent.world.cells = [parent]

    def _fake_mutate_dna(dna):
        return dna, False

    monkeypatch.setattr(cell_actions, "mutate_DNA", _fake_mutate_dna)

    ok = cell_actions.reproduce(parent)

    assert ok is True
    assert parent.gene_DNA == "<>!!><"
    assert parent.transcript_called == 0
    assert parent.ribosome == 3
    assert len(parent.world.new_cells) == 1
    assert parent.world.new_cells[0].gene_DNA == "<>!!><"
    assert parent.world.new_cells[0].direction == "a"


def test_reproduce_direction_only_wraparound_and_kills_front_cell(monkeypatch):
    parent = _DummyCell(x=0, y=2, gene_dna="<>!!><", direction="a")
    victim = _DummyCell(x=9, y=2, gene_dna="<>??><", direction="d", world=parent.world)
    parent.world.cells = [parent, victim]

    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))

    from fauna.config import MapConfig
    prev_width = MapConfig.width
    prev_height = MapConfig.height
    MapConfig.width = 10
    MapConfig.height = 10
    try:
        ok = cell_actions.reproduce(parent)
    finally:
        MapConfig.width = prev_width
        MapConfig.height = prev_height

    assert ok is True
    assert victim.dead is True
    assert len(parent.world.new_cells) == 1
    child = parent.world.new_cells[0]
    assert int(child.x) == 9
    assert int(child.y) == 2
    assert child.direction == "a"


def test_reproduce_with_missing_direction_is_normalized_and_can_kill_front_target(monkeypatch):
    parent = _DummyCell(x=0, y=2, gene_dna="<>!!><", direction=None)
    victim = _DummyCell(x=1, y=2, gene_dna="<>??><", direction="d", world=parent.world)
    parent.world.cells = [parent, victim]

    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))
    monkeypatch.setattr("fauna.simulation.cell_actions.random.shuffle", lambda items: None)
    monkeypatch.setattr("fauna.simulation.cell_actions.random.choice", lambda items: "d")

    from fauna.config import MapConfig
    prev_width = MapConfig.width
    prev_height = MapConfig.height
    MapConfig.width = 10
    MapConfig.height = 10
    try:
        ok = cell_actions.reproduce(parent)
    finally:
        MapConfig.width = prev_width
        MapConfig.height = prev_height

    assert ok is True
    assert victim.dead is True
    assert len(parent.world.new_cells) == 1
    child = parent.world.new_cells[0]
    assert (int(child.x), int(child.y)) == (1, 2)
    assert parent.direction == "d"


def test_reproduce_wraparound_all_boundaries(monkeypatch):
    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))

    from fauna.config import MapConfig
    prev_width = MapConfig.width
    prev_height = MapConfig.height
    MapConfig.width = 10
    MapConfig.height = 10
    try:
        cases = [
            (0, 5, "a", (9, 5)),
            (9, 5, "d", (0, 5)),
            (5, 0, "w", (5, 9)),
            (5, 9, "s", (5, 0)),
        ]
        for x, y, direction, expected in cases:
            parent = _DummyCell(x=x, y=y, gene_dna="<>!!><", direction=direction)
            parent.world.cells = [parent]
            ok = cell_actions.reproduce(parent)
            assert ok is True
            assert len(parent.world.new_cells) == 1
            child = parent.world.new_cells[0]
            assert (int(child.x), int(child.y)) == expected
            assert child.direction == direction
    finally:
        MapConfig.width = prev_width
        MapConfig.height = prev_height


def test_dot_command_kills_front_cell_not_self():
    parent = _DummyCell(x=2, y=2, gene_dna="<>!!><", direction="d")
    victim = _DummyCell(x=3, y=2, gene_dna="<>??><", direction="a", world=parent.world)
    parent.world.cells = [parent, victim]
    parent.gene_RNA = ["."]
    parent.ribosome = 0

    execute_rna(parent)

    assert parent.dead is False
    assert victim.dead is True
    assert parent.ribosome == 1


def test_reproduce_calls_forward_kill_before_spawning(monkeypatch):
    parent = _DummyCell(x=2, y=2, gene_dna="<>!!><", direction="d")
    victim = _DummyCell(x=3, y=2, gene_dna="<>??><", direction="a", world=parent.world)
    parent.world.cells = [parent, victim]

    monkeypatch.setattr(cell_actions, "mutate_DNA", lambda dna: (dna, False))

    ok = cell_actions.reproduce(parent)

    assert ok is True
    assert victim.dead is True


def test_initial_cells_all_have_wasd_direction(monkeypatch):
    class _CellForInit:
        def __init__(self, x, y, gene_dna, nts, world=None):
            self.x = x
            self.y = y
            self.gene_DNA = gene_dna
            self.direction = None

    world = object()
    old_original_num = CellConfig.original_num
    old_pure_mode = CellConfig.pure_mode
    old_subculture = CellConfig.cell_subculture
    try:
        CellConfig.original_num = 3
        CellConfig.pure_mode = False
        CellConfig.cell_subculture = None
        monkeypatch.setattr("fauna.simulation.cell_factory.random.normalvariate", lambda mean, std: mean)
        monkeypatch.setattr("fauna.simulation.cell_factory.random.choice", lambda items: "w")
        cells = cell_factory.build_initial_cells(_CellForInit, nts=object(), world=world)
    finally:
        CellConfig.original_num = old_original_num
        CellConfig.pure_mode = old_pure_mode
        CellConfig.cell_subculture = old_subculture

    assert len(cells) == 3
    assert all(c.direction in {"w", "a", "s", "d"} for c in cells)


def test_initial_cells_pick_from_dna_choices(monkeypatch):
    class _CellForInit:
        def __init__(self, x, y, gene_dna, nts, world=None):
            self.x = x
            self.y = y
            self.gene_DNA = gene_dna
            self.direction = "w"

    def _fake_choice(items):
        if items == CellConfig.gene_DNA_choices:
            return items[1]
        return items[0]

    old_original_num = CellConfig.original_num
    old_pure_mode = CellConfig.pure_mode
    old_subculture = CellConfig.cell_subculture
    try:
        CellConfig.original_num = 2
        CellConfig.pure_mode = False
        CellConfig.cell_subculture = None
        monkeypatch.setattr("fauna.simulation.cell_factory.random.normalvariate", lambda mean, std: mean)
        monkeypatch.setattr("fauna.simulation.cell_factory.random.choice", _fake_choice)
        cells = cell_factory.build_initial_cells(_CellForInit, nts=object(), world=object())
    finally:
        CellConfig.original_num = old_original_num
        CellConfig.pure_mode = old_pure_mode
        CellConfig.cell_subculture = old_subculture

    assert [cell.gene_DNA for cell in cells] == [CellConfig.gene_DNA_choices[1], CellConfig.gene_DNA_choices[1]]


def test_spawn_uses_dna_choices_when_missing_dna(monkeypatch):
    class _DummyLogger:
        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

    class _DummyWorldForSpawn:
        def __init__(self):
            self.width = 20
            self.height = 20
            self.logger = _DummyLogger()
            self.NTs = object()
            self.cells = []
            self.pending_positions = set()
            self.new_cells = []

        def spawn_cells(self, **kwargs):
            self.last_spawn = kwargs
            return 1, []

    def _fake_choice(items):
        if items == CellConfig.gene_DNA_choices:
            return items[1]
        return items[0]

    panel = ControlPanel()
    world = _DummyWorldForSpawn()
    monkeypatch.setattr("fauna.control_panel._pick_initial_gene_dna", lambda: CellConfig.gene_DNA_choices[1])
    result = panel._execute_command(world, 'spawn x=1 y=1')

    assert result is False
    assert world.last_spawn['dna'] == CellConfig.gene_DNA_choices[1]
