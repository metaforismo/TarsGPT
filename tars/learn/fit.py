"""Sim calibration (system identification, the cheap honest kind).

Searches over the simulator's unknown physical constants - friction,
servo strength, servo speed - for the combination under which the sim
RANKS your logged real evaluations most like reality did (Spearman).
The result persists and recenters the domain randomization, so the
pre-filter adapts to your specific build, floor and servos.
"""
import logging
import random

from .correlate import correlate_log, spearman  # noqa: F401  (re-export)

log = logging.getLogger("tars.learn.fit")

CONSTANT_RANGES = {
    "friction": (0.3, 1.2),
    "kp_scale": (0.6, 1.4),
    "speed_scale": (0.6, 1.4),
}


def fit_sim(s, log_data: dict, trials: int = 30, steps: int = 3,
            seed: int = 0, print_fn=print, reward_factory=None) -> dict:
    """Random search over sim constants maximizing rank correlation with the
    logged real rewards. Returns {"friction":..., "kp_scale":...,
    "speed_scale":..., "rho":..., "samples":...}.

    reward_factory(constants) -> callable(params); injectable for tests."""
    if reward_factory is None:
        from .mujoco_reward import MujocoReward

        def reward_factory(constants):
            world = dict(constants, mass_scale=1.0)
            return MujocoReward(s, steps=steps, worlds=[world])

    rng = random.Random(seed)
    candidates = [{k: (lo + hi) / 2 for k, (lo, hi) in CONSTANT_RANGES.items()}]
    candidates += [{k: rng.uniform(lo, hi)
                    for k, (lo, hi) in CONSTANT_RANGES.items()}
                   for _ in range(max(0, trials - 1))]

    best, best_rho, samples = None, -2.0, 0
    for i, constants in enumerate(candidates):
        try:
            rho, samples = correlate_log(reward_factory(constants), log_data)
        except ValueError:
            raise
        except Exception as e:
            log.warning("trial %d failed (%s) - skipping", i + 1, e)
            continue
        marker = ""
        if rho > best_rho:
            best, best_rho = dict(constants), rho
            marker = "  <- best"
        print_fn(f"  trial {i + 1}/{len(candidates)}: "
                 + " ".join(f"{k}={v:.2f}" for k, v in constants.items())
                 + f" -> rho {rho:+.2f}{marker}")
    if best is None:
        raise RuntimeError("every calibration trial failed")
    return dict(best, rho=round(best_rho, 3), samples=samples)
