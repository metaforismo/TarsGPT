"""Text-to-speech with three engines and graceful fallback:

- elevenlabs: the closest to the movie voice (clone/choose a deep, dry voice)
- openai:     good quality, cheap, one API key for everything
- espeak:     offline robotic fallback, zero cost
"""
import logging
import subprocess
import shutil
import tempfile
from . import audio
from .config import Settings

log = logging.getLogger("tars.tts")


def speak(text: str, s: Settings):
    if not text:
        return
    engine = s.tts_engine
    if engine == "auto":
        engine = ("elevenlabs" if s.elevenlabs_api_key
                  else "openai" if s.openai_api_key else "espeak")
    try:
        if engine == "elevenlabs":
            _elevenlabs(text, s)
        elif engine == "openai":
            _openai(text, s)
        else:
            _espeak(text, s)
    except Exception as e:
        log.warning("TTS engine %s failed (%s), falling back to espeak", engine, e)
        _espeak(text, s)


def _elevenlabs(text: str, s: Settings):
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
    audio.play(path)


def _openai(text: str, s: Settings):
    from openai import OpenAI
    client = OpenAI(api_key=s.openai_api_key)
    path = tempfile.mktemp(suffix=".mp3", prefix="tars_tts_")
    with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice="onyx", input=text) as resp:
        resp.stream_to_file(path)
    audio.play(path)


def _espeak(text: str, s: Settings):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        log.warning("espeak not installed; cannot speak: %r", text)
        return
    subprocess.run([exe, "-v", s.language, "-p", "20", "-s", "150", text], check=False)
