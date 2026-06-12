"""Streaming speech pipeline: TARS starts talking on the first finished sentence.

LLM tokens stream in, get cut at sentence boundaries and queued; a worker
thread synthesizes and plays them one by one while the model is still
generating the rest of the reply.
"""
import logging
import queue
import re
import threading
from . import tts
from .config import Settings

log = logging.getLogger("tars.speech")

SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|(?<=[.!?…])$")
MIN_SENTENCE_CHARS = 12  # merge tiny fragments ("Dr.", "No.") into the next one


class Speaker:
    def __init__(self, s: Settings):
        self.s = s
        self.muted = False
        self._q: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._worker, daemon=True, name="tars-speaker").start()

    def say(self, text: str):
        """Queue a complete utterance (used by skills for proactive speech)."""
        text = text.strip()
        if text and not self.muted:
            self._q.put(text)

    def speak_stream(self, chunks) -> str:
        """Consume an iterator of text chunks, speaking sentence by sentence.
        Returns the full assembled text."""
        buffer, full = "", []
        for chunk in chunks:
            full.append(chunk)
            buffer += chunk
            parts = SENTENCE_END.split(buffer)
            # everything but the last part is a complete sentence
            while len(parts) > 1:
                sentence = parts.pop(0).strip()
                if len(sentence) < MIN_SENTENCE_CHARS and parts:
                    parts[0] = sentence + " " + parts[0]
                    break
                self.say(sentence)
            buffer = parts[0] if parts else ""
        self.say(buffer)
        return "".join(full)

    def wait(self):
        """Block until everything queued has been spoken."""
        self._q.join()

    @property
    def busy(self) -> bool:
        return self._q.unfinished_tasks > 0

    def _worker(self):
        while True:
            text = self._q.get()
            try:
                tts.speak(text, self.s)
            except Exception:
                log.exception("TTS failed for %r", text[:50])
            finally:
                self._q.task_done()
