import pygame
import sys
import random
import math

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────── ───────────
CANVAS_W, CANVAS_H = 480, 270
WIN_W,    WIN_H    = 1280, 720 
FPS        = 60 
TITLE      = "PEDRO BALANZAT - La Raqueta de la Justicia"

FLOOR_Y    = 248   # Y donde pisan todos los personajes (midbottom)
FLOOR_TOP  = 212   # límite superior de la zona caminable
FLOOR_BOT  = 254   # límite inferior

BG_COLOR   = (255, 255, 255)   # colorkey sprites (fondo blanco)

# ─────────────────────────────────────────────────────────────────────────────
#  UTILIDADES DE CARGA
# ─────────────────────────────────────────────────────────────────────────────
def load_sheet(path, n_frames, out_h, colorkey=None, trim=False):
    """Carga un spritesheet horizontal de n_frames con fondo transparente.
    trim=True recorta el espacio vacío de cada frame para evitar jitter.
    colorkey=(r,g,b) hace transparente ese color en imágenes sin canal alpha."""
    try:
        from PIL import Image as PILImage
        pil = PILImage.open(path).convert("RGBA")

        # Si el original no tenía alpha y hay colorkey, reemplazar ese color por transparente
        if colorkey is not None:
            import numpy as np
            arr = np.array(pil)
            r, g, b = colorkey
            mask = (arr[:, :, 0] == r) & (arr[:, :, 1] == g) & (arr[:, :, 2] == b)
            arr[mask, 3] = 0
            pil = PILImage.fromarray(arr)

        pw, ph = pil.size
        fw = pw // n_frames
        scale = out_h / ph
        frames = []
        for i in range(n_frames):
            cell = pil.crop((i * fw, 0, (i + 1) * fw, ph))
            if trim:
                bbox = cell.getbbox()
                if bbox:
                    cell = cell.crop(bbox)
            cw, ch = cell.size
            new_w = max(1, round(cw * scale))
            new_h = max(1, round(ch * scale))
            cell = cell.resize((new_w, new_h), PILImage.NEAREST)
            raw = pygame.image.fromstring(cell.tobytes(), cell.size, "RGBA")
            frames.append(raw.convert_alpha())
        return frames
    except Exception as e:
        print(f"[WARN] {path}: {e}")
        s = pygame.Surface((int(out_h * 0.55), out_h), pygame.SRCALPHA)
        s.fill((255, 0, 0, 255))
        return [s]


def load_image(path, out_h, colorkey=BG_COLOR):
    try:
        img = pygame.image.load(path).convert()
        img.set_colorkey(colorkey, pygame.RLEACCEL)
        iw, ih = img.get_size()
        nw = int(iw * out_h / ih)
        return pygame.transform.scale(img, (nw, out_h))
    except Exception as e:
        print(f"[WARN] {path}: {e}")
        s = pygame.Surface((int(out_h * 0.55), out_h))
        s.fill((200, 0, 200))
        return s


# ─────────────────────────────────────────────────────────────────────────────
#  GENERADOR DE FONDO (fallback)
# ─────────────────────────────────────────────────────────────────────────────
def make_fallback_bg():
    s = pygame.Surface((CANVAS_W, CANVAS_H))
    s.fill((90, 120, 180))
    pygame.draw.rect(s, (160,150,135), (0, FLOOR_TOP, CANVAS_W, CANVAS_H - FLOOR_TOP))
    pygame.draw.rect(s, (50, 50, 55),  (0, FLOOR_BOT, CANVAS_W, CANVAS_H - FLOOR_BOT))
    return s


# ─────────────────────────────────────────────────────────────────────────────
#  JUGADOR
# ─────────────────────────────────────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    HEIGHT = 96   # altura del sprite en pantalla

    def __init__(self, x):
        super().__init__()

        self.atk_frames  = load_sheet("assets/spritesheet-bz.png",        7, self.HEIGHT)
        self.walk_frames = load_sheet("assets/balanzat_movimiento.png",    8, self.HEIGHT, trim=True)

        # Estado
        self.facing       = 1       # 1=der, -1=izq
        self.is_attacking = False
        self.is_walking   = False
        self.cur_frame    = 0
        self.last_anim    = 0
        self.atk_active   = False   # ventana de daño activa

        # Posición — usamos midbottom como anchor
        self.x    = float(x)
        self.y    = float(FLOOR_Y)
        self.speed = 2

        # Imagen inicial
        self.image = self.atk_frames[0]
        self.rect  = self.image.get_rect()
        self._sync_rect()

        # Stats
        self.hp     = 200
        self.max_hp = 200
        self.alive  = True
        self.score  = 0

    def _sync_rect(self):
        """Mantiene rect.midbottom sincronizado con (x, y)."""
        self.rect.midbottom = (round(self.x), round(self.y))

    def _set_frame(self, frames, idx):
        """Cambia frame respetando el facing sin mover la posición."""
        f = frames[idx % len(frames)]
        if self.facing == -1:
            f = pygame.transform.flip(f, True, False)
        self.image = f
        # Recalcular rect manteniendo midbottom
        mb = self.rect.midbottom
        self.rect  = self.image.get_rect()
        self.rect.midbottom = mb

    def get_hitbox(self):
        r = self.rect
        return pygame.Rect(r.x + r.w//4, r.y + r.h//6, r.w//2, r.h*5//6)

    def get_attack_rect(self):
        hb = self.get_hitbox()
        reach = 55
        if self.facing == 1:
            return pygame.Rect(hb.right - 10, hb.y + hb.h//4, reach, hb.h//2)
        else:
            return pygame.Rect(hb.x - reach + 10, hb.y + hb.h//4, reach, hb.h//2)

    def start_attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.cur_frame    = 0
            self.last_anim    = pygame.time.get_ticks()
            self.atk_active   = False

    def take_damage(self, dmg):
        if not self.alive: return
        self.hp = max(0, self.hp - dmg)
        if self.hp == 0:
            self.alive = False

    def update(self):
        keys = pygame.key.get_pressed()
        now  = pygame.time.get_ticks()

        # ── ATAQUE (bloquea movimiento) ───────────────────────────────────
        if self.is_attacking:
            spd = 75  # ms por frame
            if now - self.last_anim >= spd:
                self.last_anim = now
                self.cur_frame += 1
                if self.cur_frame >= len(self.atk_frames):
                    self.is_attacking = False
                    self.atk_active   = False
                    self.cur_frame    = 0
                else:
                    # Ventana de daño: frames 2-4
                    self.atk_active = 2 <= self.cur_frame <= 4
                    self._set_frame(self.atk_frames, self.cur_frame)
            return

        self.atk_active = False

        # ── MOVIMIENTO ────────────────────────────────────────────────────
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        moving = dx != 0 or dy != 0

        if moving:
            ln = math.hypot(dx, dy)
            self.x += (dx / ln) * self.speed
            self.y += (dy / ln) * self.speed * 0.5   # perspectiva 2.5D
            if dx != 0:
                self.facing = 1 if dx > 0 else -1

        # Límites canvas (ancho fijo para evitar jitter entre frames de distinto tamaño)
        hw = 30
        self.x = max(hw, min(CANVAS_W - hw, self.x))
        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()

        # ── ANIMACIÓN ────────────────────────────────────────────────────
        if moving:
            spd = 90  # ms por frame walk
            if now - self.last_anim >= spd:
                self.last_anim  = now
                self.cur_frame  = (self.cur_frame + 1) % len(self.walk_frames)
                self._set_frame(self.walk_frames, self.cur_frame)
        else:
            self.cur_frame = 0
            self._set_frame(self.atk_frames, 0)


# ─────────────────────────────────────────────────────────────────────────────
#  ENEMIGO BASE
# ─────────────────────────────────────────────────────────────────────────────
SHIRT_COLORS = [
    (180,30,30),(30,80,200),(30,160,60),(200,100,30),
    (130,30,180),(200,30,120),(90,90,90),(160,160,30),
    (30,160,160),(160,80,20),
]

class Enemy(pygame.sprite.Sprite):
    HEIGHT  = 88    # mismo orden de magnitud que el jugador
    _eid    = 0

    def __init__(self, x, y=None):
        super().__init__()
        self.eid   = Enemy._eid % 10
        Enemy._eid += 1

        self.frames  = self._gen_frames(SHIRT_COLORS[self.eid])
        self.image   = self.frames[0]

        self.x = float(x)
        self.y = float(y if y else FLOOR_Y)
        self.rect  = self.image.get_rect()
        self._sync_rect()

        self.hp      = 50   # aguanta exactamente 2 golpes de 22
        self.max_hp  = 50
        self.alive   = True
        self.speed   = random.uniform(0.4, 1.0)
        self.facing  = -1

        self.fi       = 0
        self.anim_t   = 0
        self.atk_cd   = random.randint(60, 120)  # offset inicial para que no ataquen todos juntos

    def _gen_frames(self, shirt, n=4):
        frames = []
        h = self.HEIGHT
        sc = h / 80  # escala relativa
        W  = int(28 * sc)
        H  = h
        for i in range(n):
            leg = int(math.sin(i * math.pi / 2) * 3 * sc)
            s   = pygame.Surface((W, H), pygame.SRCALPHA)
            pw  = max(1, int(sc))
            # piernas
            pygame.draw.rect(s, (40,40,90),     (int(4*sc),  int(52*sc)+leg, int(7*sc), int(22*sc)))
            pygame.draw.rect(s, (40,40,90),     (int(14*sc), int(52*sc)-leg, int(7*sc), int(22*sc)))
            # zapatos
            pygame.draw.rect(s, (20,20,20),     (int(2*sc),  int(73*sc)+leg, int(11*sc),int(5*sc)))
            pygame.draw.rect(s, (20,20,20),     (int(12*sc), int(73*sc)-leg, int(11*sc),int(5*sc)))
            # cuerpo
            pygame.draw.rect(s, shirt,          (int(3*sc),  int(28*sc), int(19*sc), int(26*sc)))
            # brazos
            pygame.draw.rect(s, shirt,          (int(-1*sc), int(30*sc), int(6*sc),  int(16*sc)))
            pygame.draw.rect(s, shirt,          (int(20*sc), int(30*sc), int(6*sc),  int(16*sc)))
            # manos
            pygame.draw.rect(s, (220,180,140),  (int(-1*sc), int(44*sc), int(5*sc),  int(6*sc)))
            pygame.draw.rect(s, (220,180,140),  (int(21*sc), int(44*sc), int(5*sc),  int(6*sc)))
            # cabeza
            pygame.draw.rect(s, (220,180,140),  (int(6*sc),  int(4*sc),  int(14*sc), int(22*sc)))
            # pelo
            pygame.draw.rect(s, (60,35,15),     (int(6*sc),  int(4*sc),  int(14*sc), int(7*sc)))
            # ojos
            pygame.draw.rect(s, (30,30,30),     (int(8*sc),  int(12*sc), int(3*sc),  int(3*sc)))
            pygame.draw.rect(s, (30,30,30),     (int(14*sc), int(12*sc), int(3*sc),  int(3*sc)))
            frames.append(s)
        return frames

    def _sync_rect(self):
        self.rect.midbottom = (round(self.x), round(self.y))

    def get_hitbox(self):
        r = self.rect
        return pygame.Rect(r.x + 2, r.y + r.h//5, r.w - 4, r.h*4//5)

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
            self.kill()

    def update(self, player):
        if not self.alive: return

        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)

        self.facing = 1 if dx > 0 else -1

        engage_dist = self.rect.w * 0.6
        if dist > engage_dist:
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed * 0.5
        else:
            if self.atk_cd <= 0 and player.alive:
                player.take_damage(5)
                self.atk_cd = 100

        if self.atk_cd > 0:
            self.atk_cd -= 1

        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()

        # animación
        self.anim_t += 1
        if self.anim_t >= 10:
            self.anim_t = 0
            self.fi     = (self.fi + 1) % len(self.frames)
            f = self.frames[self.fi]
            if self.facing == -1:
                f = pygame.transform.flip(f, True, False)
            self.image = f
            mb = self.rect.midbottom
            self.rect  = self.image.get_rect()
            self.rect.midbottom = mb

    def draw_hp_bar(self, surface):
        bw   = self.rect.w
        fill = max(0, int(bw * self.hp / self.max_hp))
        bx, by = self.rect.x, self.rect.y - 5
        pygame.draw.rect(surface, (120, 0, 0), (bx, by, bw, 3))
        pygame.draw.rect(surface, (0, 210, 50), (bx, by, fill, 3))


# ─────────────────────────────────────────────────────────────────────────────
#  BOSS: FOREST GUMP
# ─────────────────────────────────────────────────────────────────────────────
class Boss(pygame.sprite.Sprite):
    HEIGHT = 110

    HEIGHT_WALK = 110
    HEIGHT_ATK  = 110   # se normaliza al HEIGHT_WALK en __init__

    def __init__(self, x):
        super().__init__()
        # Intentar cargar sprites reales de Forest Gump
        self.walk_frames = load_sheet("assets/boss_walk.png",   8, self.HEIGHT_WALK, colorkey=(0,0,0))
        self.atk_frames  = load_sheet("assets/boss_attack.png", 8, self.HEIGHT_ATK,  colorkey=(0,0,0))
        # Asegurar que atk tenga el mismo alto que walk
        if self.atk_frames[0].get_height() != self.walk_frames[0].get_height():
            h = self.walk_frames[0].get_height()
            self.atk_frames = [pygame.transform.scale(f, (int(f.get_width() * h / f.get_height()), h)) for f in self.atk_frames]
        self.frames      = self.walk_frames   # alias para compatibilidad

        self.image  = self.frames[0]
        self.x = float(x)
        self.y = float(FLOOR_Y)
        self.rect = self.image.get_rect()
        self._sync_rect()

        self.hp      = 800
        self.max_hp  = 800
        self.alive   = True
        self.speed   = 0.7
        self.facing  = -1
        self.fi      = 0
        self.anim_t  = 0
        self.atk_cd  = 80
        self.phase   = 1   # fase 2 cuando hp < 50%
        self.is_attacking_anim = False
        self.atk_fi  = 0

    def _gen_frames(self, n=6):
        frames = []
        h  = self.HEIGHT
        sc = h / 100
        W  = int(40 * sc)
        H  = h
        for i in range(n):
            leg = int(math.sin(i * math.pi / 3) * 4 * sc)
            arm = int(math.sin(i * math.pi / 3 + math.pi) * 5 * sc)
            s   = pygame.Surface((W, H), pygame.SRCALPHA)

            # piernas (pantalón beis)
            pygame.draw.rect(s, (195,170,115), (int(8*sc),  int(58*sc)+leg, int(9*sc), int(30*sc)))
            pygame.draw.rect(s, (195,170,115), (int(20*sc), int(58*sc)-leg, int(9*sc), int(30*sc)))
            # zapatillas blancas
            pygame.draw.rect(s, (240,240,240), (int(5*sc),  int(87*sc)+leg, int(13*sc),int(7*sc)))
            pygame.draw.rect(s, (240,240,240), (int(18*sc), int(87*sc)-leg, int(13*sc),int(7*sc)))
            # cuerpo remera blanca
            pygame.draw.rect(s, (235,235,235), (int(7*sc),  int(30*sc), int(23*sc), int(30*sc)))
            # número
            font_s = pygame.font.SysFont("monospace", max(6, int(10*sc)), bold=True)
            num = font_s.render("9", False, (40,60,160))
            s.blit(num, (int(15*sc), int(35*sc)))
            # brazos
            pygame.draw.rect(s, (235,235,235), (int(0*sc),  int(33*sc)+arm, int(9*sc), int(18*sc)))
            pygame.draw.rect(s, (235,235,235), (int(28*sc), int(33*sc)-arm, int(9*sc), int(18*sc)))
            # manos
            pygame.draw.rect(s, (215,175,135), (int(0*sc),  int(49*sc)+arm, int(8*sc), int(8*sc)))
            pygame.draw.rect(s, (215,175,135), (int(29*sc), int(49*sc)-arm, int(8*sc), int(8*sc)))
            # cabeza
            pygame.draw.rect(s, (215,175,135), (int(9*sc),  int(5*sc),  int(20*sc), int(24*sc)))
            # gorra
            pygame.draw.rect(s, (205,165,85),  (int(8*sc),  int(5*sc),  int(22*sc), int(8*sc)))
            pygame.draw.rect(s, (185,145,65),  (int(4*sc),  int(9*sc),  int(6*sc),  int(4*sc)))
            # ojos
            pygame.draw.rect(s, (30,30,30),    (int(12*sc), int(14*sc), int(3*sc),  int(4*sc)))
            pygame.draw.rect(s, (30,30,30),    (int(22*sc), int(14*sc), int(3*sc),  int(4*sc)))
            # sonrisa
            pygame.draw.rect(s, (175,75,75),   (int(13*sc), int(22*sc), int(11*sc), int(3*sc)))
            pygame.draw.rect(s, (175,75,75),   (int(11*sc), int(20*sc), int(3*sc),  int(3*sc)))
            pygame.draw.rect(s, (175,75,75),   (int(23*sc), int(20*sc), int(3*sc),  int(3*sc)))

            frames.append(s)
        return frames

    def _sync_rect(self):
        self.rect.midbottom = (round(self.x), round(self.y))

    def get_hitbox(self):
        r = self.rect
        return pygame.Rect(r.x + 3, r.y + r.h//6, r.w - 6, r.h*5//6)

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        # Fase 2: más rápido y agresivo
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            self.speed = 1.2
        if self.hp <= 0:
            self.alive = False
            self.kill()

    def update(self, player):
        if not self.alive: return

        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)

        self.facing = 1 if dx > 0 else -1
        engage = self.rect.w * 0.7

        if dist > engage:
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed * 0.5

        else:
            spd = 60 if self.phase == 1 else 45
            if self.atk_cd <= 0 and player.alive:
                dmg = 12 if self.phase == 1 else 18
                player.take_damage(dmg)
                self.atk_cd = spd

        if self.atk_cd > 0:
            self.atk_cd -= 1

        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()

        # animación: ataque cuando está cerca, walk cuando persigue
        self.anim_t += 1
        anim_delay = 7 if self.phase == 1 else 5
        if self.anim_t >= anim_delay:
            self.anim_t = 0
            if dist <= engage * 1.2:
                # animación de ataque
                self.atk_fi = (self.atk_fi + 1) % len(self.atk_frames)
                f = self.atk_frames[self.atk_fi]
            else:
                # animación de caminar
                self.fi = (self.fi + 1) % len(self.walk_frames)
                f = self.walk_frames[self.fi]
            if self.facing == -1:
                f = pygame.transform.flip(f, True, False)
            self.image = f
            mb = self.rect.midbottom
            self.rect  = self.image.get_rect()
            self.rect.midbottom = mb

    def draw_boss_bar(self, canvas, font):
        bw   = 220
        bh   = 9
        bx   = (CANVAS_W - bw) // 2
        by   = CANVAS_H - 20
        fill = max(0, int(bw * self.hp / self.max_hp))

        pygame.draw.rect(canvas, (30,30,30),  (bx-1, by-1, bw+2, bh+2))
        pygame.draw.rect(canvas, (140,20,20), (bx, by, bw, bh))
        col  = (230,80,20) if self.phase == 1 else (255,30,30)
        pygame.draw.rect(canvas, col,         (bx, by, fill, bh))
        pygame.draw.rect(canvas, (220,220,220),(bx, by, bw, bh), 1)

        lbl = font.render("BOSS: FOREST GUMP", False, (255,255,255))
        canvas.blit(lbl, (bx, by - 9))
        if self.phase == 2:
            ph2 = font.render("¡FASE 2!", False, (255,50,50))
            canvas.blit(ph2, (bx + bw + 4, by))


# ─────────────────────────────────────────────────────────────────────────────
#  HIT EFFECT
# ─────────────────────────────────────────────────────────────────────────────
class HitFX:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t   = 0
        self.max = 12

    def update(self): self.t += 1
    def done(self):   return self.t >= self.max

    def draw(self, surf):
        prog = self.t / self.max
        r    = int(8 * (1 - prog))
        alpha = int(255 * (1 - prog))
        c = (255, int(220 * (1-prog)), 0)
        if r > 0:
            pygame.draw.circle(surf, c, (self.x, self.y), r)
        for ang in range(0, 360, 45):
            rad = math.radians(ang + self.t * 25)
            ex  = int(self.x + (r + 5) * math.cos(rad))
            ey  = int(self.y + (r + 5) * math.sin(rad))
            if r > 0:
                pygame.draw.line(surf, c, (self.x, self.y), (ex, ey), 1)




# ─────────────────────────────────────────────────────────────────────────────
#  CORAZÓN RECUPERABLE
# ─────────────────────────────────────────────────────────────────────────────
class HeartPickup:
    HEAL_AMOUNT  = 30
    SPAWN_EVERY  = 5   # cada 5 enemigos eliminados aparece un corazón
    LIFETIME     = 600 # frames que dura en pantalla (10 seg a 60fps)
    BOB_SPEED    = 0.08
    BOB_AMP      = 3

    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.alive  = True
        self.timer  = 0
        self.size   = 10

    def update(self, player):
        self.timer += 1
        if self.timer >= self.LIFETIME:
            self.alive = False
            return
        # Recoger si el jugador está cerca
        dx = player.x - self.x
        dy = player.y - self.y
        if abs(dx) < 20 and abs(dy) < 25 and player.alive:
            player.hp = min(player.max_hp, player.hp + self.HEAL_AMOUNT)
            self.alive = False

    def draw(self, canvas):
        if not self.alive: return
        # Bobbing
        bob_y = int(self.y - 20 + math.sin(self.timer * self.BOB_SPEED) * self.BOB_AMP)
        cx, cy = int(self.x), bob_y
        s = self.size

        # Parpadea cuando le queda poco tiempo
        if self.timer > self.LIFETIME - 120 and (self.timer // 8) % 2 == 0:
            return

        # Dibujar corazón pixel art
        heart_color  = (220, 30, 50)
        heart_shadow = (140, 10, 25)
        heart_shine  = (255, 120, 130)

        # Sombra
        pygame.draw.ellipse(canvas, (0,0,0,0).__class__((20,20,20)),
                            (cx - s//2 - 1, cy - s//2 + 1, s+2, s+2))
        # Cuerpo del corazón (dos círculos + triángulo)
        half = s // 2
        pygame.draw.circle(canvas, heart_color, (cx - half//2, cy - half//3), half//2 + 1)
        pygame.draw.circle(canvas, heart_color, (cx + half//2, cy - half//3), half//2 + 1)
        # Relleno triangular inferior
        points = [(cx - s//2, cy - half//4),
                  (cx + s//2, cy - half//4),
                  (cx,        cy + s//2)]
        pygame.draw.polygon(canvas, heart_color, points)
        # Brillo
        pygame.draw.circle(canvas, heart_shine, (cx - half//3, cy - half//2), max(1, half//4))

        # Texto "+30" parpadeante
        if (self.timer // 20) % 2 == 0:
            font = pygame.font.SysFont("monospace", 7, bold=True)
            txt = font.render(f"+{self.HEAL_AMOUNT}", True, (255,255,100))
            canvas.blit(txt, (cx - txt.get_width()//2, cy - s - 8))

# ─────────────────────────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────────────────────────
def draw_hud(canvas, player, score, wave, enemies_left, font):
    # Barra de vida jugador
    bw, bh = 110, 8
    bx, by = 5, 5
    fill   = max(0, int(bw * player.hp / player.max_hp))
    col_hp = (30,200,60) if player.hp > 40 else (220,180,0) if player.hp > 20 else (220,40,40)

    pygame.draw.rect(canvas, (20,20,20),  (bx-1, by-1, bw+2, bh+2))
    pygame.draw.rect(canvas, (100,0,0),   (bx, by, bw, bh))
    pygame.draw.rect(canvas, col_hp,      (bx, by, fill, bh))
    pygame.draw.rect(canvas, (200,200,200),(bx, by, bw, bh), 1)

    name_lbl = font.render(f"PEDRO  {player.hp}/{player.max_hp}", False, (255,255,255))
    canvas.blit(name_lbl, (bx, by + bh + 2))

    # Score
    sc_lbl = font.render(f"SCORE: {score}", False, (255,220,0))
    canvas.blit(sc_lbl, (CANVAS_W - sc_lbl.get_width() - 4, 5))

    # Oleada / enemigos
    if enemies_left > 0:
        en_lbl = font.render(f"OLA {wave}  ENEMIGOS: {enemies_left}", False, (220,220,220))
        canvas.blit(en_lbl, (CANVAS_W//2 - en_lbl.get_width()//2, 5))


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA GENÉRICA (intro / game over / victoria)
# ─────────────────────────────────────────────────────────────────────────────
def show_screen(canvas, win, clock, lines):
    """
    lines = lista de dict: {text, color, size ('big'|'med'|'small'), blink}
    Espera ENTER / SPACE / cualquier tecla.
    """
    font_big  = pygame.font.SysFont("monospace", 24, bold=True)
    font_med  = pygame.font.SysFont("monospace", 14)
    font_sml  = pygame.font.SysFont("monospace", 11)

    waiting = True
    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                waiting = False

        canvas.fill((8, 8, 20))

        total_h = len(lines) * 22
        start_y = (CANVAS_H - total_h) // 2

        for i, ln in enumerate(lines):
            if ln.get("blink") and (pygame.time.get_ticks() // 500) % 2 == 0:
                continue
            f = {"big": font_big, "med": font_med, "small": font_sml}.get(ln["size"], font_med)
            t = f.render(ln["text"], False, ln["color"])
            canvas.blit(t, (CANVAS_W//2 - t.get_width()//2, start_y + i * 22))

        blit_canvas(win, canvas)
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA DE TÍTULO LLAMATIVA
# ─────────────────────────────────────────────────────────────────────────────
def show_title(canvas, win, clock):
    font_title = pygame.font.SysFont("monospace", 22, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 13, bold=True)
    font_hint  = pygame.font.SysFont("monospace", 11)

    t_start = pygame.time.get_ticks()
    waiting = True
    particles = [(random.randint(0,CANVAS_W), random.randint(0,CANVAS_H),
                  random.uniform(-0.3,0.3), random.uniform(-0.5,-0.1),
                  random.choice([(255,220,0),(255,100,30),(200,50,200),(50,150,255)]))
                 for _ in range(40)]

    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                waiting = False

        t = pygame.time.get_ticks() - t_start

        # Fondo degradado simulado con líneas
        for row in range(CANVAS_H):
            c = int(8 + row * 0.18)
            pygame.draw.line(canvas, (c, c//3, c//2), (0,row), (CANVAS_W,row))

        # Partículas
        for p in particles:
            px, py, pvx, pvy, pc = p
            pygame.draw.circle(canvas, pc, (int(px), int(py)), 1)
        particles = [(px+pvx, py+pvy if py > -5 else CANVAS_H+5, pvx, pvy, pc)
                     for px,py,pvx,pvy,pc in particles]

        # Sombra del título
        offset = int(math.sin(t * 0.003) * 2)
        shadow = font_title.render("PEDRO BALANZAT", False, (60, 20, 20))
        canvas.blit(shadow, (CANVAS_W//2 - shadow.get_width()//2 + 2, 52))

        # Título principal con efecto de color pulsante
        pulse = int(abs(math.sin(t * 0.004)) * 60)
        title_col = (255, 200 + pulse//3, pulse)
        title = font_title.render("PEDRO BALANZAT", False, title_col)
        canvas.blit(title, (CANVAS_W//2 - title.get_width()//2, 50))

        # Subtítulo
        sub1 = font_sub.render("La Raqueta de la Justicia", False, (200, 200, 255))
        canvas.blit(sub1, (CANVAS_W//2 - sub1.get_width()//2, 78))

        # VS
        vs_scale = 1.0 + abs(math.sin(t * 0.005)) * 0.15
        vs_surf  = font_sub.render("~~  VS  ~~", False, (255, 80, 80))
        canvas.blit(vs_surf, (CANVAS_W//2 - vs_surf.get_width()//2, 98))

        # Boss name
        boss_col = (255, int(80 + abs(math.sin(t*0.006))*120), 30)
        boss = font_sub.render("FOREST GUMP", False, boss_col)
        canvas.blit(boss, (CANVAS_W//2 - boss.get_width()//2, 115))

        # Línea separadora decorativa
        lw = int(160 + math.sin(t*0.003)*20)
        lx = (CANVAS_W - lw)//2
        pygame.draw.line(canvas, (100,80,200), (lx, 132), (lx+lw, 132), 1)

        # Controles
        ctrl1 = font_hint.render("WASD / Flechas: Mover", False, (180,180,180))
        ctrl2 = font_hint.render("ESPACIO / Z: Atacar con raqueta", False, (180,180,180))
        canvas.blit(ctrl1, (CANVAS_W//2 - ctrl1.get_width()//2, 148))
        canvas.blit(ctrl2, (CANVAS_W//2 - ctrl2.get_width()//2, 158))

        # Parpadeo inicio
        if (t // 500) % 2 == 0:
            start = font_hint.render(">> PRESIONA ENTER PARA COMENZAR <<", False, (255,255,100))
            canvas.blit(start, (CANVAS_W//2 - start.get_width()//2, 175))

        # IFTS badge
        badge = font_hint.render("IFTS N°21 - 2025", False, (120,120,120))
        canvas.blit(badge, (CANVAS_W//2 - badge.get_width()//2, CANVAS_H - 12))

        blit_canvas(win, canvas)
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA DE CUENTA REGRESIVA (continuar / volver al inicio)
# ─────────────────────────────────────────────────────────────────────────────
def show_countdown(canvas, win, clock, lines):
    """
    Muestra el resultado con un contador de 10 segundos.
    Retorna True si el jugador presionó una tecla (reiniciar ya),
    False si el tiempo se agotó (volver al título).
    """
    font_big = pygame.font.SysFont("monospace", 24, bold=True)
    font_med = pygame.font.SysFont("monospace", 14)
    font_sml = pygame.font.SysFont("monospace", 11)

    deadline = pygame.time.get_ticks() + 10000  # 10 segundos

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                return True  # el jugador quiere continuar

        remaining = max(0, (deadline - pygame.time.get_ticks() + 999) // 1000)
        if remaining == 0:
            return False  # tiempo agotado → ir al título

        canvas.fill((8, 8, 20))
        total_h = (len(lines) + 3) * 22
        start_y = (CANVAS_H - total_h) // 2

        for i, ln in enumerate(lines):
            f = {"big": font_big, "med": font_med, "small": font_sml}.get(ln["size"], font_med)
            t = f.render(ln["text"], False, ln["color"])
            canvas.blit(t, (CANVAS_W//2 - t.get_width()//2, start_y + i * 22))

        y_cd = start_y + len(lines) * 22 + 11
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cd = font_med.render(f"Presiona una tecla para jugar de nuevo  ({remaining}s)", False, (255, 220, 0))
            canvas.blit(cd, (CANVAS_W//2 - cd.get_width()//2, y_cd))
        hint = font_sml.render("Sin tecla → volver al inicio", False, (140, 140, 140))
        canvas.blit(hint, (CANVAS_W//2 - hint.get_width()//2, y_cd + 16))

        blit_canvas(win, canvas)
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def blit_canvas(win, canvas):
    """Escala el canvas al mayor múltiplo entero que entre en la ventana (sin distorsión)."""
    scale = min(WIN_W // CANVAS_W, WIN_H // CANVAS_H)
    sw, sh = CANVAS_W * scale, CANVAS_H * scale
    ox, oy = (WIN_W - sw) // 2, (WIN_H - sh) // 2
    win.fill((0, 0, 0))
    win.blit(pygame.transform.scale(canvas, (sw, sh)), (ox, oy))


def main():
    global WIN_W, WIN_H
    pygame.init()
    win   = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIN_W, WIN_H = win.get_size()
    pygame.display.set_caption(TITLE)
    canvas   = pygame.Surface((CANVAS_W, CANVAS_H))
    clock    = pygame.time.Clock()
    font_hud = pygame.font.SysFont("monospace", 12, bold=True)

    while True:
        show_title(canvas, win, clock)

        player      = Player(60)
        total_score = 0

        for level_num in range(1, 6):  # niveles 1 al 5
            # Restaurar HP parcialmente entre niveles
            if level_num > 1:
                player.hp = min(player.max_hp, player.hp + 25)
                player.x  = 60.0
                player.y  = float(LEVEL_CONFIG[level_num]["floor_y"])

            result, score_delta = run_level(
                canvas, win, clock, player, level_num, font_hud)
            total_score += score_delta

            if result == 'quit':
                pygame.quit(); sys.exit()

            if result == 'lose':
                show_countdown(canvas, win, clock, [
                    {"text": "GAME OVER",
                     "color":(220,40,40), "size":"big"},
                    {"text": "Pedro cayó en la batalla...",
                     "color":(180,180,180), "size":"med"},
                    {"text": f"Llegaste al nivel {level_num}",
                     "color":(200,200,200), "size":"med"},
                    {"text": f"Score: {total_score}",
                     "color":(255,255,255), "size":"med"},
                ])
                break  # volver al título

            # Entre niveles: pantalla de éxito
            boss_name = LEVEL_CONFIG[level_num]["boss_name"]
            if level_num < 5:
                next_title = LEVEL_CONFIG[level_num+1]["title"]
                show_countdown(canvas, win, clock, [
                    {"text": f"¡NIVEL {level_num} COMPLETADO!",
                     "color":(255,220,0), "size":"big"},
                    {"text": f"{boss_name} fue derrotado.",
                     "color":(100,220,100), "size":"med"},
                    {"text": f"Score parcial: {total_score}",
                     "color":(255,255,255), "size":"med"},
                    {"text": f"Siguiente: {next_title}",
                     "color":(180,180,255), "size":"med"},
                ])
            else:
                # Victoria final
                show_countdown(canvas, win, clock, [
                    {"text": "¡VICTORIA TOTAL!",
                     "color":(255,220,0), "size":"big"},
                    {"text": "¡Pedro salvó el mundo!",
                     "color":(100,255,100), "size":"big"},
                    {"text": "Los 5 jefes fueron derrotados.",
                     "color":(180,220,255), "size":"med"},
                    {"text": f"Score final: {total_score}",
                     "color":(255,255,255), "size":"med"},
                ])


# ═════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE NIVELES
# ═════════════════════════════════════════════════════════════════════════════
LEVEL_CONFIG = {
    1: {"floor_y":248, "floor_top":230, "floor_bot":254,
        "bg":["assets/ifts21.png","assets/ifts.png"],
        "boss_class":"Boss", "boss_name":"FOREST GUMP",
        "n_enemies":10, "title":"NIVEL 1 - IFTS 21"},
    2: {"floor_y":240, "floor_top":228, "floor_bot":248,
        "bg":["assets/nivel2.png","assets/volver-al-futuro-fondo.png"],
        "boss_class":"Boss2", "boss_name":"BIFF TANNEN",
        "n_enemies":10, "title":"NIVEL 2 - VOLVER AL FUTURO"},
    3: {"floor_y":245, "floor_top":232, "floor_bot":252,
        "bg":["assets/nivel3.png","assets/la-bombonera-fondo.png"],
        "boss_class":"BossGallina", "boss_name":"LA GALLINA",
        "n_enemies":10, "title":"NIVEL 3 - LA BOMBONERA"},
    4: {"floor_y":248, "floor_top":233, "floor_bot":255,
        "bg":["assets/nivel4.png","assets/el-padrino-fondo.png"],
        "boss_class":"BossAlCapone", "boss_name":"AL CAPONE",
        "n_enemies":10, "title":"NIVEL 4 - EL PADRINO"},
    5: {"floor_y":245, "floor_top":230, "floor_bot":253,
        "bg":["assets/nivel5.png","assets/el-eternauta-fondo.png"],
        "boss_class":"BossEternauta", "boss_name":"EL ETERNAUTA",
        "n_enemies":10, "title":"NIVEL 5 - EL ETERNAUTA"},
}

# ═════════════════════════════════════════════════════════════════════════════
#  CLASE BASE PARA BOSSES
# ═════════════════════════════════════════════════════════════════════════════
class BossBase(pygame.sprite.Sprite):
    HEIGHT = 110

    def __init__(self, x, walk_f, atk_f, hp, speed, name, bar_color=(230,80,20)):
        super().__init__()
        self.walk_frames = walk_f
        self.atk_frames  = atk_f
        self.x      = float(x)
        self.y      = float(FLOOR_Y)
        self.image  = self.walk_frames[0]
        self.rect   = self.image.get_rect()
        self._sync_rect()
        self.hp         = hp
        self.max_hp     = hp
        self.alive      = True
        self.speed      = speed
        self.facing     = -1
        self.fi         = 0
        self.anim_t     = 0
        self.atk_cd     = 80
        self.phase      = 1
        self.name       = name
        self.bar_color  = bar_color
        self.phase2_col = (255, 30, 30)

    def _sync_rect(self):
        self.rect.midbottom = (round(self.x), round(self.y))

    def get_hitbox(self):
        r = self.rect
        return pygame.Rect(r.x+3, r.y+r.h//6, r.w-6, r.h*5//6)

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        if self.hp < self.max_hp//2 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.5
        if self.hp <= 0:
            self.alive = False
            self.kill()

    def _advance_anim(self, frames, delay=7):
        self.anim_t += 1
        spd = delay if self.phase == 1 else max(4, delay-2)
        if self.anim_t >= spd:
            self.anim_t = 0
            self.fi = (self.fi + 1) % len(frames)
            f = frames[self.fi]
            if self.facing == -1:
                f = pygame.transform.flip(f, True, False)
            self.image = f
            mb = self.rect.midbottom
            self.rect = self.image.get_rect()
            self.rect.midbottom = mb

    def update(self, player):
        if not self.alive: return
        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)
        self.facing = 1 if dx > 0 else -1
        engage = self.rect.w * 0.7

        if dist > engage:
            if dist > 0:
                self.x += (dx/dist) * self.speed
                self.y += (dy/dist) * self.speed * 0.5
            self._advance_anim(self.walk_frames)
        else:
            cd = 55 if self.phase == 1 else 38
            if self.atk_cd <= 0 and player.alive:
                player.take_damage(12 if self.phase == 1 else 20)
                self.atk_cd = cd
            self._advance_anim(self.atk_frames)

        if self.atk_cd > 0: self.atk_cd -= 1
        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()

    def draw_boss_bar(self, canvas, font):
        bw, bh = 220, 9
        bx = (CANVAS_W - bw)//2
        by = CANVAS_H - 20
        fill = max(0, int(bw * self.hp / self.max_hp))
        pygame.draw.rect(canvas, (30,30,30),    (bx-1, by-1, bw+2, bh+2))
        pygame.draw.rect(canvas, (140,20,20),   (bx, by, bw, bh))
        col = self.bar_color if self.phase == 1 else self.phase2_col
        pygame.draw.rect(canvas, col,           (bx, by, fill, bh))
        pygame.draw.rect(canvas, (220,220,220), (bx, by, bw, bh), 1)
        lbl = font.render(f"BOSS: {self.name}", True, (255,255,255))
        canvas.blit(lbl, (bx, by-9))
        if self.phase == 2:
            ph2 = font.render("¡FASE 2!", True, self.phase2_col)
            canvas.blit(ph2, (bx+bw+4, by))


# ═════════════════════════════════════════════════════════════════════════════
#  BOSS 2: BIFF TANNEN  (nivel 2)
# ═════════════════════════════════════════════════════════════════════════════
class Boss2(BossBase):
    def __init__(self, x):
        walk_f = load_sheet("assets/biff_walk.png",   8, self.HEIGHT)
        atk_f  = load_sheet("assets/biff_attack_new.png", 8, self.HEIGHT)
        super().__init__(x, walk_f, atk_f, hp=1000, speed=0.9,
                         name="BIFF TANNEN", bar_color=(60,100,220))
        self.phase2_col = (200,30,200)


# ═════════════════════════════════════════════════════════════════════════════
#  BOSS 3: LA GALLINA  (nivel 3 - La Bombonera)
# ═════════════════════════════════════════════════════════════════════════════
class BossGallina(BossBase):
    def __init__(self, x):
        walk_f = load_sheet("assets/gallina_walk.png",   4, self.HEIGHT)
        atk_f  = load_sheet("assets/gallina_attack.png", 4, self.HEIGHT)
        super().__init__(x, walk_f, atk_f, hp=900, speed=1.2,
                         name="LA GALLINA", bar_color=(220,180,0))
        self.phase2_col = (255,100,0)

    def update(self, player):
        """La gallina es más rápida y errática."""
        if not self.alive: return
        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)
        self.facing = 1 if dx > 0 else -1

        # Movimiento errático: pequeña oscilación lateral
        jitter = math.sin(pygame.time.get_ticks() * 0.01) * 0.5
        spd = self.speed * (1.3 if self.phase == 2 else 1.0)

        if dist > self.rect.w * 0.6:
            if dist > 0:
                self.x += (dx/dist) * spd + jitter
                self.y += (dy/dist) * spd * 0.5
            self._advance_anim(self.walk_frames, delay=6)
        else:
            cd = 45 if self.phase == 1 else 30
            if self.atk_cd <= 0 and player.alive:
                player.take_damage(10 if self.phase == 1 else 18)
                self.atk_cd = cd
            self._advance_anim(self.atk_frames, delay=5)

        if self.atk_cd > 0: self.atk_cd -= 1
        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()


# ═════════════════════════════════════════════════════════════════════════════
#  BOSS 4: AL CAPONE  (nivel 4 - El Padrino)
# ═════════════════════════════════════════════════════════════════════════════
class BossAlCapone(BossBase):
    def __init__(self, x):
        walk_f = load_sheet("assets/alcapone_walk.png",   8, self.HEIGHT)
        atk_f  = load_sheet("assets/alcapone_attack.png", 4, self.HEIGHT)
        super().__init__(x, walk_f, atk_f, hp=1200, speed=0.7,
                         name="AL CAPONE", bar_color=(180,140,40))
        self.phase2_col = (220,60,20)
        # Al Capone: ataque fuerte pero lento
        self.atk_cd = 100

    def update(self, player):
        if not self.alive: return
        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)
        self.facing = 1 if dx > 0 else -1

        if dist > self.rect.w * 0.8:
            if dist > 0:
                self.x += (dx/dist) * self.speed
                self.y += (dy/dist) * self.speed * 0.5
            self._advance_anim(self.walk_frames, delay=10)
        else:
            cd = 90 if self.phase == 1 else 55
            if self.atk_cd <= 0 and player.alive:
                # Al Capone pega fuerte
                player.take_damage(20 if self.phase == 1 else 30)
                self.atk_cd = cd
            self._advance_anim(self.atk_frames, delay=8)

        if self.atk_cd > 0: self.atk_cd -= 1
        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()


# ═════════════════════════════════════════════════════════════════════════════
#  BOSS 5: EL ETERNAUTA  (nivel 5 - ataca a distancia)
# ═════════════════════════════════════════════════════════════════════════════
class Proyectil:
    """Bala/disparo del Eternauta."""
    def __init__(self, x, y, facing):
        self.x      = float(x)
        self.y      = float(y)
        self.speed  = 4.0
        self.facing = facing
        self.alive  = True
        self.r      = 4

    def update(self, player):
        self.x += self.speed * self.facing
        # Fuera de pantalla
        if self.x < -20 or self.x > CANVAS_W + 20:
            self.alive = False
            return
        # Colisión con jugador
        phb = player.get_hitbox()
        if phb.collidepoint(int(self.x), int(self.y)) and player.alive:
            player.take_damage(18)
            self.alive = False

    def draw(self, canvas):
        # Efecto de destello de disparo
        pygame.draw.circle(canvas, (255,220,80),
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(canvas, (255,255,200),
                           (int(self.x), int(self.y)), self.r//2)


class BossEternauta(BossBase):
    SHOOT_RANGE = 160   # distancia a la que empieza a disparar

    def __init__(self, x):
        walk_f = load_sheet("assets/eternauta_walk.png",   4, self.HEIGHT)
        atk_f  = load_sheet("assets/eternauta_attack.png", 8, self.HEIGHT)
        super().__init__(x, walk_f, atk_f, hp=1400, speed=0.6,
                         name="EL ETERNAUTA", bar_color=(80,200,180))
        self.phase2_col = (120,80,255)
        self.proyectiles = []
        self.shoot_cd    = 80
        self.atk_cd      = 120  # cuerpo a cuerpo raro

    def update(self, player):
        if not self.alive: return
        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)
        self.facing = 1 if dx > 0 else -1

        # Lógica de distancia: si está lejos dispara, si está cerca ataca
        if dist > self.SHOOT_RANGE:
            # Acercarse lentamente
            if dist > 0:
                self.x += (dx/dist) * self.speed
                self.y += (dy/dist) * self.speed * 0.5
            self._advance_anim(self.walk_frames, delay=10)
        else:
            # Mantener distancia: si el jugador se acerca demasiado, retroceder
            if dist < 60:
                if dist > 0:
                    self.x -= (dx/dist) * self.speed * 0.8
            self._advance_anim(self.atk_frames, delay=7)

        # Disparar
        shoot_cd_val = 60 if self.phase == 1 else 35
        if self.shoot_cd <= 0 and dist < self.SHOOT_RANGE * 1.2:
            # Disparar hacia el jugador
            proj_y = self.y - self.rect.h * 0.45  # altura del torso
            self.proyectiles.append(Proyectil(self.x, proj_y, self.facing))
            self.shoot_cd = shoot_cd_val
            # Fase 2: doble disparo
            if self.phase == 2:
                self.proyectiles.append(
                    Proyectil(self.x, proj_y - 8, self.facing))

        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.atk_cd > 0:   self.atk_cd -= 1

        # Actualizar proyectiles
        for p in self.proyectiles:
            p.update(player)
        self.proyectiles = [p for p in self.proyectiles if p.alive]

        self.y = max(FLOOR_TOP, min(FLOOR_BOT, self.y))
        self._sync_rect()

    def draw_projectiles(self, canvas):
        for p in self.proyectiles:
            p.draw(canvas)


# ═════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN run_level — ejecuta un nivel completo
# ═════════════════════════════════════════════════════════════════════════════
BOSS_CLASSES = {
    "Boss":          lambda: Boss,
    "Boss2":         lambda: Boss2,
    "BossGallina":   lambda: BossGallina,
    "BossAlCapone":  lambda: BossAlCapone,
    "BossEternauta": lambda: BossEternauta,
}

def run_level(canvas, win, clock, player, level_num, font_hud):
    """Ejecuta un nivel completo. Retorna ('win'|'lose'|'quit', score_delta)."""
    global FLOOR_Y, FLOOR_TOP, FLOOR_BOT

    cfg = LEVEL_CONFIG[level_num]
    # Aplicar constantes de suelo
    FLOOR_Y   = cfg["floor_y"]
    FLOOR_TOP = cfg["floor_top"]
    FLOOR_BOT = cfg["floor_bot"]

    # Cargar fondo
    background = make_fallback_bg()
    for bg_name in cfg["bg"]:
        try:
            img = pygame.image.load(bg_name).convert()
            background = pygame.transform.scale(img, (CANVAS_W, CANVAS_H))
            print(f"[OK] {cfg['title']} fondo: {bg_name}")
            break
        except: pass

    # Pantalla de transición de nivel
    show_screen(canvas, win, clock, [
        {"text": cfg["title"],              "color":(255,220,0),  "size":"big"},
        {"text": f"BOSS: {cfg['boss_name']}","color":(220,100,100),"size":"med"},
        {"text": "Presiona cualquier tecla","color":(150,150,150),"size":"small","blink":True},
    ])

    # Crear enemigos
    enemies = pygame.sprite.Group()
    Enemy._eid = (level_num-1) * 10
    for i in range(cfg["n_enemies"]):
        ex = CANVAS_W + 40 + i * 60
        ey = random.uniform(FLOOR_TOP + 5, FLOOR_BOT - 5)
        enemies.add(Enemy(ex, ey))

    BossClass   = BOSS_CLASSES[cfg["boss_class"]]()
    boss        = None
    boss_spawned= False
    hit_fx      = []
    hearts      = []       # corazones en el escenario
    kills       = 0        # contador de enemigos eliminados este nivel
    score       = 0
    result      = None

    while True:
        clock.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit', score
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 'quit', score
                if ev.key in (pygame.K_SPACE, pygame.K_z, pygame.K_j):
                    player.start_attack()

        player.update()

        if player.atk_active:
            ar = player.get_attack_rect()
            for en in list(enemies):
                if en.alive and ar.colliderect(en.get_hitbox()):
                    was_alive = en.alive
                    en.take_damage(22); score += 10
                    hit_fx.append(HitFX(en.rect.centerx, en.rect.centery))
                    # Contar kill y spawnear corazón si corresponde
                    if was_alive and not en.alive:
                        kills += 1
                        if kills % HeartPickup.SPAWN_EVERY == 0:
                            hx = max(20, min(CANVAS_W-20, en.rect.centerx))
                            hy = random.uniform(FLOOR_TOP+5, FLOOR_BOT-10)
                            hearts.append(HeartPickup(hx, hy))
                            print(f"[OK] Corazón spawneado (kill #{kills})")
            if boss and boss.alive and ar.colliderect(boss.get_hitbox()):
                boss.take_damage(8); score += 25
                hit_fx.append(HitFX(boss.rect.centerx, boss.rect.centery))

        for en in list(enemies):
            en.update(player)

        if boss:
            boss.update(player)

        # Detectar enemigos recién eliminados y contar kills
        prev_alive = len([e for e in enemies if e.alive])
        alive_enemies = [e for e in enemies if e.alive]
        new_kills = prev_alive - len(alive_enemies)  # siempre 0 aqui, se cuenta abajo

        if not boss_spawned and len(alive_enemies) == 0:
            boss_spawned = True
            boss = BossClass(CANVAS_W + 30)
            print(f"[OK] {cfg['boss_name']} spawneado!")

        # Actualizar corazones
        for heart in hearts:
            heart.update(player)
        hearts = [h for h in hearts if h.alive]

        for fx in hit_fx: fx.update()
        hit_fx = [fx for fx in hit_fx if not fx.done()]

        # ── RENDER ──
        canvas.blit(background, (0,0))

        drawables = [en for en in enemies if en.alive]
        if boss and boss.alive: drawables.append(boss)
        drawables.append(player)
        drawables.sort(key=lambda o: o.y)

        for obj in drawables:
            canvas.blit(obj.image, obj.rect)
            if isinstance(obj, Enemy): obj.draw_hp_bar(canvas)

        # Proyectiles del Eternauta
        if isinstance(boss, BossEternauta) and boss.alive:
            boss.draw_projectiles(canvas)

        for fx in hit_fx: fx.draw(canvas)

        # Dibujar corazones
        for heart in hearts:
            heart.draw(canvas)

        alive_count = len([e for e in enemies if e.alive])
        draw_hud(canvas, player, score, level_num,
                 alive_count if not boss_spawned else 0, font_hud)

        if boss and boss.alive:
            boss.draw_boss_bar(canvas, font_hud)

        blit_canvas(win, canvas)
        pygame.display.flip()

        if not player.alive:
            return 'lose', score
        if boss and not boss.alive:
            return 'win', score


if __name__ == "__main__":
    main()
