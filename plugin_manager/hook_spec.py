import pluggy
from PIL import Image

hookspec = pluggy.HookspecMarker("pixel_art")

class MySpec:
    """Pixel Art hook (plugin) specifications."""
    @hookspec
    def rgb_hook(self, path: str, image: Image, num: int):
        """RGB hook specification."""

    @hookspec
    def ai_hook(self, text: str, path: str, audio: list[int], task: dict):
        """AI hook specification."""

    @hookspec
    def game_hook(self):
        """Game hook specification."""
