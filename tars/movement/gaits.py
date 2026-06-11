"""High-level TARS gaits built from interpolated servo sweeps.

The walking cycle: lift the torso, rotate the legs forward, then drop and
re-lift the torso quickly ("bump") so TARS pivots over its legs and lands with
the torso flush to the floor - this keeps the gait working across surfaces
with different friction.
"""
import threading
import time
from .driver import ServoDriver
from ..config import Settings


class Gaits:
    def __init__(self, driver: ServoDriver, s: Settings):
        self.d = driver
        self.s = s
        self.p = s.pwm
        self._lock = threading.Lock()  # one whole-body move at a time
        self.arm = dict(port_main=self.p["port_main"], star_main=self.p["star_main"],
                        port_forearm=self.p["port_forearm"], star_forearm=self.p["star_forearm"],
                        port_hand=self.p["port_hand"], star_hand=self.p["star_hand"])
        self._posed = False

    # ---------- primitives ----------

    def _sweep(self, channel: int, start: int, end: int, delay: float):
        step = 1 if end > start else -1
        for v in range(start, end, step):
            self.d.set_pwm(channel, v)
            time.sleep(delay)
        self.d.set_pwm(channel, end)

    def _sweep_pair(self, ch_a, start_a, end_a, ch_b, start_b, end_b, delay):
        """Sweep two channels in lockstep (drive servos move mirrored)."""
        steps = abs(end_a - start_a)
        dir_a = 1 if end_a > start_a else -1
        dir_b = 1 if end_b > start_b else -1
        a, b = start_a, start_b
        for _ in range(steps):
            a += dir_a
            b += dir_b
            self.d.set_pwm(ch_a, a)
            self.d.set_pwm(ch_b, b)
            time.sleep(delay)

    # ---------- torso ----------

    def lift_up(self):
        self._sweep(self.s.ch_center_lift, self.p["neutral_height"], self.p["up_height"], 0.001)

    def lift_down(self):
        self._sweep(self.s.ch_center_lift, self.p["neutral_height"], self.p["down_height"], 0.001)

    def legs_forward(self):
        self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["forward_port"],
                         self.s.ch_star_drive, self.p["neutral_star"], self.p["forward_star"], 0.0001)

    def legs_backward(self):
        self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["back_port"],
                         self.s.ch_star_drive, self.p["neutral_star"], self.p["back_star"], 0.0001)

    def torso_bump(self):
        """Fast down-up of the lift servo: makes TARS pivot onto its torso."""
        self._sweep(self.s.ch_center_lift, self.p["up_height"], self.p["down_height"], 0.000001)
        self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["up_height"], 0.0001)

    def _return_rotation(self, slow=False):
        self._sweep_pair(self.s.ch_port_drive, self.p["forward_port"], self.p["neutral_port"],
                         self.s.ch_star_drive, self.p["forward_star"], self.p["neutral_star"],
                         0.01 if slow else 0.005)

    def _return_vertical(self, slow=False):
        d1, d2 = (0.001, 0.001) if slow else (0.00005, 0.00001)
        self._sweep(self.s.ch_center_lift, self.p["up_height"], self.p["down_height"], d1)
        if slow:
            time.sleep(0.25)
        self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], d2)

    def torso_return(self, slow=False):
        """Vertical + rotation back to neutral, in parallel."""
        t1 = threading.Thread(target=self._return_rotation, args=(slow,))
        t2 = threading.Thread(target=self._return_vertical, args=(slow,))
        t1.start(); t2.start()
        t1.join(); t2.join()

    # ---------- public moves ----------

    def step_forward(self):
        with self._lock:
            self.lift_up()
            self.legs_forward()
            self.torso_bump()
            self.torso_return()

    def turn_right(self):
        with self._lock:
            self.lift_down()
            self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["forward_port"],
                             self.s.ch_star_drive, self.p["neutral_star"], self.p["back_star"], 0.001)
            self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], 0.001)
            self._sweep_pair(self.s.ch_port_drive, self.p["forward_port"], self.p["neutral_port"],
                             self.s.ch_star_drive, self.p["back_star"], self.p["neutral_star"], 0.005)

    def turn_left(self):
        with self._lock:
            self.lift_down()
            self._sweep_pair(self.s.ch_port_drive, self.p["neutral_port"], self.p["back_port"],
                             self.s.ch_star_drive, self.p["neutral_star"], self.p["forward_star"], 0.001)
            self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["neutral_height"], 0.001)
            self._sweep_pair(self.s.ch_port_drive, self.p["back_port"], self.p["neutral_port"],
                             self.s.ch_star_drive, self.p["forward_star"], self.p["neutral_star"], 0.005)

    def pose(self):
        """Lean back into the 'monolith' display pose (toggles)."""
        with self._lock:
            if not self._posed:
                self.lift_down()
                self.legs_backward()
                self._sweep(self.s.ch_center_lift, self.p["down_height"], self.p["up_height"], 0.001)
                self._posed = True
            else:
                t1 = threading.Thread(target=self._sweep_pair, args=(
                    self.s.ch_port_drive, self.p["back_port"], self.p["neutral_port"],
                    self.s.ch_star_drive, self.p["back_star"], self.p["neutral_star"], 0.01))
                t2 = threading.Thread(target=self._return_vertical, args=(True,))
                t1.start(); t2.start()
                t1.join(); t2.join()
                self._posed = False

    def neutral(self):
        """Drive everything to the calibrated neutral stance."""
        with self._lock:
            self.d.set_pwm(self.s.ch_center_lift, self.p["neutral_height"])
            self.d.set_pwm(self.s.ch_port_drive, self.p["neutral_port"])
            self.d.set_pwm(self.s.ch_star_drive, self.p["neutral_star"])
            for key, ch in (("port_main", self.s.ch_port_main), ("star_main", self.s.ch_star_main),
                            ("port_forearm", self.s.ch_port_forearm), ("star_forearm", self.s.ch_star_forearm),
                            ("port_hand", self.s.ch_port_hand), ("star_hand", self.s.ch_star_hand)):
                self.arm[key] = self.p[key]
                self.d.set_pwm(ch, self.p[key])

    # ---------- arms ----------

    def nudge_arm(self, joint: str, direction: int, amount: int = 10):
        """joint: port_main|star_main|port_forearm|star_forearm|port_hand|star_hand.
        direction: +1 / -1. Port joints are mirrored, so +1 decreases their PWM."""
        sign = -1 if joint.startswith("port") else 1
        self.arm[joint] += sign * direction * amount
        ch = getattr(self.s, f"ch_{joint}")
        self.d.set_pwm(ch, self.arm[joint])
