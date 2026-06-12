"""Domain-randomized simulation reward.

Each candidate gait walks in N randomized worlds (friction, servo strength,
mass) and the reward is mean - lambda*std across them: what survives every
world has a chance of surviving reality. The same N worlds are reused for
every candidate (common random numbers), so the optimizer compares gaits,
not luck.
"""
import logging
import random
import statistics

from ..movement.gaits import Gaits
from .mujoco_sim import MujocoDriver

log = logging.getLogger("tars.learn.mujoco")


class MujocoReward:
    def __init__(self, s, steps: int = 3, randomizations: int = 6,
                 seed: int | None = None, fall_penalty: float = -5.0,
                 wobble_weight: float = 0.01, robustness: float = 0.5,
                 print_fn=None):
        self.s = s
        self.steps = steps
        self.fall_penalty = fall_penalty
        self.wobble_weight = wobble_weight
        self.robustness = robustness
        self.print_fn = print_fn or (lambda *_: None)
        rng = random.Random(seed)
        self.worlds = [{
            "friction": rng.uniform(0.35, 1.2),
            "kp_scale": rng.uniform(0.7, 1.3),
            "mass_scale": rng.uniform(0.8, 1.2),
        } for _ in range(max(1, randomizations))]

    def _episode(self, params: dict, world: dict) -> float:
        driver = MujocoDriver(self.s, **world)
        gaits = Gaits(driver, self.s)
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
        rewards = [self._episode(params, world) for world in self.worlds]
        mean = statistics.fmean(rewards)
        spread = statistics.pstdev(rewards) if len(rewards) > 1 else 0.0
        score = mean - self.robustness * spread
        self.print_fn(f"  sim worlds: mean {mean:+.2f} cm/step, "
                      f"spread {spread:.2f} -> score {score:+.2f}")
        return score
