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
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
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
    
    # 收集DNA
    world.collect_DNAs()
    # 收集RNA
    world.collect_RNAs()
if __name__ == '__main__':
    main()