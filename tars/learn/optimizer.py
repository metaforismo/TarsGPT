"""(1+1) evolution strategy over the gait timing parameters.

Why this and not gradient RL: the search space is 5 bounded scalars, every
evaluation costs real robot wear, and the reward (centimeters walked) is
noisy - a simple adaptive hill climber is the right tool and is fully
inspectable. Mutations happen in log-space because the parameters span
several orders of magnitude; the step size adapts with a 1/5th-success
rule so the search widens when it is winning and narrows when it stalls.
"""
import logging
import math
import random
from dataclasses import dataclass, field

from ..movement.gaits import DEFAULT_GAIT_PARAMS

log = logging.getLogger("tars.learn")


@dataclass(frozen=True)
class ParamSpec:
    name: str
    lo: float
    hi: float


SEARCH_SPACE = [
    ParamSpec("lift_delay",      2e-4, 4e-3),
    ParamSpec("drive_delay",     2e-5, 1e-3),
    ParamSpec("bump_down_delay", 1e-7, 5e-5),
    ParamSpec("bump_up_delay",   1e-5, 1e-3),
    ParamSpec("return_delay",    1e-3, 2e-2),
]


@dataclass
class OptResult:
    best_params: dict
    best_reward: float
    history: list = field(default_factory=list)  # [(params, reward), ...]


class GaitOptimizer:
    def __init__(self, reward_fn, space=None, seed=None, sigma=0.5):
        """reward_fn(params: dict) -> float; higher is better."""
        self.reward_fn = reward_fn
        self.space = space or SEARCH_SPACE
        self.rng = random.Random(seed)
        self.sigma = sigma

    def _clip(self, spec: ParamSpec, value: float) -> float:
        return max(spec.lo, min(spec.hi, value))

    def _mutate(self, params: dict) -> dict:
        child = dict(params)
        for spec in self.space:
            mutated = math.exp(math.log(params[spec.name])
                               + self.rng.gauss(0, self.sigma))
            child[spec.name] = self._clip(spec, mutated)
        return child

    def optimize(self, start: dict | None = None, iterations: int = 20,
                 on_step=None) -> OptResult:
        best = {spec.name: self._clip(spec, (start or DEFAULT_GAIT_PARAMS)[spec.name])
                for spec in self.space}
        best_reward = self.reward_fn(best)
        history = [(dict(best), best_reward)]
        log.info("baseline reward: %.3f", best_reward)

        for i in range(iterations):
            candidate = self._mutate(best)
            try:
                reward = self.reward_fn(candidate)
            except KeyboardInterrupt:
                # hardware sessions get interrupted; keep the best found so far
                log.info("interrupted at iteration %d - keeping best so far", i + 1)
                break
            history.append((dict(candidate), reward))
            if reward > best_reward:
                best, best_reward = candidate, reward
                self.sigma = min(1.0, self.sigma * 1.1)   # winning: explore wider
                log.info("iter %d: improved to %.3f", i + 1, reward)
            else:
                self.sigma = max(0.05, self.sigma * 0.85)  # stalling: narrow down
            if on_step:
                on_step(i + 1, candidate, reward, best_reward)

        return OptResult(best_params=best, best_reward=best_reward,
                         history=history)
