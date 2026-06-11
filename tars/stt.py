"""Speech-to-text: OpenAI Whisper API (best quality) or Vosk (fully offline)."""
import logging
from .config import Settings

log = logging.getLogger("tars.stt")


def transcribe(wav_path: str, s: Settings) -> str:
    engine = s.stt_engine
    if engine == "auto":
        engine = "openai" if s.openai_api_key else "vosk"
    if engine == "openai":
        return _openai(wav_path, s)
    return _vosk(wav_path, s)


def _openai(wav_path: str, s: Settings) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=s.openai_api_key)
    with open(wav_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1", file=f, language=s.language)
    return (result.text or "").strip()


def _vosk(wav_path: str, s: Settings) -> str:
    import json
    import wave
    try:
        from vosk import KaldiRecognizer
    except ImportError:
        log.warning("vosk not installed and no OpenAI key - cannot transcribe")
        return ""
    model = _vosk_model(s)
    with wave.open(wav_path, "rb") as w:
        rec = KaldiRecognizer(model, w.getframerate())
        while True:
            data = w.readframes(4000)
            if not data:
                break
            rec.AcceptWaveform(data)
    return json.loads(rec.FinalResult()).get("text", "").strip()


_model_cache = {}

# Vosk model identifiers differ from our two-letter codes where noted
VOSK_LANG = {"en": "en-us", "pt": "pt-br"}


def vosk_lang(language: str) -> str:
    return VOSK_LANG.get(language, language)


def _vosk_model(s: Settings):
    """Load (and cache) the small Vosk model for the configured language."""
    from vosk import Model
    lang = vosk_lang(s.language)
    if lang not in _model_cache:
        # downloads the small model on first use (e.g. vosk-model-small-en-us)
        _model_cache[lang] = Model(lang=lang)
    return _model_cache[lang]
