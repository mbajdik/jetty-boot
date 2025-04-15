"""
Inspiration: https://github.com/TimoWilken/flappy-bird-pygame
"""
import os
import random

import pygame
from pygame.locals import *

LEVEL_LENGTH = 15

TICK_RATE = 60
G = 0.35  # pixels/tick^2
V_HORIZONTAL = 1.5

EVERYTHING_COLOR = (42, 176, 65)


def colored_rectangle(width, height, color):
    rect_surf = pygame.Surface((width, height))
    rect_surf.fill(color)
    return rect_surf


def draw_text_centered(display_surface, y, font, text):
    text_surface = font.render(text, True, (42, 176, 65))
    x = 160 - text_surface.get_width() / 2
    display_surface.blit(text_surface, (x, y))


def draw_text(display_surface, x, y, font, text):
    text_surface = font.render(text, True, (42, 176, 65))
    display_surface.blit(text_surface, (x, y))


def load_image(img_file_name):
    file_name = os.path.join(os.path.dirname(__file__), 'assets', img_file_name)
    img = pygame.image.load(file_name)
    img.convert()
    return img


class Boot(pygame.sprite.Sprite):
    WIDTH = 32
    HEIGHT = 32

    def __init__(self, image_base, image_climb, x=48, y=320):
        super(Boot, self).__init__()
        self.x, self.y = x, y
        self.v_vertical = 0
        self.climb_cooldown = 5
        self._image_base = pygame.transform.scale(image_base, (Boot.WIDTH, Boot.HEIGHT))
        self._image_climb = pygame.transform.scale(image_climb, (Boot.WIDTH, Boot.HEIGHT))
        self.mask = pygame.mask.from_surface(self._image_base)

    def update(self, ticks=1, ending=False):
        self.climb_cooldown = max(self.climb_cooldown - 1, 0)
        self.y += self.v_vertical*ticks
        self.v_vertical = min(self.v_vertical + ticks*G, 3) if not ending else self.v_vertical - 0.1
        if ending:
            self.x += V_HORIZONTAL*ticks

    def climb_event(self, ending=False):
        if self.climb_cooldown == 0 and not ending:
            self.v_vertical = -5
            self.climb_cooldown = 15

    @property
    def image(self):
        if self.v_vertical > 0:
            return self._image_base
        else:
            return self._image_climb

    @property
    def rect(self):
        return Rect(self.x, self.y, Boot.WIDTH, Boot.HEIGHT)


class Pillars(pygame.sprite.Sprite):
    WIDTH = 24
    SPACING = 120
    OPENING_SIZE_RANGE = [80, 120]
    CAP_HEIGHT = 16

    BASE_COLOR = (42, 176, 65)
    CAP_COLOR = (73, 184, 92)

    def __init__(self, pillar_index):
        super(Pillars, self).__init__()
        self.x = 320 * (3/4) + pillar_index * (Pillars.WIDTH + Pillars.SPACING)
        self.y = 160

        self.image = pygame.Surface((Pillars.WIDTH, 320), SRCALPHA)
        self.image.convert()
        self.image.fill((0, 0, 0, 0))
        opening_size = random.randint(Pillars.OPENING_SIZE_RANGE[0], Pillars.OPENING_SIZE_RANGE[1])
        opening_center = 160 + random.randint(-int(opening_size*3/4), int(opening_size*3/4))

        bottom_top = opening_center + opening_size/2
        bottom_full_height = 320 - bottom_top
        bottom_top_cap = colored_rectangle(Pillars.WIDTH, Pillars.CAP_HEIGHT, Pillars.CAP_COLOR)
        bottom_base = colored_rectangle(Pillars.WIDTH, bottom_full_height - Pillars.CAP_HEIGHT, Pillars.BASE_COLOR)
        self.image.blit(bottom_top_cap, (0, bottom_top))
        self.image.blit(bottom_base, (0, bottom_top + Pillars.CAP_HEIGHT))

        top_bottom = opening_center - opening_size / 2
        top_full_height = top_bottom
        top_base = colored_rectangle(Pillars.WIDTH, top_full_height - Pillars.CAP_HEIGHT, Pillars.BASE_COLOR)
        top_bottom_cap = colored_rectangle(Pillars.WIDTH, Pillars.CAP_HEIGHT, Pillars.CAP_COLOR)
        self.image.blit(top_base, (0, 0))
        self.image.blit(top_bottom_cap, (0, top_bottom - Pillars.CAP_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

    @property
    def rect(self):
        return Rect(self.x, 160, Pillars.WIDTH, 320)

    def update(self, ticks=1):
        self.x -= V_HORIZONTAL*ticks

    def collides_with(self, boot):
        return pygame.sprite.collide_mask(self, boot)


def main():
    pygame.init()

    display_surface = pygame.display.set_mode((320, 640))
    pygame.display.set_caption('Jetty Boot')

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("JetBrains Mono", 16, bold=False)
    font_large = pygame.font.SysFont("JetBrains Mono", 48, bold=True)
    image_base = load_image("boot_base.png")
    image_climb = load_image("boot_climb.png")

    boot: Boot | None = None
    all_pillars: list[Pillars] | None = None

    def regenerate_objects():
        nonlocal boot, all_pillars

        boot = Boot(image_base, image_climb)
        all_pillars = []
        for pillar_index in range(LEVEL_LENGTH):
            pillars = Pillars(pillar_index)
            all_pillars.append(pillars)

    regenerate_objects()

    level = 1

    total_offset = 0
    ticks_since_level_start = 0
    running = True
    ending = False
    paused = False
    initial_paused = True if level == 1 else False

    def new_level():
        nonlocal ending, level, ticks_since_level_start, total_offset

        ending = False
        level += 1
        ticks_since_level_start = 0
        total_offset = 0
        regenerate_objects()

    high_score = 0
    if os.path.exists("hs.txt"):
        with open("hs.txt", "r", encoding="UTF-8") as r:
            hs_str = r.read()
            try:
                high_score = int(hs_str)
            except ValueError:
                print("Couldn't load high score")

    def update_high_score():
        with open("hs.txt", "w", encoding="UTF-8") as w:
            w.write(str(high_score))

    while running:
        clock.tick(TICK_RATE)

        for e in pygame.event.get():
            if e.type == KEYUP and initial_paused:
                initial_paused = False
                break
            elif e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                running = False
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and e.key in (K_UP, K_RETURN, K_SPACE)):
                boot.climb_event(ending)

        pressed = pygame.key.get_pressed()
        if pressed[K_SPACE] or pressed[K_UP] or pressed[K_RETURN] or pressed[K_e]:
            boot.climb_event(ending)

        if initial_paused:
            display_surface.blit(colored_rectangle(320, 640, (16, 32, 48)), (0, 0))
            draw_text_centered(display_surface, 312, font, "Press any key to start...")
            pygame.display.flip()

        if paused or initial_paused:
            continue

        pillar_collides = any(pillars.collides_with(boot) for pillars in all_pillars)
        if pillar_collides or 160 >= boot.y or boot.y >= 480:
            if ending:
                new_level()
                continue
            else:
                level = 0
                new_level()
                continue

        display_surface.blit(colored_rectangle(320, 640, (16, 32, 48)), (0, 0))

        for pillars in all_pillars:
            pillars.update()
            display_surface.blit(pillars.image, pillars.rect)
        total_offset += V_HORIZONTAL
        first_pillars_offset = 320*(3/4) - 48
        pillars_offset = Pillars.WIDTH + Pillars.SPACING
        pillars_offsets = total_offset - first_pillars_offset
        float_score = pillars_offsets/pillars_offset + 1
        level_score = min(int(float_score), LEVEL_LENGTH)
        score = (level-1)*LEVEL_LENGTH + level_score

        if score > high_score:
            high_score = score
            update_high_score()

        if float_score >= LEVEL_LENGTH + 0.25:
            ending = True

        boot.update(ending=ending)
        display_surface.blit(boot.image, boot.rect)

        pygame.draw.line(display_surface, EVERYTHING_COLOR, (0, 160), (320, 160))
        pygame.draw.line(display_surface, EVERYTHING_COLOR, (0, 480), (320, 480))

        #draw_text_centered(display_surface, 4, font, "Jetty Boot Safety Protocol")
        draw_text_centered(display_surface, 76, font, f"HIGH SCORE")
        draw_text_centered(display_surface, 96, font, f"{high_score}")
        draw_text_centered(display_surface, 116, font, f"SCORE")
        draw_text_centered(display_surface, 136, font, f"{score}")
        #draw_text_centered(display_surface, 484, font, f"Hack: [space] or [E]")
        draw_text(display_surface, 240, 136, font, f"LVL  {level}")

        if ticks_since_level_start < 60:
            draw_text_centered(display_surface, 320-48/2, font_large, f"LEVEL {level}")

        pygame.display.flip()

        ticks_since_level_start += 1
    pygame.quit()


if __name__ == '__main__':
    main()
