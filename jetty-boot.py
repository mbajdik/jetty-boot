"""
Inspiration: https://github.com/TimoWilken/flappy-bird-pygame
"""
import os
import random

import pygame
from pygame.locals import *

# Window/Screen
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 640

# Mechanics and physics
TICK_RATE = 60  # Clock follows this, frame rate is fixed
V_HORIZONTAL = 2
V_HORIZONTAL_RESPAWN_MULTIPLIER = 4
A_VERTICAL = 0.4  # pixels/tick^2
V_VERTICAL_JUMP = 3.5
V_VERTICAL_MAX = 10
V_VERTICAL_FLYAWAY_SLOW = V_HORIZONTAL-0.5
V_VERTICAL_FLYAWAY_NORMAL = V_HORIZONTAL+0.5
V_VERTICAL_FLYAWAY_FAST = V_HORIZONTAL+1.5
V_VERTICAL_RESPAWN = 3

# Colors
FG_DEFAULT = (42, 176, 65)
FG_LIGHT = (82, 204, 102)
FG_HIGHLIGHT = (201, 137, 26)
BG_DEFAULT = (16, 32, 48)

# Others
MAX_NAME_LENGTH = 16


class GameUtilities:
    FONT_SMALL_NORMAL: pygame.font.Font | None = None
    FONT_LARGE_BOLD: pygame.font.Font | None = None
    FONT_LARGE_BOLD_ITALIC: pygame.font.Font | None = None

    @staticmethod
    def effect_crt(screen: pygame.Surface):
        GameUtilities.effect_crt_blur(screen)
        GameUtilities.effect_crt_backlight_bleed(screen)
        GameUtilities.effect_crt_scanlines(screen)
        GameUtilities.effect_crt_flicker(screen)
        GameUtilities.effect_crt_static(screen)

    @staticmethod
    def effect_crt_blur(screen: pygame.Surface):
        glow_surf = pygame.transform.smoothscale(screen, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        glow_surf = pygame.transform.smoothscale(glow_surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
        glow_surf.set_alpha(127)
        screen.blit(glow_surf, (0, 0))

    @staticmethod
    def effect_crt_backlight_bleed(screen: pygame.Surface):
        screen.fill((223, 223, 223, 1), special_flags=pygame.BLEND_MULT)

    @staticmethod
    def effect_crt_scanlines(screen: pygame.Surface):
        scanline_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(scanline_surface, (0, 0, 0, 60), (0, y), (SCREEN_WIDTH, y))

        screen.blit(scanline_surface, (0, 0))

    @staticmethod
    def effect_crt_flicker(screen: pygame.Surface):
        if random.randint(0, 20) == 0:
            flicker_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flicker_surface.fill((255, 255, 255, 5))
            screen.blit(flicker_surface, (0, 0))

    @staticmethod
    def effect_crt_static(screen: pygame.Surface):
        static_chance = 0.005
        static_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for y in range(0, SCREEN_HEIGHT, 8):
            if random.random() < static_chance:
                pygame.draw.line(static_surface, (*BG_DEFAULT, random.randint(30, 80)), (0, y), (SCREEN_WIDTH, y))

        screen.blit(static_surface, (0, 0), special_flags=pygame.BLEND_ADD)

    @staticmethod
    def draw_text(
            surface: pygame.Surface,
            font: pygame.font.Font,
            text: str,
            y: float,
            x: float = None,
            color: tuple[int, int, int] = (42, 176, 65)
    ):
        text_surface = font.render(text, True, color)
        x = (surface.get_width() / 2 - text_surface.get_width() / 2) if x is None else x
        surface.blit(text_surface, (x, y))

    @staticmethod
    def colored_rectangle(width, height, color) -> pygame.Surface:
        rect_surf = pygame.Surface((width, height))
        rect_surf.fill(color)
        return rect_surf

    @staticmethod
    def load_image(img_file_name):
        file_name = os.path.join(os.path.dirname(__file__), 'assets', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img


class GamePhase:
    NORMAL = 0
    INIT = 1
    FLYAWAY = 2
    RESPAWN = 3
    GAME_OVER = 4


class Boot(pygame.sprite.Sprite):
    WIDTH = 40
    HEIGHT = 40

    def __init__(self, image_base, image_climb):
        super(Boot, self).__init__()

        # Physics
        self.default_x = 48
        self.default_y = 320
        self.x = self.default_x
        self.y = self.default_y
        self.v_vertical = 0
        # self.climb_cooldown = 5

        # Textures
        self._image_base = pygame.transform.scale(image_base, (Boot.WIDTH, Boot.HEIGHT))
        self._image_climb = pygame.transform.scale(image_climb, (Boot.WIDTH, Boot.HEIGHT))

        # Collision mask
        self.mask = pygame.mask.from_surface(self._image_base)

    def update(self, ticks: int = 1, phase: int = 0):
        if phase in [GamePhase.INIT]:
            self.x = min(self.x + V_HORIZONTAL*ticks, 160-32)

        if phase in [GamePhase.NORMAL]:
            #self.climb_cooldown = max(self.climb_cooldown - 1, 0)
            self.y += self.v_vertical * ticks
            self.v_vertical = min(self.v_vertical + ticks * A_VERTICAL, 3)

        if phase in [GamePhase.RESPAWN]:
            self.x = max(self.x - V_HORIZONTAL*ticks, self.default_x)
            self.y = max(self.y - V_VERTICAL_RESPAWN*ticks, self.default_y)

        if phase in [GamePhase.FLYAWAY]:
            effective_y = self.y - 160
            self.x += V_HORIZONTAL * ticks

            v_vertical = V_VERTICAL_FLYAWAY_NORMAL if effective_y == self.x else (
                V_VERTICAL_FLYAWAY_FAST if effective_y < self.x else V_VERTICAL_FLYAWAY_SLOW
            )
            self.y = max(self.y - v_vertical*ticks, 160)

    def climb_event(self, phase: int = 0):
        self.v_vertical = -V_VERTICAL_JUMP

    def get_image(self, phase: int = 0):
        if self.v_vertical >= 0 and phase not in [GamePhase.FLYAWAY]:
            return self._image_base
        else:
            return self._image_climb

    @property
    def image(self):
        return self.get_image()

    @property
    def rect(self):
        return Rect(self.x, self.y, Boot.WIDTH, Boot.HEIGHT)


class Pillars(pygame.sprite.Sprite):
    WIDTH = 24
    SPACING = 120
    OPENING_SIZE_RANGE = [80, 120]
    CAP_HEIGHT = 16

    BASE_COLOR = FG_DEFAULT
    CAP_COLOR = FG_LIGHT

    def __init__(self, pillar_index: int):
        super(Pillars, self).__init__()

        # Physics
        self.default_x = 320 * (7 / 8) + pillar_index * (Pillars.WIDTH + Pillars.SPACING)
        self.x = self.default_x
        self.y = 160

        # Textures
        self.image = pygame.Surface((Pillars.WIDTH, 320), SRCALPHA)
        self.image.convert()
        self.image.fill((0, 0, 0, 0))
        opening_size = random.randint(Pillars.OPENING_SIZE_RANGE[0], Pillars.OPENING_SIZE_RANGE[1])
        opening_center = 160 + random.randint(-int(opening_size * 3 / 4), int(opening_size * 3 / 4))

        bottom_top = opening_center + opening_size / 2
        bottom_full_height = 320 - bottom_top
        bottom_top_cap = GameUtilities.colored_rectangle(Pillars.WIDTH, Pillars.CAP_HEIGHT, Pillars.CAP_COLOR)
        bottom_base = GameUtilities.colored_rectangle(Pillars.WIDTH, bottom_full_height - Pillars.CAP_HEIGHT, Pillars.BASE_COLOR)
        self.image.blit(bottom_top_cap, (0, bottom_top))
        self.image.blit(bottom_base, (0, bottom_top + Pillars.CAP_HEIGHT))

        top_bottom = opening_center - opening_size / 2
        top_full_height = top_bottom
        top_base = GameUtilities.colored_rectangle(Pillars.WIDTH, top_full_height - Pillars.CAP_HEIGHT, Pillars.BASE_COLOR)
        top_bottom_cap = GameUtilities.colored_rectangle(Pillars.WIDTH, Pillars.CAP_HEIGHT, Pillars.CAP_COLOR)
        self.image.blit(top_base, (0, 0))
        self.image.blit(top_bottom_cap, (0, top_bottom - Pillars.CAP_HEIGHT))

        # Collision mask
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def rect(self):
        return Rect(self.x, 160, Pillars.WIDTH, 320)

    def update(self, phase: int, ticks: int = 1):
        if phase in [GamePhase.NORMAL, GamePhase.FLYAWAY]:
            self.x -= V_HORIZONTAL * ticks
        if phase in [GamePhase.RESPAWN]:
            self.x = min(self.default_x, self.x + V_HORIZONTAL*V_HORIZONTAL_RESPAWN_MULTIPLIER*ticks)

    def collides_with(self, boot: Boot):
        return pygame.sprite.collide_mask(self, boot)


class JettyBootGame:
    class Mode:
        INIT = 0
        MAIN_MENU = 1
        GAME = 2

    def __init__(self):
        pygame.init()

        # Initializing the fonts here
        GameUtilities.FONT_SMALL_NORMAL = pygame.font.SysFont("JetBrains Mono", 16, bold=False)
        GameUtilities.FONT_LARGE_BOLD = pygame.font.SysFont("JetBrains Mono", 48, bold=True)
        GameUtilities.FONT_LARGE_BOLD_ITALIC = pygame.font.SysFont("JetBrains Mono", 48, bold=True, italic=True)

        self.running = True

        self.screen = pygame.display.set_mode((320, 640))
        pygame.display.set_caption('Jetty Boot')

        self.clock = pygame.time.Clock()

        self.textures = {
            "base": GameUtilities.load_image("boot_base.png"),
            "climb": GameUtilities.load_image("boot_climb.png"),
            "life": pygame.transform.scale(GameUtilities.load_image("boot_life.png"), (16, 16))
        }

        self.mode = JettyBootGame.Mode.INIT

        self.init_name_text = ""
        self.init_ticks = 0

        self.menu_ticks_in_menu = 0

        self.game_boot: Boot | None = None
        self.game_pillars: list[Pillars] | None = None
        self.game_level = 1
        self.game_paused = False
        self.game_ticks_in_level = 0
        self.game_ticks_in_phase = 0
        self.game_phase = GamePhase.INIT
        self.game_lives = 3
        self.game_total_offset = 0
        self.game_last_score_value = 0
        self.game_score = 0
        self.game_high_score = 0
        self.game_player_name = "player1"

        if os.path.exists("jb.txt"):
            with open("jb.txt", "r", encoding="UTF-8") as r:
                jb_str = r.read()
                try:
                    self.game_high_score = int(jb_str.split("\n")[1])
                except ValueError:
                    print("Couldn't load high score")
                self.init_name_text = jb_str.split("\n")[0]

    def mode_change(self, mode: int):
        self.mode = mode
        if mode in [JettyBootGame.Mode.GAME]:
            self.game_level = 1
            self.game_ticks_in_level = 0
            self.game_ticks_in_phase = 0
            self.game_phase = GamePhase.INIT
            self.game_lives = 3
            self.game_total_offset = 0
            self.game_last_score_value = 0
            self.game_score = 0
            self.game_generate_game_objects()

    def game_level_pillar_count(self):
        return 1 + self.game_level

    def game_generate_game_objects(self):
        pillars_temp = []
        for pillar_index in range(self.game_level_pillar_count()):
            pillar = Pillars(pillar_index)
            pillars_temp.append(pillar)

        self.game_boot = Boot(self.textures["base"], self.textures["climb"])
        self.game_pillars = pillars_temp

    def game_change_phase(self, phase: int):
        self.game_phase = phase
        self.game_ticks_in_phase = 0

    def game_handle_life(self):
        self.game_lives -= 1
        if self.game_lives == 0:
            self.game_change_phase(GamePhase.GAME_OVER)
        else:
            self.game_change_phase(GamePhase.RESPAWN)
            self.game_boot.v_vertical = 0

    def game_handle_new_level(self):
        self.game_level += 1
        self.game_ticks_in_level = 0
        self.game_total_offset = 0
        self.game_generate_game_objects()
        self.game_change_phase(GamePhase.INIT)

    def game_handle_high_score(self):
        if self.game_score > self.game_high_score:
            self.game_high_score = self.game_score
            self.game_save_data()

    def game_save_data(self):
        with open("jb.txt", "w", encoding="UTF-8") as w:
            w.write(f"{self.game_player_name}\n{str(self.game_high_score)}")

    def mainloop(self):
        while self.running:
            self.clock.tick(TICK_RATE)

            events = []
            for e in pygame.event.get():
                events.append(e)

            # Universal background
            self.screen.blit(GameUtilities.colored_rectangle(SCREEN_WIDTH, SCREEN_HEIGHT, BG_DEFAULT), (0, 0))

            match self.mode:
                case JettyBootGame.Mode.INIT:
                    self.tick_init(events)
                case JettyBootGame.Mode.MAIN_MENU:
                    self.tick_main_menu(events)
                case JettyBootGame.Mode.GAME:
                    self.tick_game(events)

            GameUtilities.effect_crt(self.screen)

            pygame.display.flip()

        pygame.quit()

    def tick_init(self, events: list[pygame.event.Event]):
        for e in events:
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
                return
            elif e.type == KEYUP and e.key in [K_RETURN, K_KP_ENTER]:
                self.game_player_name = self.init_name_text
                self.game_save_data()
                self.mode_change(JettyBootGame.Mode.MAIN_MENU)
            elif e.type == KEYUP and e.key in [K_BACKSPACE]:
                self.init_name_text = self.init_name_text[:-1]
            elif e.type == KEYUP and len(self.init_name_text) < MAX_NAME_LENGTH:
                self.init_name_text += e.unicode

        name_cursored_text = self.init_name_text + (("_" if self.init_ticks // 30 % 2 == 0 else " ") if len(self.init_name_text) < MAX_NAME_LENGTH else "")
        name_cursored_text_bracketed = f"[{name_cursored_text}{(MAX_NAME_LENGTH-len(name_cursored_text))*"_"}]"

        GameUtilities.draw_text(self.screen, GameUtilities.FONT_LARGE_BOLD_ITALIC, "JETTY BOOT", 48, color=FG_LIGHT)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, "Choose a name:", 140)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, name_cursored_text_bracketed, 160, color=FG_LIGHT)

        self.init_ticks += 1

    def tick_main_menu(self, events: list[pygame.event.Event]):
        for e in events:
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
                return
            elif e.type == KEYUP and e.key in [K_UP, K_RETURN, K_SPACE, K_e]:
                self.mode_change(JettyBootGame.Mode.GAME)

        GameUtilities.draw_text(self.screen, GameUtilities.FONT_LARGE_BOLD_ITALIC, "JETTY BOOT", 48, color=FG_LIGHT)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, "High Scores", 140)

        dummy_highscores = [
            ("Bosco", 999999),
            ("Steve", 99999),
            ("Lloyd", 9999),
            (self.game_player_name, self.game_high_score, True)
        ]
        for i, high_scorer in enumerate(dummy_highscores):
            color = FG_DEFAULT if len(high_scorer) == 2 else FG_LIGHT
            GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{i + 1}.", 170 + i * 20, 32, color=color)
            GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{high_scorer[0]}", 170 + i * 20, 56, color=color)
            GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{high_scorer[1]}", 170 + i * 20, 220, color=color)

        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, "INSERT 5 CREDITS", 460)

    def tick_game(self, events: list[pygame.event.Event]):
        for e in events:
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
                return
            elif e.type == KEYUP and e.key in [K_PAUSE, K_p]:
                self.game_paused = not self.game_paused
            elif e.type == KEYUP and e.key in [K_UP, K_RETURN, K_SPACE, K_e]:
                if self.game_phase in [GamePhase.NORMAL]:
                    self.game_boot.climb_event(self.game_phase)
                elif self.game_phase in [GamePhase.GAME_OVER]:
                    self.mode_change(JettyBootGame.Mode.MAIN_MENU)

        pressed = pygame.key.get_pressed()
        if pressed[K_SPACE] or pressed[K_UP] or pressed[K_RETURN] or pressed[K_e]:
            self.game_boot.climb_event(self.game_phase)

        # Game elements - only update and check if not paused
        if not self.game_paused:
            if self.game_phase in [GamePhase.NORMAL, GamePhase.FLYAWAY]:
                self.game_total_offset += V_HORIZONTAL
            elif self.game_phase in [GamePhase.RESPAWN]:
                self.game_total_offset = max(self.game_total_offset - V_HORIZONTAL*V_HORIZONTAL_RESPAWN_MULTIPLIER, 0)

            self.game_boot.update(phase=self.game_phase)
            for pillar in self.game_pillars:
                pillar.update(phase=self.game_phase)

            pillar_collision = any(pillar.collides_with(self.game_boot) for pillar in self.game_pillars)
            if pillar_collision or 160 >= self.game_boot.y or self.game_boot.y >= 480-Boot.HEIGHT/2:
                if self.game_phase in [GamePhase.NORMAL]:
                    self.game_handle_life()
                    return
                if self.game_phase in [GamePhase.FLYAWAY]:
                    self.game_handle_new_level()
                    return

        self.screen.blit(self.game_boot.get_image(phase=self.game_phase), self.game_boot.rect)
        for pillar in self.game_pillars:
            self.screen.blit(pillar.image, pillar.rect)

        first_pillars_offset = 320 * (7 / 8) - (160-Boot.WIDTH)
        pillars_offset = Pillars.WIDTH + Pillars.SPACING
        pillars_offsets = self.game_total_offset - first_pillars_offset
        float_score = pillars_offsets / pillars_offset + 1
        level_score = min(int(float_score), self.game_level_pillar_count())
        if self.game_last_score_value < level_score:
            self.game_score += 1
            self.game_handle_high_score()
        self.game_last_score_value = level_score
        if float_score >= self.game_level_pillar_count() + 0.1:
            self.game_change_phase(GamePhase.FLYAWAY)

        if self.game_phase in [GamePhase.INIT] and self.game_ticks_in_phase >= 60:
            self.game_change_phase(GamePhase.NORMAL)

        if self.game_phase in [GamePhase.RESPAWN] and self.game_total_offset == 0 and self.game_boot.y == self.game_boot.default_y:
            self.game_change_phase(GamePhase.INIT)

        # HUD elements
        pygame.draw.line(self.screen, FG_DEFAULT, (0, 160), (320, 160))
        pygame.draw.line(self.screen, FG_DEFAULT, (0, 480), (320, 480))

        for l in range(self.game_lives):
            self.screen.blit(
                self.textures["life"],
                Rect(4 + (16 + 4)*l, 140, 16, 16)
            )

        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"HIGH SCORE", 76)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{self.game_high_score}", 96)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{self.game_player_name}", 116)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"{self.game_score}", 136)
        GameUtilities.draw_text(self.screen, GameUtilities.FONT_SMALL_NORMAL, f"LVL  {self.game_level}", 136, 240)

        if self.game_phase in [GamePhase.INIT] and self.game_ticks_in_level <= 60:
            GameUtilities.draw_text(self.screen, GameUtilities.FONT_LARGE_BOLD, f"LEVEL {self.game_level}", 320 - 48 / 2, color=FG_LIGHT)

        if self.game_phase in [GamePhase.GAME_OVER]:
            GameUtilities.draw_text(self.screen, GameUtilities.FONT_LARGE_BOLD, f"GAME OVER", 320 - 48 / 2, color=FG_HIGHLIGHT)

        if not self.game_paused:
            self.game_ticks_in_phase += 1
            self.game_ticks_in_level += 1


def main():
    game = JettyBootGame()
    game.mainloop()


if __name__ == '__main__':
    main()
