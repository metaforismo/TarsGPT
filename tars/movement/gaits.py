"""High-level TARS gaits built from interpolated servo sweeps.

The walking cycle: lift the torso, rotate the legs forward, then drop and
re-lift the torso quickly ("bump") so TARS pivots over its legs and lands with
the torso flush to the floor - this keeps the gait working across surfaces
with different friction.
"""
import json
import logging
import threading
import time
from .driver import ServoDriver
from ..config import DATA_DIR, Settings

log = logging.getLogger("tars.gaits")

GAIT_PARAMS_FILE = DATA_DIR / "gait_params.json"

# Tunable walking-gait timing (seconds of sleep per PWM tick). These are the
# parameters the gait optimizer searches over; learned values persist in
# data/gait_params.json and are loaded here at startup.
DEFAULT_GAIT_PARAMS = {
    "lift_delay": 0.001,        # torso lift speed
    "drive_delay": 0.0001,      # leg rotation speed
    "bump_down_delay": 1e-6,    # the fast drop that makes TARS pivot
    "bump_up_delay": 1e-4,      # the recovery right after the bump
    "return_delay": 0.005,      # rotation back to neutral
}


class Gaits:
    def __init__(self, driver: ServoDriver, s: Settings):
        self.d = driver
        self.s = s
        self.p = s.pwm
        self.gp = dict(DEFAULT_GAIT_PARAMS)
        self._load_gait_params()
        self._lock = threading.Lock()  # one whole-body move at a time
        self.arm = dict(port_main=self.p["port_main"], star_main=self.p["star_main"],
                        port_forearm=self.p["port_forearm"], star_forearm=self.p["star_forearm"],
                        port_hand=self.p["port_hand"], star_hand=self.p["star_hand"])
        self._posed = False

    # ---------- gait parameters (learned or hand-tuned) ----------

    def _load_gait_params(self):
        if GAIT_PARAMS_FILE.exists():
            try:
                stored = json.loads(GAIT_PARAMS_FILE.read_text())
                self.gp.update({k: float(v) for k, v in stored.items()
                                if k in DEFAULT_GAIT_PARAMS})
                log.info("loaded learned gait parameters from %s", GAIT_PARAMS_FILE)
            except (json.JSONDecodeError, OSError, ValueError) as e:
                log.warning("ignoring bad gait params file: %s", e)

    def apply_gait_params(self, params: dict):
        self.gp.update({k: float(v) for k, v in params.items()
                        if k in DEFAULT_GAIT_PARAMS})

    def save_gait_params(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        GAIT_PARAMS_FILE.write_text(json.dumps(self.gp, indent=2))

    # ---------- primitives ----------

    def _sweep(self, channel: int, start: int, end: int, delay: float):
        step = 1 if end > start else -1
        for v in range(start, end, step):
            self.d.set_pwm(channel, v)
            time.sleep(delay)
        self.d.set_pwm(channel, end)

    def _sweep_pair(self, ch_a, start_a, end_a, ch_b, start_b, end_b, delay):
        """Sweep two channels in lockstep. Ranges may be asymmetric: both
        channels are interpolated proportionally and land exactly on their
        own end value."""
        steps = max(abs(end_a - start_a), abs(end_b - start_b))
        if steps == 0:
            return
        for i in range(1, steps + 1):
            self.d.set_pwm(ch_a, start_a + round((end_a - start_a) * i / steps))
            self.d.set_pwm(ch_b, start_b + round((end_b - start_b) * i / steps))
            time.sleep(delay)

    # ---------- torso ----------

    def lift_up(self):
        self._sweep(self.s.ch_center_lift, self.p["neutral_height"], self.p["up_height"], self.gp["lift_delay"])

    def lift_down(self):
        self._sweep(self.s.ch_center_lift, self.p["neutral_height"], self.p["down_height"], self.gp["lift_delay"])

    def legs_forward(self):
        self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["forward_port"],
                         self.s.ch_star_drive, self.p["neutral_star"], self.p["forward_star"], self.gp["drive_delay"])

    def legs_backward(self):
        self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["back_port"],
                         self.s.ch_star_drive, self.p["neutral_star"], self.p["back_star"], self.gp["drive_delay"])

    def torso_bump(self):
        """Fast down-up of the lift servo: makes TARS pivot onto its torso."""
        self._sweep(self.s.ch_center_lift, self.p["up_height"], self.p["down_height"], self.gp["bump_down_delay"])
        self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["up_height"], self.gp["bump_up_delay"])

    def _return_rotation(self, slow=False):
        self._sweep_pair(self.s.ch_port_drive, self.p["forward_port"], self.p["neutral_port"],
                         self.s.ch_star_drive, self.p["forward_star"], self.p["neutral_star"],
                         self.gp["return_delay"] * (2 if slow else 1))

    def _return_vertical(self, slow=False):
        d1, d2 = (0.001, 0.001) if slow else (0.00005, 0.00001)
        self._sweep(self.s.ch_center_lift, self.p["up_height"], self.p["down_height"], d1)
        if slow:
            time.sleep(0.25)
        self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], d2)

    def torso_return(self, slow=False):
        """Vertical + rotation back to neutral, in parallel."""
        t1 = threading.Thread(target=self._return_rotation, args=(slow,))
        t2 = threading.Thread(target=self._return_vertical, args=(slow,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    # ---------- public moves ----------

    def step_forward(self):
        with self._lock:
            self.lift_up()
            self.legs_forward()
            self.torso_bump()
            self.torso_return()

    def turn_right(self):
        with self._lock:
            self.lift_down()
            self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["forward_port"],
                             self.s.ch_star_drive, self.p["neutral_star"], self.p["back_star"], 0.001)
            self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], 0.001)
            self._sweep_pair(self.s.ch_port_drive, self.p["forward_port"], self.p["neutral_port"],
                             self.s.ch_star_drive, self.p["back_star"], self.p["neutral_star"], 0.005)

    def turn_left(self):
        with self._lock:
            self.lift_down()
            self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["back_port"],
                             self.s.ch_star_drive, self.p["neutral_star"], self.p["forward_star"], 0.001)
            self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], 0.001)
            self._sweep_pair(self.s.ch_port_drive, self.p["back_port"], self.p["neutral_port"],
                             self.s.ch_star_drive, self.p["forward_star"], self.p["neutral_star"], 0.005)

    def pose(self):
        """Lean back into the 'monolith' display pose (toggles)."""
        with self._lock:
            if not self._posed:
                self.lift_down()
                self.legs_backward()
                self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["up_height"], 0.001)
                self._posed = True
            else:
                t1 = threading.Thread(target=self._sweep_pair, args=(
                    self.s.ch_port_drive, self.p["back_port"], self.p["neutral_port"],
                    self.s.ch_star_drive, self.p["back_star"], self.p["neutral_star"], 0.01))
                t2 = threading.Thread(target=self._return_vertical, args=(True,))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                self._posed = False

    def neutral(self):
        """Drive everything to the calibrated neutral stance."""
        with self._lock:
            self.d.set_pwm(self.s.ch_center_lift, self.p["neutral_height"])
            self.d.set_pwm(self.s.ch_port_drive, self.p["neutral_port"])
            self.d.set_pwm(self.s.ch_star_drive, self.p["neutral_star"])
            for key, ch in (("port_main", self.s.ch_port_main), ("star_main", self.s.ch_star_main),
                            ("port_forearm", self.s.ch_port_forearm), ("star_forearm", self.s.ch_star_forearm),
                            ("port_hand", self.s.ch_port_hand), ("star_hand", self.s.ch_star_hand)):
                self.arm[key] = self.p[key]
                self.d.set_pwm(ch, self.p[key])

    # ---------- arms ----------

    # absolute PWM bounds a servo may ever be driven to (matches servo_tester)
    SAFE_MIN, SAFE_MAX = 130, 680

    def nudge_arm(self, joint: str, direction: int, amount: int = 10):
        """joint: port_main|star_main|port_forearm|star_forearm|port_hand|star_hand.
        direction: +1 / -1. Port joints are mirrored, so +1 decreases their PWM.
        Clamped to SAFE_MIN..SAFE_MAX so repeated nudges cannot force a servo
        past its mechanical stop."""
        sign = -1 if joint.startswith("port") else 1
        self.arm[joint] = max(self.SAFE_MIN,
                              min(self.SAFE_MAX,
                                  self.arm[joint] + sign * direction * amount))
        ch = getattr(self.s, f"ch_{joint}")
        self.d.set_pwm(ch, self.arm[joint])
