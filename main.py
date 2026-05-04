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

BG_COLOR   = (0, 0, 0)   # colorkey sprites (fondo negro)

# ─────────────────────────────────────────────────────────────────────────────
#  UTILIDADES DE CARGA
# ─────────────────────────────────────────────────────────────────────────────
def load_sheet(path, n_frames, out_h, colorkey=BG_COLOR):
    """
    Carga un spritesheet horizontal de n_frames.
    Escala cada frame proporcionalmente a out_h de altura.
    Retorna lista de (Surface, pivot_offset_x) donde pivot_offset_x
    es el desplazamiento para que el centro visual coincida con rect.centerx.
    """
    try:
        sheet = pygame.image.load(path).convert()
        sheet.set_colorkey(colorkey, pygame.RLEACCEL)
        sw, sh  = sheet.get_size()
        fw      = sw // n_frames
        scale   = out_h / sh
        out_w   = int(fw * scale)
        frames  = []
        for i in range(n_frames):
            raw = pygame.Surface((fw, sh))
            raw.fill(colorkey)
            raw.blit(sheet, (0, 0), (i * fw, 0, fw, sh))
            raw.set_colorkey(colorkey, pygame.RLEACCEL)
            scaled = pygame.transform.scale(raw, (out_w, out_h))
            frames.append(scaled)
        return frames
    except Exception as e:
        print(f"[WARN] {path}: {e}")
        s = pygame.Surface((int(out_h * 0.55), out_h))
        s.fill((255, 0, 0))
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
        self.walk_frames = load_sheet("assets/balanzat_movimiento.png",    7, self.HEIGHT)

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
        self.hp     = 100
        self.max_hp = 100
        self.alive  = True
        self.score  = 0

    def _sync_rect(self):
        """Mantiene rect.midbottom sincronizado con (x, y)."""
        self.rect.midbottom = (int(self.x), int(self.y))

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
            self.y += (dy / ln) * self.speed * 0.55  # perspectiva 2.5D
            if dx != 0:
                self.facing = 1 if dx > 0 else -1

        # Límites canvas
        hw = self.rect.w // 2
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

        self.hp      = 40
        self.max_hp  = 40
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
        self.rect.midbottom = (int(self.x), int(self.y))

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
            num = font_s.render("9", True, (40,60,160))
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
        self.rect.midbottom = (int(self.x), int(self.y))

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

        lbl = font.render("BOSS: FOREST GUMP", True, (255,255,255))
        canvas.blit(lbl, (bx, by - 9))
        if self.phase == 2:
            ph2 = font.render("¡FASE 2!", True, (255,50,50))
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

    name_lbl = font.render(f"PEDRO  {player.hp}/{player.max_hp}", True, (255,255,255))
    canvas.blit(name_lbl, (bx, by + bh + 2))

    # Score
    sc_lbl = font.render(f"SCORE: {score}", True, (255,220,0))
    canvas.blit(sc_lbl, (CANVAS_W - sc_lbl.get_width() - 4, 5))

    # Oleada / enemigos
    if enemies_left > 0:
        en_lbl = font.render(f"OLA {wave}  ENEMIGOS: {enemies_left}", True, (220,220,220))
        canvas.blit(en_lbl, (CANVAS_W//2 - en_lbl.get_width()//2, 5))


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA GENÉRICA (intro / game over / victoria)
# ─────────────────────────────────────────────────────────────────────────────
def show_screen(canvas, win, clock, lines):
    """
    lines = lista de dict: {text, color, size ('big'|'med'|'small'), blink}
    Espera ENTER / SPACE / cualquier tecla.
    """
    font_big  = pygame.font.SysFont("monospace", 20, bold=True)
    font_med  = pygame.font.SysFont("monospace", 10, bold=False)
    font_sml  = pygame.font.SysFont("monospace", 7)

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
            t = f.render(ln["text"], True, ln["color"])
            canvas.blit(t, (CANVAS_W//2 - t.get_width()//2, start_y + i * 22))

        scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
        win.blit(scaled, (0,0))
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA DE TÍTULO LLAMATIVA
# ─────────────────────────────────────────────────────────────────────────────
def show_title(canvas, win, clock):
    font_title = pygame.font.SysFont("monospace", 18, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 9,  bold=True)
    font_hint  = pygame.font.SysFont("monospace", 7)

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
        shadow = font_title.render("PEDRO BALANZAT", True, (60, 20, 20))
        canvas.blit(shadow, (CANVAS_W//2 - shadow.get_width()//2 + 2, 52))

        # Título principal con efecto de color pulsante
        pulse = int(abs(math.sin(t * 0.004)) * 60)
        title_col = (255, 200 + pulse//3, pulse)
        title = font_title.render("PEDRO BALANZAT", True, title_col)
        canvas.blit(title, (CANVAS_W//2 - title.get_width()//2, 50))

        # Subtítulo
        sub1 = font_sub.render("La Raqueta de la Justicia", True, (200, 200, 255))
        canvas.blit(sub1, (CANVAS_W//2 - sub1.get_width()//2, 78))

        # VS
        vs_scale = 1.0 + abs(math.sin(t * 0.005)) * 0.15
        vs_surf  = font_sub.render("~~  VS  ~~", True, (255, 80, 80))
        canvas.blit(vs_surf, (CANVAS_W//2 - vs_surf.get_width()//2, 98))

        # Boss name
        boss_col = (255, int(80 + abs(math.sin(t*0.006))*120), 30)
        boss = font_sub.render("FOREST GUMP", True, boss_col)
        canvas.blit(boss, (CANVAS_W//2 - boss.get_width()//2, 115))

        # Línea separadora decorativa
        lw = int(160 + math.sin(t*0.003)*20)
        lx = (CANVAS_W - lw)//2
        pygame.draw.line(canvas, (100,80,200), (lx, 132), (lx+lw, 132), 1)

        # Controles
        ctrl1 = font_hint.render("WASD / Flechas: Mover", True, (180,180,180))
        ctrl2 = font_hint.render("ESPACIO / Z: Atacar con raqueta", True, (180,180,180))
        canvas.blit(ctrl1, (CANVAS_W//2 - ctrl1.get_width()//2, 148))
        canvas.blit(ctrl2, (CANVAS_W//2 - ctrl2.get_width()//2, 158))

        # Parpadeo inicio
        if (t // 500) % 2 == 0:
            start = font_hint.render(">> PRESIONA ENTER PARA COMENZAR <<", True, (255,255,100))
            canvas.blit(start, (CANVAS_W//2 - start.get_width()//2, 175))

        # IFTS badge
        badge = font_hint.render("IFTS N°21 - 2025", True, (120,120,120))
        canvas.blit(badge, (CANVAS_W//2 - badge.get_width()//2, CANVAS_H - 12))

        scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
        win.blit(scaled, (0,0))
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
    font_big = pygame.font.SysFont("monospace", 20, bold=True)
    font_med = pygame.font.SysFont("monospace", 10, bold=False)
    font_sml = pygame.font.SysFont("monospace", 7)

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
            t = f.render(ln["text"], True, ln["color"])
            canvas.blit(t, (CANVAS_W//2 - t.get_width()//2, start_y + i * 22))

        y_cd = start_y + len(lines) * 22 + 11
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cd = font_med.render(f"Presiona una tecla para jugar de nuevo  ({remaining}s)", True, (255, 220, 0))
            canvas.blit(cd, (CANVAS_W//2 - cd.get_width()//2, y_cd))
        hint = font_sml.render("Sin tecla → volver al inicio", True, (140, 140, 140))
        canvas.blit(hint, (CANVAS_W//2 - hint.get_width()//2, y_cd + 16))

        scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
        win.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    global WIN_W, WIN_H
    pygame.init()
    win   = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIN_W, WIN_H = win.get_size()
    pygame.display.set_caption(TITLE)
    canvas = pygame.Surface((CANVAS_W, CANVAS_H))
    clock  = pygame.time.Clock()
    font_hud = pygame.font.SysFont("monospace", 6, bold=True)

    # ── Fondo ──
    background = make_fallback_bg()
    for name in ["assets/ifts21.png", "assets/ifts.png"]:
        try:
            img = pygame.image.load(name).convert()
            background = pygame.transform.scale(img, (CANVAS_W, CANVAS_H))
            print(f"[OK] Fondo: {name}")
            break
        except:
            pass

    go_to_title = True

    # ── LOOP EXTERNO DE REINICIO ──
    while True:
        if go_to_title:
            show_title(canvas, win, clock)

        # ── Inicializar estado de juego ──
        player = Player(60)
        enemies = pygame.sprite.Group()
        Enemy._eid = 0
        for i in range(10):
            ex = CANVAS_W + 40 + i * 60
            ey = random.uniform(FLOOR_TOP + 5, FLOOR_BOT - 5)
            enemies.add(Enemy(ex, ey))

        boss         = None
        boss_spawned = False
        hit_fx       = []
        score        = 0
        wave         = 1
        outcome      = None

        # ── LOOP PRINCIPAL ──
        running = True
        while running:
            clock.tick(FPS)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if ev.key in (pygame.K_SPACE, pygame.K_z, pygame.K_j):
                        player.start_attack()

            player.update()

            if player.atk_active:
                ar = player.get_attack_rect()
                for en in list(enemies):
                    if en.alive and ar.colliderect(en.get_hitbox()):
                        en.take_damage(22)
                        score += 10
                        hit_fx.append(HitFX(en.rect.centerx, en.rect.centery))
                if boss and boss.alive and ar.colliderect(boss.get_hitbox()):
                    boss.take_damage(8)
                    score += 20
                    hit_fx.append(HitFX(boss.rect.centerx, boss.rect.centery))

            for en in list(enemies):
                en.update(player)

            if boss:
                boss.update(player)

            alive_enemies = [e for e in enemies if e.alive]
            if not boss_spawned and len(alive_enemies) == 0:
                boss_spawned = True
                wave = 2
                boss = Boss(CANVAS_W - 50)
                print("[OK] Boss spawneado!")

            for fx in hit_fx: fx.update()
            hit_fx = [fx for fx in hit_fx if not fx.done()]

            # ── RENDER ──
            canvas.blit(background, (0, 0))

            drawables = []
            for en in enemies:
                if en.alive: drawables.append(en)
            if boss and boss.alive: drawables.append(boss)
            drawables.append(player)
            drawables.sort(key=lambda o: o.y)

            for obj in drawables:
                canvas.blit(obj.image, obj.rect)
                if isinstance(obj, Enemy):
                    obj.draw_hp_bar(canvas)

            for fx in hit_fx: fx.draw(canvas)

            alive_count = len([e for e in enemies if e.alive])
            draw_hud(canvas, player, score, wave, alive_count if not boss_spawned else 0, font_hud)

            if boss and boss.alive:
                boss.draw_boss_bar(canvas, font_hud)

            scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
            win.blit(scaled, (0, 0))
            pygame.display.flip()

            # ── CONDICIONES DE FIN ──
            if not player.alive:
                outcome = "lose"
                running = False
            elif boss and not boss.alive:
                outcome = "win"
                running = False

        # ── PANTALLA DE RESULTADO CON CUENTA REGRESIVA ──
        if outcome == "lose":
            result_lines = [
                {"text": "GAME OVER",                   "color": (220, 40, 40),   "size": "big"},
                {"text": "Pedro cayó en la batalla...", "color": (180, 180, 180), "size": "med"},
                {"text": f"Score: {score}",             "color": (255, 255, 255), "size": "med"},
            ]
        else:
            result_lines = [
                {"text": "¡VICTORIA!",                 "color": (255, 220, 0),   "size": "big"},
                {"text": "Forest Gump fue derrotado.", "color": (100, 220, 100), "size": "med"},
                {"text": "IFTS 21 está a salvo!",      "color": (180, 220, 255), "size": "med"},
                {"text": f"Score final: {score}",      "color": (255, 255, 255), "size": "med"},
            ]

        pressed = show_countdown(canvas, win, clock, result_lines)
        go_to_title = not pressed  # si no presionó → mostrar título; si presionó → reiniciar directo


if __name__ == "__main__":
    main()
