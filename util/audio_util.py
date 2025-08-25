from pvrecorder import PvRecorder
from pvspeaker import PvSpeaker

def init_recorder(frame_length: int = 512) -> PvRecorder:
    audio_devices = PvRecorder.get_available_devices()
    mic_index = [i for i, mic in enumerate(audio_devices) if "UAC 1.0 Microphone & HID-Mediak" in mic][0]
    return PvRecorder(frame_length=frame_length, device_index=mic_index)

def init_speaker(sample_rate: int = 22050, bits_per_sample: int = 16) -> PvSpeaker:
    speaker_index = [i for i, s in enumerate(PvSpeaker.get_available_devices()) if "UACDemoV1.0" in s][0]
    # speaker = PvSpeaker(sample_rate=self.orca.sample_rate, bits_per_sample=16, device_index=speaker_index)
    speaker = PvSpeaker(sample_rate=sample_rate, bits_per_sample=bits_per_sample, device_index=speaker_index)
    return speaker

def audio_frame_extractor(audio: list[int], chunk_size: int = 512):
        """Splits a list into chunks of the specified size.

        Args:
            audio: The list to be split.
            chunk_size: The desired size of each chunk.

        Yields:
            Successive chunks of the list.
        """
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]