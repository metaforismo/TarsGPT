"""The hands-free voice loop: wake word -> listen -> think -> speak (streaming).

Wake word detection runs fully offline with Vosk (a tiny model recognizing
just the wake word). The reply is spoken sentence by sentence while the LLM
is still generating, via the Speaker pipeline. Without Vosk, use push-to-talk
from the web UI instead.
"""
import json
import logging
import os
import threading
from . import audio, stt
from .config import Settings
from .llm import Brain
from .speech import Speaker

log = logging.getLogger("tars.voice")

ACK_DEFAULTS = {"en": "Yes?", "it": "Sì?", "es": "¿Sí?", "fr": "Oui ?",
                "de": "Ja?", "pt": "Sim?", "ja": "Hai?"}


def resolve_ack(s: Settings) -> str | None:
    """The short phrase spoken right after the wake word, so the user knows
    TARS is listening. 'auto' picks per language, 'off'/'' disables."""
    if s.ack in ("off", ""):
        return None
    if s.ack == "auto":
        return ACK_DEFAULTS.get(s.language, "Yes?")
    return s.ack


class VoiceLoop:
    def __init__(self, s: Settings, brain: Brain, speaker: Speaker,
                 speaker_id=None):
        self.s = s
        self.brain = brain
        self.speaker = speaker
        self.speaker_id = speaker_id  # optional SpeakerID instance
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
        if not self._wake_capable():
            log.warning("Vosk not available: voice loop limited to push-to-talk")
            self.state = "off"
            self.running = False
            return
        while self.running:
            self.state = "waiting"
            if self._wait_for_wake_word():
                ack = resolve_ack(self.s)
                if ack:
                    # speak before opening the mic, or TARS hears itself
                    self.speaker.say(ack)
                    self.speaker.wait()
                self._interact()

    def _wake_capable(self) -> bool:
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
        """One wake-word interaction, then keep the conversation open: for
        followup_window seconds the user can reply without saying the wake
        word again (like talking to the movie TARS)."""
        self.state = "listening"
        wav = audio.record_until_silence()
        while wav:
            understood = self._exchange(wav)
            if (not understood or self.s.followup_window <= 0
                    or not self.running):
                break
            self.state = "listening"
            wav = audio.record_until_silence(wait_seconds=self.s.followup_window)
        self.state = "waiting" if self.running else "off"

    def _exchange(self, wav: str) -> bool:
        """Transcribe one utterance, answer it, speak the reply.
        Returns True if speech was understood."""
        try:
            self.state = "thinking"
            text = stt.transcribe(wav, self.s)
            if not text:
                return False
            who = self.speaker_id.identify(wav) if self.speaker_id else None
            log.info("Heard%s: %s", f" ({who})" if who else "", text)
            self.state = "speaking"
            reply = self.speaker.speak_stream(
                self.brain.chat_stream(text, speaker=who))
            self.speaker.wait()
            log.info("Replied: %s", reply)
            return True
        finally:
            os.unlink(wav)
