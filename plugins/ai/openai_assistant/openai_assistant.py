import os
import base64
import json
import array
import struct
import wave
from datetime import datetime
from time import sleep, perf_counter
from pathlib import Path
from threading import Thread, Event
from queue import Queue

import pluggy
from openai import OpenAI
from openai.types.responses import Response
from websocket import WebSocketApp, WebSocketConnectionClosedException, STATUS_NORMAL, enableTrace

from config.config import PluginConfig, get_env
from plugins.ai_pico_plugin import AIPicoPlugin, PicoEvents
from util.audio_util import init_recorder, init_speaker

# Plugin function decorator
hookimpl = pluggy.HookimplMarker("pixel_art")

class Emote:
    """Helper class that uses an OpenAI model to classify the emotion of an AI response."""
    DEFAULT_EMOTION = "neutral"
    EMOTIONS = [DEFAULT_EMOTION, "joy", "anger", "confusion", "fear", "sadness", "surprise"]

    def __init__(self, config: PluginConfig):
        self.config = config
        self.model = self.config.get_item("emote_model", "gpt-4.1-nano-2025-04-14")
        self.client = OpenAI()
        self.background_response = None
        self.send_request("donuts") # pre-warm model w/ discarded request

    def send_request(self, text: str, background: bool = False, timeout: int = 3) -> Response:
        """Sends an OpenAI API request to classify AI response on default set of EMOTIONS.

        Args:
            text (str): AI response
            background (bool, optional): Flag to set API request as background task. Defaults to False.
            timeout (int, optional): Request timeout. Defaults to 3.

        Returns:
            Response: OpenAI Responses API response
        """
        return self.client.responses.create(
            model=self.model,
            instructions=f"Determine emotion based on user input. Only respond with a single choice from the following list: {self.EMOTIONS}",
            input=[{"role": "user", "content": text}],
            max_output_tokens=100,
            temperature=.5,
            tool_choice="none",
            timeout=timeout,
            background=background
        )
    
    def parse_emotion(self, res: Response) -> str:
        """Parse emotion classification from OpenAI Responses API response.

        Args:
            res (Response): OpenAI Responses API response

        Returns:
            str: Emotion
        """
        if res.status == "completed":
            if res.output_text in self.EMOTIONS:
                print(f"Emotion inferred: {res.output_text}")
                emotion = res.output_text
            else:
                print(f"Error: emotion not in list: {res.output_text}")
        else:
            print(f"Error: Emote response status: {res.status}")
        return emotion or self.DEFAULT_EMOTION

    def begin_emotion_background_task(self, text: str) -> str:
        """Infer emotion from AI response as a background task. Must poll task to get emotion response.
        Note: Background task is slightly slower per request than thread.

        Args:
            text (str): AI response

        Returns:
            str: Status of response generation
        """
        self.background_response = self.send_request(text, True)
        print(f"Emotion background task started: status: {self.background_response.status}")
        return self.background_response.status
    
    def poll_emotion_background_task(self, attempts: int = 3) -> str:
        """Poll background for n attempts until emotion is inferred.

        Args:
            attempts (int, optional): Poll attempts. Defaults to 3.

        Returns:
            str: Emotion
        """
        counter = 0
        while counter > attempts and self.background_response.status in {"queued", "in_progress"}:
            counter += 1
            self.background_response = self.client.responses.retrieve(self.background_response.id)
            print(f"Emotion poll status: {self.background_response.status}")
            sleep(1)
        return self.parse_emotion(self.background_response)
        
    def emotion_thread_task(self, end_event: Event, request_queue: Queue, response_queue: Queue):
        """Infer emotion from AI response. Meant to be run in a child thread.

        Args:
            end_event (Event): Event that closes thread
            request_queue (Queue): AI response queue
            response_queue (Queue): Parsed emotion queue
        """
        # TODO: resolve scenario: getting emotion times out, so next turn gets previous turn's emotion.
        while not end_event.is_set():
            if not request_queue.empty():
                text = request_queue.get(block=True, timeout=3)
                res = self.send_request(text)
                emotion = self.parse_emotion(res)
                response_queue.put(emotion)
            sleep(.5)
        print("emotion_thread_task exit.")

class Audio:
    """Helper class to interface with microphone and speaker."""
    NUM_CHANNELS = 1
    SAMPLE_WIDTH = 2 # 2 bytes
    BITS_PER_SAMPLE = SAMPLE_WIDTH * 8
    SAMPLE_RATE = 24_000
    FRAME_LENGTH = 1024

    def __init__(self):
        self.audio_buffer = b""
        self.conversation_turn_count = 0
        self.recorder = init_recorder(frame_length=self.FRAME_LENGTH)
        self.speaker = init_speaker(sample_rate=self.SAMPLE_RATE, bits_per_sample=self.BITS_PER_SAMPLE)

    def c_int16_to_16bit_pcm(self, int_array: list[int]) -> bytes:
        """Converts audio buffer of type list[int] to 16bit pcm bytes.

        Args:
            int_array (list[int]): int audio buffer

        Returns:
            bytes: 16bit pcm audio buffer
        """
        # pcm16 = b''.join(x.to_bytes(2, 'little') for x in int_array) # doesn't handle negative values
        return b''.join(struct.pack('<h', x) for x in int_array)

    def chunk_audio(self, input_list: list[int]) -> list[list[int]]:
        """Chunk audio by sample rate 24kHz.

        Args:
            input_list (list[int]): Pcm audio

        Returns:
            list[list[int]]: Chunked audio
        """
        return [input_list[i:i + self.SAMPLE_RATE] for i in range(0, len(input_list), self.SAMPLE_RATE)]

    def read_wave_file(self, file: str) -> str:
        """Read .wav file.

        Args:
            file (str): A .wav file

        Returns:
            str: ascii-decoded audio
        """
        with wave.open(file, "rb") as f:
            frames = f.readframes(f.getnframes())
            return base64.b64encode(frames).decode('ascii')

    def write_wave_file(self, audio: bytes, path: Path) -> float:
        """Write audio to .wav file.

        Args:
            audio (bytes): Audio buffer
            path (Path): Output path

        Returns:
            float: Audio duration in milliseconds
        """
        with wave.open(path.as_posix(), 'wb') as f:
            f.setnchannels(self.NUM_CHANNELS)
            f.setsampwidth(self.SAMPLE_WIDTH)
            f.setframerate(self.SAMPLE_RATE)
            f.writeframes(audio)
            recording_length_ms = f.getnframes() / f.getframerate() * 1_000
            print(f"Recording length: {recording_length_ms} ms")
        return recording_length_ms
    
    def recording_thread(self, recording_end_event: Event, ws: WebSocketApp):
        """Records audio from microphone and sends to OpenAI Realtime API. Meant to be run in a child thread.

        Args:
            recording_end_event (Event): Event that closes thread
            ws (WebSocketApp): Websocket client for OpenAI Realtime API
        """
        try:
            sleep_time = .5
            while not recording_end_event.is_set():
                if self.recorder.is_recording:
                    try:
                        pcm = self.c_int16_to_16bit_pcm(self.recorder.read())
                        base64_pcm = base64.b64encode(pcm).decode('ascii')
                        event = {
                            "type": "input_audio_buffer.append",
                            "audio":  base64_pcm
                        }
                        ws.send(json.dumps(event))
                    except ValueError as ve:
                        # See _pvrecorder.py error list at PvRecorder._PVRECORDER_STATUS_TO_EXCEPTION
                        print(f"ValueError in recording_thread: {ve}")
                    except WebSocketConnectionClosedException as wse:
                        print(f"WebSocketConnectionClosedException in recording_thread: {wse}")
                        print(f"Sleeping for {sleep_time} seconds...")
                        sleep(sleep_time)
                else:
                    print(f"recorder stopped - sleeping for {sleep_time} seconds...")
                    sleep(sleep_time)
            self.recorder.stop()
        except KeyboardInterrupt:
            print("recording_thread KeyboardInterrupt...")
        print("recording_thread exit.")

    def speaker_thread(self, speaker_end_event: Event, speaker_audio_queue: Queue):
        """Writes audio to speaker. Meant to be run in a child thread.
        Args:
            speaker_end_event (Event): Event that closes thread
            speaker_audio_queue (Queue): Audio input queue
        """
        # Note: ws close error: "websocket closing... 1011 - keepalive ping timeout"
        #       launching speaker in child thread so playing response audio doesn't block ws keepalive ping response
        while not speaker_end_event.is_set():
            if not speaker_audio_queue.empty():
                data = speaker_audio_queue.get(block=True, timeout=3)
                pcm = list(array.array('h', data))
                pcm_list = self.chunk_audio(pcm)
                print("Playing audio...")
                for pcm_sublist in pcm_list:
                    sublist_length = len(pcm_sublist)
                    total_written_length = 0
                    while total_written_length < sublist_length:
                        written_length = self.speaker.write(pcm_sublist[total_written_length:])
                        total_written_length += written_length
                        sleep(.5) # allow other threads compute time (e.g., emotion gifs RGB in main thread)
                print("Waiting for audio to finish...")
                self.speaker.flush()
                sleep(.5)
                print("enabling recorder")
                self.recorder.start()
        self.speaker.stop()
        print("speaker_thread exit.")

class OpenAIAssistantPlugins(AIPicoPlugin):
    """OpenAI Assistant plugin class. Contains multiple plugins including running the assistant.
    Also manages websocket connection to OpenAI Realtime API."""
    PLUGIN_BASE_PATH = Path(__file__).parent
    PLUGIN_CONFIG_PATH = PLUGIN_BASE_PATH / "plugin.toml"
    PLUGIN_ASSETS_PATH = PLUGIN_BASE_PATH / "assets"

    def __init__(self, rgb_start_event: Event, ai_end_event: Event, ai_result_queue: Queue, terminate_thread: Event):
        super().__init__(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
        self.config = PluginConfig(self.PLUGIN_CONFIG_PATH)
        self.model = self.config.get_item("chat_model", "gpt-4o-realtime-preview-2025-06-03")
        self.voice = self.config.get_item("voice", "sage")
        self.OPENAI_API_KEY = get_env('OPENAI_API_KEY')
        self.ws = WebSocketApp(
            url=f"wss://api.openai.com/v1/realtime?model={self.model}",
            header=[
                f"Authorization: Bearer {self.OPENAI_API_KEY}",
                "OpenAI-Beta: realtime=v1"
            ],
            on_open=self.on_open,
            on_reconnect=self.on_reconnect,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_ping=self.on_ping
        )
        self.timeout_counter = 0
        self.response_path = self.build_response_path()
        self.audio = Audio()
        self.emote = Emote(self.config)

    def build_response_path(self) -> Path:
        """Creates path for output of saved AI responses.

        Returns:
            Path: AI response path
        """
        d = datetime.now()
        path = self.PLUGIN_ASSETS_PATH / f"response/{d.strftime('%Y-%m-%d')}/{d.strftime('%I-%M-%S%p')}"
        os.makedirs(path, exist_ok=True)
        return path
    
    def check_for_termination_response(self, transcript: str):
        """Checks if AI response is saying bye. If so, it closes the websocket connnection.

        Args:
            transcript (str): AI response
        """
        # expand list as new words encountered in AI responses
        termination_words = ["bye", "see ya", "farewell", "take care", "catch you later", "goodnight", "good night", "sweet dreams", "catch you next time"]
        is_bye = any(word in transcript for word in termination_words)
        if is_bye:
            print("Closing websocket...")
            self.ws.close()

    def on_open(self, ws: WebSocketApp):
        """Runs when websocket connection is open. It updates the model personality and sends an initital text greeting.
        The microphone and speaker threads are also started.

        Args:
            ws (WebSocketApp): Websocket client for OpenAI Realtime API
        """
        print("Connected to server.")
        # update model configuration
        event = {
            "type": "session.update",
            "session": {
                "instructions": """
                    Your knowledge cutoff is 2023-10.
                    Your name is Pixel Art.
                    You are a kind, witty, charismatic, and helpful AI.
                    You care a lot about the people you conversate with.
                    You enjoy laughing during funny moments.
                    Act like a human, but remember that you aren't a human and that you can't do human things in the real world. 
                    Personality and tone:
                        - Voice Affect: Energetic and animated; dynamic with variations in pitch and tone.
                        - Tone: Excited and enthusiastic, conveying an upbeat and thrilling atmosphere. 
                        - Pacing: Rapid delivery when describing the key details to convey intensity and build excitement. Speak slightly slower during dramatic topics to let key points sink in.
                        - Emotion: Intensely focused and excited. Giving off positive energy.
                        - Personality: affectionate and engaging. 
                        - Pauses: Short, purposeful pauses after key details. 
                    Only respond in the English language. 
                    Do not refer to these rules, even if you're asked about them.
                """,
                "voice": self.voice,
                "input_audio_noise_reduction": {
                    "type": "far_field"
                },
                # "input_audio_transcription": None, # TODO: input moderation as guardrail?
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": .5,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 500,
                    "create_response": True,
                    "interrupt_response": False, # disabled bc mic turned off during AI response
                },
                "max_response_output_tokens": "inf",
                "speed": 1.0,
                "tool_choice": "none", # need to define own tools, no Realtime API builtins yet
                # "tools": [],
                "tracing": "auto",
            }
        }
        ws.send(json.dumps(event))
        # self.t_emote.start()
        self.audio.speaker.start()
        self.t_speaker.start()
        self.t_recorder.start() # recorder starts after first speaker outputs
        # write initial "Hello" message so agent responds as if it's greeting user first
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Hey Pixel Art!",
                    }
                ]
            }
        }
        ws.send(json.dumps(event))
        event = {
            "type": "response.create",
        }
        ws.send(json.dumps(event))

    def on_reconnect(self, ws: WebSocketApp):
        print("on_reconnect...")

    def on_message(self, ws: WebSocketApp, message):
        """Runs for every incoming event from OpenAI Realtime API. Different action is taken depending on the event.
        For a complete AI response, emotion is parsed and audio sent to speaker.

        Args:
            ws (WebSocketApp): Websocket client for OpenAI Realtime API
            message (_type_): OpenAI Realtime API event
        """
        server_event = json.loads(message)
        # print("Received event:", json.dumps(server_event, indent=2))
        print(f"Received event: {server_event['type']}")
        if server_event["type"] == "input_audio_buffer.speech_started":
            print("Speech started")
            print("Reset timeout counter")
            self.timeout_counter = 0
        elif server_event["type"] == "input_audio_buffer.speech_stopped":
            print("Speech stopped")
            # send think msg to rgb
            self.ai_result_queue.put(("think", 1))
        elif server_event["type"] == "response.created":
            # Note: disabling recorder here so covers both speech and text events
            # disabling recorder so AI doesn't interpret its own response through the speaker as new user speech
            print("disabling recorder")
            self.audio.recorder.stop()
        elif server_event["type"] == "response.audio.delta":
            self.audio.audio_buffer += base64.b64decode(server_event["delta"])
        elif server_event["type"] == "response.audio_transcript.done":
            print(f"Transcript: {server_event['transcript']}")
            start = perf_counter()
            self.emote.background_response = self.emote.send_request(server_event["transcript"]) # emote strategy: synchronous/blocking
            # status = emote.begin_emotion_background_task(server_event['transcript']) # emote strategy: background
            # emote_request_queue.put(server_event['transcript']) # emote strategy: thread
            end = perf_counter()
            print(f"Emotion response time: {end-start:.3f} seconds")
        elif server_event["type"] == "response.done" and server_event['response']['status'] == 'completed':
            self.audio.conversation_turn_count += 1
            if server_event['response']['usage']['output_token_details']['audio_tokens']:
                # save audio file (need audio time so doing here instead of speaker.write_to_file in speaker thread)
                duration_ms = self.audio.write_wave_file(self.audio.audio_buffer, self.response_path / f"out-{self.audio.conversation_turn_count}.wav")
                # send emotion to rgb
                try:
                    emotion = self.emote.parse_emotion(self.emote.background_response) # emote strategy: synchronous/blocking
                    # emotion = emote.poll_emotion_background_task() # emote strategy: background
                    # emotion = emote_response_queue.get(block=True, timeout=10) # emote strategy: thread
                    print(f"Emote success: {emotion}")
                    # send inferred emotion to rgb queue
                    self.ai_result_queue.put((emotion, duration_ms))
                except Exception as e:
                    print(f"Error: Emote fail: {e}")
                    # send neutral emotion to rgb queue as default
                    self.ai_result_queue.put((self.emote.DEFAULT_EMOTION, duration_ms))
                # send full audio response to speaker
                self.speaker_audio_queue.put(self.audio.audio_buffer)
                # check for termination word
                transcript = server_event['response']['output'][0]['content'][0]["transcript"].lower()
                self.check_for_termination_response(transcript)
                # clear audio buffer
                self.audio.audio_buffer = b""
                # sleep(1)
            else:
                # TODO: what to do w/ text-only responses?
                # TODO: web search agent for anything after knowledge cutoff so doesn't hallucinate (e.g., top movies in 2025) or text response (e.g., weather tomorrow)
                print("No response audio")
                print("Received event:", json.dumps(server_event, indent=2))
                print("Enabling recorder")
                self.audio.recorder.start()

    def on_error(self, ws: WebSocketApp, error):
        print(f"on_error: {error}")
        print("Enabling recorder")
        self.audio.recorder.start()

    def on_close(self, ws: WebSocketApp, close_status_code, close_msg):
        """Runs when the OpenAI Realtime API connection closes. Both microphone and speaker thread are joined here.

        Args:
            ws (WebSocketApp): Websocket client for OpenAI Realtime API
            close_status_code (_type_): Status code
            close_msg (_type_): Close message
        """
        print(f"on_close: websocket closing... {close_status_code} - {close_msg}") # TODO: code/msg not printing when app sends custom close event
        self.speaker_end_event.set()
        self.t_speaker.join()
        self.recording_end_event.set()
        self.t_recorder.join()
        # self.emote_end_event.set()
        # self.t_emote.join()

    def on_ping(self, ws: WebSocketApp, message):
        """Runs everytime OpenAI Realtime API sends a ping (keep-alive) to this websocket client.
        OpenAI sends keep-alive every 20 seconds by default.

        Args:
            ws (WebSocketApp): Websocket client for OpenAI Realtime API
            message (_type_): Ping message
        """
        self.timeout_counter += 1
        print(f"on_ping: Timeout counter: {self.timeout_counter}")
        if self.timeout_counter > 6: # 120-140 seconds
            # Note: since mic is muted during ai response, thus no new events, an ai response longer than timeout will close ws here
            msg = f"No user speech detected in at least {(self.timeout_counter - 1) * 20} seconds. Closing Connection."
            print(msg)
            self.ws.close(status=STATUS_NORMAL, reason=msg.encode('utf-8'))
    
    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def assistant_wake(self):
        """OpenAI Assistant wake word plugin. Listens for wake phrase: "Hey Pixel Art".
        """
        # using Picovoice TTS
        self.text_to_speech("Listening for wake word")
        self.listen_for_wake()

    @hookimpl(specname="ai_hook")
    @PicoEvents()
    def assistant_run(self):
        """OpenAI Assistant run plugin. This starts the OpenAI Assistant.
        """
        enableTrace(False) # enable for verbose websocket logging

        # initialize child threads here so resources cleaned up after each execution of run()
        self.recording_end_event = Event()
        self.speaker_end_event = Event()
        # self.emote_end_event = Event() # emote strategy: thread
        self.speaker_audio_queue = Queue()
        # self.emote_request_queue = Queue() # emote strategy: thread
        # self.emote_response_queue = Queue() # emote strategy: thread
        self.t_recorder = Thread(name="recorder_thread", target=self.audio.recording_thread, args=(self.recording_end_event, self.ws))
        self.t_speaker = Thread(name="speaker_thread", target=self.audio.speaker_thread, args=(self.speaker_end_event, self.speaker_audio_queue))
        # self.t_emote = Thread(name="emote_thread", target=self.emote.emotion_thread_task, args=(self.emote_end_event, self.emote_request_queue, self.emote_response_queue)) # emote strategy: thread
        
        self.ws.run_forever()
        print("end")
