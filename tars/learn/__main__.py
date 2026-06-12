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


def correlate(args):
    """Replay logged real evaluations through the sim: the honesty check."""
    from .correlate import correlate_log, verdict
    from .mujoco_reward import MujocoReward
    from .training_log import TrainingLog
    log_data = TrainingLog.load()
    if log_data is None:
        print("No training log found - run a real session first "
              "(--reward measured or camera).")
        return 1
    if log_data.get("mode") not in ("measured", "camera"):
        print(f"Warning: last logged session was '{log_data.get('mode')}', "
              "not a real-robot one; correlation against it is circular.")
    reward_fn = MujocoReward(settings, steps=args.steps,
                             randomizations=args.dr, seed=args.seed or 0)
    try:
        rho, n = correlate_log(reward_fn, log_data)
    except ValueError as e:
        print(f"Cannot correlate: {e}")
        return 1
    print(f"Spearman rank correlation sim vs real over {n} evaluations: "
          f"rho = {rho:+.2f}")
    print(f"Verdict: {verdict(rho)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="TARS gait optimizer")
    parser.add_argument("--reward", choices=["measured", "camera", "mujoco", "sim"],
                        default="measured")
    parser.add_argument("--dr", type=int, default=6,
                        help="randomized worlds per candidate for --reward "
                             "mujoco (default 6)")
    parser.add_argument("--correlate", action="store_true",
                        help="replay logged real sessions through the MuJoCo "
                             "reward and report rank correlation")
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
    parser.add_argument("--wobble-weight", type=float, default=0.01,
                        help="stability tax: reward minus WEIGHT x mean gyro "
                             "rate in deg/s (default 0.01, 0 disables)")
    parser.add_argument("--calibrate-camera", action="store_true",
                        help="one-time px-per-cm calibration: slide TARS a "
                             "known distance, the camera reward then scores "
                             "in real centimeters")
    args = parser.parse_args()

    if args.calibrate_camera:
        return calibrate_camera()
    if args.correlate:
        return correlate(args)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gaits = Gaits(ServoDriver(settings.pwm_frequency,
                              sim=args.sim or settings.sim_mode), settings)

    if args.reward == "measured":
        reward_fn = MeasuredReward(gaits, steps=args.steps)
        print(f"Gait training: {args.iterations} candidates x {args.steps} steps.")
        print("You need ~2 m of free floor and a tape measure (or floor tiles).")
    elif args.reward == "mujoco":
        from .mujoco_reward import MujocoReward
        reward_fn = MujocoReward(settings, steps=args.steps,
                                 randomizations=args.dr, seed=args.seed,
                                 print_fn=print)
        print(f"Sim pre-filter: {args.iterations} candidates x {args.steps} "
              f"steps x {args.dr} randomized worlds. The sim proposes - "
              "verify the winner on the real robot before trusting it.")
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
            reward_fn = FallGuard(reward_fn, imu,
                                  wobble_weight=max(0.0, args.wobble_weight))
            print("MPU-6050 detected: automatic fall penalty active"
                  + (f", stability tax x{args.wobble_weight}."
                     if args.wobble_weight > 0 else "."))

    from .training_log import TrainingLog
    train_log = TrainingLog(args.reward)
    optimizer = GaitOptimizer(reward_fn, seed=args.seed)
    result = optimizer.optimize(
        start=dict(gaits.gp), iterations=args.iterations,
        on_step=lambda i, params, reward, best:
            train_log.record(i, reward, best, params=params))

    print(f"\nBest reward: {result.best_reward:.3f}")
    print("Best parameters:")
    for key, value in result.best_params.items():
        print(f"  {key:18s} = {value:.3e}")

    if args.reward in ("measured", "camera") or args.save:
        gaits.apply_gait_params(result.best_params)
        gaits.save_gait_params()
        print("Saved to data/gait_params.json - active from the next start.")
    elif args.reward == "mujoco":
        print("(sim result NOT saved: verify the winner on the robot with "
              "--reward measured/camera, or force with --save)")
    else:
        print("(dry run: pass --save to persist)")


if __name__ == "__main__":
    main()
