"""The hands-free voice loop: wake word -> listen -> think -> speak.

Wake word detection runs fully offline with Vosk (a tiny model recognizing just
the wake word). Without Vosk, set push-to-talk from the web UI instead.
"""
import json
import logging
import os
import threading
from . import audio, stt, tts
from .config import Settings
from .llm import Brain

log = logging.getLogger("tars.voice")


class VoiceLoop:
    def __init__(self, s: Settings, brain: Brain):
        self.s = s
        self.brain = brain
        self.running = False
        self.state = "off"  # off | waiting | listening | thinking | speaking
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self.state = "off"

    def push_to_talk(self):
        """One interaction without the wake word (used by the web UI button)."""
        threading.Thread(target=self._interact, daemon=True).start()

    # ----- internals -----

    def _loop(self):
        if not self._wait_capable():
            log.warning("Vosk not available: voice loop limited to push-to-talk")
            self.state = "off"
            self.running = False
            return
        while self.running:
            self.state = "waiting"
            if self._wait_for_wake_word():
                self._interact()

    def _wait_capable(self) -> bool:
        try:
            import vosk  # noqa: F401
            import sounddevice  # noqa: F401
            return True
        except ImportError:
            return False

    def _wait_for_wake_word(self) -> bool:
        import sounddevice as sd
        from vosk import KaldiRecognizer
        model = stt._vosk_model(self.s)
        grammar = json.dumps([self.s.wake_word.lower(), "[unk]"])
        rec = KaldiRecognizer(model, 16000, grammar)
        with sd.RawInputStream(samplerate=16000, blocksize=4000,
                               dtype="int16", channels=1) as stream:
            while self.running:
                data, _ = stream.read(4000)
                if rec.AcceptWaveform(bytes(data)):
                    text = json.loads(rec.Result()).get("text", "")
                    if self.s.wake_word.lower() in text:
                        return True
        return False

    def _interact(self):
        self.state = "listening"
        wav = audio.record_until_silence()
        if not wav:
            return
        try:
            self.state = "thinking"
            text = stt.transcribe(wav, self.s)
            if not text:
                return
            log.info("Heard: %s", text)
            reply = self.brain.chat(text)
            log.info("Reply: %s", reply)
            self.state = "speaking"
            tts.speak(reply, self.s)
        finally:
            os.unlink(wav)
            self.state = "waiting" if self.running else "off"
