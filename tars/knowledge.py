"""Knowledge graph: persistent subject-relation-object facts.

Unlike free-text memory notes, triples are structured ("Francesco", "owns",
"a Bambu Lab P1S") so TARS can answer entity questions precisely and the
dashboard can render the graph. Facts relevant to the current message are
injected into the LLM context automatically.
"""
import json
import re
import threading
import time
from .config import DATA_DIR

KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
MAX_TRIPLES = 2000


class KnowledgeGraph:
    def __init__(self):
        self._lock = threading.Lock()
        self.triples: list[dict] = []  # {"s", "r", "o", "ts"}
        self._load()

    def _load(self):
        if KNOWLEDGE_FILE.exists():
            try:
                self.triples = json.loads(KNOWLEDGE_FILE.read_text()).get("triples", [])
            except (json.JSONDecodeError, OSError):
                self.triples = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_FILE.write_text(json.dumps({"triples": self.triples},
                                             indent=2, ensure_ascii=False))

    def add(self, subject: str, relation: str, obj: str) -> bool:
        """Store a fact; returns False if it was already known."""
        triple = {"s": subject.strip(), "r": relation.strip(), "o": obj.strip(),
                  "ts": time.strftime("%Y-%m-%d %H:%M")}
        with self._lock:
            for t in self.triples:
                if (t["s"].lower(), t["r"].lower(), t["o"].lower()) == \
                   (triple["s"].lower(), triple["r"].lower(), triple["o"].lower()):
                    return False
            self.triples.append(triple)
            self.triples = self.triples[-MAX_TRIPLES:]
            self._save()
        return True

    def forget(self, subject: str) -> int:
        """Remove all facts about a subject; returns how many were removed."""
        with self._lock:
            before = len(self.triples)
            self.triples = [t for t in self.triples
                            if t["s"].lower() != subject.lower()]
            if len(self.triples) != before:
                self._save()
            return before - len(self.triples)

    def about(self, entity: str) -> list[dict]:
        """All facts where the entity appears as subject or object.
        Whole-word match, so 'rome' does not match 'chrome'."""
        pattern = re.compile(rf"\b{re.escape(entity.strip())}\b", re.IGNORECASE)
        with self._lock:
            return [t for t in self.triples
                    if pattern.search(t["s"]) or pattern.search(t["o"])]

    def search(self, text: str, k: int = 6) -> list[dict]:
        """Facts whose words overlap the given text, best matches first."""
        words = {w for w in re.findall(r"\w+", text.lower()) if len(w) > 3}
        if not words:
            return []
        scored = []
        with self._lock:
            for t in self.triples:
                fact_words = set(re.findall(r"\w+", f"{t['s']} {t['r']} {t['o']}".lower()))
                score = len(words & fact_words)
                if score:
                    scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:k]]

    @staticmethod
    def render(triples: list[dict]) -> str:
        return "\n".join(f"- {t['s']} {t['r']} {t['o']}" for t in triples)
