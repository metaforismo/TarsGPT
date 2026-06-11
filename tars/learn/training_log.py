"""Persistent record of gait-training sessions, rendered as a learning
curve in the dashboard (/api/training)."""
import json
import time
from ..config import DATA_DIR

TRAINING_LOG_FILE = DATA_DIR / "gait_training.json"


class TrainingLog:
    def __init__(self, mode: str):
        self.data = {"mode": mode,
                     "started": time.strftime("%Y-%m-%d %H:%M"),
                     "entries": []}

    def record(self, iteration: int, reward: float, best: float):
        self.data["entries"].append({"i": iteration,
                                     "reward": round(float(reward), 4),
                                     "best": round(float(best), 4)})
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        TRAINING_LOG_FILE.write_text(json.dumps(self.data, indent=2))

    @staticmethod
    def load() -> dict | None:
        if not TRAINING_LOG_FILE.exists():
            return None
        try:
            return json.loads(TRAINING_LOG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return None
