"""Pipeline latency benchmark: `tars --benchmark`.

Times the three stages that decide how snappy a conversation feels - LLM
(first token and full reply), TTS synthesis, STT transcription - with
whatever engines are configured. Stages that aren't configured are skipped,
not failed: run `tars --doctor` first for configuration problems.
"""
import math
import os
import struct
import tempfile
import time
import wave
from dataclasses import dataclass

from .config import Settings

OK, SKIP = "ok", "skip"
MARKS = {OK: "[ OK ]", SKIP: "[SKIP]"}


@dataclass
class Result:
    name: str
    status: str
    detail: str


def _test_wav(seconds: float = 1.0, rate: int = 16000) -> str:
    """A short spoken-band test tone (440 Hz) for timing STT."""
    path = tempfile.mktemp(suffix=".wav", prefix="tars_bench_")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        for i in range(int(rate * seconds)):
            sample = int(12000 * math.sin(2 * math.pi * 440 * i / rate))
            w.writeframes(struct.pack("<h", sample))
    return path


def bench_llm(s: Settings) -> Result:
    if not (s.openai_api_key or s.llm_base_url):
        return Result("LLM reply", SKIP, "not configured")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=s.openai_api_key or "local",
                        base_url=s.llm_base_url or None)
        start = time.monotonic()
        first_token = None
        stream = client.chat.completions.create(
            model=s.openai_model, stream=True, max_tokens=60,
            messages=[{"role": "user",
                       "content": "Reply with one short sentence."}])
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if first_token is None:
                    first_token = time.monotonic() - start
        total = time.monotonic() - start
        return Result("LLM reply", OK,
                      f"first token {first_token:.2f}s, full {total:.2f}s "
                      f"({s.openai_model})")
    except Exception as e:
        return Result("LLM reply", SKIP, f"errored: {e}")


def bench_tts(s: Settings) -> Result:
    from . import tts
    start = time.monotonic()
    path = tts.synthesize("Systems nominal. All readings in the green.", s)
    elapsed = time.monotonic() - start
    if path is None:
        return Result("TTS synthesis", SKIP, "no engine available")
    os.unlink(path)
    return Result("TTS synthesis", OK,
                  f"{elapsed:.2f}s ({tts.engine_chain(s)[0]} first in chain)")


def bench_stt(s: Settings) -> Result:
    from . import stt
    try:
        import vosk  # noqa: F401
        have_vosk = True
    except ImportError:
        have_vosk = False
    if not (s.openai_api_key or have_vosk):
        return Result("STT transcription", SKIP, "not configured")
    wav = _test_wav()
    try:
        start = time.monotonic()
        stt.transcribe(wav, s)
        return Result("STT transcription", OK,
                      f"{time.monotonic() - start:.2f}s for 1s of audio")
    except Exception as e:
        return Result("STT transcription", SKIP, f"errored: {e}")
    finally:
        os.unlink(wav)


def run_benchmark(s: Settings) -> list[Result]:
    return [bench_llm(s), bench_tts(s), bench_stt(s)]


def print_report(s: Settings) -> int:
    print("TARS pipeline benchmark (lower is snappier)\n" + "-" * 50)
    results = run_benchmark(s)
    width = max(len(r.name) for r in results)
    for r in results:
        print(f"{MARKS[r.status]} {r.name:<{width}}  {r.detail}")
    print("-" * 50)
    print("Tip: a spoken answer starts after roughly "
          "STT + LLM-first-token + first-sentence TTS.")
    return 0
