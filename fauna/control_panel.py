from __future__ import annotations

import ast
import shlex
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pygame

from .config import CellConfig, LogConfig, UITheme
from .simulation.cell_factory import _pick_initial_gene_dna


class ControlPanel:
    def __init__(self) -> None:
        self.visible = True
        self.input_buffer = ''
        self.messages: list[str] = []
        self._executed_command_history: list[str] = []
        self._local_clipboard = ''
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._max_messages = 10
        self._scrap_ready = False

        self.dna_popup_visible = False
        self._dna_close_rect: pygame.Rect | None = None
        self._dna_open_rect: pygame.Rect | None = None
        self._dna_title_rect: pygame.Rect | None = None
        self._dna_popup_rect: pygame.Rect | None = None
        self._dna_dragging = False
        self._dna_drag_offset = (0, 0)
        self._dna_popup_lines = [
            'DNA -> RNA transcription rules',
            'DNA bases: ! ? > <',
            '!! -> +; !? -> ,; !> -> d; !< -> a',
            '?! -> .; ?? -> -; ?> -> w; ?< -> s',
            '>! -> [; >? -> }; >> -> >; >< -> e',
            '<! -> ]; <? -> {; << -> <; <> -> b',
            'Open: command "dna", key "/", right-panel button',
            'Close: ESC or top-right button',
        ]

    def _open_dna_popup(self, world, source: str) -> None:
        if self.dna_popup_visible:
            self._push_message('DNA rules popup is already open.')
            world.logger.info('ControlPanel dna popup focus requested by %s while open.', source)
            return
        self.dna_popup_visible = True
        self._dna_dragging = False
        self._push_message('DNA rules popup opened.')
        world.logger.info('ControlPanel dna popup opened by %s.', source)

    def _close_dna_popup(self, world, source: str) -> None:
        self.dna_popup_visible = False
        self._dna_dragging = False
        self._push_message('DNA rules popup closed.')
        world.logger.info('ControlPanel dna popup closed by %s.', source)

    def _remember_command(self, command: str) -> None:
        self._executed_command_history.append(command)
        if len(self._executed_command_history) > 200:
            self._executed_command_history = self._executed_command_history[-200:]

    def _undo_command_to_input(self, world, source: str) -> None:
        if not self._executed_command_history:
            self._push_message('Undo failed: no command history.')
            world.logger.warning('ControlPanel undo failed by %s: no history.', source)
            return
        self.input_buffer = self._executed_command_history.pop()
        self._push_message('Undo restored previous command to input.')
        world.logger.info('ControlPanel undo restored command by %s.', source)

    def _ensure_scrap(self, world) -> None:
        if self._scrap_ready:
            return
        try:
            pygame.scrap.init()
            self._scrap_ready = True
        except Exception as error:
            self._scrap_ready = False
            world.logger.warning('ControlPanel clipboard init failed: %s', error)

    def _set_clipboard_text(self, world, text: str, source: str) -> None:
        self._local_clipboard = text
        self._ensure_scrap(world)
        if not self._scrap_ready:
            self._push_message('Clipboard fallback: local buffer only.')
            world.logger.warning('ControlPanel clipboard unavailable for %s copy.', source)
            return
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
        except Exception as error:
            self._push_message('Clipboard fallback: local buffer only.')
            world.logger.warning('ControlPanel clipboard write failed (%s): %s', source, error)

    def _get_clipboard_text(self, world, source: str) -> str:
        self._ensure_scrap(world)
        if self._scrap_ready:
            try:
                data = pygame.scrap.get(pygame.SCRAP_TEXT)
                if data:
                    decoded = data.decode('utf-8', errors='ignore').replace('\x00', '')
                    if decoded:
                        self._local_clipboard = decoded
                        return decoded
            except Exception as error:
                self._push_message('Clipboard fallback: local buffer only.')
                world.logger.warning('ControlPanel clipboard read failed (%s): %s', source, error)
        return self._local_clipboard

    def _flush_log_handlers(self, world) -> None:
        for handler in world.logger.handlers:
            flush = getattr(handler, 'flush', None)
            if callable(flush):
                flush()

    def _collect_recent_logs(self, minutes: int = 5, max_lines: int = 300) -> list[str]:
        log_path = Path(LogConfig.file)
        log_dir = log_path.parent
        candidates: list[Path] = []
        if log_path.exists():
            candidates.append(log_path)
        if log_dir.exists():
            pattern = f'{log_path.stem}_*{log_path.suffix}'
            candidates.extend(log_dir.glob(pattern))
        if not candidates:
            return []
        cutoff = datetime.now() - timedelta(minutes=max(1, int(minutes)))
        entries: list[tuple[datetime, str]] = []
        # 先读新的，再读旧的；最后按时间排序输出。
        for file_path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                for line in file_path.read_text(encoding='utf-8', errors='ignore').splitlines():
                    if len(line) < 19:
                        continue
                    try:
                        ts = datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                    if ts >= cutoff:
                        entries.append((ts, line))
            except Exception:
                continue
        entries.sort(key=lambda item: item[0])
        if len(entries) > max_lines:
            entries = entries[-max_lines:]
        return [line for _, line in entries]

    def _wrap_text(self, font: pygame.font.Font, text: str, max_width: int) -> list[str]:
        if not text:
            return ['']
        lines: list[str] = []
        current = ''
        for char in text:
            trial = current + char
            if font.size(trial)[0] <= max_width:
                current = trial
                continue
            if current:
                lines.append(current.rstrip())
            if char.isspace():
                current = ''
            else:
                current = char
        if current:
            lines.append(current.rstrip())
        return lines or ['']

    def _draw_wrapped_text(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
        max_width: int,
        line_height: int,
        y_limit: int | None = None,
    ) -> int:
        for line in self._wrap_text(font, text, max_width):
            if y_limit is not None and y + line_height > y_limit:
                return y
            rendered = font.render(line, True, color)
            screen.blit(rendered, (x, y))
            y += line_height
        return y

    def _ensure_fonts(self) -> None:
        if self._font is None:
            self._font = pygame.font.SysFont('Consolas', 18)
        if self._small_font is None:
            self._small_font = pygame.font.SysFont('Consolas', 15)

    def _push_message(self, message: str) -> None:
        self.messages.append(message)
        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages :]

    def _parse_value(self, raw: str) -> Any:
        lowered = raw.lower()
        if lowered == 'true':
            return True
        if lowered == 'false':
            return False
        if lowered == 'none':
            return None
        try:
            return ast.literal_eval(raw)
        except Exception:
            return raw

    def _parse_key_values(self, parts: list[str]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for part in parts:
            if '=' not in part:
                raise ValueError(f'Expected key=value token, got: {part}')
            key, raw_value = part.split('=', 1)
            if not key:
                raise ValueError(f'Invalid key=value token: {part}')
            parsed[key] = self._parse_value(raw_value)
        return parsed

    def _execute_command(self, world, command: str) -> bool:
        recreate_display = False
        self._push_message(f'> {command}')
        try:
            parts = shlex.split(command)
        except Exception as error:
            self._push_message(f'Parse error: {error}')
            world.logger.error('ControlPanel parse error: %s', error)
            return False
        if not parts:
            return False

        cmd = parts[0].lower()
        args = parts[1:]
        if cmd != 'undo':
            self._remember_command(command)

        if cmd == 'help':
            self._push_message('spawn (use default cell config)')
            self._push_message('spawn dna=... x=.. y=.. count=.. channel=.. ribosome=.. x_step=.. y_step=..')
            self._push_message('set CellConfig.die_mode=4')
            self._push_message('dna  (open transcription rules popup)')
            self._push_message('log5 (export/show recent 5-minute logs)')
            self._push_message('undo | copy [text] | paste')
            self._push_message('Shortcuts apply only when input is empty (including "/").')
            self._push_message('Edit shortcuts: Ctrl/Cmd+C, Ctrl/Cmd+V, Ctrl/Cmd+Z')
            self._push_message('pause | resume | toggle | step | back | restart | status | export-log | clear')
            return False

        if cmd == 'dna':
            self._open_dna_popup(world, 'command')
            return False

        if cmd == 'undo':
            self._undo_command_to_input(world, 'command')
            return False

        if cmd == 'copy':
            text_to_copy = ' '.join(args) if args else self.input_buffer
            if not text_to_copy:
                self._push_message('Copy failed: empty input.')
                world.logger.warning('ControlPanel copy failed: empty input.')
                return False
            self._set_clipboard_text(world, text_to_copy, 'command')
            self._push_message(f'Copied {len(text_to_copy)} chars.')
            world.logger.info('ControlPanel copied %s chars by command.', len(text_to_copy))
            return False

        if cmd == 'paste':
            pasted = self._get_clipboard_text(world, 'command')
            if not pasted:
                self._push_message('Paste failed: clipboard is empty.')
                world.logger.warning('ControlPanel paste failed: clipboard empty.')
                return False
            self.input_buffer += pasted
            self._push_message(f'Pasted {len(pasted)} chars to input.')
            world.logger.info('ControlPanel pasted %s chars by command.', len(pasted))
            return False

        if cmd in {'pause', 'resume', 'toggle'}:
            if cmd == 'pause':
                world.paused = True
            elif cmd == 'resume':
                world.paused = False
            else:
                world.toggle_pause()
            message = f'Paused={world.paused}'
            self._push_message(message)
            world.logger.info('ControlPanel %s -> %s', cmd, message)
            return False

        if cmd in {'step', 'next', 'forward'}:
            if not world.paused:
                self._push_message('Step requires paused mode.')
                return False
            _, message = world.step_forward()
            self._push_message(message)
            return False

        if cmd in {'back', 'prev', 'backward'}:
            if not world.paused:
                self._push_message('Back requires paused mode.')
                return False
            _, message = world.step_backward()
            self._push_message(message)
            return False

        if cmd == 'status':
            self._push_message(f'tick={world.ticks} cells={len(world.cells)} paused={world.paused}')
            return False

        if cmd == 'clear':
            self.messages.clear()
            world.logger.info('ControlPanel messages cleared.')
            return False

        if cmd in {'restart', 'reset'}:
            _, message = world.restart_world()
            self._push_message(message)
            return False

        if cmd == 'export-log':
            self._flush_log_handlers(world)
            self._push_message(f'Log flushed to {LogConfig.file}')
            world.logger.info('ControlPanel export-log invoked.')
            return False

        if cmd in {'log5', 'logs-5m', 'recent-log'}:
            try:
                self._flush_log_handlers(world)
                lines = self._collect_recent_logs(minutes=5, max_lines=500)
                output_path = Path(LogConfig.file).parent / 'recent_5m.log'
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if lines:
                    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
                    self._push_message(f'log5: {len(lines)} lines -> {output_path}')
                    for line in lines[-3:]:
                        self._push_message(line if len(line) <= 110 else f'{line[:107]}...')
                else:
                    output_path.write_text('', encoding='utf-8')
                    self._push_message(f'log5: no logs in last 5 minutes -> {output_path}')
                world.logger.info('ControlPanel log5 exported to %s (lines=%s).', output_path, len(lines))
            except Exception as error:
                self._push_message(f'log5 failed: {error}')
                world.logger.error('ControlPanel log5 failed: %s', error)
            return False

        if cmd == 'spawn':
            default_x = int(world.width // 2)
            default_y = int(world.height // 2)
            if not args:
                dna = _pick_initial_gene_dna()
                x = default_x
                y = default_y
                count = 1
                channel = 0
                ribosome = 0
                x_step = 0
                y_step = 0
                fields: dict[str, Any] = {}
            else:
                fields = self._parse_key_values(args)
                dna = str(fields.pop('dna', _pick_initial_gene_dna()))
                x = int(fields.pop('x', default_x))
                y = int(fields.pop('y', default_y))
                count = int(fields.pop('count', 1))
                channel = int(fields.pop('channel', 0))
                ribosome = int(fields.pop('ribosome', 0))
                x_step = int(fields.pop('x_step', 0))
                y_step = int(fields.pop('y_step', 0))
            created, errors = world.spawn_cells(
                dna=dna,
                x=x,
                y=y,
                count=count,
                channel=channel,
                ribosome=ribosome,
                x_step=x_step,
                y_step=y_step,
                attributes=fields,
            )
            self._push_message(f'Spawned={created} errors={len(errors)}')
            for error in errors[:3]:
                self._push_message(error)
            return False

        if cmd in {'set', 'set-config', 'config'}:
            if len(args) != 1 or '=' not in args[0]:
                raise ValueError('Usage: set ClassName.attr=value')
            path, raw_value = args[0].split('=', 1)
            value = self._parse_value(raw_value)
            success, message, recreate_display = world.apply_config_update(path, value)
            self._push_message(message)
            if not success:
                world.logger.error('ControlPanel set-config failed: %s', message)
            return recreate_display

        self._push_message(f'Unknown command: {cmd}')
        world.logger.warning('ControlPanel unknown command: %s', cmd)
        return False

    def handle_event(self, event: pygame.event.Event, world) -> bool:
        recreate_display = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.dna_popup_visible and self._dna_close_rect and self._dna_close_rect.collidepoint(event.pos):
                self._close_dna_popup(world, 'mouse')
                return recreate_display
            if self.dna_popup_visible and self._dna_title_rect and self._dna_title_rect.collidepoint(event.pos):
                if self._dna_popup_rect is not None:
                    self._dna_dragging = True
                    self._dna_drag_offset = (
                        event.pos[0] - self._dna_popup_rect.x,
                        event.pos[1] - self._dna_popup_rect.y,
                    )
                return recreate_display
            if self.visible and self._dna_open_rect and self._dna_open_rect.collidepoint(event.pos):
                self._open_dna_popup(world, 'button')
                return recreate_display
            return recreate_display

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dna_dragging = False
            return recreate_display

        if event.type == pygame.MOUSEMOTION and self._dna_dragging and self._dna_popup_rect is not None:
            screen_info = pygame.display.get_surface()
            if screen_info is None:
                return recreate_display
            new_x = event.pos[0] - self._dna_drag_offset[0]
            new_y = event.pos[1] - self._dna_drag_offset[1]
            max_x = max(0, screen_info.get_width() - self._dna_popup_rect.width)
            max_y = max(0, screen_info.get_height() - self._dna_popup_rect.height)
            self._dna_popup_rect.x = max(0, min(new_x, max_x))
            self._dna_popup_rect.y = max(0, min(new_y, max_y))
            return recreate_display

        if event.type != pygame.KEYDOWN:
            return recreate_display

        if self.dna_popup_visible and event.key == pygame.K_ESCAPE:
            self._close_dna_popup(world, 'ESC')
            return recreate_display

        if self.visible and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
            if event.key == pygame.K_c:
                if not self.input_buffer:
                    self._push_message('Copy failed: empty input.')
                    world.logger.warning('ControlPanel shortcut copy failed: empty input.')
                    return recreate_display
                self._set_clipboard_text(world, self.input_buffer, 'shortcut')
                self._push_message(f'Copied {len(self.input_buffer)} chars.')
                world.logger.info('ControlPanel copied %s chars by shortcut.', len(self.input_buffer))
                return recreate_display
            if event.key == pygame.K_v:
                pasted = self._get_clipboard_text(world, 'shortcut')
                if not pasted:
                    self._push_message('Paste failed: clipboard is empty.')
                    world.logger.warning('ControlPanel shortcut paste failed: clipboard empty.')
                    return recreate_display
                self.input_buffer += pasted
                self._push_message(f'Pasted {len(pasted)} chars to input.')
                world.logger.info('ControlPanel pasted %s chars by shortcut.', len(pasted))
                return recreate_display
            if event.key == pygame.K_z:
                self._undo_command_to_input(world, 'shortcut')
                return recreate_display

        empty_input = self.input_buffer == ''

        if event.key == pygame.K_TAB:
            self.visible = not self.visible
            world.logger.info('ControlPanel visibility changed: %s', self.visible)
            return recreate_display

        if event.key == pygame.K_F5 and empty_input:
            world.toggle_pause()
            self._push_message(f'Paused={world.paused}')
            return recreate_display
        if event.key == pygame.K_F6 and empty_input:
            if world.paused:
                _, message = world.step_forward()
                self._push_message(message)
            else:
                self._push_message('F6 step requires paused mode.')
            return recreate_display
        if event.key == pygame.K_F7 and empty_input:
            if world.paused:
                _, message = world.step_backward()
                self._push_message(message)
            else:
                self._push_message('F7 back requires paused mode.')
            return recreate_display
        if event.key == pygame.K_F8 and empty_input:
            _, message = world.restart_world()
            self._push_message(message)
            return recreate_display

        if event.key == pygame.K_SLASH and empty_input:
            self._open_dna_popup(world, 'hotkey(/)')
            return recreate_display

        if event.key == pygame.K_SPACE and empty_input:
            world.toggle_pause()
            self._push_message(f'Paused={world.paused}')
            return recreate_display

        if event.key == pygame.K_RIGHT and world.paused and empty_input:
            _, message = world.step_forward()
            self._push_message(message)
            return recreate_display

        if event.key == pygame.K_LEFT and world.paused and empty_input:
            _, message = world.step_backward()
            self._push_message(message)
            return recreate_display

        if not self.visible:
            return recreate_display

        if event.key == pygame.K_ESCAPE:
            self.visible = False
            return recreate_display
        if event.key == pygame.K_RETURN:
            command = self.input_buffer.strip()
            self.input_buffer = ''
            if command:
                try:
                    recreate_display = self._execute_command(world, command)
                except Exception as error:
                    message = f'Command error: {error}'
                    self._push_message(message)
                    world.logger.error(message)
            return recreate_display
        if event.key == pygame.K_BACKSPACE:
            self.input_buffer = self.input_buffer[:-1]
            return recreate_display
        if event.key == pygame.K_SPACE:
            self.input_buffer += ' '
            return recreate_display

        char = event.unicode
        if char and char.isprintable():
            self.input_buffer += char
        return recreate_display

    def _render_dna_popup(self, screen: pygame.Surface) -> None:
        self._ensure_fonts()
        assert self._font is not None
        assert self._small_font is not None

        screen_w, screen_h = screen.get_size()
        padding = 12
        header_h = 34
        line_h = 20

        max_popup_w = int(screen_w * 0.80)
        min_popup_w = 360
        raw_max_w = max(self._small_font.size(line)[0] for line in self._dna_popup_lines)
        popup_w = min(max(raw_max_w + padding * 2 + 12, min_popup_w), max_popup_w)

        wrapped_lines: list[str] = []
        for line in self._dna_popup_lines:
            wrapped_lines.extend(self._wrap_text(self._small_font, line, popup_w - padding * 2))

        content_h = len(wrapped_lines) * line_h
        max_popup_h = int(screen_h * 0.82)
        popup_h = min(max(header_h + content_h + padding * 2, 170), max_popup_h)

        if self._dna_popup_rect is None:
            self._dna_popup_rect = pygame.Rect((screen_w - popup_w) // 2, (screen_h - popup_h) // 2, popup_w, popup_h)
        self._dna_popup_rect.size = (popup_w, popup_h)
        max_x = max(0, screen_w - popup_w)
        max_y = max(0, screen_h - popup_h)
        self._dna_popup_rect.x = max(0, min(self._dna_popup_rect.x, max_x))
        self._dna_popup_rect.y = max(0, min(self._dna_popup_rect.y, max_y))
        popup_rect = self._dna_popup_rect

        backdrop = pygame.Surface((popup_rect.width, popup_rect.height), pygame.SRCALPHA)
        backdrop.fill((*UITheme.bg_card, 232))
        screen.blit(backdrop, popup_rect.topleft)
        pygame.draw.rect(screen, UITheme.border, popup_rect, width=2)
        self._dna_title_rect = pygame.Rect(popup_rect.x, popup_rect.y, popup_rect.width, header_h)

        title = self._font.render('DNA Transcription Rules', True, UITheme.accent_hover)
        screen.blit(title, (popup_rect.x + padding, popup_rect.y + 8))

        close_rect = pygame.Rect(popup_rect.right - 30, popup_rect.y + 8, 22, 22)
        self._dna_close_rect = close_rect
        pygame.draw.rect(screen, UITheme.accent_muted, close_rect, border_radius=3)
        close_text = self._small_font.render('X', True, UITheme.text_primary)
        screen.blit(close_text, (close_rect.x + 6, close_rect.y + 2))

        y = popup_rect.y + header_h
        y_limit = popup_rect.bottom - padding
        for line in wrapped_lines:
            if y + line_h > y_limit:
                ellipsis = self._small_font.render('...', True, UITheme.text_secondary)
                screen.blit(ellipsis, (popup_rect.x + padding, y_limit - line_h))
                break
            rendered = self._small_font.render(line, True, UITheme.text_secondary)
            screen.blit(rendered, (popup_rect.x + padding, y))
            y += line_h

    def render(self, screen: pygame.Surface, world, panel_rect: pygame.Rect | None = None) -> None:
        self._ensure_fonts()
        assert self._font is not None
        assert self._small_font is not None
        self._dna_open_rect = None

        if self.visible:
            if panel_rect is None:
                width, height = screen.get_size()
                panel_rect = pygame.Rect(0, 0, min(600, width), height)

            panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            panel.fill((*UITheme.bg_panel, 218))
            screen.blit(panel, panel_rect.topleft)

            x0 = panel_rect.x + 12
            y = panel_rect.y + 12
            y_limit = panel_rect.bottom - 10
            max_text_width = panel_rect.width - 24

            header = self._font.render('Sandbox Control Panel', True, UITheme.accent_primary)
            screen.blit(header, (x0, y))
            y += 32

            status_lines = [
                f'cells={len(world.cells)}  paused={world.paused}',
                f'size={world.width}x{world.height} channels={world.NTs.map.shape[2]}',
                'Hotkeys: TAB, SPACE, LEFT, RIGHT, /, F5, F6, F7, F8',
                'Edit: Ctrl/Cmd+C copy, Ctrl/Cmd+V paste, Ctrl/Cmd+Z undo',
                'Shortcuts work only when input is empty',
                'Type "help" then press ENTER for full commands',
                'Example: spawn dna=<>!?!?>< x=10 y=10 count=3 channel=1',
                'Example: set CellConfig.die_mode=4',
                'Example: dna',
                'Example: log5',
            ]
            for line in status_lines:
                y = self._draw_wrapped_text(
                    screen,
                    self._small_font,
                    line,
                    UITheme.text_secondary,
                    x0,
                    y,
                    max_text_width,
                    20,
                    y_limit=y_limit,
                )
                y += 2

            button_w = min(170, max_text_width)
            button_h = 28
            if y + button_h <= y_limit:
                self._dna_open_rect = pygame.Rect(x0, y, button_w, button_h)
                button_color = UITheme.accent_muted if self.dna_popup_visible else UITheme.accent_primary
                pygame.draw.rect(screen, button_color, self._dna_open_rect, border_radius=5)
                pygame.draw.rect(screen, UITheme.border, self._dna_open_rect, width=1, border_radius=5)
                button_label = self._small_font.render('DNA Rules (/)', True, UITheme.text_primary)
                label_x = self._dna_open_rect.x + 10
                label_y = self._dna_open_rect.y + (button_h - button_label.get_height()) // 2
                screen.blit(button_label, (label_x, label_y))
                y += button_h + 8

            y += 6
            prompt_lines = self._wrap_text(self._font, f': {self.input_buffer}', max_text_width)[-2:]
            last_prompt_line = ''
            for line in prompt_lines:
                if y + 22 > y_limit:
                    break
                prompt = self._font.render(line, True, UITheme.text_primary)
                screen.blit(prompt, (x0, y))
                last_prompt_line = line
                y += 22

            if last_prompt_line and (pygame.time.get_ticks() // 500) % 2 == 0:
                cursor_text = self._font.render('|', True, UITheme.accent_hover)
                cursor_x = x0 + self._font.size(last_prompt_line)[0] + 2
                cursor_y = y - 22
                if cursor_x < panel_rect.right - 8:
                    screen.blit(cursor_text, (cursor_x, cursor_y))
            y += 8

            for message in self.messages[-10:]:
                y = self._draw_wrapped_text(
                    screen,
                    self._small_font,
                    message,
                    UITheme.text_primary,
                    x0,
                    y,
                    max_text_width,
                    18,
                    y_limit=y_limit,
                )
                y += 2
                if y >= y_limit:
                    break

        if self.dna_popup_visible:
            try:
                self._render_dna_popup(screen)
            except Exception as error:
                self.dna_popup_visible = False
                self._dna_close_rect = None
                self._dna_title_rect = None
                self._dna_popup_rect = None
                self._dna_dragging = False
                self._push_message(f'DNA popup error: {error}')
                world.logger.error('DNA popup render failed: %s', error)
        else:
            self._dna_close_rect = None
            self._dna_title_rect = None
            self._dna_popup_rect = None
            self._dna_dragging = False
