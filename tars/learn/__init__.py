"""Gait learning: derivative-free optimization of walking parameters
against a verifiable reward (measured distance per step, or a simulated
surrogate for testing the machinery).

    python -m tars.learn --reward measured     # on the robot, tape measure
    python -m tars.learn --reward sim --sim    # dry-run of the whole loop
"""
from .optimizer import GaitOptimizer, SEARCH_SPACE, OptResult
from .rewards import SimReward, MeasuredReward
from .vision_reward import CameraReward, estimate_shift

__all__ = ["GaitOptimizer", "SEARCH_SPACE", "OptResult",
           "SimReward", "MeasuredReward", "CameraReward", "estimate_shift"]
