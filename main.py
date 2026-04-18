import pygame
import sys

# Configuración inicial
WIDTH, HEIGHT = 480, 270  # Resolución retro (estilo GBA/Arcade)
SCALED_WIDTH, SCALED_HEIGHT = 1280, 720 # Ventana que verás en tu monitor

def main():
    pygame.init()
    
    # Creamos la ventana real y una superficie pequeña para el pixel art
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    pixel_canvas = pygame.Surface((WIDTH, HEIGHT))
    pygame.display.set_caption("Proyecto Pixel Art - Proyecto Integrador")
    
    clock = pygame.time.Clock()
    running = True

    while running:
        # 1. Gestión de Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Lógica de juego (Aquí irá el movimiento de tus 3 personajes)

        # 3. Dibujo (Renderizado)
        pixel_canvas.fill((30, 30, 50)) # Color de fondo (un azul oscuro callejero)
        
        # Dibujamos un rectángulo como placeholder del Personaje 1
        pygame.draw.rect(pixel_canvas, (255, 0, 0), (50, 150, 32, 48)) 

        # Escalamos el canvas de pixel art al tamaño de la ventana
        scaled_surface = pygame.transform.scale(pixel_canvas, (SCALED_WIDTH, SCALED_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60) # Limitamos a 60 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()