"""Microphone capture (with end-of-speech detection) and audio playback helpers."""
import logging
import shutil
import subprocess
import tempfile
import wave

log = logging.getLogger("tars.audio")

SAMPLE_RATE = 16000
SILENCE_SECONDS = 1.2     # stop recording after this much trailing silence
MAX_SECONDS = 15
ENERGY_FLOOR = 350        # minimum RMS threshold even in a silent room
AMBIENT_BLOCKS = 3        # first 0.3s measure background noise, not speech


def record_until_silence(wait_seconds: float | None = None) -> str | None:
    """Record from the default microphone until the speaker stops. Returns a
    wav path, or None if nobody spoke. The speech threshold auto-calibrates
    on the ambient noise heard in the first instants, so it works in noisy
    rooms too. wait_seconds bounds how long to wait for speech to *start*
    (used by the follow-up conversation window)."""
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        log.warning("sounddevice/numpy not installed - microphone disabled")
        return None

    block = int(SAMPLE_RATE * 0.1)
    frames, silent_blocks, spoke = [], 0, False
    ambient, threshold = [], ENERGY_FLOOR
    wait_blocks = int((wait_seconds or MAX_SECONDS) / 0.1) + AMBIENT_BLOCKS
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=block) as stream:
        for i in range(int(MAX_SECONDS / 0.1)):
            data, _ = stream.read(block)
            frames.append(bytes(data))
            rms = float(np.sqrt(np.mean(data.astype(np.float64) ** 2)))
            if i < AMBIENT_BLOCKS:
                ambient.append(rms)
                continue
            if i == AMBIENT_BLOCKS:
                threshold = max(ENERGY_FLOOR, 2.5 * sum(ambient) / len(ambient))
            if rms > threshold:
                spoke, silent_blocks = True, 0
            elif spoke:
                silent_blocks += 1
                if silent_blocks * 0.1 >= SILENCE_SECONDS:
                    break
            elif i >= wait_blocks:
                break  # nobody started talking within the wait window
    if not spoke:
        return None

    path = tempfile.mktemp(suffix=".wav", prefix="tars_stt_")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(frames))
    return path


def play(path: str):
    """Play an audio file with whatever player is installed (Pi: aplay/mpg123)."""
    for player, args in (("mpv", ["--really-quiet"]), ("mpg123", ["-q"]),
                         ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
                         ("aplay", ["-q"])):
        if shutil.which(player):
            subprocess.run([player, *args, path], check=False)
            return
    log.warning("No audio player found (install mpv, mpg123 or alsa-utils)")
