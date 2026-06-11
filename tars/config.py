"""TARS configuration: environment variables, defaults and persisted settings."""
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATA_DIR = Path(os.environ.get("TARS_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
SETTINGS_FILE = DATA_DIR / "settings.json"


@dataclass
class Settings:
    # --- AI ---
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_model: str = os.environ.get("TARS_MODEL", "gpt-4o-mini")
    embedding_model: str = os.environ.get("TARS_EMBEDDING_MODEL", "text-embedding-3-small")
    # Any OpenAI-compatible server: Ollama (http://localhost:11434/v1),
    # LM Studio, llama.cpp, vLLM... leave empty for the OpenAI cloud.
    llm_base_url: str = os.environ.get("TARS_LLM_BASE_URL", "")
    # --- Voice ---
    tts_engine: str = os.environ.get("TARS_TTS", "auto")        # elevenlabs | openai | espeak | auto
    stt_engine: str = os.environ.get("TARS_STT", "auto")        # openai | vosk | auto
    elevenlabs_api_key: str = os.environ.get("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.environ.get("ELEVENLABS_VOICE_ID", "")
    piper_voice: str = os.environ.get("TARS_PIPER_VOICE", "")   # path to a piper .onnx voice
    wake_word: str = os.environ.get("TARS_WAKE_WORD", "tars")
    language: str = os.environ.get("TARS_LANGUAGE", "en")       # en | it | ...
    # after TARS answers, keep listening this many seconds for a follow-up
    # question without requiring the wake word again (0 disables)
    followup_window: float = float(os.environ.get("TARS_FOLLOWUP_WINDOW", "6"))
    # --- Personality (adjustable at runtime, persisted) ---
    humor: int = 75
    honesty: int = 90
    sarcasm: int = 30
    robot_name: str = "TARS"
    character: str = "tars"        # active character card (characters/*.json)
    persona_extra: str = ""        # extra persona text from the character card
    # --- Web ---
    web_host: str = os.environ.get("TARS_WEB_HOST", "0.0.0.0")
    web_port: int = int(os.environ.get("TARS_WEB_PORT", "8000"))
    web_password: str = os.environ.get("TARS_WEB_PASSWORD", "")  # empty = no login
    # --- Integrations ---
    ha_url: str = os.environ.get("HA_URL", "")
    ha_token: str = os.environ.get("HA_TOKEN", "")
    music_dir: str = os.environ.get("TARS_MUSIC_DIR", str(DATA_DIR / "music"))
    # --- Hardware ---
    sim_mode: bool = os.environ.get("TARS_SIM", "") == "1"
    pwm_frequency: int = 60
    battery_low_pct: int = 20
    gamepad_device: str = os.environ.get("TARS_GAMEPAD", "/dev/input/event3")
    # Servo channels on the PCA9685
    ch_center_lift: int = 0
    ch_port_drive: int = 1
    ch_star_drive: int = 2
    ch_port_main: int = 3
    ch_port_forearm: int = 4
    ch_port_hand: int = 5
    ch_star_main: int = 6
    ch_star_forearm: int = 7
    ch_star_hand: int = 8
    # Calibrated PWM positions (tune with the servo tester for your build)
    pwm: dict = field(default_factory=lambda: {
        "up_height": 205, "neutral_height": 275, "down_height": 450,
        "forward_port": 440, "neutral_port": 375, "back_port": 330,
        "forward_star": 292, "neutral_star": 357, "back_star": 402,
        "port_main": 610, "star_main": 200,
        "port_forearm": 570, "star_forearm": 200,
        "port_hand": 570, "star_hand": 240,
    })

    PERSISTED = ("humor", "honesty", "sarcasm", "robot_name", "character",
                 "persona_extra", "wake_word", "language", "pwm")

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                stored = json.loads(SETTINGS_FILE.read_text())
                for key in self.PERSISTED:
                    if key not in stored:
                        continue
                    if key == "pwm":
                        # merge so new default keys survive old settings files
                        self.pwm = {**self.pwm, **stored["pwm"]}
                    else:
                        setattr(self, key, stored[key])
            except (json.JSONDecodeError, OSError):
                pass
        return self

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({k: getattr(self, k) for k in self.PERSISTED}, indent=2))

    def public(self):
        d = asdict(self)
        for secret in ("openai_api_key", "elevenlabs_api_key", "ha_token"):
            d.pop(secret, None)
        return d


settings = Settings().load()
