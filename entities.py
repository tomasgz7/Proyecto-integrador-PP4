import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, color, controls, speed):
        super().__init__()
        # Por ahora usamos un Surface sólido, luego lo reemplazaremos con el Sprite de Aseprite
        self.image = pygame.Surface((40, 80)) 
        self.image.fill(color)
        
        # El rect es para colisiones, pos es para movimiento suave (float)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos = pygame.Vector2(self.rect.midbottom)
        self.vel = pygame.Vector2()
        
        self.speed = speed
        self.controls = controls # Diccionario con las teclas: {'up': K_UP, ...}
        self.state = "IDLE"

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = keys[self.controls['right']] - keys[self.controls['left']]
        # El eje Y se mueve al 60% para simular la profundidad 2.5D
        self.vel.y = (keys[self.controls['down']] - keys[self.controls['up']]) * 0.6

        if self.vel.length() > 0:
            self.vel = self.vel.normalize()
            self.state = "WALK"
        else:
            self.state = "IDLE"

    def update(self):
        self.get_input()
        self.pos += self.vel * self.speed
        self.rect.midbottom = self.pos # Actualizamos la caja de colisión

        # Límite de la pantalla (para que no se vaya de la calle)
        self.pos.y = max(180, min(self.pos.y, 270))