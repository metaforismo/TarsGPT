"""Named movement sequences: choreography built from gait primitives.

Built-in routines below; add your own in data/sequences.json with the
same structure - they are merged in (and can override the defaults).
"""
import json
import logging
import time
from ..config import DATA_DIR

log = logging.getLogger("tars.sequences")

SEQUENCES_FILE = DATA_DIR / "sequences.json"
ALLOWED_ACTIONS = ("step_forward", "turn_left", "turn_right",
                   "strafe_left", "strafe_right", "pose", "neutral")

DEFAULT_SEQUENCES = {
    "greet": [
        {"action": "pose", "pause": 1.2},
        {"action": "pose", "pause": 0.5},
    ],
    "wiggle": [
        {"action": "turn_left", "pause": 0.2},
        {"action": "turn_right", "pause": 0.2},
        {"action": "turn_left", "pause": 0.2},
        {"action": "turn_right", "pause": 0.2},
        {"action": "neutral"},
    ],
    "patrol": [
        {"action": "step_forward", "repeat": 3, "pause": 0.3},
        {"action": "turn_right", "repeat": 2, "pause": 0.3},
        {"action": "step_forward", "repeat": 3, "pause": 0.3},
        {"action": "turn_right", "repeat": 2, "pause": 0.3},
    ],
    "slalom": [
        {"action": "strafe_left", "pause": 0.3},
        {"action": "strafe_right", "pause": 0.3},
        {"action": "strafe_right", "pause": 0.3},
        {"action": "strafe_left", "pause": 0.3},
    ],
}


def load_sequences() -> dict:
    sequences = dict(DEFAULT_SEQUENCES)
    if SEQUENCES_FILE.exists():
        try:
            sequences.update(json.loads(SEQUENCES_FILE.read_text()))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("ignoring bad %s: %s", SEQUENCES_FILE, e)
    return sequences


def perform(name: str, gaits) -> str:
    sequences = load_sequences()
    steps = sequences.get(name.lower().strip())
    if steps is None:
        return f"error: unknown sequence '{name}'. Available: {', '.join(sorted(sequences))}"
    for step in steps:
        action = step.get("action")
        if action not in ALLOWED_ACTIONS:
            return f"error: sequence '{name}' contains invalid action '{action}'"
        for _ in range(int(step.get("repeat", 1))):
            getattr(gaits, action)()
        time.sleep(float(step.get("pause", 0)))
    return f"ok: performed {name}"
