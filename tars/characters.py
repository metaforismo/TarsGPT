"""Character cards: switchable personas loaded from characters/*.json.

A card sets the robot's name, an extra persona paragraph and default
personality dials. Switch at runtime via the set_character skill or the
dashboard ("TARS, become CASE").
"""
import json
import logging
from pathlib import Path
from .config import Settings

log = logging.getLogger("tars.characters")

CHAR_DIR = Path(__file__).resolve().parent.parent / "characters"


def list_characters() -> list[str]:
    if not CHAR_DIR.is_dir():
        return []
    return sorted(p.stem for p in CHAR_DIR.glob("*.json"))


def load_card(name: str) -> dict | None:
    path = CHAR_DIR / f"{name.lower()}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        log.warning("bad character card %s: %s", path, e)
        return None


def apply_character(name: str, s: Settings) -> bool:
    card = load_card(name)
    if card is None:
        return False
    s.character = name.lower()
    s.robot_name = card.get("name", name.upper())
    s.persona_extra = card.get("persona", "")
    for dial in ("humor", "honesty", "sarcasm"):
        if dial in card:
            setattr(s, dial, max(0, min(100, int(card[dial]))))
    if card.get("elevenlabs_voice_id"):
        s.elevenlabs_voice_id = card["elevenlabs_voice_id"]
    s.save()
    log.info("character switched to %s", s.robot_name)
    return True
