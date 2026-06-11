"""Reward functions for gait optimization.

MeasuredReward is the verifiable one: the robot physically walks and the
reward is the distance it actually covered (tape measure on the floor, or
marks on tiles). SimReward is a deterministic surrogate with a known
optimum, used to test and demo the optimization machinery off-robot.
"""
import math
import random


class SimReward:
    """Surrogate landscape with a hidden optimum in log-space.

    reward = 10 - sum((log10(v) - log10(optimum))^2) + noise
    Deterministic when noise=0, so the optimizer's behavior is verifiable
    in tests; with noise>0 it mimics real measurement jitter.
    """

    OPTIMUM = {
        "lift_delay": 8e-4,
        "drive_delay": 1.5e-4,
        "bump_down_delay": 3e-6,
        "bump_up_delay": 2e-4,
        "return_delay": 6e-3,
    }

    def __init__(self, noise: float = 0.0, seed: int | None = None):
        self.noise = noise
        self.rng = random.Random(seed)

    def __call__(self, params: dict) -> float:
        err = sum((math.log10(params[k]) - math.log10(opt)) ** 2
                  for k, opt in self.OPTIMUM.items() if k in params)
        jitter = self.rng.gauss(0, self.noise) if self.noise else 0.0
        return 10.0 - err + jitter


class FallGuard:
    """Wrap any reward with an IMU check: if TARS is not upright after the
    candidate's steps, the reward becomes a fixed penalty - falling must
    never look profitable, whatever the camera or surrogate said."""

    def __init__(self, inner, imu, penalty: float = -5.0, print_fn=print):
        self.inner = inner
        self.imu = imu
        self.penalty = penalty
        self.print_fn = print_fn

    def __call__(self, params: dict) -> float:
        reward = self.inner(params)
        if self.imu.is_upright() is False:
            self.print_fn("  IMU: fall detected -> penalty applied")
            return self.penalty
        return reward


class MeasuredReward:
    """Walk a few steps with the candidate parameters, then record the
    distance actually covered. Reward = centimeters per step; enter a
    negative number if TARS fell or walked backwards."""

    def __init__(self, gaits, steps: int = 3, input_fn=input, print_fn=print):
        self.gaits = gaits
        self.steps = steps
        self.input_fn = input_fn
        self.print_fn = print_fn

    def __call__(self, params: dict) -> float:
        self.gaits.apply_gait_params(params)
        self.print_fn(f"\nCandidate: { {k: f'{v:.2e}' for k, v in params.items()} }")
        self.input_fn(f"Place TARS at the start mark and press Enter "
                      f"({self.steps} steps incoming)... ")
        for i in range(self.steps):
            self.print_fn(f"  step {i + 1}/{self.steps}")
            self.gaits.step_forward()
        while True:
            raw = self.input_fn("Distance covered in cm (negative if it fell): ").strip()
            try:
                return float(raw.replace(",", ".")) / self.steps
            except ValueError:
                self.print_fn("Please enter a number, e.g. 12.5")
