"""Interactive gait trainer.

    python -m tars.learn --reward measured              # on the robot
    python -m tars.learn --reward sim --sim --save      # full dry-run

Measured runs save the best parameters to data/gait_params.json (loaded
automatically at the next start); sim runs only save with --save.
"""
import argparse
import logging

from ..config import settings
from ..movement import ServoDriver, Gaits
from .optimizer import GaitOptimizer
from .rewards import MeasuredReward, SimReward


def main():
    parser = argparse.ArgumentParser(description="TARS gait optimizer")
    parser.add_argument("--reward", choices=["measured", "camera", "sim"],
                        default="measured")
    parser.add_argument("--iterations", type=int, default=12,
                        help="candidate gaits to try (default 12)")
    parser.add_argument("--steps", type=int, default=3,
                        help="steps walked per candidate (default 3)")
    parser.add_argument("--sim", action="store_true", help="simulate servos")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--save", action="store_true",
                        help="save the result even for --reward sim")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gaits = Gaits(ServoDriver(settings.pwm_frequency,
                              sim=args.sim or settings.sim_mode), settings)

    if args.reward == "measured":
        reward_fn = MeasuredReward(gaits, steps=args.steps)
        print(f"Gait training: {args.iterations} candidates x {args.steps} steps.")
        print("You need ~2 m of free floor and a tape measure (or floor tiles).")
    elif args.reward == "camera":
        from .vision_reward import CameraReward
        reward_fn = CameraReward(gaits, steps=args.steps)
        print(f"Camera-rewarded training: {args.iterations} candidates x "
              f"{args.steps} steps. Keep the scene static; Ctrl-C saves the "
              "best gait found so far.")
    else:
        reward_fn = SimReward(noise=0.3, seed=args.seed)

    optimizer = GaitOptimizer(reward_fn, seed=args.seed)
    result = optimizer.optimize(start=dict(gaits.gp), iterations=args.iterations)

    print(f"\nBest reward: {result.best_reward:.3f}")
    print("Best parameters:")
    for key, value in result.best_params.items():
        print(f"  {key:18s} = {value:.3e}")

    if args.reward in ("measured", "camera") or args.save:
        gaits.apply_gait_params(result.best_params)
        gaits.save_gait_params()
        print("Saved to data/gait_params.json - active from the next start.")
    else:
        print("(dry run: pass --save to persist)")


if __name__ == "__main__":
    main()
