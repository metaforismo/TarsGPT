"""Conversation memory: a rolling short-term window plus persistent long-term notes.

Long-term notes are facts TARS decides to remember (via the `remember` tool) and
survive restarts in data/memory.json.
"""
import json
import threading
import time
from .config import DATA_DIR

MEMORY_FILE = DATA_DIR / "memory.json"
SHORT_TERM_TURNS = 20  # user+assistant message pairs kept verbatim


class Memory:
    def __init__(self):
        self._lock = threading.Lock()
        self.turns: list[dict] = []          # [{"role": ..., "content": ...}]
        self.notes: list[dict] = []          # [{"ts": ..., "note": ...}]
        self._load()

    def _load(self):
        if MEMORY_FILE.exists():
            try:
                self.notes = json.loads(MEMORY_FILE.read_text()).get("notes", [])
            except (json.JSONDecodeError, OSError):
                self.notes = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps({"notes": self.notes}, indent=2, ensure_ascii=False))

    def add_turn(self, role: str, content: str):
        with self._lock:
            self.turns.append({"role": role, "content": content})
            self.turns = self.turns[-SHORT_TERM_TURNS * 2:]

    def add_note(self, note: str):
        with self._lock:
            self.notes.append({"ts": time.strftime("%Y-%m-%d %H:%M"), "note": note})
            self.notes = self.notes[-200:]
            self._save()

    def context_messages(self) -> list[dict]:
        """Messages to prepend to an LLM call: long-term notes + recent turns."""
        with self._lock:
            msgs = []
            if self.notes:
                facts = "\n".join(f"- ({n['ts']}) {n['note']}" for n in self.notes[-30:])
                msgs.append({"role": "system",
                             "content": f"Long-term memory, facts you chose to remember:\n{facts}"})
            msgs.extend(self.turns)
            return msgs

    def clear(self):
        with self._lock:
            self.turns = []
