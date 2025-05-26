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
DODGE_COOLDOWN = 1000  # milliseconds
MAX_IFRAMES = 1000
ENEMY_SPAWN_INTERVAL = 1000
ENEMY_SPEED = 1
BULLET_SPEED = 3
GRENADE_SPEED = 10
GRAVITY = 0.3



#SCORES
score = 0
try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except:
    high_score = 0

#DIFFICULTY LEVELS
difficulty_levels = ["Easy", "Normal", "Hard"]
difficulty_speeds = {"Easy": 0.75, "Normal": 1.0, "Hard": 1.75}
volume_levels = ["Mute", "Low", "Normal", "High"]

#SPAWN RATE
difficulty_spawn_multipliers = {
    "Easy": 0.5,
    "Normal": 1.0,
    "Hard": 1.25
}

#CURRENT LEVELS
current_difficulty = "Normal"
current_volume = "Normal"


def settings_menu():
    global current_difficulty, current_volume

    options = ["Difficulty", "Volume", "Back"]
    selected_option = 0
    difficulty_index = difficulty_levels.index(current_difficulty)
    volume_index = volume_levels.index(current_volume)

    while True:
        screen.fill(BLACK)
        title_text, title_rect = create_text(font_large, RED, "SETTINGS", WIDTH // 2, 80)
        screen.blit(title_text, title_rect)

        for i, option in enumerate(options):
            color = RED if i == selected_option else WHITE
            y_pos = 200 + i * 60

            if option == "Difficulty":
                text_str = f"Difficulty: {difficulty_levels[difficulty_index]}"
            elif option == "Volume":
                text_str = f"Volume: {volume_levels[volume_index]}"
            else:
                text_str = option

            text, rect = create_text(font_medium, color, text_str, WIDTH // 2, y_pos)
            screen.blit(text, rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  # Back to title screen
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    selected_option = (selected_option - 1) % len(options)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    selected_option = (selected_option + 1) % len(options)
                elif event.key in (pygame.K_w, pygame.K_UP):
                    if selected_option == 0:  # DIFFICULTY OPTIOANFOASNF 
                        difficulty_index = (difficulty_index - 1) % len(difficulty_levels)
                        current_difficulty = difficulty_levels[difficulty_index]
                    elif selected_option == 1:  # VOLUME
                        volume_index = (volume_index - 1) % len(volume_levels)
                        current_volume = volume_levels[volume_index]
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    if selected_option == 0:  # DIFFICULTY PARIN
                        difficulty_index = (difficulty_index + 1) % len(difficulty_levels)
                        current_difficulty = difficulty_levels[difficulty_index]
                    elif selected_option == 1:  # VOLUME
                        volume_index = (volume_index + 1) % len(volume_levels)
                        current_volume = volume_levels[volume_index]
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if options[selected_option] == "Back":
                        return

        pygame.display.flip()
        clock.tick(FPS)


# === COLORS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
SKY_COLOR = (135, 206, 235)


# === INIT ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
#ORIGINAL SPAWN INTERVAL pygame.time.set_timer(pygame.USEREVENT, ENEMY_SPAWN_INTERVAL)
adjusted_spawn_interval = int(ENEMY_SPAWN_INTERVAL / difficulty_spawn_multipliers[current_difficulty])
pygame.time.set_timer(pygame.USEREVENT, adjusted_spawn_interval)


font_large = pygame.font.SysFont(None, 64)
font_medium = pygame.font.SysFont(None, 32)
font_small = pygame.font.SysFont(None, 16)

#LOADING BACGKROUND IMAGE
background_img = pygame.image.load("assets/art/gameproper.png").convert()


def create_vignette_surface(width, height):
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(width):
            dx = x - width / 2
            dy = y - height / 2
            distance = math.sqrt(dx * dx + dy * dy)
            max_distance = math.sqrt((width / 2) ** 2 + (height / 2) ** 2)
            alpha = min(255, max(0, int((distance / max_distance) * 255)))
            vignette.set_at((x, y), (0, 0, 0, alpha // 2))
    return vignette

vignette = create_vignette_surface(WIDTH, HEIGHT)

# === PLAYER CLASS ===
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        #ORIGINAL PLAYER CHAR
        #self.image = pygame.Surface((40, 40))
        #self.image.fill(WHITE)

        #NEW AHSDBHABSDHBASHFB
        original_image = pygame.image.load("assets/player/mainchar.png").convert_alpha()
        # MAXIMUM SIZE OF THE CHARACTER
        max_size = 100
        scale_ratio = min(max_size / original_image.get_width(), max_size / original_image.get_height())
        new_width = int(original_image.get_width() * scale_ratio)
        new_height = int(original_image.get_height() * scale_ratio)
        self.original_image = pygame.transform.smoothscale(original_image, (new_width, new_height))
        self.image = self.original_image


        self.base_y = HEIGHT // 2
        self.offset_y = 0
        self.vel_y = 0
        self.rect = self.image.get_rect(center=(WIDTH // 2, self.base_y))

        # Aiming
        self.aiming = False
        self.aim_angle = -90
        self.dragging = False
        self.drag_start = None
        self.current_mouse = None

        # Health and Dodge
        self.hp = MAX_HP
        self.max_hp = MAX_HP
        self.dodge_step = 10
        self.available_dodge = MAX_DODGE
        self.dodge_gauge = MAX_DODGE
        self.dodge_delay = 200
        self.last_dodged = 0
        self.max_iframes = MAX_IFRAMES
        self.initial_iframe = 0
        self.i_status = False
        self.center_pull_strength = CENTER_FORCE
        self.dodge_speed = 0.6

    def dodge(self, keys):
        current_tick = pygame.time.get_ticks()
        if self.dodge_gauge > 0 and current_tick - self.last_dodged >= self.dodge_delay:
            moved = False
            if keys[pygame.K_a]:
                self.vel_y -= self.dodge_step
                moved = True
            elif keys[pygame.K_d]:
                self.vel_y += self.dodge_step
                moved = True
            if moved:
                max_up = -self.base_y + self.rect.height // 2 + MOVEMENT_PADDING
                max_down = HEIGHT - self.base_y - self.rect.height // 2 - MOVEMENT_PADDING
                self.offset_y = max(min(self.offset_y, max_down), max_up)
                self.dodge_gauge -= 1
                self.last_dodged = current_tick
                self.i_status = True
                self.initial_iframe = current_tick

    def restore_dodge_counter(self):
        if self.dodge_gauge < MAX_DODGE:
            if pygame.time.get_ticks() - self.last_dodged > DODGE_COOLDOWN:
                self.dodge_gauge = MAX_DODGE

    def update(self, keys, time_scale):
        if not self.aiming:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y -= self.dodge_speed
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.vel_y += self.dodge_speed
        self.dodge(keys)
        self.restore_dodge_counter()

        drag_factor = 0.2 if self.aiming else 1.0
        self.offset_y += self.vel_y * drag_factor * time_scale
        self.vel_y *= 0.9
        center_diff = -self.offset_y
        self.offset_y += center_diff * self.center_pull_strength * time_scale

        max_up = -self.base_y + self.rect.height // 2 + MOVEMENT_PADDING
        max_down = HEIGHT - self.base_y - self.rect.height // 2 - MOVEMENT_PADDING
        self.offset_y = max(min(self.offset_y, max_down), max_up)


        #CENTER OF MAIN CHARACTER
        #self.rect.center = (WIDTH // 2, self.base_y + self.offset_y)

        #NEW CHARACTER MOTION
        # Rotate the sprite to face the aim angle
        rotated_image = pygame.transform.rotate(self.original_image, -self.aim_angle - 90)
        self.image = rotated_image
        self.rect = self.image.get_rect(center=(WIDTH // 2, self.base_y + self.offset_y))

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        self.aim_angle = math.degrees(math.atan2(dy, dx))

        if self.dragging:
            self.current_mouse = pygame.mouse.get_pos()

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
            global score, high_score
            if score > high_score:
                high_score = score
                with open("highscore.txt", "w") as file:
                    file.write(str(high_score))
            score = 0

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

    def update(self, time_scale):
        self.rect.x += self.vel_x * time_scale
        self.rect.y += self.vel_y * time_scale
        if (self.rect.right < 0 or self.rect.left > WIDTH or
            self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, player):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.radius = 0
        self.max_radius = 80
        self.lifetime = 30
        self.frame = 0
        self.image = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hit_enemies = set()
        self.has_pushed = set()  # new
        self.player = player

    def update(self, time_scale):
        self.frame += 1 * time_scale
        self.radius = int(self.max_radius * (self.frame / self.lifetime))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (255, 100, 100, 150), (self.max_radius, self.max_radius), self.radius)
        self.rect = self.image.get_rect(center=self.pos)
        if self.frame >= self.lifetime:
            self.kill()

        for enemy in enemies:
            if enemy not in self.hit_enemies:
                if self.pos.distance_to(enemy.rect.center) < self.radius:
                    enemy.kill()
                    self.hit_enemies.add(enemy)
            

            # Push enemies
            if enemy not in self.has_pushed and self.pos.distance_to(enemy.rect.center) < self.radius:
                direction = pygame.math.Vector2(enemy.rect.center) - self.pos
                if direction.length() > 0:
                    direction = direction.normalize()
                enemy.rect.x += int(direction.x * 10)
                enemy.rect.y += int(direction.y * 10)
                self.has_pushed.add(enemy)
        # Push player
        if self.pos.distance_to(self.player.rect.center) < self.radius:
            direction = pygame.math.Vector2(self.player.rect.center) - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
            self.player.vel_y += direction.y * 2  # subtle knock



# === GRENADE CLASS ===
class Grenade(pygame.sprite.Sprite):
    def __init__(self, pos, angle_deg, player, power=GRENADE_SPEED):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=pos)

        rad = math.radians(angle_deg)
        self.vel_x = power * math.cos(rad)
        self.vel_y = power * math.sin(rad)
        self.player = player

    def update(self, time_scale):
        self.vel_y += GRAVITY * time_scale
        self.rect.x += int(self.vel_x * time_scale)
        self.rect.y += int(self.vel_y * time_scale)

        hit_enemies = pygame.sprite.spritecollide(self, enemies, False)
        if hit_enemies:
            for enemy in hit_enemies:
                enemy.kill()
            global score
            score += 1
            # explosion = Explosion(self.rect.center)
            # all_sprites.add(explosion)
            # explosions.add(explosion)
            self.kill()
            return

        # Collision with ground
        if self.rect.top > HEIGHT:
            # explosion = Explosion(self.rect.center)
            #all_sprites.add(explosion)
            # explosions.add(explosion)
            self.kill()

# === ENEMY CLASS ===
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()

        #RED SQUARE 
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()

        #UPDATED SPRITE ASFDJANSJDNASJDNKASNFJADNIFJANDIJGNADIJNGIJADNGFIJAND
        original_image = pygame.image.load("assets/enemy/enemy1.png").convert_alpha()
        max_size = 80  # smaller than player max_size 100
        scale_ratio = min(max_size / original_image.get_width(), max_size / original_image.get_height())
        new_width = int(original_image.get_width() * scale_ratio)
        new_height = int(original_image.get_height() * scale_ratio)
        self.original_image = pygame.transform.smoothscale(original_image, (new_width, new_height))
        self.image = self.original_image
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

    def update(self, time_scale):
        self.rect.y += self.vel_y * time_scale
        if self.rect.bottom < 0:
            self.kill()


        #MAKE THEM LOOK AT YOUUUUUu
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(dy, dx))

        rotated_image = pygame.transform.rotate(self.original_image, -angle - 90)
        old_center = self.rect.center
        self.image = rotated_image
        self.rect = self.image.get_rect(center=old_center)

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
explosions = pygame.sprite.Group()

# === MODULAR FUNCTIONS ===
def create_HUD(screen, player):
    # Draw health bar
    bar_wid = 200
    bar_len = 20
    position_x = 20
    postion_y = 20
    hp_ratio = player.hp / player.max_hp
    pygame.draw.rect(screen, RED, (position_x, postion_y, bar_wid, bar_len))
    pygame.draw.rect(screen, GREEN, (position_x, postion_y, bar_wid * hp_ratio, bar_len))

    # Draw dodge bar
    for i in range(player.available_dodge):
        color = BLUE if i  < player.dodge_gauge else BLACK
        pygame.draw.rect(screen, color, (position_x + i * 25, postion_y + 30, 20, 20))

    # SCORE AND HIGH SCORE
    score_text, score_rect = create_text(font_medium, WHITE, f"Score: {score}", WIDTH - 150, 20)
    screen.blit(score_text, score_rect)

    high_score_text, high_score_rect = create_text(font_medium, WHITE, f"High Score: {high_score}", WIDTH - 150, 50)
    screen.blit(high_score_text, high_score_rect)


def create_text(font_size, color, string, pos_x, pos_y):
    text = font_size.render(string, True, color) #2nd param for AA, can be a universal constant s.t. it is configurable and makes everything uniform
    text_rect = text.get_rect(center=(pos_x,pos_y))
    return text, text_rect

def load_titlebg_screen():
    frames = []
    for i in range(15):
        image = pygame.image.load(f"assets/art/title_screen/{i:03}.png").convert()
        frames.append(pygame.transform.scale(image, screen.get_size()))
    return frames







# === MAIN LOOPS ===
def title_screen():
    title_text, title_rect = create_text(font_large, RED, "GAME", 400, 100)

    sub_texts = ["play", "settings", "quit"]
    selected = 0
    spacing = 100
    pos_y = 125
    start_x = 400 - spacing

    bg_frames = load_titlebg_screen()
    frame_index = 0

    while True:
        screen.blit(bg_frames[int(frame_index)], (0,0))
        frame_index += 0.09
        if frame_index >= 15:
            frame_index = 0
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
                    choice = sub_texts[selected]
                    if choice == "play":
                        return "play"
                    elif choice == "settings":
                        settings_menu()
                    elif choice == "quit":
                        pygame.quit()
                        sys.exit()

        pygame.display.flip()
        clock.tick(FPS)






def main():
    global all_sprites
    player = Player()
    all_sprites.add(player)

    time_scale = 1.0
    background_scroll_y = 0

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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                player.aiming = True
                player.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                player.aiming = False
                if player.dragging:
                    dx = pygame.mouse.get_pos()[0] - player.rect.centerx
                    dy = pygame.mouse.get_pos()[1] - player.rect.centery
                    angle = math.degrees(math.atan2(dy, dx))
                    grenade = Grenade(player.rect.center, angle, player)
                    all_sprites.add(grenade)
                    grenades.add(grenade)
                player.dragging = False
                player.drag_start = None
                player.current_mouse = None
                player.current_mouse = None

        time_scale = difficulty_speeds[current_difficulty] * (0.4 if player.aiming else 1.0)


        player.update(keys, time_scale)
        for bullet in bullets:
            bullet.update(time_scale)
        for grenade in grenades:
            grenade.update(time_scale)
        for enemy in enemies:
            enemy.update(time_scale)

        # Bullet collision
        hit_bullets = pygame.sprite.spritecollide(player, bullets, True)
        for bullet in hit_bullets:
            player.take_dmg(10)

        #MOVING BACKGROUNDDDDDDDD
        background_scroll_y += 2 


        if background_scroll_y >= HEIGHT:
            background_scroll_y = 0


        screen.blit(background_img, (0, background_scroll_y))
        screen.blit(background_img, (0, background_scroll_y - HEIGHT))

#=========================================

        all_sprites.draw(screen)
        create_HUD(screen, player)

        # Aiming visuals
        if player.aiming:
            screen.blit(vignette, (0, 0))
            rad = math.radians(player.aim_angle)
            x, y = player.rect.center
            vx = GRENADE_SPEED * math.cos(rad)
            vy = GRENADE_SPEED * math.sin(rad)
            points = []
            for t in range(0, 60, 2):
                px = x + vx * t * 0.1
                py = y + vy * t * 0.1 + 0.5 * GRAVITY * (t * 0.1)**2
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
