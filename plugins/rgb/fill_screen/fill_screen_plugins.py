from random import randint
from time import sleep
from datetime import datetime
from pathlib import Path
from threading import Event
from queue import Queue

import pluggy
import numpy as np
from PIL import Image

from config.config import PluginConfig
from plugins.rgb_plugin import RGBPlugin, RGBEvents
from util.rgb_util import get_color_from_moonlightgb_palette, get_color_from_sodacap_palette

hookimpl = pluggy.HookimplMarker("pixel_art")

class FillScreenPlugins(RGBPlugin):
    """RGB plugin class. Contains plugins that fill entire LED array screen programatically."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"

    def __init__(self, matrix, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue):
        super().__init__(matrix, rgb_start_event, ai_end_event, ai_result_queue)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.save_gif = self.config.get_item("save_gif", False)
        self.strobe_color = self.config.get_item("strobe_color", None)

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_strobe_fill(self):
        """Fill Screen RGB plugin for fade-in/out strobe pattern.
        Uses sodacap color palette if `strobe_color` not set in plugin config.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        # TODO: improve fade effect
        print("> Init display_strobe_fill")
        gif = []
        direction = False
        frames = 100
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        is_color_set = isinstance(self.strobe_color, list) and len(self.strobe_color) == 3
        color = self.strobe_color if is_color_set else get_color_from_sodacap_palette(randint(0, 3))
        
        while not self.ai_end_event.is_set():
            direction_range = (1, frames) if direction else (frames - 1, 0, -1)
            for i in range(*direction_range):
                # generate image rgb values
                mod_color = tuple([i * c // frames for c in color])
                offscreen_canvas.Fill(*mod_color)
                # send image to screen
                self.matrix.SwapOnVSync(offscreen_canvas)
                # collect first set of evenly spaced 18 images (9 each direction) for saving gif
                if len(gif) < 18 and i % (frames // 10) == 0:
                    gif.append(Image.new("RGB", (self.matrix.width, self.matrix.height), mod_color))
                # sleep timestep for fade-in/fade-out effect
                s = .1 / i if i > frames / 2 else .1 / (frames - i)
                sleep(s)
            direction = not direction

        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH)
        
        self.matrix.Clear()
        print("> Exit display_strobe_fill")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_scatter_fill(self):
        """Fill Screen RGB plugin for random pixel colors. Uses moonlightgb color palette.\n
        Save gif example by setting `save_gif = true` in plugin config.
        """
        print("> Init display_scatter_fill")
        gif = []
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        while not self.ai_end_event.is_set():
            # generate image rgb values
            img = [[get_color_from_moonlightgb_palette(randint(0, 3)) for _ in range(self.matrix.height)] for _ in range(self.matrix.width)]
            # send image to screen
            temp = Image.fromarray(np.array(img, dtype=np.uint8))
            temp.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
            offscreen_canvas.SetImage(temp.convert("RGB"))
            self.matrix.SwapOnVSync(offscreen_canvas)
            # collect first 5 images for saving gif
            if self.save_gif and len(gif) < 5:
                gif.append(temp)
            sleep(1)

        if self.save_gif:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH)
        
        self.matrix.Clear()
        print("> Exit display_scatter_fill")
