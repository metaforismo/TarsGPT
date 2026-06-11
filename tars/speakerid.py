"""Lightweight speaker identification (experimental).

Builds a compact voice fingerprint per speaker - the average log-energy
profile across frequency bands plus an autocorrelation pitch estimate -
and identifies the closest enrolled profile by cosine similarity. Designed
to tell apart the handful of people living with the robot, not for
security. Profiles persist in data/speakers.json.
"""
import json
import logging
import threading
import wave
from .config import DATA_DIR

log = logging.getLogger("tars.speakerid")

SPEAKERS_FILE = DATA_DIR / "speakers.json"
BANDS = 24
FRAME = 1024
MATCH_THRESHOLD = 0.93   # cosine similarity below this -> unknown speaker
PITCH_TOLERANCE = 0.35   # relative pitch difference allowed for a match


def _numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None


class SpeakerID:
    def __init__(self):
        self._lock = threading.Lock()
        self.profiles: dict[str, dict] = {}  # name -> {"bands": [...], "pitch": float}
        self._load()

    @property
    def available(self) -> bool:
        return _numpy() is not None

    def _load(self):
        if SPEAKERS_FILE.exists():
            try:
                self.profiles = json.loads(SPEAKERS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                self.profiles = {}

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SPEAKERS_FILE.write_text(json.dumps(self.profiles, indent=2))

    # ---------- fingerprinting ----------

    def fingerprint(self, wav_path: str) -> dict | None:
        np = _numpy()
        if np is None:
            return None
        try:
            with wave.open(wav_path, "rb") as w:
                rate = w.getframerate()
                samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        except (OSError, wave.Error) as e:
            log.warning("cannot fingerprint %s: %s", wav_path, e)
            return None
        return self._fingerprint_samples(samples.astype(np.float64), rate)

    def _fingerprint_samples(self, samples, rate: int) -> dict | None:
        np = _numpy()
        n_frames = len(samples) // FRAME
        if n_frames < 5:
            return None
        frames = samples[:n_frames * FRAME].reshape(n_frames, FRAME)
        energy = (frames ** 2).mean(axis=1)
        # voiced frames only: above 20% of the loudest frame
        voiced = frames[energy > 0.2 * energy.max()]
        if len(voiced) < 3:
            return None

        window = np.hanning(FRAME)
        spectrum = np.abs(np.fft.rfft(voiced * window, axis=1)).mean(axis=0)
        # collapse the spectrum into BANDS log-energy bands
        edges = np.linspace(0, len(spectrum), BANDS + 1, dtype=int)
        bands = np.array([np.log1p(spectrum[a:b].mean())
                          for a, b in zip(edges[:-1], edges[1:])])
        norm = np.linalg.norm(bands)
        if norm == 0:
            return None
        bands = bands / norm

        # pitch via autocorrelation on the median voiced frame (60-400 Hz)
        frame = voiced[len(voiced) // 2] * window
        ac = np.correlate(frame, frame, mode="full")[FRAME - 1:]
        lo, hi = int(rate / 400), int(rate / 60)
        pitch = rate / (lo + int(np.argmax(ac[lo:hi]))) if hi > lo else 0.0

        return {"bands": bands.tolist(), "pitch": round(float(pitch), 1)}

    # ---------- enrollment & identification ----------

    def enroll(self, name: str, wav_path: str) -> bool:
        fp = self.fingerprint(wav_path)
        if fp is None:
            return False
        np = _numpy()
        with self._lock:
            old = self.profiles.get(name)
            if old:  # average with the previous enrollment
                fp["bands"] = ((np.array(old["bands"]) + np.array(fp["bands"])) / 2).tolist()
                fp["pitch"] = round((old["pitch"] + fp["pitch"]) / 2, 1)
            self.profiles[name] = fp
            self._save()
        return True

    def identify(self, wav_path: str) -> str | None:
        if not self.profiles:
            return None
        fp = self.fingerprint(wav_path)
        if fp is None:
            return None
        np = _numpy()
        query = np.array(fp["bands"])
        best_name, best_score = None, 0.0
        with self._lock:
            for name, prof in self.profiles.items():
                ref = np.array(prof["bands"])
                score = float(query @ ref)  # both unit-normalized
                if prof["pitch"] and fp["pitch"]:
                    drift = abs(prof["pitch"] - fp["pitch"]) / prof["pitch"]
                    if drift > PITCH_TOLERANCE:
                        continue
                if score > best_score:
                    best_name, best_score = name, score
        return best_name if best_score >= MATCH_THRESHOLD else None
