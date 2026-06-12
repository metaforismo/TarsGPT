"""Domain-randomized simulation reward.

Each candidate gait walks in N randomized worlds (friction, servo strength,
speed, mass) and the reward is mean - lambda*std across them: what survives
every world has a chance of surviving reality. The same N worlds are reused
for every candidate (common random numbers), so the optimizer compares
gaits, not luck - and the compiled physics is reused across episodes, so a
candidate costs milliseconds.

If `--fit-sim` calibrated the sim against your real sessions, the world
randomization is centered on the calibrated constants.
"""
import json
import logging
import random
import statistics

from ..config import DATA_DIR
from ..movement.gaits import Gaits
from .mujoco_sim import MujocoDriver

log = logging.getLogger("tars.learn.mujoco")

SIM_CALIBRATION_FILE = DATA_DIR / "sim_calibration.json"


def load_sim_calibration() -> dict | None:
    if not SIM_CALIBRATION_FILE.exists():
        return None
    try:
        return json.loads(SIM_CALIBRATION_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_sim_calibration(constants: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SIM_CALIBRATION_FILE.write_text(json.dumps(constants, indent=2))


class MujocoReward:
    def __init__(self, s, steps: int = 3, randomizations: int = 6,
                 seed: int | None = None, fall_penalty: float = -5.0,
                 wobble_weight: float = 0.01, robustness: float = 0.5,
                 worlds: list[dict] | None = None, print_fn=None):
        self.s = s
        self.steps = steps
        self.fall_penalty = fall_penalty
        self.wobble_weight = wobble_weight
        self.robustness = robustness
        self.print_fn = print_fn or (lambda *_: None)
        if worlds is None:
            worlds = self._draw_worlds(max(1, randomizations), seed)
        self.worlds = worlds
        # compile each world's physics once; episodes then just reset()
        self._drivers = [MujocoDriver(s, **world) for world in self.worlds]
        self._gaits = [Gaits(driver, s) for driver in self._drivers]

    @staticmethod
    def _draw_worlds(n: int, seed) -> list[dict]:
        rng = random.Random(seed)
        calibration = load_sim_calibration() or {}

        def around(key, lo, hi, spread):
            center = calibration.get(key)
            if center is None:
                return rng.uniform(lo, hi)
            return rng.uniform(max(lo, center * (1 - spread)),
                               min(hi, center * (1 + spread)))

        return [{
            "friction": around("friction", 0.35, 1.2, 0.25),
            "kp_scale": around("kp_scale", 0.7, 1.3, 0.2),
            "speed_scale": around("speed_scale", 0.7, 1.3, 0.2),
            "mass_scale": rng.uniform(0.8, 1.2),
        } for _ in range(n)]

    def _episode(self, params: dict, index: int) -> float:
        driver = self._drivers[index]
        driver.reset()
        gaits = self._gaits[index]
        gaits.apply_gait_params(params)
        start_x = driver.torso_x
        for _ in range(self.steps):
            gaits.step_forward()
        driver.sleep(0.4)
        if not driver.upright:
            return self.fall_penalty
        distance_cm = (driver.torso_x - start_x) * 100
        return (distance_cm / self.steps
                - self.wobble_weight * driver.mean_wobble())

    def __call__(self, params: dict) -> float:
        rewards = []
        for index in range(len(self.worlds)):
            reward = self._episode(params, index)
            if reward <= self.fall_penalty:
                # fail fast: one fall disqualifies the candidate outright
                self.print_fn(f"  sim world {index + 1}: FELL -> "
                              f"{self.fall_penalty}")
                return self.fall_penalty
            rewards.append(reward)
        mean = statistics.fmean(rewards)
        spread = statistics.pstdev(rewards) if len(rewards) > 1 else 0.0
        score = mean - self.robustness * spread
        self.print_fn(f"  sim worlds: mean {mean:+.2f} cm/step, "
                      f"spread {spread:.2f} -> score {score:+.2f}")
        return score
