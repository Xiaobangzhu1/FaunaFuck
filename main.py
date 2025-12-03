import pygame
import sys

from world import World
from config import * 
from logger_setup import setup_logging
from pathlib import Path



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
    DNAs = world.collect_DNAs(statistics=False)
    world.logger.info(f"\n{DNAs}")

if __name__ == '__main__':
    main()