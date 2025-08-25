from pathlib import Path
from threading import Event
from queue import Queue

import pluggy

from config.config import PluginConfig
from plugins.game_plugin import pygame, GamePlugin, AIGame

hookimpl = pluggy.HookimplMarker("pixel_art")

class BasicGame(GamePlugin):
    """Basic game plugin class and example of using the AIGame voice_controller."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"

    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        super().__init__(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.runtime = self.config.get_item("runtime", 15)
    
    @hookimpl(specname="game_hook")
    @AIGame(voice_controller="stt")
    def play(self):
        """Plugin game loop that moves a pixel on screen based on directional voice events.
        Say 'quit' to end game early.
        """
        FPS = 30
        x = 32
        y = 32
        # run game for `runtime` seconds
        for _ in range(FPS * self.runtime):
            self.screen.fill("blue")
            color = "red"

            # poll for events
            for event in pygame.event.get():
                if event.type == self.UP_VOICE_EVENT.type:
                    print("---> cmd: up")
                    y -= 2
                elif event.type == self.DOWN_VOICE_EVENT.type:
                    print("---> cmd: down")
                    y += 2
                elif event.type == self.LEFT_VOICE_EVENT.type:
                    print("---> cmd: left")
                    x -= 2
                elif event.type == self.RIGHT_VOICE_EVENT.type:
                    print("---> cmd: right")
                    x += 2
                elif event.type == self.QUIT_VOICE_EVENT.type:
                    print("---> cmd: quit")

            self.screen.set_at([x, y], color)
            self.draw() # replaces flip()
            self.clock.tick(FPS)
