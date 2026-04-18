import pygame
import sys
import random

# Configuración básica
WIDTH, HEIGHT = 480, 270 
SCALED_WIDTH, SCALED_HEIGHT = 1280, 720 

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.sheet = pygame.image.load("assets/spritesheet-bz.png").convert_alpha()
        self.num_frames = 7
        self.frame_width = self.sheet.get_width() // self.num_frames
        self.frames = [self.sheet.subsurface((i * self.frame_width, 0, self.frame_width, self.sheet.get_height())) for i in range(self.num_frames)]
        
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(100, 240))
        self.speed = 4
        self.is_attacking = False
        self.last_anim = pygame.time.get_ticks()

    def update(self):
        keys = pygame.key.get_pressed()
        if not self.is_attacking:
            # Movimiento estilo Streets of Rage (8 direcciones)
            if keys[pygame.K_LEFT]: self.rect.x -= self.speed
            if keys[pygame.K_RIGHT]: self.rect.x += self.speed
            if keys[pygame.K_UP]: self.rect.y -= self.speed // 2 # Menos velocidad en Y para profundidad
            if keys[pygame.K_DOWN]: self.rect.y += self.speed // 2

        # Lógica de animación de ataque
        if self.is_attacking:
            now = pygame.time.get_ticks()
            if now - self.last_anim > 80:
                self.current_frame += 1
                if self.current_frame < self.num_frames:
                    self.image = self.frames[self.current_frame]
                else:
                    self.is_attacking = False
                    self.current_frame = 0
                    self.image = self.frames[0]
                self.last_anim = now

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 48))
        self.image.fill((200, 0, 0)) # Cuadrado rojo temporal
        self.rect = self.image.get_rect(midbottom=(WIDTH + 50, random.randint(200, 260)))
        self.speed = 2

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0: self.kill()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    canvas = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    player = Player()
    player_group = pygame.sprite.Group(player)
    enemies = pygame.sprite.Group()
    spawn_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.is_attacking = True

        # 1. Lógica
        player_group.update()
        enemies.update()

        # Spawner simple de enemigos
        if pygame.time.get_ticks() - spawn_timer > 2000:
            enemies.add(Enemy())
            spawn_timer = pygame.time.get_ticks()

        # 2. Renderizado (Orden de capas)
        canvas.fill((20, 20, 30)) # ACÁ va tu fondo (canvas.blit(fondo, (0,0)))
        
        # Dibujar sombras o suelo si querés
        pygame.draw.rect(canvas, (10, 10, 15), (0, 200, WIDTH, 70)) 
        
        enemies.draw(canvas)
        player_group.draw(canvas)

        # 3. Escalar y mostrar
        screen.blit(pygame.transform.scale(canvas, (SCALED_WIDTH, SCALED_HEIGHT)), (0, 0))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()