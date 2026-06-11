"""Camera-based gait reward: no tape measure needed.

The robot's camera grabs a frame before and after the candidate steps;
phase correlation between the two recovers the image translation, which is
proportional to the ground actually covered when the camera looks at a
textured static scene (point it at the floor for best results).

The reward is in pixels - a relative unit, which is all an optimizer needs
(more pixels = more distance, on the same floor with the same camera).
"""
import logging

log = logging.getLogger("tars.learn.camera")


def estimate_shift(image_a, image_b) -> tuple[float, float]:
    """Translation (dx, dy) in pixels between two images (paths or arrays),
    via OpenCV phase correlation with a Hanning window. Raises RuntimeError
    if OpenCV is missing or the images can't be read."""
    try:
        import cv2
        import numpy as np
    except ImportError as e:
        raise RuntimeError("camera reward requires opencv-python "
                           "(pip install opencv-python-headless)") from e

    def to_gray(img):
        if isinstance(img, str):
            loaded = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
            if loaded is None:
                raise RuntimeError(f"cannot read image {img}")
            img = loaded
        elif img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return np.float32(img)

    a, b = to_gray(image_a), to_gray(image_b)
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    window = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
    (dx, dy), _response = cv2.phaseCorrelate(a, b, window)
    return float(dx), float(dy)


class CameraReward:
    """Reward = pixels of camera translation across the candidate's steps.

    capture_fn must return the path of a fresh camera frame (defaults to the
    vision skill's capture). The robot should watch a static, textured scene;
    a fall typically produces a wildly rotated frame whose correlation is
    weak, but supervise the first sessions and prefer MeasuredReward when in
    doubt - it is the ground truth.
    """

    def __init__(self, gaits, steps: int = 3, capture_fn=None, print_fn=print,
                 axis: str = "mag"):
        """axis: 'mag' rewards any translation magnitude; 'x', '-x', 'y' or
        '-y' reward the signed component along one image axis, so walking
        backwards scores negative. Find your build's forward axis with one
        manual push and `estimate_shift` on the two frames."""
        if capture_fn is None:
            from ..skills.vision import capture as capture_fn
        if axis not in ("mag", "x", "-x", "y", "-y"):
            raise ValueError(f"invalid axis {axis!r}")
        self.gaits = gaits
        self.steps = steps
        self.capture_fn = capture_fn
        self.print_fn = print_fn
        self.axis = axis

    def __call__(self, params: dict) -> float:
        import math
        import os
        self.gaits.apply_gait_params(params)
        before = self.capture_fn()
        if before is None:
            raise RuntimeError("no camera frame captured")
        try:
            for i in range(self.steps):
                self.print_fn(f"  step {i + 1}/{self.steps}")
                self.gaits.step_forward()
            after = self.capture_fn()
            if after is None:
                raise RuntimeError("no camera frame captured")
            try:
                dx, dy = estimate_shift(before, after)
            finally:
                if isinstance(after, str):
                    os.unlink(after)
        finally:
            if isinstance(before, str) and os.path.exists(before):
                os.unlink(before)
        distance_px = {"mag": math.hypot(dx, dy), "x": dx, "-x": -dx,
                       "y": dy, "-y": -dy}[self.axis]
        self.print_fn(f"  camera shift: {distance_px:.1f} px (axis={self.axis})")
        return distance_px / self.steps
