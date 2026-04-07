# world.py
'''管理游戏世界'''

import pygame
from typing import List
import logging
import random

from .config import CellConfig, DispConfig, LogConfig, MapConfig, RandomConfig, SaveConfig
from .nts import NTs
from .cell import Cell
import numpy as np
from .world_persistence import read_world_state as load_world_state, save_world_state
from .rendering import draw_tick as render_tick, render_world
from .simulation.world_runner import (
    autosave_if_needed,
    cells_act as run_cells_act,
    check_dead as world_check_dead,
    reserve_position as reserve_world_position,
    should_stop,
    update_cells_map as refresh_cells_map,
    log_periodic_summary,
)
from .simulation.world_stats import collect_dnas, collect_rnas


class World:
    """创建和管理游戏中的所有实体和系统"""
    def __init__(self, width : int, height : int, start_empty: bool = False, max_history_frames: int = 12):
        self.logger = logging.getLogger("fauna.world")
        # 基础状态
        self.width = width
        self.height = height
        self.allow_empty_world = start_empty
        self.paused = True
        self.max_history_frames = max(2, int(max_history_frames))
         
        self.cells : List[Cell] = []
        self.cells_map = np.zeros((self.width + 1, self.height + 1), dtype=bool)
        self.cell_cls = Cell
        
        # 初始化细胞
        self.NTs = NTs.initialize_NTs()
        if start_empty:
            self.cells = []
        else:
            self.cells = Cell.initialize_cells(self.NTs, self)
        self.new_cells = []  # 用于存储新生成的细胞
        self.pending_positions: set[tuple[int,int]] = set()  # 本帧预占位置
        self.ticks = 0
        self._history: list[dict] = []
        self._history_index = -1
        self.update_cells_map()
        self._record_snapshot('init')
        
    def collect_RNAs(self):
        """收集并统计所有不同的RNA序列"""
        return collect_rnas(self)

    def collect_DNAs(self) -> str | list:
        #TODO:分离非统计的DNA收集功能
        """收集并统计所有不同的DNA序列"""
        return collect_dnas(self)
    
    def save_world_state(self, filename: str) -> None:
        """保存当前世界状态到文件"""
        save_world_state(self, filename)

    def read_world_state(self, filename: str) -> None:
        """从文件读取世界状态"""
        load_world_state(self, filename)

    def add_new_cells(self) -> None:
        """将新生成的细胞添加到世界中，并清理预占位"""
        from .simulation.world_runner import add_new_cells

        add_new_cells(self)
        
    def begin_frame(self) -> None:
        """开始一帧：清空预占位"""
        from .simulation.world_runner import begin_frame

        begin_frame(self)
        
    def reserve_position(self, x: int, y: int) -> bool:
        """尝试预占 (x,y)，避免同一帧重复落子"""
        return reserve_world_position(self, x, y)

    def cells_act(self)-> None:
        """让所有细胞执行动作"""
        run_cells_act(self)
        
    def check_dead(self, cell) -> None:
        '''检查细胞是否死亡'''
        world_check_dead(self, cell)
            
    def update_cells_map(self) -> None:
        """更新细胞位置映射"""
        refresh_cells_map(self)
                
        
    def draw_tick(self) -> None:
        """绘制当前帧数"""
        render_tick(self)

    def _build_snapshot(self) -> dict:
        cells_snapshot = []
        for cell in self.cells:
            cells_snapshot.append(
                {
                    'x': float(cell.x),
                    'y': float(cell.y),
                    'gene_DNA': str(cell.gene_DNA),
                    'ribosome': int(cell.ribosome),
                    'channel': int(cell.channel),
                    'dead': bool(cell.dead),
                    'locked': bool(getattr(cell, 'locked', False)),
                    'transcripted_flag': bool(getattr(cell, 'transcripted_flag', False)),
                    'age_ticks': int(getattr(cell, 'age_ticks', 0)),
                    'direction': getattr(cell, 'direction', None),
                }
            )
        return {
            'ticks': int(self.ticks),
            'cells': cells_snapshot,
            'nts_map': self.NTs.map.copy(),
        }

    def _restore_snapshot(self, snapshot: dict) -> None:
        self.ticks = int(snapshot['ticks'])
        self.NTs = NTs.initialize_NTs(map=np.array(snapshot['nts_map'], copy=True))
        self.cells = []
        for item in snapshot['cells']:
            cell = self.cell_cls.create_cell_from_DNA(
                item['gene_DNA'],
                int(item['x']),
                int(item['y']),
                self.NTs,
                self,
                ribosome=int(item['ribosome']),
                channel=int(item['channel']),
            )
            cell.x = float(item['x'])
            cell.y = float(item['y'])
            cell.dead = bool(item['dead'])
            cell.locked = bool(item['locked'])
            cell.transcripted_flag = bool(item['transcripted_flag'])
            cell.age_ticks = int(item.get('age_ticks', 0))
            direction = item.get('direction')
            cell.direction = direction if direction in {'w', 'a', 's', 'd'} else random.choice(['w', 'a', 's', 'd'])
            self.cells.append(cell)
        self.new_cells = []
        self.pending_positions.clear()
        self.update_cells_map()

    def _record_snapshot(self, reason: str) -> None:
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]
        self._history.append(self._build_snapshot())
        if len(self._history) > self.max_history_frames:
            overflow = len(self._history) - self.max_history_frames
            self._history = self._history[overflow:]
            self._history_index = max(0, self._history_index - overflow)
        self._history_index = len(self._history) - 1
        if reason and reason != 'tick':
            self.logger.info('Snapshot recorded: %s (index=%s)', reason, self._history_index)

    def step_backward(self) -> tuple[bool, str]:
        if self._history_index <= 0:
            message = 'No previous frame to restore.'
            self.logger.warning(message)
            return False, message
        self._history_index -= 1
        self._restore_snapshot(self._history[self._history_index])
        message = f'Restored previous frame at tick={self.ticks}.'
        self.logger.info(message)
        return True, message

    def step_forward(self) -> tuple[bool, str]:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_snapshot(self._history[self._history_index])
            message = f'Restored next frame at tick={self.ticks}.'
            self.logger.info(message)
            return True, message
        alive = self._simulate_one_tick()
        if not alive:
            message = 'Cannot step forward: world is stopped.'
            self.logger.warning(message)
            return False, message
        self._record_snapshot('step_forward')
        message = f'Stepped forward to tick={self.ticks}.'
        self.logger.info(message)
        return True, message

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        self.logger.info('Pause toggled: %s', self.paused)
        return self.paused

    def restart_world(self, keep_paused: bool = True) -> tuple[bool, str]:
        try:
            self.cells = []
            self.new_cells = []
            self.pending_positions.clear()
            self.NTs = NTs.initialize_NTs()
            self.ticks = 0
            self.paused = bool(keep_paused)
            self._history = []
            self._history_index = -1
            self.update_cells_map()
            self._record_snapshot('restart')
            message = 'World restarted: empty sandbox restored.'
            self.logger.info(message)
            return True, message
        except Exception as error:
            message = f'World restart failed: {error}'
            self.logger.error(message)
            return False, message

    def spawn_cells(
        self,
        dna: str,
        x: int,
        y: int,
        count: int = 1,
        channel: int = 0,
        ribosome: int = 0,
        x_step: int = 0,
        y_step: int = 0,
        attributes: dict | None = None,
    ) -> tuple[int, list[str]]:
        count = max(1, int(count))
        created = 0
        errors: list[str] = []
        for index in range(count):
            cell_x = int(x) + index * int(x_step)
            cell_y = int(y) + index * int(y_step)
            if not (0 <= cell_x < self.width and 0 <= cell_y < self.height):
                errors.append(f'Out of bounds: ({cell_x}, {cell_y})')
                continue
            normalized_channel = int(channel)
            if MapConfig.channels > 0:
                normalized_channel = normalized_channel % MapConfig.channels
            cell = self.cell_cls.create_cell_from_DNA(
                dna,
                cell_x,
                cell_y,
                self.NTs,
                self,
                ribosome=int(ribosome),
                channel=normalized_channel,
            )
            if attributes:
                for key, value in attributes.items():
                    if key in {'world', 'NTs', 'logger'}:
                        continue
                    if key == 'direction' and value not in {'w', 'a', 's', 'd'}:
                        continue
                    if hasattr(cell, key):
                        setattr(cell, key, value)
            self.cells.append(cell)
            created += 1
        self.update_cells_map()
        if created > 0:
            self._record_snapshot('spawn')
            self.logger.info(
                'Spawned cells: count=%s dna=%s origin=(%s,%s) step=(%s,%s) channel=%s',
                created,
                dna,
                x,
                y,
                x_step,
                y_step,
                channel,
            )
        if errors:
            self.logger.warning('Spawn errors: %s', '; '.join(errors))
        return created, errors

    def apply_config_update(self, path: str, value) -> tuple[bool, str, bool]:
        config_types = {
            'MapConfig': MapConfig,
            'CellConfig': CellConfig,
            'DispConfig': DispConfig,
            'SaveConfig': SaveConfig,
            'RandomConfig': RandomConfig,
            'LogConfig': LogConfig,
        }
        if '.' not in path:
            return False, 'Config path must be ClassName.attr format.', False
        class_name, attr_name = path.split('.', 1)
        config_cls = config_types.get(class_name)
        if config_cls is None:
            return False, f'Unsupported config class: {class_name}', False
        if not hasattr(config_cls, attr_name):
            return False, f'Unknown config attr: {path}', False

        if class_name == 'MapConfig' and attr_name in {'width', 'height', 'channels'}:
            value = int(value)
            if value <= 0:
                return False, f'{path} must be > 0.', False
        if class_name == 'DispConfig' and attr_name in {'fps', 'scale'}:
            value = int(value)
            if value <= 0:
                return False, f'{path} must be > 0.', False

        setattr(config_cls, attr_name, value)

        requires_display_reset = False
        if class_name == 'MapConfig' and attr_name in {'width', 'height', 'channels'}:
            self.width = int(MapConfig.width)
            self.height = int(MapConfig.height)
            if self.width <= 0 or self.height <= 0:
                return False, 'Map size must be positive.', False
            self.NTs.set_map(self.NTs.map)
            for cell in self.cells:
                cell.x = int(cell.x) % self.width
                cell.y = int(cell.y) % self.height
                cell.channel = int(cell.channel) % MapConfig.channels
            self.update_cells_map()
            requires_display_reset = True
        if class_name == 'DispConfig' and attr_name == 'scale':
            requires_display_reset = True

        self._record_snapshot(f'config:{path}')
        message = f'Updated {path}={value!r}'
        self.logger.info(message)
        return True, message, requires_display_reset

    def _simulate_one_tick(self) -> bool:
        run_cells_act(self)
        self.ticks += 1
        log_periodic_summary(self)
        autosave_if_needed(self)
        return not should_stop(self)
            
    def update(self, screen: pygame.surface.Surface, simulate: bool = True, draw_tick_on_map: bool = True) -> bool:
        """更新一帧世界"""
        self.screen = screen
        if simulate:
            if self._simulate_one_tick() is False:
                return False
            self._record_snapshot('tick')
        render_world(self.screen, self)
        if draw_tick_on_map:
            self.draw_tick()
        return True
