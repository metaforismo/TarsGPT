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


def calibrate_camera(input_fn=input, print_fn=print, capture_fn=None):
    """Measure the camera's px-per-cm factor with one manual slide."""
    from .vision_reward import estimate_shift, save_camera_scale
    import math
    if capture_fn is None:
        from ..skills.vision import capture as capture_fn
    print_fn("Camera calibration: TARS will take a frame, then you slide it "
             "forward by a known distance and it takes another.")
    before = capture_fn()
    if before is None:
        print_fn("error: no camera frame captured")
        return 1
    input_fn("Slide TARS forward 10-20 cm (do not rotate it), then press Enter... ")
    after = capture_fn()
    if after is None:
        print_fn("error: no camera frame captured")
        return 1
    dx, dy = estimate_shift(before, after)
    pixels = math.hypot(dx, dy)
    while True:
        raw = input_fn("How many cm did you slide it? ").strip()
        try:
            cm = float(raw.replace(",", "."))
            break
        except ValueError:
            print_fn("Please enter a number, e.g. 15")
    if pixels < 1.0 or cm <= 0:
        print_fn(f"error: shift too small to calibrate ({pixels:.1f} px / {cm} cm)")
        return 1
    save_camera_scale(pixels / cm)
    print_fn(f"Saved: {pixels / cm:.2f} px/cm "
             f"- camera rewards are now in centimeters.")
    return 0


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
    parser.add_argument("--camera-axis", choices=["mag", "x", "-x", "y", "-y"],
                        default="mag",
                        help="image axis for the camera reward (signed; "
                             "'mag' = any direction)")
    parser.add_argument("--no-imu", action="store_true",
                        help="skip the automatic fall penalty even if an "
                             "MPU-6050 is present")
    parser.add_argument("--calibrate-camera", action="store_true",
                        help="one-time px-per-cm calibration: slide TARS a "
                             "known distance, the camera reward then scores "
                             "in real centimeters")
    args = parser.parse_args()

    if args.calibrate_camera:
        return calibrate_camera()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gaits = Gaits(ServoDriver(settings.pwm_frequency,
                              sim=args.sim or settings.sim_mode), settings)

    if args.reward == "measured":
        reward_fn = MeasuredReward(gaits, steps=args.steps)
        print(f"Gait training: {args.iterations} candidates x {args.steps} steps.")
        print("You need ~2 m of free floor and a tape measure (or floor tiles).")
    elif args.reward == "camera":
        from .vision_reward import CameraReward
        reward_fn = CameraReward(gaits, steps=args.steps, axis=args.camera_axis)
        print(f"Camera-rewarded training: {args.iterations} candidates x "
              f"{args.steps} steps. Keep the scene static; Ctrl-C saves the "
              "best gait found so far.")
    else:
        reward_fn = SimReward(noise=0.3, seed=args.seed)

    if args.reward in ("measured", "camera") and not args.no_imu:
        from ..sensors import get_imu
        from .rewards import FallGuard
        imu = get_imu()
        if imu.available:
            reward_fn = FallGuard(reward_fn, imu)
            print("MPU-6050 detected: automatic fall penalty active.")

    from .training_log import TrainingLog
    train_log = TrainingLog(args.reward)
    optimizer = GaitOptimizer(reward_fn, seed=args.seed)
    result = optimizer.optimize(
        start=dict(gaits.gp), iterations=args.iterations,
        on_step=lambda i, _params, reward, best: train_log.record(i, reward, best))

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
