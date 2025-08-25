import os
import functools
from datetime import datetime
from pathlib import Path
from threading import Event
from queue import Queue

import cv2
import numpy as np
from PIL import Image

#####################
# PLUGIN DECORATORS #
#####################

class RGBEventStart:
    """Decorator for RGB start event. Synchronizes the start of an RGB plugin
    with the start of it's corresponding AI plugin.\n
    Example use: `@RGBEventStart()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            obj.rgb_start_event.set()
            # call decorated func
            result = func(*args, **kwargs)
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class RGBEventEnd:
    """Decorator for RGB end event. Synchronizes the end of an RGB plugin
    with the end of it's corresponding AI plugin.\n
    Example use: `@RGBEventEnd()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            # call decorated func
            result = func(*args, **kwargs)
            obj.ai_end_event.clear() # acknowledged and cleared
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class RGBEvents:
    """Decorator for both RGB start and end events. Synchronizes an RGB plugin
    with it's corresponding AI plugin.\n
    Example use: `@RGBEvents()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        @RGBEventStart()
        @RGBEventEnd()
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            # call decorated func
            result = func(*args, **kwargs)
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper

#######################
# PLUGIN PARENT CLASS #
#######################

class RGBPlugin():
    """RGB parent plugin class. Should be extended by RGB plugins that want to integrate draw to LED array screen.
    """
    def __init__(self, matrix, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue):
        self.matrix = matrix
        self.rgb_start_event = rgb_start_event
        self.ai_end_event = ai_end_event
        self.ai_result_queue = ai_result_queue

    def save_to_gif(self, images: list[Image.Image], base_path: Path, filename: str = "out", duration: int = 1000):
        """Save images as a new GIF file.

        Args:
            images (list[Image.Image]): Images included in GIF
            base_path (Path): GIF output base path
            filename (str, optional): GIF output filename. Defaults to "out".
            duration (int, optional): GIF delay between frames in milliseconds. Defaults to 1000.
        """
        d = datetime.now()
        out_path = base_path / f"response/{d.strftime('%Y-%m-%d')}"
        os.makedirs(out_path, exist_ok=True)

        # save gif
        images[0].save(
            out_path / f"{filename}_{d.strftime('%I-%M-%S%p')}.gif",
            save_all = True,
            append_images = images[1:],
            duration = duration,  # ms
            loop = 0  # infinite loop
        )

    def save_to_mp4(self, images: list[Image.Image], base_path: Path, filename: str = "out"):
        """Save images as a new MP4 file.

        Args:
            images (list[Image.Image]): Images included in MP4
            base_path (Path): MP4 output base path
            filename (str, optional): MP4 output filename. Defaults to "out".
        """
        d = datetime.now()
        out_path = base_path / f"response/{d.strftime('%Y-%m-%d')}"
        os.makedirs(out_path, exist_ok=True)

        out_path = out_path / f"{filename}_{d.strftime('%I-%M-%S%p')}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # mp4 codec
        video = cv2.VideoWriter(out_path, fourcc, 30, (64, 64))

        # save mp4
        for img in images:
            img_arr = np.array(img, dtype=np.uint8)
            frame = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            video.write(frame)

        video.release()
        cv2.destroyAllWindows()
