from time import sleep, time
from random import randint
from pathlib import Path
from threading import Event
from queue import Queue

import pluggy
from PIL import Image, ImageSequence, ImageDraw, ImageFont
from rgbmatrix import graphics

from config.config import PluginConfig
from plugins.rgb_plugin import RGBPlugin, RGBEvents

hookimpl = pluggy.HookimplMarker("pixel_art")

class DisplayImagePlugins(RGBPlugin):
    """RGB plugin class. Contains plugins that draw pixel patterns randomly on the screen programatically."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"

    def __init__(self, matrix, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue):
        super().__init__(matrix, rgb_start_event, ai_end_event, ai_result_queue)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.save_gameplay = self.config.get_item("save_gameplay", False)
        self.image_display_time = self.config.get_item("image_display_time", 5)

    def loading(self, delay: int, color: tuple[int] = (255, 255, 255)):
        """Display "Loading" text on LED array screen.

        Args:
            delay (int): Delay in seconds before method exit
            color (tuple[int]): Text color. Defaults to (255, 255, 255).
        """
        # draw text
        img = Image.new("RGB", (self.matrix.width, self.matrix.height))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(f"{self.PLUGIN_ASSETS_PATH}/font/Tiny5-Regular.ttf", size=12)
        draw.text((9, 24), "Loading...", font=font, fill=color)

        # send image to screen
        self.matrix.SetImage(img)
        sleep(delay)
    
    def img_viewer(self, path: str, duration: int = 5):
        """View an image on LED array screen.\n
        Choose display time by setting `image_display_time` in plugin config.

        Args:
            path (str): Image path
            duration (int): Display time in seconds. Defaults to 5.
        """
        print(f"> Displaying image: {path}")
        with Image.open(path) as img:
            # send image to screen
            img.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
            self.matrix.SetImage(img.convert('RGB'))
            sleep(duration)

    def gif_viewer(self, path: str, default_duration_ms: float = 100, override_peak_duration_ms: float = 0):
        """View a GIF on LED array screen.

        Args:
            path (str): GIF path
            default_duration_ms (float, optional): Default pause between GIF frames in milliseconds. Defaults to 100.
            override_peak_duration_ms (float, optional): Override value for peak (median) frame in GIF. Defaults to 0.
        """
        # preprocess the gifs frames into canvases to improve playback performance
        canvases = [] # (canvas, duration_ms)
        with Image.open(path) as gif:
            print("> Preprocessing gif")
            for frame in ImageSequence.Iterator(gif):
                # must copy the frame out of the gif, since thumbnail() modifies the image in-place
                temp = frame.copy()
                temp.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
                canvas = self.matrix.CreateFrameCanvas()
                canvas.SetImage(temp.convert("RGB"))
                canvases.append((canvas, frame.info.get("duration", default_duration_ms)))

        # set peak (median) animation frame
        if override_peak_duration_ms:
            i_peak = len(canvases) // 2
            canvases[i_peak] = (canvases[i_peak][0], override_peak_duration_ms - 200)

        # loop through gif
        for i, frame in enumerate(canvases):
            # send frame to screen
            print(f"> Playing frame {i} for {frame[1]} ms")
            self.matrix.SwapOnVSync(frame[0], framerate_fraction=1)
            # sleep between gif frames
            sleep_seconds = frame[1] / 1_000
            sleep(sleep_seconds)
        print("> Done playing gif")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_image(self):
        """Display Image RGB plugin for displaying an image on the LED array screen.
        Shows loading text if waiting for image.
        """
        print("> Init display_image")
        while not self.ai_end_event.is_set():
            if not self.ai_result_queue.empty():
                # display image
                # path = "/opt/pixel-software/plugins/rgb/display_image/assets/examples/tree.png" # for testing
                path = self.ai_result_queue.get(block=True, timeout=3)
                self.img_viewer(path, self.image_display_time)
                self.matrix.Clear()
            else:
                # display loading screen
                self.loading(1)
                self.matrix.Clear()
        print("> Exit display_image")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_gif(self):
        """Display Image RGB plugin for displaying a GIF on the LED array screen.
        """
        print("> Init display_gif")
        while not self.ai_end_event.is_set():
            if not self.ai_result_queue.empty():
                # display GIF
                # path = "/opt/pixel-software/plugins/rgb/display_image/assets/examples/eyes.gif" # for testing
                path = self.ai_result_queue.get(block=True, timeout=3)
                self.gif_viewer(path)
                self.matrix.Clear()
            else:
                # display loading screen
                self.loading(1)
                self.matrix.Clear()
        print("> Exit display_gif")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_game(self):
        """Display Image RGB plugin for displaying games frames (images) on the LED array screen.\n
        This plugin consumes any frames sent in the `ai_result_queue` (e.g., frames from a game plugin).\n
        Save gameplay example as gif by setting `save_gameplay = true` in plugin config.
        """
        print("> Init display_game")
        FPS = 30
        gif = []

        # stream gameplay images to screen
        while not self.ai_end_event.is_set():
            if not self.ai_result_queue.empty():
                image = self.ai_result_queue.get(block=True, timeout=3)
                # print(f"> Displaying game image: {image.size}")
                image.thumbnail((self.matrix.width, self.matrix.height), Image.Resampling.LANCZOS)
                self.matrix.SetImage(image.convert('RGB'))
                # collect and save the first 5 seconds of gameplay
                if self.save_gameplay and len(gif) < 5 * FPS:
                    gif.append(image)
            sleep(.01)

        if self.save_gameplay:
            self.save_to_gif(gif, self.PLUGIN_ASSETS_PATH, "gameplay", 1000 // FPS)

        self.matrix.Clear()
        print("> Exit display_game")

    @hookimpl(specname="rgb_hook")
    @RGBEvents()
    def display_emotion_avatar(self):
        """Display Image RGB plugin for displaying an avatar's emotional expressions on the LED array screen.\n
        This plugin consumes any emotions sent in the `ai_result_queue` (e.g., "joy").
        """
        print("> Init display_emotion_avatar")
        AVATAR_ROOT = f"{self.PLUGIN_ASSETS_PATH}/avatar"
        DEFAULT_EMOTION = "neutral"
        emotions = {
            DEFAULT_EMOTION: f"{AVATAR_ROOT}/surprise.gif",
            "joy": f"{AVATAR_ROOT}/joy.gif",
            "anger": f"{AVATAR_ROOT}/anger.gif",
            "confusion": f"{AVATAR_ROOT}/confusion.gif",
            "fear": f"{AVATAR_ROOT}/fear.gif",
            "sadness": f"{AVATAR_ROOT}/sadness.gif",
            "surprise": f"{AVATAR_ROOT}/surprise.gif"
        }

        blink = lambda min_seconds, max_seconds: (time(), randint(min_seconds, max_seconds))
        blink_timer, blink_gap = blink(3, 10)
        sleep(1) # allow some time for AI plugin start

        # display base image
        self.img_viewer(f"{AVATAR_ROOT}/base.png", .1)

        while not self.ai_end_event.is_set():
            if not self.ai_result_queue.empty():
                # wait for emotion
                choice, duration_ms = self.ai_result_queue.get(block=True, timeout=3)
                print(f"> display_emotion_avatar gets emotion: {choice}")
                if choice == "think":
                    # display think image
                    self.img_viewer(f"{AVATAR_ROOT}/think.png", 1)
                    blink_timer, blink_gap = blink(15, 15)
                else:
                    # display emotion
                    self.gif_viewer(emotions.get(choice, DEFAULT_EMOTION), 50, duration_ms)
                    blink_timer, blink_gap = blink(3, 10)
            elif time() > blink_timer + blink_gap:
                # blink every random n seconds
                print("> Blinking...")
                self.gif_viewer(f"{AVATAR_ROOT}/blink.gif")
                blink_timer, blink_gap = blink(3, 10)
            sleep(.1)
        
        self.matrix.Clear()
        print("> Exit display_emotion_avatar")
