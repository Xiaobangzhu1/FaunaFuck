import pygame

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
        self.paused = True
        self.step_forward_calls = 0
        self.step_backward_calls = 0

    def step_forward(self):
        self.step_forward_calls += 1
        return True, "step-forward"

    def step_backward(self):
        self.step_backward_calls += 1
        return True, "step-backward"


def _key_event(key: int, unicode: str = "", mod: int = 0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=mod)


def test_copy_command_prefers_selected_history_when_no_explicit_text():
    panel = ControlPanel()
    world = DummyWorld()

    panel._remember_command("spawn dna=<>!?!?>< x=2 y=2")
    panel._remember_command("set CellConfig.reproduction_fail_rate=0.2")
    panel._select_history(world, -1)
    panel.input_buffer = ""
    panel.cursor_index = 0

    panel._execute_command(world, "copy")
    assert panel._local_clipboard == "set CellConfig.reproduction_fail_rate=0.2"
    assert any("from history" in message for message in panel.messages)


def test_ctrl_c_can_copy_selected_history_when_input_empty():
    panel = ControlPanel()
    world = DummyWorld()

    panel._remember_command("save saves/manual.txt")
    panel._select_history(world, -1)
    panel.input_buffer = ""
    panel.cursor_index = 0

    event = _key_event(pygame.K_c, mod=pygame.KMOD_CTRL)
    panel.handle_event(event, world)
    assert panel._local_clipboard == "save saves/manual.txt"


def test_non_empty_left_right_move_cursor_and_insert_at_cursor():
    panel = ControlPanel()
    world = DummyWorld()

    panel.input_buffer = "abcd"
    panel.cursor_index = 2

    panel.handle_event(_key_event(pygame.K_LEFT), world)
    assert panel.cursor_index == 1
    assert world.step_backward_calls == 0

    panel.handle_event(_key_event(pygame.K_RIGHT), world)
    assert panel.cursor_index == 2
    assert world.step_forward_calls == 0

    panel.handle_event(_key_event(pygame.K_x, unicode="X"), world)
    assert panel.input_buffer == "abXcd"
    assert panel.cursor_index == 3


def test_empty_input_left_right_keep_frame_controls():
    panel = ControlPanel()
    world = DummyWorld()
    panel.input_buffer = ""
    panel.cursor_index = 0

    panel.handle_event(_key_event(pygame.K_RIGHT), world)
    panel.handle_event(_key_event(pygame.K_LEFT), world)

    assert world.step_forward_calls == 1
    assert world.step_backward_calls == 1
