import pygame
import sys
import random

# Configuración básica
WIDTH, HEIGHT = 480, 270 
SCALED_WIDTH, SCALED_HEIGHT = 1280, 720 

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.new_size = (120, 120)
        
        # --- CARGA DE ANIMACIONES ---
        # 1. Movimiento (8 frames)
        self.walk_frames = self.load_frames("assets/balanzat_movimiento.png", 8)
        # 2. Ataque / Idle (7 frames)
        self.attack_frames = self.load_frames("assets/spritesheet-bz.png", 7)
        
        # El estado inicial es el frame 0 del sheet de la raqueta
        self.image = self.attack_frames[0] 
        self.rect = self.image.get_rect(midbottom=(100, 240))
        
        # Estados
        self.speed = 3
        self.is_attacking = False
        self.current_frame = 0
        self.last_anim = pygame.time.get_ticks()

    def load_frames(self, path, num_frames):
        """Carga, corta y escala los frames de un spritesheet."""
        try:
            sheet = pygame.image.load(path).convert_alpha()
            frame_width = sheet.get_width() // num_frames
            temp_list = []
            for i in range(num_frames):
                frame_original = sheet.subsurface((i * frame_width, 0, frame_width, sheet.get_height()))
                frame_escalado = pygame.transform.scale(frame_original, self.new_size)
                temp_list.append(frame_escalado)
            return temp_list
        except:
            surf = pygame.Surface(self.new_size)
            surf.fill((255, 0, 0))
            return [surf]

    def update(self):
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()
        moving = False

        if not self.is_attacking:
            # Control de movimiento[cite: 2]
            if keys[pygame.K_LEFT]: 
                self.rect.x -= self.speed
                moving = True
            if keys[pygame.K_RIGHT]: 
                self.rect.x += self.speed
                moving = True
            if keys[pygame.K_UP]: 
                self.rect.y -= self.speed // 2
                moving = True
            if keys[pygame.K_DOWN]: 
                self.rect.y += self.speed // 2

            # --- LÓGICA DE ANIMACIÓN ---
            if moving:
                # Si camina, usa el spritesheet de movimiento[cite: 2]
                if now - self.last_anim > 100:
                    self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
                    self.image = self.walk_frames[self.current_frame]
                    self.last_anim = now
            else:
                # Si está PARADO, usa el frame 0 de la raqueta (IDLE)[cite: 3]
                self.image = self.attack_frames[0]
                self.current_frame = 0
        else:
            # Si está ATACANDO, recorre todo el spritesheet de la raqueta[cite: 3]
            if now - self.last_anim > 80:
                self.current_frame += 1
                if self.current_frame < len(self.attack_frames):
                    self.image = self.attack_frames[self.current_frame]
                    self.last_anim = now
                else:
                    self.is_attacking = False
                    self.current_frame = 0
                    self.image = self.attack_frames[0] # Vuelve a idle

        # LÍMITES (Vereda del IFTS)[cite: 2]
        if self.rect.bottom < 215: self.rect.bottom = 215
        if self.rect.bottom > 270: self.rect.bottom = 270
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((25, 40))
        self.image.fill((200, 0, 0))
        self.rect = self.image.get_rect(midbottom=(WIDTH + 50, random.randint(220, 265)))
        self.speed = random.randint(1, 2)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < -50: self.kill()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    canvas = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    try:
        bg_original = pygame.image.load("assets/ifts.png").convert()
        background = pygame.transform.scale(bg_original, (WIDTH, HEIGHT))
    except:
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((50, 50, 50))

    player = Player()
    enemies = pygame.sprite.Group()
    spawn_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            # Ataque con espacio[cite: 3]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not player.is_attacking:
                    player.is_attacking = True
                    player.current_frame = 0
                    player.last_anim = pygame.time.get_ticks()

        # Actualización
        player.update()
        enemies.update()

        if pygame.time.get_ticks() - spawn_timer > 2000:
            enemies.add(Enemy())
            spawn_timer = pygame.time.get_ticks()

        # Renderizado con profundidad (Y-sorting)[cite: 2]
        canvas.blit(background, (0, 0))
        all_sprites = sorted(enemies.sprites() + [player], key=lambda s: s.rect.bottom)
        for sprite in all_sprites:
            canvas.blit(sprite.image, sprite.rect)

        # Mostrar en pantalla escalada
        final_frame = pygame.transform.scale(canvas, (SCALED_WIDTH, SCALED_HEIGHT))
        screen.blit(final_frame, (0, 0))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()