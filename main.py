import pygame
import sys

from world import World
from config import * 



def main():
    pygame.init()
    WIDTH, HEIGHT = MapConfig.width, MapConfig.height
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption('Fauna Fuck')
    
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
    
    genesequence = world.collect_gene()
    print(genesequence)

if __name__ == '__main__':
    main()