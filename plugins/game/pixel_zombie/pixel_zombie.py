import math
import os
import random
from time import sleep, time
from pathlib import Path
from threading import Event
from queue import Queue

import numpy as np
import pluggy
from pygame.joystick import JoystickType

from config.config import PluginConfig
from plugins.game_plugin import pygame, GamePlugin, AIGame

hookimpl = pluggy.HookimplMarker("pixel_art")

# TODO: review other env vars: https://www.pygame.org/docs/ref/pygame.html#environment-variables
# Enables background joystick updates. Must be set before calling pygame.init() or pygame.joystick.init().
os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = "1"

LEVEL = 1
FPS = 30
DISPLAY_FACTOR = 1

class Zombie(pygame.sprite.Sprite):
    """A zombie sprite (which is also the main player)."""
    def __init__(self, joystick: JoystickType, spawn_rect: pygame.Rect = None, color: str = "green", horde: int = 1):
        pygame.sprite.Sprite.__init__(self)
        self.screen_width, self.screen_height = pygame.display.get_surface().get_size()
        self.color = color
        self.horde = horde
        self.image = pygame.Surface((DISPLAY_FACTOR, DISPLAY_FACTOR)).convert()
        self.image.fill("green")
        self.rect = spawn_rect or pygame.Rect(pygame.display.get_surface().get_rect().center, self.image.get_size())
        self.joystick = joystick

    def update_horde(self, size: int):
        """Updates the horde size.

        Args:
            size (int): Target horde size

        Raises:
            Exception: Size must be int >= 0
        """
        # print(f"New horde size: {size}")
        if size < 0:
            raise Exception(f"update_horde(): can't sqaure root negative: {size}")
        self.horde = size
        base, mod = divmod(self.horde - 1, 3) # horde grows every 3 humans eaten
        # update horde image
        horde_shape = [DISPLAY_FACTOR * (base + 1)] * 2 # horde size + zombie player
        self.image = pygame.Surface(tuple(horde_shape)).convert()
        self.image.fill(self.color)
        self.rect.size = self.image.get_size()

    def update(self):
        """Handle controller input and update zombie position.
        Zombies don't overflow the screen.
        """
        pos = list(self.rect.topleft)
        if round(self.joystick.get_axis(1)) == -1:
            # print("up")
            pos[1] -= DISPLAY_FACTOR
            if pos[1] < 0:
                pos[1] = 0
        elif round(self.joystick.get_axis(1)) == 1:
            # print("down")
            pos[1] += DISPLAY_FACTOR
            if self.rect.bottomright[1] >= self.screen_height:
                pos[1] = self.screen_height - self.rect.height
        if round(self.joystick.get_axis(0)) == -1:
            # print("left")
            pos[0] -= DISPLAY_FACTOR
            if pos[0] < 0:
                pos[0] = 0
        elif round(self.joystick.get_axis(0)) == 1:
            # print("right")
            pos[0] += DISPLAY_FACTOR
            if self.rect.bottomright[0] >= self.screen_width:
                pos[0] = self.screen_width - self.rect.width
        self.rect.topleft = pos

class Human(pygame.sprite.Sprite):
    """A human sprite."""
    def __init__(self, zombie_rect: pygame.Rect, delay: float = 1):
        pygame.sprite.Sprite.__init__(self)
        self.screen_width, self.screen_height = pygame.display.get_surface().get_size()
        self.image = pygame.Surface((DISPLAY_FACTOR, DISPLAY_FACTOR)).convert()
        self.image.fill("white")
        self.rect = pygame.Rect((-DISPLAY_FACTOR, -DISPLAY_FACTOR), self.image.get_size())
        self.vector = [0.0, self.get_level_speed()] # [rad_angle, speed]
        self.delay = time() + delay # delays display of human
        self.frame_counter = FPS
        self.state = "inactive" # inactive, init, active
        self.zombie_rect = zombie_rect

    def get_level_speed(self) -> int:
        """Get human speed for level. Lower number equals greater speed.
        Speed stops increasing after level 20.

        Returns:
            int: Speed
        """
        if LEVEL < 20:
            base, mod = divmod(LEVEL, 5) # speed increases every 5 levels
            speed = 6 - base
        else:
            speed = 2
        return speed
    
    def new_start_pos(self):
        """Generate new random start position on screen's edge
        (excluding corners so zombie can't camp in corner eating humans).
        """
        pos = []
        choices = [1 * random.randint(1, self.screen_width - DISPLAY_FACTOR - 1), random.choice([0, self.screen_width - DISPLAY_FACTOR])]
        for i in range(2):
            choice = choices.pop(random.randint(-1, 0))
            pos.append(choice)
        # print(f"Human new start pos: {pos}")
        self.rect.topleft = tuple(pos)
    
    def new_vector(self):
        """Calculate across screen vector for new humans."""
        dest = []
        for i in range(2):
            if self.rect.topleft[i] == self.screen_width - DISPLAY_FACTOR:
                dest.append(0)
            elif self.rect.topleft[i] == 0:
                dest.append(self.screen_width - DISPLAY_FACTOR)
            else:
                dest.append(self.rect.topleft[i])
        dx = dest[0] - self.rect.topleft[0]
        dy = dest[1] - self.rect.topleft[1]
        self.vector = [
            math.atan2(dy, dx),  # angle in radians
            self.get_level_speed()
        ]
        # print(f"Human new start vector: {self.vector}")
    
    def calculate_next_pos(self, attract = False):
        """Calculate new vector based on current angle and position.\n
        Increase speed and maintain or reverse vector if zombie within a certain radius (e.g., running away).

        Args:
            attract (bool, optional): Whether zombie attracts or repels a human. Defaults to False.
        """
        angle, speed = self.vector
        # print(f"pre angle: {angle}")

        # calculate vector to zombie
        midpoint_delta = np.array(self.zombie_rect.center) - np.array(self.rect.center)
        z_angle = math.atan2(*midpoint_delta.tolist()[::-1])  # angle in radians
        # print(f"z_angle: {z_angle}")
        
        # get modified vector if zombie within r radius
        px_radius = LEVEL * 1.5 * DISPLAY_FACTOR
        midpoint_euclidean_dist = np.linalg.norm(midpoint_delta)
        # print(midpoint_euclidean_dist)
        if midpoint_euclidean_dist < px_radius:
            angle = z_angle if attract else z_angle + math.pi
            if LEVEL < 20:
                speed -= 1 # temp radius speed stops increasing after level 20
                # print(speed)
        
        # print(f"post angle: {angle}")
        self.vector[0] = angle
        if self.frame_counter % speed == 0:
            # moves during evenly spaced subset of frames
            # print(speed)
            self.rect.topleft = (
                round(self.rect.topleft[0] + math.cos(angle)),
                round(self.rect.topleft[1] + math.sin(angle))
            )
        
        if self.frame_counter > 0:
            self.frame_counter -= 1
        else:
            self.frame_counter = FPS
    
    def update(self):
        """Update human position. Humans do overflow the screen.
        """
        match self.state:
            case "active":
                # self.new_start_pos()
                self.calculate_next_pos()
                if self.rect.topleft[0] < 0 or self.rect.topleft[1] < 0 or self.rect.bottomright[0] > self.screen_width or self.rect.bottomright[1] > self.screen_height:
                    self.new_start_pos()
                    self.new_vector()
                    self.calculate_next_pos()
            case "init":
                self.new_start_pos()
                self.new_vector()
                self.state = "active"
            case "inactive":
                if time() > self.delay:
                    self.state = "init"

class Hunter(Human):
    """A hunter sprite."""
    def __init__(self, zombie_rect: pygame.Rect, delay: float = 3):
        super().__init__(zombie_rect, delay)
        self.image.fill("red")
        self.cooloff = 0
    
    def calculate_next_pos(self, attract = True):
        """Calculate new vector based on current angle and position.\n
        Modifies vector relative to zombie (e.g., chasing zombie).

        Args:
            attract (bool, optional): Whether zombie attracts or repels a hunter. Defaults to True.
        """
        angle, speed = self.vector
        # print(f"pre angle: {angle}")

        # calculate vector to zombie
        midpoint_delta = np.array(self.zombie_rect.center) - np.array(self.rect.center)
        z_angle = math.atan2(*midpoint_delta.tolist()[::-1])  # angle in radians
        # print(f"z_angle: {z_angle}")
        
        # get modified vector angle relative to zombie
        angle = z_angle if attract else z_angle + math.pi
        # print(f"post angle: {angle}")
        self.vector[0] = angle
        if self.frame_counter % speed == 0:
            # moves during evenly spaced subset of frames.
            # print(speed)
            self.rect.topleft = (
                round(self.rect.topleft[0] + math.cos(angle)),
                round(self.rect.topleft[1] + math.sin(angle))
            )
        
        if self.frame_counter > 0:
            self.frame_counter -= 1
        else:
            self.frame_counter = FPS
    
    def update(self):
        """Update hunter position. Hunters don't overflow the screen.
        """
        match self.state:
            case "active":
                if self.cooloff == 0:
                    # self.new_start_pos()
                    self.calculate_next_pos()
                    if self.rect.topleft[0] < 0 or self.rect.topleft[1] < 0 or self.rect.bottomright[0] > self.screen_width or self.rect.bottomright[1] > self.screen_height:
                        self.new_start_pos()
                        self.new_vector()
                        self.calculate_next_pos()
                else:
                    self.cooloff -= 1
            case "init":
                self.new_start_pos()
                self.new_vector()
                self.state = "active"
            case "inactive":
                if time() > self.delay:
                    self.state = "init"

class PixelZombieGame(GamePlugin):
    """Pixel Zombie game plugin class."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"

    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        super().__init__(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.zombie_color = self.config.get_item("zombie_color", "green")

    def load_image(self, filename: str, colorkey: tuple[int] = (0, 0, 0), scale: int = 1) -> tuple[pygame.Surface, pygame.Rect]:
        """Load an image as pygame surface and rect.

        Args:
            filename (str): Image filename
            colorkey (tuple[int], optional): Image transparent color. Defaults to None.
            scale (int, optional): Image scale factor. Defaults to 1.

        Returns:
            tuple[pygame.Surface, pygame.Rect]: Pygame image representation
        """
        image = pygame.image.load(self.PLUGIN_ASSETS_PATH / "img" / filename)
        size = image.get_size()
        size = (size[0] * scale, size[1] * scale)
        image = pygame.transform.scale(image, size)

        image = image.convert()
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image, image.get_rect()

    def load_sound(self, filename: str, volume: float = 1.0) -> pygame.mixer.Sound:
        """Load sound.

        Args:
            filename (str): Sound filename
            volume (float, optional): Sound volume. Defaults to 1.0.

        Returns:
            pygame.mixer.Sound: Pygame sound
        """
        class NoneSound:
            def play(self):
                pass
        if not pygame.mixer or not pygame.mixer.get_init():
            return NoneSound()
        sound = pygame.mixer.Sound(self.PLUGIN_ASSETS_PATH / "sound" / filename)
        sound.set_volume(volume)
        return sound

    def next_level(self, zombie_sprites: pygame.sprite.RenderPlain, human_sprites: pygame.sprite.RenderPlain, hunter_sprites: pygame.sprite.RenderPlain):
        """Set sprites for next level. Humans increase by 3 each level while
        hunters increase by 1.

        Args:
            zombie_sprites (pygame.sprite.RenderPlain): Zombies
            human_sprites (pygame.sprite.RenderPlain): Humans
            hunter_sprites (pygame.sprite.RenderPlain): Hunters
        """
        human_sprites.empty()
        hunter_sprites.empty()
        for i in range(LEVEL * 3):
            human_sprites.add(Human(zombie_sprites.sprites()[0].rect, i))
        for i in range(LEVEL):
            hunter_sprites.add(Hunter(zombie_sprites.sprites()[0].rect, 3 + i))

    def display_connect_controller(self):
        """Display "Connect Controller" screen.
        """
        self.screen.fill("black")
        font_size = DISPLAY_FACTOR * 8 if DISPLAY_FACTOR > 1 else 14
        font = pygame.font.Font(None, font_size)
        text = font.render(f"Connect", True, "white")
        textpos = text.get_rect(centerx=self.screen.get_rect().centerx, y=self.screen.get_rect().centery-12*DISPLAY_FACTOR)
        self.screen.blit(text, textpos)
        text = font.render(f"Controller", True, "white")
        textpos = text.get_rect(centerx=self.screen.get_rect().centerx, y=self.screen.get_rect().centery-2*DISPLAY_FACTOR)
        self.screen.blit(text, textpos)
        self.draw()

    def handle_controller_hotplugging(self, event: pygame.event.Event, zombie_sprites: pygame.sprite.RenderPlain, zombie_spawn_pos: list):
        """Creates zombies (players) by handle controller hotplugging (unplugging and plugging in controllers).

        Args:
            event (pygame.event.Event): Pygame event
            zombie_sprites (pygame.sprite.RenderPlain): Zombies
            zombie_spawn_pos (list): Zombie spawn position history
        """
        if event.type == pygame.JOYDEVICEADDED:
            # This event will be generated when the program starts for every
            # joystick, filling up the list without needing to create them manually
            joy = pygame.joystick.Joystick(event.device_index)
            if not len(zombie_spawn_pos):
                zombie = Zombie(joy, color=self.zombie_color)
            else:
                zombie = Zombie(joy, *zombie_spawn_pos.pop(), color=self.zombie_color)
                zombie.update_horde(zombie.horde)
            zombie_sprites.add(zombie)
            print(f"Joystick {joy.get_instance_id()} connected")
        elif event.type == pygame.JOYDEVICEREMOVED:
            for z in zombie_sprites.sprites():
                if z.joystick.get_instance_id() == event.instance_id:
                    zombie_spawn_pos.append((z.rect, z.horde))
                    z.kill()
                    print(f"Joystick {event.instance_id} disconnected")

    def run_title_screen(self, title_sound: pygame.mixer.Sound, zombie_sprites: pygame.sprite.RenderPlain, zombie_spawn_pos: list) -> bool:
        """Displays title screen. Options are to start or quit game.

        Args:
            title_sound (pygame.mixer.Sound): Title screen music
            zombie_sprites (pygame.sprite.RenderPlain): Zombies
            zombie_spawn_pos (list): Zombie spawn position history

        Returns:
            bool: Whether start was chosen
        """
        title_sound.play()
        states = ["start", "quit"]
        images = [self.load_image("start.png"), self.load_image("quit.png")]
        current_state = 0
        running = True
        while running:
            self.clock.tick(FPS)
            # poll for events
            for event in pygame.event.get():
                self.handle_controller_hotplugging(event, zombie_sprites, zombie_spawn_pos)
                # handle start/quit selection
                if event.type == pygame.JOYAXISMOTION:
                    if event.axis == 1 and round(event.value) in [-1, 1]:
                        print("Joystick axis pressed.")
                        current_state = not current_state
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 2:
                        print("Joystick 'B' button pressed.")
                        print(f"Start screen: user selected {states[current_state]}")
                        running = False
            # check if controller connected
            if not pygame.joystick.get_count():
                self.display_connect_controller()
                continue
            self.screen.blit(*images[current_state])
            self.draw()
        title_sound.fadeout(2_000)
        return states[current_state] == "start"
    
    @hookimpl(specname="game_hook")
    @AIGame()
    def play(self):
        """Plugin game loop.
        """
        global LEVEL  
        
        # load sounds
        title_sound = self.load_sound("title.wav")
        level_sound = self.load_sound("level.wav")
        zombie_sound = self.load_sound("zombie.wav")
        human_sounds = [self.load_sound(f"human-{i + 1}.wav") for i in range(3)]

        # prepare sprites
        zombie_spawn_pos = []
        zombie_sprites = pygame.sprite.RenderPlain()
        human_sprites = pygame.sprite.RenderPlain()
        hunter_sprites = pygame.sprite.RenderPlain()

        backup_screen = self.screen.copy()
        title_screen = True
        completed_level = False
        paused = False
        running = True

        # game loop
        while running:
            self.clock.tick(FPS)
            # poll for events
            for event in pygame.event.get():
                # dynamically load/unload any controllers
                self.handle_controller_hotplugging(event, zombie_sprites, zombie_spawn_pos)
                if event.type == pygame.JOYBUTTONDOWN:
                    # SNES controller start button
                    if event.button == 9:
                        print("Joystick 'START' button pressed.")
                        paused = not paused
                        if paused:
                            title_sound.play()
                        else:
                            title_sound.fadeout(1_000)

            # check if controller connected
            if not pygame.joystick.get_count():
                self.display_connect_controller()
                continue
            
            # title screen
            if title_screen:
                play_game = self.run_title_screen(title_sound, zombie_sprites, zombie_spawn_pos)
                if play_game:
                    # player chose start
                    title_screen = False
                    self.next_level(zombie_sprites, human_sprites, hunter_sprites)
                else:
                    # player chose quit
                    break

            # pause screen
            if paused:
                font_size = DISPLAY_FACTOR * 4 if DISPLAY_FACTOR > 1 else 14
                font = pygame.font.Font(None, font_size)
                level_text = font.render(f"Paused", True, (255, 255, 255))
                level_textpos = level_text.get_rect(center=self.screen.get_rect().center)
                self.screen.blit(backup_screen, backup_screen.get_rect())
                self.screen.blit(level_text, level_textpos)
                self.draw()
                continue
            
            # update metrics from collisions
            human_collisions: dict[Zombie, list[Human]] = pygame.sprite.groupcollide(zombie_sprites, human_sprites, False, True)
            for zombie, humans in human_collisions.items():
                for i in range(len(humans)):
                    human_sounds[random.randint(0, 2)].play()
                zombie.update_horde(zombie.horde + len(humans))
            hunter_collisions: dict[Hunter, list[Zombie]] = pygame.sprite.groupcollide(hunter_sprites, zombie_sprites, False, False)
            for hunter, zombies in hunter_collisions.items():
                if hunter.cooloff == 0:
                    hunter.cooloff = 3 * 30 # time based on FPS
                    zombie_sound.play()
                    for z in zombies:
                        if zombie_sprites.has(z):
                            z.update_horde(z.horde - 1)
                            if z.horde <= 0:
                                print(f"Zombie {z.joystick.get_instance_id()} dead. Horde size: {z.horde}")
                                z.kill()
            
            # end game if no more zombies
            if not len(zombie_sprites.sprites()):
                print("Last zombie died. Ending game.")
                sleep(2)
                running = False
                break
            
            # update sprites
            zombie_sprites.update()
            human_sprites.update()
            for hunter in hunter_sprites.sprites():
                hunter.zombie_pos = zombie_sprites.sprites()[0].rect.topleft
            hunter_sprites.update()

            # set to next level if all humans eaten
            if not len(human_sprites.sprites()):
                completed_level = True
                LEVEL += 1
                print(f"All humans eaten. Moving to Level {LEVEL}")
                self.next_level(zombie_sprites, human_sprites, hunter_sprites)

            # clear screen (TODO: update only diff pixels)
            self.screen.fill("black")

            # draw level and horde score
            if pygame.font:
                font_size = DISPLAY_FACTOR * 3 if DISPLAY_FACTOR > 1 else 12
                font = pygame.font.Font(None, font_size)
                level_text = font.render(f"L {LEVEL}", True, (255, 255, 255))
                level_textpos = level_text.get_rect(centerx=self.screen.get_width() * .2, y=DISPLAY_FACTOR)
                self.screen.blit(level_text, level_textpos)
                horde_text = font.render(f"H {zombie_sprites.sprites()[0].horde}", True, (255, 255, 255))
                horde_textpos = horde_text.get_rect(centerx=self.screen.get_width() * .8, y=DISPLAY_FACTOR)
                self.screen.blit(horde_text, horde_textpos)
            
            # draw sprites    
            zombie_sprites.draw(self.screen)
            human_sprites.draw(self.screen)
            hunter_sprites.draw(self.screen)
            backup_screen = self.screen.copy()
            self.draw()

            # go to next level if current level completed
            if completed_level:
                completed_level = False
                sleep(0.5)
                level_sound.play()
                level_sound.fadeout(4_500)
                sleep(3)
