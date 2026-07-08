import subprocess

import numpy as np

SAMPLE_RATE = 48000


def decode_audio_to_waveform(audio_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Decodes a compressed audio clip (mp4/AAC, webm/Opus, etc) into a mono
    float32 waveform at the given sample rate, via an ffmpeg subprocess.
    """
    result = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-f",
            "f32le",
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "pipe:1",
        ],
        input=audio_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)
