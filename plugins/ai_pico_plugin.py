from time import time, perf_counter
from datetime import datetime
import functools
from threading import Event
from queue import Queue

import pvcobra
import pvporcupine
import pvleopard
import pvrhino
import pvorca
from pvrecorder import PvRecorder
from pvspeaker import PvSpeaker

from config.config import get_env
from util.audio_util import init_recorder, init_speaker

#####################
# PLUGIN DECORATORS #
#####################

class PicoRecord:
    """Decorator to automatically start recording audio.\n
    Decorated function can read audio with `self.recorder.read()`.\n
    Example use: `@PicoRecord()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            if not obj.recorder:
                obj.recorder = init_recorder()
            obj.recorder.start()
            # call decorated func
            result = func(*args, **kwargs)
            obj.recorder.stop()
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper

class PicoSpeaker:
    """Decorator to automatically start the speaker.\n
    Decorated function can write audio to the speaker with `self.speaker.write(audio)`.\n
    Example use: `@PicoSpeaker()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            if not obj.speaker:
                obj.speaker = init_speaker()
            obj.speaker.start()
            # call decorated func
            result = func(*args, **kwargs)
            obj.speaker.flush()
            obj.speaker.stop()
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class PicoEventStart:
    """Decorator for AI start event. Synchronizes the start of an AI plugin
    with the start of it's corresponding RGB plugin.\n
    Example use: `@PicoEventStart()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            if obj.terminate_thread.is_set():
                raise Exception("ai thread interrupted")
            obj.rgb_start_event.wait() # comment when testing ai only
            obj.rgb_start_event.clear() # acknowledged and cleared
            # call decorated func
            result = func(*args, **kwargs)
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class PicoEventEnd:
    """Decorator for AI end event. Synchronizes the end of an AI plugin
    with the end of it's corresponding RGB plugin.\n
    Example use: `@PicoEventEnd()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            if obj.terminate_thread.is_set():
                raise Exception("ai thread interrupted")
            # call decorated func
            result = func(*args, **kwargs)
            obj.ai_end_event.set()
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class PicoEvents:
    """Decorator for both AI start and end events. Synchronizes an AI plugin
    with it's corresponding RGB plugin.\n
    Example use: `@PicoEvents()`
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def __call__(self, func):
        @PicoEventStart()
        @PicoEventEnd()
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            # call decorated func
            result = func(*args, **kwargs)
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
class PicoModels:
    """Decorator for initializing different Picovoice AI models.
    Once initialized, use models as plugin member variables: `self.leopard.version`.\n
    Supported models: cobra, leopard, orca, porcupine, rhino.\n
    Example use: `@PicoModels(models = ["leopard"])`
    """
    def __init__(self, models: list[str]):
        self.models = models

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"Before {self.__class__.__name__}")
            obj = args[0]
            self.standup_models(obj, self.models)#args[1])
            # call decorated func
            result = func(*args, **kwargs)
            self.cleanup_models(obj, self.models)#args[1])
            print(f"After {self.__class__.__name__}")
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper
    
    def standup_models(self, decorated_self: object, models: list[str]):
        """Initialize specified Picovoice models."""
        if "orca" in models:
            decorated_self.orca = pvorca.create(access_key=decorated_self.PICOVOICE_TOKEN)
        if "cobra" in models:
            decorated_self.cobra = pvcobra.create(access_key=decorated_self.PICOVOICE_TOKEN)
        if "porcupine" in models:
            decorated_self.porcupine = pvporcupine.create(
                access_key=decorated_self.PICOVOICE_TOKEN,
                keyword_paths=["models/pico/wake/wake-word_v3_0_0.ppn"]
            )
        if "leopard" in models:
            print("> Loading ASR model...")
            decorated_self.leopard = pvleopard.create(
                access_key=decorated_self.PICOVOICE_TOKEN,
                model_path="models/pico/asr/speech-to-text_v2.0.0_04-12-25.pv"
            )
            print("> ASR model loaded.")
        if "rhino" in models:
            decorated_self.rhino = pvrhino.create(
                access_key=decorated_self.PICOVOICE_TOKEN,
                context_path="models/pico/intent/speech-to-intent_v3_0_0.rhn"
            )

    def cleanup_models(self, decorated_self: object, models: list[str]):
        """Delete initialized Picovoice models."""
        if "orca" in models:
            decorated_self.orca.delete()
        if "cobra" in models:
            decorated_self.cobra.delete()
        if "porcupine" in models:
            decorated_self.porcupine.delete()
        if "leopard" in models:
            decorated_self.leopard.delete()
        if "rhino" in models:
            decorated_self.rhino.delete()

class PicoAI:
    """Decorator that wraps `PicoEvents`, `PicoModels`, `PicoRecord`, and `PicoSpeaker`.
    Use as an easy short-hand to all previously listed decorators.\n
    Example use: `@PicoAI(models = ["leopard"])`
    """
    def __init__(self, models: list[str]):
        self.models = models

    def __call__(self, func):
        @PicoModels(self.models)
        @PicoEvents()
        @PicoRecord()
        @PicoSpeaker()
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

class AIPicoPlugin():
    """AI parent plugin class. Should be extended by plugins that want to use Picovoice models."""
    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        self.PICOVOICE_TOKEN = get_env("PICOVOICE_TOKEN")
        self.rgb_start_event = rgb_start_event
        self.ai_end_event = ai_end_event
        self.ai_result_queue = ai_result_queue
        self.terminate_thread = terminate_thread
        self.orca: pvorca.Orca = None
        self.cobra: pvcobra.Cobra = None
        self.porcupine: pvporcupine.Porcupine = None
        self.leopard: pvleopard.Leopard = None
        self.rhino: pvrhino.Rhino = None
        self.recorder: PvRecorder = None
        self.speaker: PvSpeaker = None

    @PicoModels(models = ["cobra"])
    @PicoRecord()
    def record_speech(self, record_time: int = 10) -> list[int]:        
        """Records speech from microphone.

        Args:
            record_time (int, optional): Recording time in seconds. Defaults to 10.

        Returns:
            list[int]: Audio buffer with format pcm c_int16, 
                single channel, 16kHz frame rate
        """
        print("> Recording speech...")
        asr_recording = []
        
        end = time() + record_time
        while not self.terminate_thread.is_set() and time() < end:
            audio_frame = self.recorder.read()
            voice_probability = self.cobra.process(audio_frame)
            if voice_probability > 0.005:
                # print(f"> Voice detected: {voice_probability}")
                asr_recording.extend(audio_frame)

        if asr_recording:
            print(f"> Captured recording of frame length: {len(asr_recording)}")
        else:
            print("> Error in record_speech(): recording not captured and is empty")
        return asr_recording
    
    @PicoModels(models = ["orca"])
    @PicoSpeaker()
    def text_to_speech(self, text: str, save_path: str = None) -> list[int]:
        """Converts text to speech audio (TTS)

        Args:
            text (str): Text to convert
            save_path (str, optional): Path to save audio. Can be parent path or also include filename. Defaults to None.

        Returns:
            list[int]: Audio buffer with format pcm c_int16, 
                single channel, 16kHz frame rate
        """
        pcm, _ = self.orca.synthesize(text=text, speech_rate=0.8)
        if save_path:
            out = f"{save_path}/{datetime.now().strftime('%H-%M-%S')}.wav" if not save_path.endswith(".wav") else save_path
            self.speaker.write_to_file(out)        
        self.speaker.write(pcm)
        self.speaker.flush()
        return pcm
    
    @PicoModels(models = ["cobra", "porcupine"])
    @PicoRecord()
    def listen_for_wake(self):
        """Listens for wake phrase: 'Hey Pixel Art'.

        Raises:
            Exception: Thread termination event
        """
        print("> Listening for wake word...")
        while True:
            if self.terminate_thread.is_set():
                raise Exception("Thread terminated in listen_for_wake().")
            audio_frame = self.recorder.read()
            voice_probability = self.cobra.process(audio_frame)
            if voice_probability < 0.01:
                continue
            # print(f"> Voice detected: {voice_probability}")
            keyword_index = self.porcupine.process(audio_frame)
            if keyword_index == 0:
                print("> Wake word detected!")
                break

    @PicoModels(models = ["leopard"])
    def speech_recognition(self, audio: list[int]) -> str:
        """Transcribes speech audio to text (STT).

        Args:
            audio (list[int]): Audio buffer with format pcm c_int16, 
                single channel, 16kHz frame rate
                (Picovoice Recorder default format)

        Returns:
            str: Speech transcription
        """
        print("> Transcribing audio...")
        if audio:
            start = perf_counter()
            transcript, _ = self.leopard.process(audio)
            print(f"> ASR inference time: {(perf_counter() - start):.3f}s")
            
            print(f"> Transcription: {transcript}")
            return transcript.lower().strip()
        else:
            print("> Error in speech_recognition(): no audio given")
            return ""
