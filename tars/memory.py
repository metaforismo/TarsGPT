"""Hybrid conversation memory.

- Short-term: a rolling window of recent turns, kept verbatim.
- Long-term: notes TARS chooses to remember, persisted to data/memory.json.
  Each note is stored with an embedding (OpenAI text-embedding-3-small) and
  retrieved by cosine similarity against the current user message; with no
  API key it falls back to keyword-overlap scoring, fully offline.
"""
import json
import logging
import math
import threading
import time
from .config import DATA_DIR, Settings

log = logging.getLogger("tars.memory")

MEMORY_FILE = DATA_DIR / "memory.json"
SHORT_TERM_TURNS = 20   # user+assistant pairs kept verbatim
RELEVANT_NOTES = 8      # notes injected per conversation turn


class Memory:
    def __init__(self, s: Settings | None = None):
        self.s = s
        self._lock = threading.Lock()
        self._client = None
        self.turns: list[dict] = []
        self.notes: list[dict] = []   # {"ts", "note", "emb": [...] | None}
        self._load()

    # ---------- persistence ----------

    def _load(self):
        if MEMORY_FILE.exists():
            try:
                stored = json.loads(MEMORY_FILE.read_text())
                self.notes = stored.get("notes", [])
                # the conversation survives restarts too
                self.turns = stored.get("turns", [])[-SHORT_TERM_TURNS * 2:]
            except (json.JSONDecodeError, OSError):
                self.notes = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps({"notes": self.notes,
                                           "turns": self.turns},
                                          indent=2, ensure_ascii=False))

    # ---------- short term ----------

    def add_turn(self, role: str, content: str):
        with self._lock:
            self.turns.append({"role": role, "content": content})
            self.turns = self.turns[-SHORT_TERM_TURNS * 2:]
            self._save()

    def clear(self):
        with self._lock:
            self.turns = []
            self._save()

    # ---------- long term ----------

    def add_note(self, note: str):
        entry = {"ts": time.strftime("%Y-%m-%d %H:%M"), "note": note,
                 "emb": self._embed(note)}
        with self._lock:
            self.notes.append(entry)
            self.notes = self.notes[-500:]
            self._save()

    def relevant_notes(self, query: str, k: int = RELEVANT_NOTES) -> list[dict]:
        with self._lock:
            notes = list(self.notes)
        if not notes:
            return []
        q_emb = self._embed(query)
        scored = []
        for n in notes:
            if q_emb and n.get("emb"):
                score = _cosine(q_emb, n["emb"])
            else:
                score = _keyword_overlap(query, n["note"])
            scored.append((score, n))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [n for score, n in scored[:k] if score > 0.05]

    # ---------- LLM context ----------

    def context_messages(self, query: str = "") -> list[dict]:
        msgs = []
        relevant = self.relevant_notes(query) if query else []
        # always keep the few most recent notes in view, even if off-topic
        recent = [n for n in self.notes[-3:] if n not in relevant]
        picked = relevant + recent
        if picked:
            facts = "\n".join(f"- ({n['ts']}) {n['note']}" for n in picked)
            msgs.append({"role": "system",
                         "content": f"Long-term memory, facts you chose to remember:\n{facts}"})
        with self._lock:
            msgs.extend(self.turns)
        return msgs

    # ---------- embeddings ----------

    def _embed(self, text: str) -> list[float] | None:
        if not (self.s and self.s.openai_api_key):
            return None
        try:
            if self._client is None:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.s.openai_api_key)
            resp = self._client.embeddings.create(model=self.s.embedding_model,
                                                  input=text[:2000])
            return resp.data[0].embedding
        except Exception as e:
            log.warning("embedding failed (%s), using keyword fallback", e)
            return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _keyword_overlap(query: str, note: str) -> float:
    q = {w for w in query.lower().split() if len(w) > 3}
    n = {w for w in note.lower().split() if len(w) > 3}
    return len(q & n) / len(q) if q else 0.0
