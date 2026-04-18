import pygame
import sys

# Configuración de resolución
WIDTH, HEIGHT = 480, 270 
SCALED_WIDTH, SCALED_HEIGHT = 1280, 720 

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        # 1. CARGA DEL SPRITESHEET
        # Cambiá el nombre del archivo al que tengas en tu carpeta assets
        self.sheet = pygame.image.load("assets/spritesheet.png").convert_alpha()
        
        # 2. CONFIGURACIÓN DEL RECORTE
        self.num_frames = 7
        # Calculamos el ancho de cada frame dividiendo el total por la cantidad de frames
        self.frame_width = self.sheet.get_width() // self.num_frames
        self.frame_height = self.sheet.get_height()
        
        self.frames = []
        for i in range(self.num_frames):
            # Recortamos cada cuadro (x, y, ancho, alto)
            rect = pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = self.sheet.subsurface(rect)
            self.frames.append(frame)
            
        # 3. ESTADO INICIAL
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (WIDTH // 4, HEIGHT - 20) # Posicionado en el suelo
        
        # Animación y tiempos
        self.is_attacking = False
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 100 # Velocidad en milisegundos

    def update(self):
        if self.is_attacking:
            now = pygame.time.get_ticks()
            if now - self.last_update > self.frame_rate:
                self.last_update = now
                self.current_frame += 1
                
                if self.current_frame < self.num_frames:
                    self.image = self.frames[self.current_frame]
                else:
                    # Finaliza el ataque y vuelve al frame 0 (Idle)
                    self.is_attacking = False
                    self.current_frame = 0
                    self.image = self.frames[self.current_frame]

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.current_frame = 0
            self.last_update = pygame.time.get_ticks()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    pixel_canvas = pygame.Surface((WIDTH, HEIGHT))
    pygame.display.set_caption("Proyecto Integrador - Fight Engine")
    
    clock = pygame.time.Clock()
    player = Player()
    all_sprites = pygame.sprite.Group(player)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Ataca con Espacio o Clic Izquierdo
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                player.attack()

        # Actualización
        all_sprites.update()

        # Renderizado
        pixel_canvas.fill((30, 30, 50)) 
        all_sprites.draw(pixel_canvas)

        # Escalado para monitor
        scaled_surface = pygame.transform.scale(pixel_canvas, (SCALED_WIDTH, SCALED_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()