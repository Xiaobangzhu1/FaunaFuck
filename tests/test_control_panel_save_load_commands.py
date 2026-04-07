from pathlib import Path

from fauna.control_panel import ControlPanel


class DummyLogger:
    def __init__(self):
        self.handlers = []

    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


class DummyWorld:
    def __init__(self):
        self.logger = DummyLogger()
        self.ticks = 12
        self.paused = False
        self.saved_paths: list[str] = []
        self.loaded_paths: list[str] = []
        self.snapshots: list[str] = []

    def save_world_state(self, filename: str) -> None:
        self.saved_paths.append(filename)
        Path(filename).write_text("ok", encoding="utf-8")

    def read_world_state(self, filename: str) -> None:
        self.loaded_paths.append(filename)

    def _record_snapshot(self, reason: str) -> None:
        self.snapshots.append(reason)


def test_save_and_load_commands(tmp_path):
    panel = ControlPanel()
    world = DummyWorld()
    save_path = tmp_path / "manual_case.txt"

    panel._execute_command(world, f"save {save_path}")
    assert str(save_path) in world.saved_paths
    assert save_path.exists()

    panel._execute_command(world, f"load {save_path}")
    assert str(save_path) in world.loaded_paths
    assert world.paused is True
    assert "load-command" in world.snapshots
