"""Self-test for builders: `tars --doctor` checks every subsystem and
prints what works, what's missing and how to fix it. Safe to run anywhere -
nothing moves, nothing is written."""
import os
import shutil
import sys
from dataclasses import dataclass

from .config import Settings

OK, WARN, FAIL = "ok", "warn", "fail"
MARKS = {OK: "[ OK ]", WARN: "[ !! ]", FAIL: "[FAIL]"}


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _python() -> Check:
    version = sys.version_info
    good = version >= (3, 10)
    return Check("Python", OK if good else FAIL,
                 f"{version.major}.{version.minor} "
                 + ("" if good else "- 3.10+ required"))


def _i2c() -> Check:
    if os.path.exists("/dev/i2c-1"):
        return Check("I2C bus", OK, "/dev/i2c-1 present")
    return Check("I2C bus", FAIL,
                  "no /dev/i2c-1 - enable I2C in raspi-config (not a Pi? expected)")


def _pca9685() -> Check:
    from .movement.driver import ServoDriver
    driver = ServoDriver(60, sim=False)
    if not driver.sim:
        return Check("PCA9685 servo driver", OK, "found on I2C")
    return Check("PCA9685 servo driver", WARN,
                  "not found - servos will run in simulation "
                  "(check wiring / i2cdetect -y 1 for 0x40)")


def _imu() -> Check:
    from .sensors import Imu
    if Imu().available:
        return Check("MPU-6050 IMU", OK, "found at 0x68 (fall detection active)")
    return Check("MPU-6050 IMU", WARN, "not found - optional sensor")


def _camera() -> Check:
    from .skills.vision import capture
    path = capture()
    if path:
        os.unlink(path)
        return Check("Camera", OK, "frame captured")
    return Check("Camera", WARN,
                  "no frame - check the ribbon cable and raspi-config")


def _microphone() -> Check:
    try:
        import sounddevice as sd
        inputs = [d["name"] for d in sd.query_devices()
                  if d["max_input_channels"] > 0]
        if inputs:
            return Check("Microphone", OK, inputs[0])
        return Check("Microphone", FAIL, "no input device - plug in a USB mic")
    except Exception as e:
        return Check("Microphone", WARN, f"sounddevice unavailable ({e})")


def _audio_out() -> Check:
    player = next((p for p in ("mpv", "mpg123", "ffplay", "aplay")
                   if shutil.which(p)), None)
    if player:
        return Check("Audio player", OK, player)
    return Check("Audio player", FAIL, "install mpv (or alsa-utils)")


def _tts(s: Settings) -> Check:
    from .tts import engine_chain
    chain = engine_chain(s)
    local_ready = shutil.which("piper") and s.piper_voice or \
        shutil.which("espeak-ng") or shutil.which("espeak")
    cloud_ready = s.elevenlabs_api_key or s.openai_api_key
    if cloud_ready or local_ready:
        return Check("Text-to-speech", OK, " -> ".join(chain))
    return Check("Text-to-speech", FAIL,
                  "no engine - install espeak-ng or set an API key")


def _stt(s: Settings) -> Check:
    if s.openai_api_key:
        return Check("Speech-to-text", OK, "Whisper API")
    try:
        import vosk  # noqa: F401
        return Check("Speech-to-text", OK, "Vosk (offline)")
    except ImportError:
        return Check("Speech-to-text", FAIL,
                      "no engine - set OPENAI_API_KEY or pip install vosk")


def _llm(s: Settings) -> Check:
    if s.openai_api_key:
        return Check("LLM brain", OK, f"OpenAI ({s.openai_model})")
    if s.llm_base_url:
        return Check("LLM brain", OK, f"local server {s.llm_base_url}")
    return Check("LLM brain", FAIL,
                  "set OPENAI_API_KEY or TARS_LLM_BASE_URL in .env")


def _ffmpeg() -> Check:
    if shutil.which("ffmpeg"):
        return Check("ffmpeg", OK, "browser voice + offline STT conversions ready")
    return Check("ffmpeg", WARN, "missing - browser mic needs it with Vosk")


def _disk() -> Check:
    du = shutil.disk_usage("/")
    free_gb = du.free / 2**30
    status = OK if free_gb > 2 else WARN
    return Check("Disk space", status, f"{free_gb:.1f} GiB free")


def run_checks(s: Settings) -> list[Check]:
    return [_python(), _i2c(), _pca9685(), _imu(), _camera(), _microphone(),
            _audio_out(), _tts(s), _stt(s), _llm(s), _ffmpeg(), _disk()]


def print_report(s: Settings) -> int:
    """Returns a shell exit code: 0 if nothing FAILed."""
    checks = run_checks(s)
    width = max(len(c.name) for c in checks)
    print("TARS self-test\n" + "-" * (width + 30))
    for c in checks:
        print(f"{MARKS[c.status]} {c.name:<{width}}  {c.detail}")
    fails = sum(1 for c in checks if c.status == FAIL)
    warns = sum(1 for c in checks if c.status == WARN)
    print("-" * (width + 30))
    print(f"{fails} failure(s), {warns} warning(s)"
          + (" - all systems nominal." if fails == 0 else ""))
    return 1 if fails else 0
