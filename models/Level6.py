#!/usr/bin/env python3

from random import randrange

# ---------------------- IMPORTS ---------------------
# Python libs
from pygame import image, font, sprite, mixer
# Own libs
from models.Block6 import Snow, Floor, Hole, Coin, SavePoint, Platform, Lava
from constants6 import COLORS, ANTIALIASING, ROOT, COIN_SIZE, FLOOR_SIZE


class _Level:
    def __init__(self, screen, scr_size, player, debug=False):
        """ This class manages all in terms of creating level structures
            and loading graphic and audio resources. Every level created
            has inheritance from this Level class.
        :param screen: A reference for the main screen
        :param scr_size: The screen size
        :param player:
        :param debug: Flag for debugging into the game
        """
        # -- Source folders -------------------
        img_dir = f'{ROOT}/resources/images/'
        # -- Attributes -----------------------
        self.debug = debug
        self.screen = screen
        self.scrSize = scr_size
        self.ID = None                              # A level identifier
        self.structure = []                         # Level structure map
        self.levelInit = [0, 0]                     # Level enter point
        self.reference = []                         # Level fixed references for scroll
        self.backgroundImg = None                   # Background image reference
        self.hud = [image.load(f'{img_dir}Life.png').convert(),
                    image.load(f'{img_dir}Energy.png').convert(),
                    image.load(f'{img_dir}Coin_Frames/coin.png').convert()]
        for x in range(len(self.hud)):
            self.hud[x].set_colorkey(COLORS['WHITE'])

        self.font = font.SysFont('Calibri', 25, True, False)
        # Sprite lists for the win!
        self.colliders = sprite.Group()             # Walls, platforms, floor, enemies, switches...
        self.temporary = sprite.Group()             # Coins, ammo, lifepoints...
        self.player_display = sprite.Group()        # The player itself
        self.player = player
        self.player_display.add(self.player)
        self.bodies = sprite.Group()                # All sprites (this is for render on the screen)
        # Music
        self.musicTheme = None
        # HUD elements
        self.lifeText = self.font.render(f': {self.player.life}', ANTIALIASING, COLORS['WHITE'])
        self.energyText = self.font.render(f': {self.player.energy}', ANTIALIASING, COLORS['WHITE'])
        self.coinText = self.font.render(f': {self.player.coins}', ANTIALIASING, COLORS['WHITE'])
        # Debug
        if self.debug:
            self.debText = self.font.render(f'X: {self.player.rect.x}; Y: {self.player.rect.y}',
                                            ANTIALIASING, COLORS['WHITE'])

    # ---------- Methods --------------------------
    def display(self):
        # We check if the level has a background image and blit it to the screen
        if self.backgroundImg is not None:
            self.screen.blit(self.backgroundImg, [0, 0])

        self.bodies.draw(self.screen)
        self.player_display.draw(self.screen)

        if self.hud is not None:
            self.screen.blit(self.hud[0], [50, 50])
            self.screen.blit(self.hud[1], [50, 80])
            self.screen.blit(self.hud[2], [50, 110])

        self.screen.blit(self.lifeText, [80, 50])
        self.screen.blit(self.energyText, [80, 80])
        self.screen.blit(self.coinText, [80, 110])

        if self.debug:
            self.screen.blit(self.debText, [50, 560])

    def fill_level(self, structure):
        """
        It fills all level gaps with elements taking a pattern

        :param structure: A string list which contains all elements available in a level (WIP)
        """
        cnt_y = 0  # Initial Y-axis tile grid
        temp_row = 0
        for row in structure:
            cnt_x = 0  # Initial X-axis tile grid
            temp_col = 0
            for column in row:
                if column == "f":  # 'f' stands for 'Floor'
                    floor = Floor(COLORS['BLUE'], FLOOR_SIZE, FLOOR_SIZE)
                    floor.rect.x = cnt_x
                    floor.rect.y = cnt_y
                    self.colliders.add(floor)
                    self.bodies.add(floor)
                    # We append the opposite level corners
                    if cnt_y == 0 and cnt_x == 0:
                        self.reference.append(floor)
                    elif cnt_y == (len(structure) - 1) * FLOOR_SIZE and cnt_x == (len(structure[0]) - 1) * FLOOR_SIZE:
                        self.reference.append(floor)
                elif column == "h":  # 'h' stands for 'Hole'
                    if structure[temp_row-1][temp_col] == ' ' or structure[temp_row-1][temp_col] == 'c':
                        hole = Hole(COLORS['BLACK'], FLOOR_SIZE, FLOOR_SIZE, "hole_metal")
                    elif structure[temp_row - 1][temp_col] == 'f':
                        hole = Hole(COLORS['BLACK'], FLOOR_SIZE, FLOOR_SIZE, "hole_floor")
                    else:
                        hole = Hole(COLORS['BLACK'], FLOOR_SIZE, FLOOR_SIZE)
                    hole.rect.x = cnt_x
                    hole.rect.y = cnt_y
                    self.colliders.add(hole)
                    self.bodies.add(hole)
                elif column == "s":  # 's' stands for 'SavePoint'
                    save = SavePoint(COLORS['WHITE'], FLOOR_SIZE, FLOOR_SIZE)
                    save.rect.x = cnt_x
                    save.rect.y = cnt_y
                    self.colliders.add(save)
                    self.bodies.add(save)
                elif column == "c":  # 'c' stands for 'Coin'
                    coin = Coin(COLORS['ORANGE'], COIN_SIZE, COIN_SIZE)
                    coin.rect.x = cnt_x + 10
                    coin.rect.y = cnt_y + 10
                    self.temporary.add(coin)
                    self.bodies.add(coin)
                elif column == "p":  # 'p' stands for 'Platform'
                    platform = Platform(COLORS['GREEN'], FLOOR_SIZE, FLOOR_SIZE, [cnt_x, cnt_y], 'Y')
                    platform.rect.x = cnt_x
                    platform.rect.y = cnt_y
                    self.colliders.add(platform)
                    self.bodies.add(platform)
                elif column == "l":
                    lava = Lava(COLORS['RED'], FLOOR_SIZE, FLOOR_SIZE)
                    lava.rect.x = cnt_x
                    lava.rect.y = cnt_y
                    self.colliders.add(lava)
                    self.bodies.add(lava)

                cnt_x += 50  # Increment X-axis for the next tile
                temp_col += 1

            cnt_y += 50  # Increment Y-axis for the next tile
            temp_row += 1

    def scroll(self):
        """
        It manages the level scrolling
        """
        # Scrolls in X axis
        # The player's coordinates are out of scope (Level enter)
        if self.player.get_rect().x < 0:
            diff = self.scrSize[0] / 2 - self.player.get_rect().x
            self.player.rect.x = self.scrSize[0] / 2
            for body in self.bodies:
                body.rect.x += diff
                if isinstance(body, Platform):
                    body.initPoint[0] += diff
        # The player's coordinates are out of scope (Level enter)
        elif self.player.get_rect().x > self.scrSize[0]:
            # diff = self.player.get_rect().x - self.scrSize[0] / 2
            # self.player.rect.x = self.scrSize[0] / 2
            diff = self.reference[1].rect.x + FLOOR_SIZE - self.scrSize[0]
            self.player.rect.x -= diff
            for body in self.bodies:
                body.rect.x -= diff
                if isinstance(body, Platform):
                    body.initPoint[0] -= diff
        # The player is going on the left of the screen (going to left)
        if self.player.get_rect().x < self.scrSize[0] / 2:
            # The player is far from the beginning of the level
            if self.player.get_rect().x - self.reference[0].get_rect().x > self.scrSize[0] / 2:
                diff = self.scrSize[0] / 2 - self.player.get_rect().x
                self.player.rect.x = self.scrSize[0] / 2
                for body in self.bodies:
                    body.rect.x += diff
                    if isinstance(body, Platform):
                        body.initPoint[0] += diff
        # The player is located near to the end of the screen (going to the right)
        elif self.player.get_rect().x > self.scrSize[0] / 2:
            # The player is far from the beginning of the level
            if self.reference[1].get_rect().x + FLOOR_SIZE - self.player.get_rect().x > self.scrSize[0] / 2:
                diff = self.player.get_rect().x - self.scrSize[0] / 2
                self.player.rect.x = self.scrSize[0] / 2
                for body in self.bodies:
                    body.rect.x -= diff
                    if isinstance(body, Platform):
                        body.initPoint[0] -= diff
        # Scrolls in Y axis
        # The player's coordinates are out of scope (Level enter)
        if self.player.get_rect().y < 0:
            diff = self.scrSize[1] / 2 - self.player.get_rect().y
            self.player.rect.y = self.scrSize[1] / 2
            for body in self.bodies:
                body.rect.y += diff
                if isinstance(body, Platform):
                    body.initPoint[1] += diff
        elif self.player.get_rect().y > self.scrSize[1]:
            diff = self.reference[1].rect.y + FLOOR_SIZE - self.scrSize[1]
            self.player.rect.y -= diff
            for body in self.bodies:
                body.rect.y -= diff
                if isinstance(body, Platform):
                    body.initPoint[1] -= diff
        # The player is going down
        if self.player.get_rect().y < self.scrSize[1] / 2:
            # The player is far from the beginning of the level
            if self.player.get_rect().y - self.reference[0].get_rect().y > self.scrSize[1] / 2:
                diff = self.scrSize[1] / 2 - self.player.get_rect().y
                self.player.rect.y = self.scrSize[1] / 2
                for body in self.bodies:
                    body.rect.y += diff
                    if isinstance(body, Platform):
                        body.initPoint[1] += diff
        # The player is located near to the end of the screen (going to the right)
        elif self.player.get_rect().y > self.scrSize[1] / 2:
            # The player is far from the beginning of the level
            if self.reference[1].get_rect().y + FLOOR_SIZE - self.player.get_rect().y > self.scrSize[1] / 2:
                diff = self.player.get_rect().y - self.scrSize[1] / 2
                self.player.rect.y = self.scrSize[1] / 2
                for body in self.bodies:
                    body.rect.y -= diff
                    if isinstance(body, Platform):
                        body.initPoint[1] -= diff

    def set_theme(self):
        """
        Set a music theme in this scene
        """
        if self.musicTheme is not None:
            mixer.music.load(self.musicTheme)

    def render_hud(self):
        """
        It renders all main hud information
        """
        self.lifeText = self.font.render(": " + str(self.player.life), ANTIALIASING, COLORS['WHITE'])
        self.energyText = self.font.render(": " + str(self.player.energy), ANTIALIASING, COLORS['WHITE'])
        self.coinText = self.font.render(": " + str(self.player.coins), ANTIALIASING, COLORS['WHITE'])


class _PlainLevel(_Level):
    def __init__(self, screen, scr_size, player, debug=False):
        """
        2D Plain level's type class

        :param screen:
        :param scr_size:
        :param player:
        :param debug:
        """
        super().__init__(screen, scr_size, player, debug)
        self.plainLevel = True

    # ---------- Methods --------------------------
    def update(self):
        # Update all elements in level
        self.bodies.update()
        self.player.update(self.colliders, self.temporary)
        self.scroll()
        self.render_hud()
        if self.debug:
            self.debText = self.font.render(f'X: {self.player.rect.x}; Y: {self.player.rect.y}; '
                                            + f'VelX: {self.player.velX}; VelY: {self.player.velY}',
                                            ANTIALIASING, COLORS['WHITE'])

        return False


class _HorizontalLevel(_Level):
    def __init__(self, screen, scr_size, player, debug=False):
        """
        2D Horizontal level's type class

        :param screen:
        :param scr_size:
        :param player:
        :param debug:
        """
        super().__init__(screen, scr_size, player, debug)
        self.backgroundImg = image.load(f'{ROOT}/resources/images/astro.jpg').convert()
        self.plainLevel = False

    # ---------- Methods --------------------------
    def update(self):
        # Update all elements in level
        self.bodies.update()
        # Checks the condition for going out the level
        if self.player.isDead:
            return True
        elif self.player.coins < 10:
            self.player.update(self.colliders, self.temporary)
            self.scroll()
            self.render_hud()
            if self.debug:
                self.debText = self.font.render(f'X: {self.player.rect.x}; Y: {self.player.rect.y}; '
                                                + f'VelX: {self.player.velX}; VelY: {self.player.velY}',
                                                ANTIALIASING, COLORS['WHITE'])

            return False

        else:
            return True


# All levels must inherit from 'HorizontalLevel' or 'Plain Level'
class Level1(_HorizontalLevel):
    # ---------- Constructor ----------------------
    def __init__(self, screen, scr_size, player, debug=False):
        # -- Parent constructor ---------------
        super().__init__(screen, scr_size, player, debug)
        # Level data
        self.ID = "Doom Valley"
        self.levelInit = (50, 900)                     # Initial player position's coordinates (50, 900)
        # Level map structure
        self.structure = ["ffffffffffffffffffffffffffffffff",
                          "fc                            cf",
                          "ff  fffffffffffffffffff  c  ffff",
                          "f                      flflf   f",
                          "f  f                    fff    f",
                          "f   ff                         f",
                          "f    f        f                f",
                          "f    ffff   fff                f",
                          "f                              f",
                          "f               p          f c f",
                          "f                          fffff",
                          "f              ffff     p      f",
                          "f   f       f  f               f",
                          "f     c    ff  f     fff ffff  f",
                          "f  f ffff fff       f       f  f",
                          "f c          f            f f  f",
                          "f fc                c     f    f",
                          "f  f              fff     f    f",
                          "f               f              f",
                          "f                       c f  c f",
                          "ffffffffllllfffffffffffffffllflf"]
        # Populating level
        self.fill_level(self.structure)

        # Random location for snow flakes
        for i in range(50):     # 50
            # Snow instance
            flake = Snow(COLORS['WHITE'], 2, 2, self.scrSize)
            # We create a random placement
            # flake.rect.x = randrange(self.scrSize[0])
            flake.rect.x = randrange(len(self.structure[0]) * 50)
            # flake.rect.y = randrange(self.scrSize[1])
            flake.rect.y = randrange(len(self.structure) * 50)
            # Then we add the flake to the block lists
            flake.firstX = flake.rect.x
            self.temporary.add(flake)
            self.bodies.add(flake)

        self.musicTheme = f'{ROOT}/resources/music/doom_valley.ogg'


# All levels must inherit from 'HorizontalLevel' or 'Plain Level'
class Level2(_PlainLevel):
    def __init__(self, screen, src_size, player, debug=False):
        super().__init__(screen, src_size, player, debug)
        # Level data
        self.ID = "The RING"
        self.levelInit = (150, 850)  # Initial player position's coordinates (50, 500)
        # -- Attributes -----------------------
        self.structure = ["ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                          "fffffff  ffff ff               ffhhchhchhchhchhff c        cffff",
                          "ff  fff  fff  ff               ffhhchhchhchhchhffcfff       cfff",
                          "ff c cf  fc   ff                               ff fhh        cff",
                          "ff  hhf  fhh                                                  cf",
                          "ff  fff  fff                   ffhhhhhh                        f",
                          "ff  fff  fff  ff            hhhffhhhhhh  hhhhhhff fhh      hhf f",
                          "f             ff            hhffffhhhhh  hhhhhhffcfff      fffcf",
                          "fffffff  fffffff            hffffffhhhh  hhhhhhff c          c f",
                          "f       fc    ffffffff  fffffffffffffff  ffffffffffffff  fffffff",
                          "f fffff fc    ffffffff  fffffffffffffff  ffffffffffffff  fffffff",
                          "fcfhf h     f ff            hffffffhhhh  hhhhhhff              f",
                          "fcf        ff ff            hhffffhhhhh  hhhhhhff fff      fff f",
                          "fcff    f fff ff            hhhffhhhhhh  hhhhhhff fhh  s   hhf f",
                          "fcf   h  c                     ffhhhhhh                        f",
                          "fcff  h                                                    hhhhf",
                          "ff    h    s  ff                               ff fhh      hhhff",
                          "fff   f       ff               ffhhchhchhchhchhff fff      hhfff",
                          "ffff  f       ff               ffhhchhchhchhchhff          hffff",
                          "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"]
        # 64 x 20
        # Populating level
        self.fill_level(self.structure)
        self.structure.clear()
        self.musicTheme = f'{ROOT}/resources/music/the_ring.ogg'