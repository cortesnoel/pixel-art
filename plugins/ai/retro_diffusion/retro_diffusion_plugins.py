import os
import base64
import re
from time import time, sleep
from pathlib import Path
from threading import Event
from queue import Queue

import requests
import pluggy

from config.config import PluginConfig, get_env
from plugins.ai_pico_plugin import AIPicoPlugin, PicoAI, PicoEvents

hookimpl = pluggy.HookimplMarker("pixel_art")

class RetroDiffusionPlugins(AIPicoPlugin):
    """Retro Diffusion plugin class. Contains multiple plugins including generating an image from text."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"
    
    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        super().__init__(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.model = self.config.get_item("model", "RD_FLUX")
        self.style = self.config.get_item("style", "detailed")
        self.record_time = self.config.get_item("record_time", 10)
        self.RETRO_DIFFUSION_TOKEN = get_env('RETRO_DIFFUSION_TOKEN')

    def generate_image(self, prompt: str) -> str:
        """Generate an image using Retro Diffusion API and saves to `assets/response`.

        Args:
            prompt (str): Image description

        Returns:
            str: Path of generated image
        """
        print(f"> Generating 64x64 pixel image for prompt: {prompt}")
        base_path = f"{self.PLUGIN_ASSETS_PATH}/response"
        os.makedirs(base_path, exist_ok=True)
        out_path = f"{base_path}/{re.sub('[ -.,!?;:]', '_', prompt.strip())}_{self.style}.png"
        out_path = re.sub("_+", '_', out_path)
        
        method = "POST"
        url = "https://api.retrodiffusion.ai/v1/inferences"
        headers = {
            "X-RD-Token": self.RETRO_DIFFUSION_TOKEN,
        }
        payload = {
            "prompt": prompt,
            "prompt_style": self.style,
            "model": self.model,
            "width": 64,
            "height": 64,
            "num_images": 1,
            "num_inference_steps": 20
        }

        response = requests.request(method, url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # data['base64_images'] is a list of base64-encoded image strings
            base64_images = data.get("base64_images", [])
            if base64_images:
                img_data = base64_images[0]
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"> Image generated and saved to {out_path}")
                return out_path
            else:
                print("> No images returned by the API.")
        else:
            print(f"> Request failed with status code {response.status_code}: {response.text}")

    @hookimpl(specname="ai_hook")
    @PicoAI(models = ["orca"])
    def rd_test_simple_wait(self):
        """Simple test plugin for debugging Pixel Art.
        """
        print(f"> simple_wait() start.")
        print(f"---> Orca model version: {self.orca.version} / Time: {time()}")
        sleep(5)
        print(f"> simple_wait() done.")

    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def rd_test_return_img_path_to_main_thread(self):
        """Simple test plugin for debugging Pixel Art's AI plugin result queue.
        """
        print(f"> test_return_img_path_to_main_thread() start.")
        sleep(3)
        self.ai_result_queue.put(f"{self.PLUGIN_ASSETS_PATH}/examples/chimpanzee_swimming_detailed.png")
        print(f"> test_return_img_path_to_main_thread() done.")
    
    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def rd_wake(self):
        """Retro Diffusion wake word plugin. Listens for wake phrase "Hey Pixel Art" using Picovoice.
        """
        self.text_to_speech("Listening for wake word")
        self.listen_for_wake()
        self.text_to_speech("Hey there! Let's use AI to create new pixel art!")

    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def rd_speech_to_text(self) -> str:
        """Retro Diffusion speech-to-text (STT) plugin. Converts speech audio to text using Picovoice.

        Returns:
            str: Transcript of speech
        """
        self.text_to_speech("What image should we create?")
        
        recording = self.record_speech(self.record_time)
        transcript = self.speech_recognition(recording)
        pattern = re.compile(r"(?:please)?\s*(draw|create|paint)\s(?:me )?(?:an )?(?:a )?")
        sanitized_transcript = re.sub(pattern, "", transcript).strip()

        self.text_to_speech(f"Oh cool! {sanitized_transcript}")
        return sanitized_transcript
    
    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def rd_text_to_image(self, text: str) -> str:
        """Retro Diffusion text-to-image plugin. Generates an image from description text using Retro Diffusion.

        Args:
            text (str): Description of image

        Returns:
            str: Image path
        """
        self.text_to_speech("Creating pixel art now")
        img_path = self.generate_image(text)

        self.ai_result_queue.put(img_path)
        sleep(5) # allow time for RGB plugin to display image
        return img_path
