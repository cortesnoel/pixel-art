from random import randint, choice
from time import sleep
from pathlib import Path
from threading import Event
from queue import Queue

import pluggy
from PIL import Image

from config.config import PluginConfig
from plugins.rgb_plugin import RGBPlugin, RGBEvents
from util.rgb_util import get_color_from_funkyfuture_palette, get_color_from_sodacap_palette

hookimpl = pluggy.HookimplMarker("pixel_art")

class RandomPixelPlugins(RGBPlugin):
    """RGB plugin class. Contains plugins that draw pixel patterns randomly on the screen programatically."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"

    def __init__(self, matrix, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue):
        super().__init__(matrix, rgb_start_event, ai_end_event, ai_result_queue)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.save_gif = self.config.get_item("save_gif", False)
        self.num_sprites = self.config.get_item("num_sprites", 3)
   
    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_pixel_rand(self):        
        """Random Pixel RGB plugin for displaying n pixels in random locations on the screen.\n
        Choose number of pixels displayed by setting `num_sprites` in plugin config.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        print("> Init display_pixel_rand")
        gif = []
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        colors = [get_color_from_funkyfuture_palette(randint(0, 7)) for _ in range(self.num_sprites)]

        while not self.ai_end_event.is_set():
            # generate image rgb values
            img = Image.new("RGB", (self.matrix.width, self.matrix.height))
            for i in range(self.num_sprites):
                img.putpixel((randint(0, 63), randint(0, 63)), colors[i])
            # send image to screen
            img.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
            offscreen_canvas.SetImage(img.convert("RGB"))
            self.matrix.SwapOnVSync(offscreen_canvas)
            # collect first 5 images for saving gif
            if self.save_gif and len(gif) < 5:
                gif.append(img)
            sleep(1)

        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH)

        self.matrix.Clear()
        print("> Exit display_pixel_rand")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_heart_rand(self):
        """Random Pixel RGB plugin for displaying n hearts in random locations on the screen.\n
        Choose number of hearts displayed by setting `num_sprites` in plugin config.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        print("> Init display_heart_rand")
        gif = []
        shape = (7, 6)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        unfill_pixels = [
            (0, 0), (3, 0), (6, 0),
            (0, 3), (6, 3),
            (0, 4), (1, 4), (5, 4), (6, 4),
            (0, 5), (1, 5), (2, 5), (4, 5), (5, 5), (6, 5)
        ]

        while not self.ai_end_event.is_set():
            # generate image rgb values
            img = Image.new("RGB", (self.matrix.width, self.matrix.height))
            for _ in range(self.num_sprites):
                color = get_color_from_funkyfuture_palette(randint(0, 7))
                top_left_pixel = (randint(0, 64 - shape[0]), randint(0, 64 - shape[1]))
                for x in range(shape[0]):
                    for y in range(shape[1]):
                        if (x, y) in unfill_pixels:
                            continue
                        img.putpixel((top_left_pixel[0] + x, top_left_pixel[1] + y), color)
            # send image to screen
            img.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
            offscreen_canvas.SetImage(img.convert("RGB"))
            self.matrix.SwapOnVSync(offscreen_canvas)
            # collect first 5 images for saving gif
            if self.save_gif and len(gif) < 5:
                gif.append(img)
            sleep(1)

        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH)

        self.matrix.Clear()
        print("> Exit display_heart_rand")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_smiley_rand(self):        
        """Random Pixel RGB plugin for displaying a smiley in random locations on the screen.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        print("> Init display_smiley_rand")
        gif = []
        shape = (9, 9)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        pixels = {
            "none": (None, [(0,0), (1,0), (7,0), (8,0), (0,1), (8,1), (0,7), (8,7), (0,8), (1,8), (7,8), (8,8)]), # transparent
            "eye": ((255, 255, 255), [(2,2), (5,2), (2,3), (3,3), (5,3), (6,3)]), # white
            "iris": ((0, 0, 139), [(3,2), (6,2)]), # dark blue
            "mouth": ((210, 4, 45), [(2,5), (3,5), (4,5), (5,5), (6,5), (3,6), (4,6), (5,6)]), # cherry
            "face": ((255, 215, 0), []) # yellow
        }

        while not self.ai_end_event.is_set():
            # generate image rgb values
            img = Image.new("RGB", (self.matrix.width, self.matrix.height))
            top_left_pixel = (randint(0, 64 - shape[0]), randint(0, 64 - shape[1]))
            for x in range(shape[0]):
                for y in range(shape[1]):
                    found_feature_px = False
                    for color, px in pixels.values():
                        if (x, y) in px:
                            found_feature_px = True
                            if color == None:
                                continue
                            img.putpixel((top_left_pixel[0] + x, top_left_pixel[1] + y), color)
                            break
                    if not found_feature_px:
                        img.putpixel((top_left_pixel[0] + x, top_left_pixel[1] + y), pixels["face"][0])
            # send image to screen
            img.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
            offscreen_canvas.SetImage(img.convert("RGB"))
            self.matrix.SwapOnVSync(offscreen_canvas)
            # collect first 5 images for saving gif
            if self.save_gif and len(gif) < 5:
                gif.append(img)
            sleep(1)
        
        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH)

        self.matrix.Clear()
        print("> Exit display_smiley_rand")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_snake_rand(self):        
        """Random Pixel RGB plugin for displaying a pixel snake on the screen.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        # TODO: minor refactor for readability
        print("> Init display_snake_rand")
        gif = []
        color_change_flag = True
        color_index = 0
        color = get_color_from_sodacap_palette(color_index)

        collision_detected = False
        nav_opts = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        new_px = (32, 32)
        snake_px = [(color, new_px)]

        offscreen_canvas = self.matrix.CreateFrameCanvas()

        while not self.ai_end_event.is_set():
            """Rules:
                1. forward five times
                2. if five times, change direction
                3. not out of bounds
                4. color only changes for non-parallel collision
                5. reset after 500 moves
            """
            if len(snake_px) > 500:
                snake_px.clear()
                snake_px.append((color, new_px))
            direction = choice(nav_opts)
            for i in range(5):
                img = Image.new("RGB", (self.matrix.width, self.matrix.height))
                new_px = (snake_px[-1][1][0] + direction[0], snake_px[-1][1][1] + direction[1])
                # if new direction breaks rules, break loop to get new direction
                is_reverse_path = new_px == snake_px[-2][1] if len(snake_px) > 1 else False
                is_out_of_bounds = new_px[0] < 0 or new_px[1] < 0 or new_px[0] >= 64 or new_px[1] >= 64
                if is_reverse_path or is_out_of_bounds:
                    break
                # change color during non-parallel collisions
                for i, p in enumerate([p for _, p in snake_px]):
                    collision_detected = new_px == p
                    if collision_detected:
                        if color_change_flag:
                            color_index = color_index + 1 if color_index < 3 else 0
                            color = get_color_from_sodacap_palette(color_index)
                            snake_px.pop(i)
                        break
                color_change_flag = not collision_detected
                # add pixel to snake
                snake_px.append((color, new_px))
                for c, px in snake_px:
                    img.putpixel(px, c)
                # send image to screen
                img.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
                offscreen_canvas.SetImage(img.convert("RGB"))
                self.matrix.SwapOnVSync(offscreen_canvas)
                # collect first 50 images for saving gif
                if self.save_gif and len(gif) < 50:
                    gif.append(img)
                sleep(.1)
        
        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH, duration=10)

        self.matrix.Clear()
        print("> Exit display_snake_rand")
