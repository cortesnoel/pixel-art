import os
import wave
import io
import struct
import functools
from time import time, sleep, perf_counter
from threading import Event, Thread
from queue import Queue

import numpy as np
from PIL import Image
import pygame
from openai import OpenAI

from plugins.ai_pico_plugin import AIPicoPlugin, PicoModels, PicoRecord, PicoEvents

#####################
# PLUGIN DECORATORS #
#####################

class AIGame:
    """Decorator to initialize a game plugin with pygame.\n
    Example use: `@AIGame()`\n
    Can optionally initialize a voice controller for your game. Options: "stt", "openai".\n
    Example use: `@AIGame(voice_controller="stt")`
    """
    def __init__(self, voice_controller: str = None):
        self.voice_controller = voice_controller
        self.voice_controller_thread = None
        self.control_end_event = None

    def __call__(self, func):
        @PicoEvents()
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            self.init_game(obj)
            self.init_voice_controller(obj)
            # call decorated func
            result = func(*args, **kwargs)
            self.terminate_voice_controller()
            pygame.quit()
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
    def init_game(self, decorated_self: object):
        """Initialize required pygame modules.

        Args:
            decorated_self (object): Game plugin object
        """
        # set SDL to use the dummy NULL video driver, so it doesn't need a windowing system
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.display.init()
        pygame.joystick.init()
        pygame.font.init()
        # init mixer w/ USB speaker
        pygame.mixer.init(devicename="UACDemoV1.0, USB Audio")
        # speakers = tuple(sdl2_audio.get_audio_device_names(0))
        # speaker = [s for s in speakers if "UACDemoV1.0" in s][0]
        # pygame.mixer.quit()
        # pygame.mixer.init(devicename=speaker)
        decorated_self.screen = pygame.display.set_mode((64, 64))
        decorated_self.clock = pygame.time.Clock()

    def init_voice_controller(self, decorated_self: object):
        """Initialize voice controller.

        Args:
            decorated_self (object): Game plugin object
        """
        if self.voice_controller == "stt":
            # run voice controller thread
            self.control_end_event = Event()
            self.voice_controller_thread = Thread(name="audio_thread", target=decorated_self.stt_voice_controller, args=(self.control_end_event,))
            self.voice_controller_thread.start()
            while not decorated_self.leopard:
                print("> Decorator 'AIGame' waiting for leopard model init...")
                sleep(1)
                continue
        elif self.voice_controller == "openai":
            # run voice controller thread
            self.control_end_event = Event()
            self.voice_controller_thread = Thread(name="audio_thread", target=decorated_self.whisper_voice_controller, args=(self.control_end_event,))
            self.voice_controller_thread.start()

    def terminate_voice_controller(self):
        """Terminate voice controller.
        """
        if self.voice_controller:
            # end voice controller thread
            self.control_end_event.set()
            self.voice_controller_thread.join()

#######################
# PLUGIN PARENT CLASS #
#######################

class GamePlugin(AIPicoPlugin):
    """Game parent plugin class. Should be extended by game plugins that want to integrate AI.

    Args:
        AIPicoPlugin (_type_): AI parent plugin class for Picovoice AI.
    """
    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        super().__init__(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
        self.screen: pygame.Surface = None
        self.clock: pygame.time.Clock = None
        # custom game events (TODO: use existing game events like CONTROLLERBUTTONUP?)
        self.UP_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.DOWN_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.LEFT_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.RIGHT_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.YES_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.NO_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.START_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.PAUSE_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.QUIT_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.CONTINUE_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.JUMP_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.SHOOT_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.TOUCH_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.TRADE_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.GRAB_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())
        self.DISCARD_VOICE_EVENT = pygame.event.Event(pygame.event.custom_type())

    def draw(self):
        """Pixel Art replacement of  `pygame.display.flip()`.
        Sends gameplay frames to rgb thread for rendering on LED array screen.
        """
        # RENDER YOUR GAME HERE
        # flip() the display to put your work on screen
        # pygame.display.flip()
        surf = pygame.display.get_surface()
        arr = pygame.surfarray.array3d(surf)
        arr = np.rot90(np.fliplr(arr)) # fix screen orientation
        # print(arr)
        img = Image.fromarray(arr)
        img.convert('RGB')
        self.ai_result_queue.put(img)

    def dispatch_game_event(self, voice_cmd: str):
        """Dispatch custom GamePlugin pygame events.

        Args:
            voice_cmd (str): Transcribed speech
        """
        print(f"---> voice_cmd: {voice_cmd}")
        match voice_cmd.lower():
            case "up":
                pygame.event.post(self.UP_VOICE_EVENT)
            case "down":
                pygame.event.post(self.DOWN_VOICE_EVENT)
            case "left":
                pygame.event.post(self.LEFT_VOICE_EVENT)
            case "right":
                pygame.event.post(self.RIGHT_VOICE_EVENT)
            case "yes":
                pygame.event.post(self.YES_VOICE_EVENT)
            case "no":
                pygame.event.post(self.NO_VOICE_EVENT)
            case "start":
                pygame.event.post(self.START_VOICE_EVENT)
            case "pause":
                pygame.event.post(self.PAUSE_VOICE_EVENT)
            case "quit":
                pygame.event.post(self.QUIT_VOICE_EVENT)
            case "continue":
                pygame.event.post(self.CONTINUE_VOICE_EVENT)
            case "jump":
                pygame.event.post(self.JUMP_VOICE_EVENT)
            case "shoot":
                pygame.event.post(self.SHOOT_VOICE_EVENT)
            case "touch":
                pygame.event.post(self.TOUCH_VOICE_EVENT)
            case "trade":
                pygame.event.post(self.TRADE_VOICE_EVENT)
            case "grab":
                pygame.event.post(self.GRAB_VOICE_EVENT)
            case "discard":
                pygame.event.post(self.DISCARD_VOICE_EVENT)

    @PicoModels(models=["rhino"])
    @PicoRecord()
    def sti_voice_controller(self, up_event, end: Event):
        """Voice controller using Picovoice rhino model for speech-to-intent.
        Note: Not as fast as stt_voice_controller.

        Args:
            end (Event): Event that ends loop
        """
        # TODO: WIP, refactor and test.
        print("> Init sti_voice_controller")
        while not end.is_set():
            audio_frame = self.recorder.read()
            is_finalized = self.rhino.process(audio_frame)
            if is_finalized:
                inference = self.rhino.get_inference()
                if inference.is_understood:
                    # print(f"> Found task: {inference.intent}")
                    # print(f"> Task slots: {inference.slots}")
                    pygame.event.post(up_event)
        print(f"> Exit: sti_voice_controller")

    @PicoModels(models=["cobra", "leopard"])
    @PicoRecord()
    def stt_voice_controller(self, end: Event):
        """Voice controller using Picovoice leopard model for speech-to-text.

        Args:
            end (Event): Event that ends loop
        """
        # TODO: WIP, refactor and test.
        print("> Init stt_voice_controller")
        while not end.is_set():
            asr_recording = []
            while len(asr_recording) < 512 * 50: # cmds transcribed as 512 * n batched frames
                audio_frame = self.recorder.read()
                if self.cobra.process(audio_frame) < 0.001:
                    continue
                asr_recording.extend(audio_frame)
            voice_cmd, _ = self.leopard.process(asr_recording)
            if voice_cmd:
                print(f"voice_cmd: {voice_cmd}")
                self.dispatch_game_event(voice_cmd)
        print(f"> Exit: stt_voice_controller")

    @PicoModels(models=["cobra"])
    @PicoRecord()
    def whisper_voice_controller(self, end: Event):
        """Voice controller using an OpenAI API transcription model.
        Note: OpenAI Transcriptions API whisper model latency ranges .5-3s.

        Args:
            end (Event): Event that ends loop
        """
        # TODO: WIP, refactor and test.
        print("> Init whisper_voice_controller")
        client = OpenAI()
        while not end.is_set():
            # collect audio
            frames = []
            while len(frames) < 512 * 10: # cmds transcribed as 512 * n batched frames
                audio_frame = self.recorder.read()
                if self.cobra.process(audio_frame) < 0.2:
                    continue
                frames.extend(audio_frame)
            # audio_frame = self.recorder.read()
            # if self.cobra.process(audio_frame) > 0.2:
            #     for _ in range(0, int(self.recorder.sample_rate // self.recorder.frame_length * 1)): # approx. 1 second loop
            #       frames.extend(self.recorder.read())
            if len(frames) > self.recorder.frame_length * 5:
                # format audio to wav
                wav_buffer = io.BytesIO()
                wav_buffer.name = "rec.wav"
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2) # 2 bytes
                    wf.setframerate(self.recorder.sample_rate)
                    wf.writeframes(struct.pack("h" * len(frames), *frames))
                # send audio to openai
                t1 = perf_counter()
                voice_cmd = client.audio.transcriptions.create(
                    model="whisper-1", # whisper-1 higher WER but gpt transcribe models too slow >2s
                    prompt="Transcribe speech. Only respond with a single choice from the following list: up, down, left, right, yes, no, start, pause, quit, continue, jump, shoot, touch, trade, grab, discard",
                    file=wav_buffer,
                    language="en",
                    response_format="text",
                    temperature=0.5
                )
                print(f"> Total inference time: {(perf_counter() - t1):.3f}s")
                # dispatch game event
                if voice_cmd:
                    self.dispatch_game_event(voice_cmd)  
            # sleep(.1)
        print("> Exit whisper_voice_controller")
