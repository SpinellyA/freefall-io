import pygame
import sys
import math
import random

# === CONFIGURABLE CONSTANTS ===
WIDTH, HEIGHT = 800, 600
FPS = 60
CENTER_FORCE = 0.05
ENEMY_SPAWN_INTERVAL = 1000  # milliseconds
ENEMY_SPEED = 1
BULLET_SPEED = 3
GRENADE_SPEED = 10
GRAVITY = 0.3

# === COLORS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# === INIT ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.time.set_timer(pygame.USEREVENT, ENEMY_SPAWN_INTERVAL)

# === PLAYER CLASS ===
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.drag_start = None
        self.current_mouse = None
        self.image = pygame.Surface((40, 40))
        self.image.fill(WHITE)
        self.base_y = HEIGHT // 2
        self.offset_y = 0
        self.vel_y = 0
        self.dodge_speed = 0.6
        self.center_pull_strength = CENTER_FORCE
        self.rect = self.image.get_rect(center=(WIDTH // 2, self.base_y))
        self.aiming = False
        self.aim_angle = -90  # Degrees

    def update(self, keys):
        if keys[pygame.K_UP]:
            self.vel_y -= self.dodge_speed
        elif keys[pygame.K_DOWN]:
            self.vel_y += self.dodge_speed
        else:
            self.vel_y -= self.offset_y * self.center_pull_strength

        self.offset_y += self.vel_y
        self.vel_y *= 0.9
        self.rect.center = (WIDTH // 2, self.base_y + self.offset_y)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        self.aim_angle = math.degrees(math.atan2(dy, dx))


# === BULLET CLASS ===
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=pos)

        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        self.vel_x = (dx / dist) * BULLET_SPEED
        self.vel_y = (dy / dist) * BULLET_SPEED

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if (self.rect.right < 0 or self.rect.left > WIDTH or
            self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()

# === GRENADE CLASS ===
class Grenade(pygame.sprite.Sprite):
    def __init__(self, pos, angle_deg):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=pos)

        rad = math.radians(angle_deg)
        self.vel_x = GRENADE_SPEED * math.cos(rad)
        self.vel_y = GRENADE_SPEED * math.sin(rad)

    def update(self):
        self.vel_y += GRAVITY
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

        if self.rect.top > HEIGHT:
            self.kill()  # TODO: Replace with explosion effect

# === ENEMY CLASS ===
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.player = player
        margin = 50
        safe_zone = 100
        side = random.choice(["left", "right"])
        if side == "left":
            self.rect.x = random.randint(margin, WIDTH // 2 - safe_zone)
        else:
            self.rect.x = random.randint(WIDTH // 2 + safe_zone, WIDTH - margin - self.rect.width)

        self.rect.y = HEIGHT + random.randint(20, 100)
        self.vel_y = -1.0
        self.shoot_cooldown = 2000
        self.last_shot_time = pygame.time.get_ticks()

    def update(self):
        self.rect.y += self.vel_y
        if self.rect.bottom < 0:
            self.kill()

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            self.last_shot_time = current_time
            bullet = Bullet(self.rect.center, self.player.rect.center)
            all_sprites.add(bullet)
            bullets.add(bullet)

# === GLOBAL GROUPS ===
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
grenades = pygame.sprite.Group()
enemies = pygame.sprite.Group()

# === MAIN LOOP ===
def main():
    global all_sprites
    player = Player()
    all_sprites.add(player)

    time_scale = 1.0

    while True:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.USEREVENT:
                enemy = Enemy(player)
                all_sprites.add(enemy)
                enemies.add(enemy)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.aiming = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    player.aiming = False
                    mouse_pos = pygame.mouse.get_pos()
                    grenade = Grenade(player.rect.center, math.degrees(math.atan2(mouse_pos[1] - player.rect.centery,
                                                                                mouse_pos[0] - player.rect.centerx)))
                    all_sprites.add(grenade)
                    grenades.add(grenade)

        player.update(keys)
        bullets.update()
        grenades.update()
        enemies.update()

        time_scale = 0.4 if player.aiming else 1.0

        screen.fill(BLACK)
        all_sprites.draw(screen)

        if player.aiming:
            # Trajectory preview
            rad = math.radians(player.aim_angle)
            x, y = player.rect.center
            vx = GRENADE_SPEED * math.cos(rad)
            vy = GRENADE_SPEED * math.sin(rad)
            points = []
            for i in range(30):
                px = x + vx * i
                py = y + vy * i + 0.5 * GRAVITY * i * i
                points.append((int(px), int(py)))
            if len(points) > 1:
                pygame.draw.lines(screen, GREEN, False, points, 2)

        pygame.display.flip()
        clock.tick(int(FPS * time_scale))

if __name__ == "__main__":
    main()
