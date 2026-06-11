"""Text-to-speech with three engines and graceful fallback:

- elevenlabs: the closest to the movie voice (clone/choose a deep, dry voice)
- openai:     good quality, cheap, one API key for everything
- espeak:     offline robotic fallback, zero cost

synthesize() returns an audio file (also served to the browser by the web
dashboard); speak() synthesizes and plays it on the robot's speaker.
"""
import logging
import subprocess
import shutil
import tempfile
from . import audio
from .config import Settings

log = logging.getLogger("tars.tts")


def engine_chain(s: Settings) -> list[str]:
    if s.tts_engine != "auto":
        return [s.tts_engine, "espeak"]
    chain = []
    if s.elevenlabs_api_key:
        chain.append("elevenlabs")
    if s.openai_api_key:
        chain.append("openai")
    chain.append("espeak")
    return chain


def synthesize(text: str, s: Settings) -> str | None:
    """Render text to an audio file; returns its path (mp3 or wav) or None."""
    if not text:
        return None
    for engine in engine_chain(s):
        try:
            fn = {"elevenlabs": _elevenlabs, "openai": _openai, "espeak": _espeak}[engine]
            path = fn(text, s)
            if path:
                return path
        except Exception as e:
            log.warning("TTS engine %s failed (%s), trying next", engine, e)
    return None


def speak(text: str, s: Settings):
    path = synthesize(text, s)
    if path:
        audio.play(path)
    else:
        log.warning("no TTS engine available; cannot speak: %r", text[:60])


def _elevenlabs(text: str, s: Settings) -> str:
    import requests
    voice = s.elevenlabs_voice_id or "onwK4e9ZLuTAKqWW03F9"  # "Daniel": deep male default
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        headers={"xi-api-key": s.elevenlabs_api_key},
        json={"text": text, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.55, "similarity_boost": 0.8}},
        timeout=60)
    r.raise_for_status()
    path = tempfile.mktemp(suffix=".mp3", prefix="tars_tts_")
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def _openai(text: str, s: Settings) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=s.openai_api_key)
    path = tempfile.mktemp(suffix=".mp3", prefix="tars_tts_")
    with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice="onyx", input=text) as resp:
        resp.stream_to_file(path)
    return path


def _espeak(text: str, s: Settings) -> str | None:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return None
    path = tempfile.mktemp(suffix=".wav", prefix="tars_tts_")
    subprocess.run([exe, "-v", s.language, "-p", "20", "-s", "150",
                    "-w", path, text], check=False)
    return path
