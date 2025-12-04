import pygame
import sys

from world import World
from config import * 
from logger_setup import setup_logging
from pathlib import Path
import os


def main():
    # 清空旧日志
    log_file = Path(LogConfig.file)
    if log_file.exists():
        log_file.unlink()
    
    logger = setup_logging()
    pygame.init()
    WIDTH, HEIGHT = MapConfig.width, MapConfig.height
    SCALE = DispConfig.scale
    flags = pygame.DOUBLEBUF
    try:
        screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE), flags, vsync=1)
    except TypeError:
        # pygame 2.0+ supports vsync; 兼容旧版本
        screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE), flags)
    pygame.display.set_caption('Fauna F**k')
    
    world = World(WIDTH, HEIGHT)
    running = True
    clock = pygame.time.Clock()
    
    if SaveConfig.read and SaveConfig.read_path != "":
        try:
            world.read_world_state(SaveConfig.read_path)
        except Exception as e:
            message = f"Failed to read world state from {SaveConfig.read_path}: {e}"
            world.logger.error(message)
            print(message)

    while running:

        clock.tick(DispConfig.fps)
        
        # 事件，目前只有退出
        for event in pygame.event.get():
            # 退出
            if event.type == pygame.QUIT:
                running = False
        
        if world.update(screen) is False:
            running = False

        pygame.display.flip()
    
    # 收集DNA和RNA统计
    filename = os.path.join(SaveConfig.autosave_dir, 'final_stats.txt')
    world.save_world_state(filename)

if __name__ == '__main__':
    main()