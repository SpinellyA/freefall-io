import pygame
import sys
import math
import random

# === CONFIGURABLE CONSTANTS ===
WIDTH, HEIGHT = 800, 600
FPS = 60
CENTER_FORCE = 0.001
MOVEMENT_PADDING = 25
MAX_HP = 100
MAX_DODGE = 2
DODGE_COOLDOWN = 1000 # milliseconds
ENEMY_SPAWN_INTERVAL = 1000  
MAX_IFRAMES = 1000
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

font_large = pygame.font.SysFont(None, 64)
font_medium = pygame.font.SysFont(None, 32)
font_small = pygame.font.SysFont(None, 16)

# === PLAYER CLASS ===
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # health points
        self.hp = MAX_HP
        self.max_hp = MAX_HP

        # for dodging
        self.dodge_step = 10
        self.available_dodge = MAX_DODGE
        self.dodge_gauge = MAX_DODGE
        self.dodge_speed = 0.6
        self.dodge_delay = 200 # milliseconds (para dili ma spam ang dodge instantly, murag delay before mo press again)
        self.last_dodged = 0

        #inviciblity frames when dodging
        self.max_iframes = MAX_IFRAMES # milliseconds
        self.initial_iframe = 0
        self.i_status = False

        self.dragging = False
        self.drag_start = None
        self.current_mouse = None
        self.image = pygame.Surface((40, 40))
        self.image.fill(WHITE)
        self.base_y = HEIGHT // 2
        self.offset_y = 0
        self.vel_y = 0
        self.center_pull_strength = CENTER_FORCE
        self.rect = self.image.get_rect(center=(WIDTH // 2, self.base_y))
        self.aiming = False
        self.aim_angle = -90  # Degrees

    def dodge(self):
        keys = pygame.key.get_pressed()
        current_tick = pygame.time.get_ticks()

        if self.dodge_gauge > 0 and (current_tick - self.last_dodged >= self.dodge_delay):
            moved = False
            if keys[pygame.K_a]:
                self.vel_y -= self.dodge_step
                moved = True
            elif keys[pygame.K_d]:
                self.vel_y += self.dodge_step
                moved = True
            if moved:
                max_upward = -self.base_y + self.rect.height // 2 + MOVEMENT_PADDING
                max_downwards = HEIGHT - self.base_y - self.rect.height // 2 - MOVEMENT_PADDING
                self.offset_y = max(min(self.offset_y, max_downwards), max_upward)

                self.dodge_gauge -= 1
                self.last_dodged = current_tick
                self.i_status = True
                self.initial_iframe = current_tick

    
    def restore_dodge_counter(self):
        cc = DODGE_COOLDOWN
        if self.dodge_gauge < self.available_dodge:
            if (pygame.time.get_ticks() - self.last_dodged > cc):
                self.dodge_gauge += 1
                self.last_dodged = pygame.time.get_ticks()
    
    def update(self, keys):
        if keys[pygame.K_a]:
            self.vel_y -= self.dodge_speed
        elif keys[pygame.K_d]:
            self.vel_y += self.dodge_speed
        else:
            self.vel_y -= self.offset_y * self.center_pull_strength

        self.offset_y += self.vel_y
        self.vel_y *= 0.9
        self.rect.center = (WIDTH // 2, self.base_y + self.offset_y)

        max_upward = -self.base_y + self.rect.height // 2 + MOVEMENT_PADDING
        max_downwards = HEIGHT - self.base_y - self.rect.height // 2 - MOVEMENT_PADDING
        self.offset_y = max(min(self.offset_y, max_downwards), max_upward)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        self.aim_angle = math.degrees(math.atan2(dy, dx))

        if self.i_status:
            elapsed = pygame.time.get_ticks() - self.initial_iframe
            if elapsed > self.max_iframes:
                self.i_status = False

    def take_dmg(self, amount):
        if self.i_status:
            return
        self.hp -= amount
        if self.hp <= 0:
            print("the guy is dead. we need to something")
            self.hp = 0

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

# === MODULAR FUNCTIONS ===
def create_HUD(screen, player):
    bar_wid = 200
    bar_len = 20
    position_x = 20
    postion_y = 20
    hp_ratio = player.hp / player.max_hp
    pygame.draw.rect(screen, RED, (position_x, postion_y, bar_wid, bar_len))
    pygame.draw.rect(screen, GREEN, (position_x, postion_y, bar_wid * hp_ratio, bar_len))

    for i in range(player.available_dodge):
        color = BLUE if i  < player.dodge_gauge else BLACK
        pygame.draw.rect(screen, color, (position_x + i * 25, postion_y + 30, 20, 20))

def create_text(font_size, color, string, pos_x, pos_y):
    text = font_size.render(string, True, color) #2nd param for AA, can be a universal constant s.t. it is configurable and makes everything uniform
    text_rect = text.get_rect(center=(pos_x,pos_y))
    return text, text_rect

# === MAIN LOOPS ===
def title_screen():
    title_text, title_rect = create_text(font_large, RED, "GAME", 400, 100)

    sub_texts = ["play", "settings", "quit"]
    selected = 0
    spacing = 100
    pos_y = 125
    start_x = 400 - spacing

    while True:
        screen.fill(BLACK)
        screen.blit(title_text, title_rect)

        for i in range(3):
            color = RED if i == selected else WHITE
            pos_x = start_x + i * spacing
            text, rect = create_text(font_medium, color, sub_texts[i], pos_x, pos_y)
            screen.blit(text, rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_a:
                    selected = (selected - 1) % 3
                elif event.key == pygame.K_d:
                    selected = (selected + 1) % 3
                elif event.key == pygame.K_SPACE:
                    return sub_texts[selected]

        pygame.display.flip()
        clock.tick(int(FPS))


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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    player.aiming = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    player.aiming = False
                    mouse_pos = pygame.mouse.get_pos()
                    grenade = Grenade(player.rect.center, math.degrees(math.atan2(mouse_pos[1] - player.rect.centery, mouse_pos[0] - player.rect.centerx)))
                    all_sprites.add(grenade)
                    grenades.add(grenade)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.dodge()

        player.update(keys)

        bullets.update()
        hit_bullets = pygame.sprite.spritecollide(player, bullets, True)
        for bullet in hit_bullets:
            player.take_dmg(10)

        player.restore_dodge_counter()
        grenades.update()
        enemies.update()

        time_scale = 0.6 if player.aiming else 1.0

        screen.fill(BLACK)
        all_sprites.draw(screen)
        create_HUD(screen, player)

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
    choice = title_screen()
    if choice == "play":
        main()
    elif choice == "settings":
        pass # TODO: adjusting the difficuly lang ig;
    elif choice == "quit":
        pygame.quit()
        sys.exit()