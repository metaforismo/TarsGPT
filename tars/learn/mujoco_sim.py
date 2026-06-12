"""MuJoCo pre-filter: the same Gaits code that drives the PCA9685 drives a
simplified physics model of TARS.

Philosophy: the sim proposes, reality disposes. The model is deliberately
crude (boxes, ballpark masses from the BOM, MG996R-class actuators) and is
meant to be used with domain randomization + the real-robot verification
step, never trusted as a digital twin. Check it against your own logged
sessions with `python -m tars.learn --correlate`.

Requires `pip install mujoco` (PC recommended; results travel to the robot
as data/gait_params.json).
"""
import logging
import math

log = logging.getLogger("tars.learn.mujoco")

# Geometry/mass ballparks for a V3-style build (~2.3 kg total).
# Forward is +x; legs pitch around y; the center "leg" slides along z.
MODEL_XML = """
<mujoco model="tars-simple">
  <option timestep="0.002"/>
  <worldbody>
    <geom name="floor" type="plane" size="5 5 .1" friction="0.8 0.005 0.0001"/>
    <body name="torso" pos="0 0 0.172">
      <freejoint/>
      <geom name="hull" type="box" size="0.040 0.060 0.140" mass="1.5"
            friction="0.8 0.005 0.0001"/>
      <body name="center_leg" pos="0 0 0">
        <joint name="lift" type="slide" axis="0 0 1" range="-0.06 0.06"
               damping="30"/>
        <geom name="center_foot" type="box" pos="0 0 -0.145"
              size="0.022 0.040 0.025" mass="0.30"
              friction="0.8 0.005 0.0001"/>
      </body>
      <body name="port_leg" pos="0 -0.085 0.02">
        <joint name="port_drive" type="hinge" axis="0 1 0" range="-0.9 0.9"
               damping="0.6"/>
        <geom name="port_geom" type="box" pos="0 0 -0.085"
              size="0.025 0.012 0.090" mass="0.25"
              friction="0.8 0.005 0.0001"/>
      </body>
      <body name="star_leg" pos="0 0.085 0.02">
        <joint name="star_drive" type="hinge" axis="0 1 0" range="-0.9 0.9"
               damping="0.6"/>
        <geom name="star_geom" type="box" pos="0 0 -0.085"
              size="0.025 0.012 0.090" mass="0.25"
              friction="0.8 0.005 0.0001"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <position name="lift" joint="lift" kp="900" forcerange="-90 90"/>
    <position name="port_drive" joint="port_drive" kp="14" forcerange="-1.1 1.1"/>
    <position name="star_drive" joint="star_drive" kp="14" forcerange="-1.1 1.1"/>
  </actuator>
</mujoco>
"""

LIFT_TRAVEL = 0.10    # meters of slider travel across the full PWM lift range
DRIVE_TRAVEL = -0.55  # radians from neutral to "forward" PWM (sign verified
                      # empirically: this orientation walks toward +x)


class MujocoDriver:
    """Duck-types ServoDriver (set_pwm/relax/sleep) against MuJoCo physics.

    sleep() advances the simulation instead of waiting, so the gait's timing
    parameters keep their exact meaning while episodes run orders of
    magnitude faster than wall time.
    """

    parallel_safe = False  # Gaits runs its parallel phases sequentially here
    sim = True

    def __init__(self, s, friction: float = 0.8, kp_scale: float = 1.0,
                 mass_scale: float = 1.0):
        import mujoco
        self._mujoco = mujoco
        self.m = mujoco.MjModel.from_xml_string(MODEL_XML)
        # --- domain randomization knobs ---
        self.m.geom_friction[:, 0] = friction
        self.m.body_mass[:] *= mass_scale
        self.m.actuator_gainprm[:, 0] *= kp_scale
        self.m.actuator_biasprm[:, 1] *= kp_scale
        self.d = mujoco.MjData(self.m)

        p = s.pwm
        # linear PWM->target maps anchored on the same calibration the real
        # robot uses; the slider extends DOWN (negative q lifts the torso)
        self._maps = {
            s.ch_center_lift: self._linear(p["up_height"], -LIFT_TRAVEL / 2,
                                           p["down_height"], LIFT_TRAVEL / 2),
            s.ch_port_drive: self._linear(p["neutral_port"], 0.0,
                                          p["forward_port"], DRIVE_TRAVEL),
            s.ch_star_drive: self._linear(p["neutral_star"], 0.0,
                                          p["forward_star"], DRIVE_TRAVEL),
        }
        self._actuators = {s.ch_center_lift: 0, s.ch_port_drive: 1,
                           s.ch_star_drive: 2}
        self._ranges = list(zip(self.m.actuator_ctrlrange[:, 0],
                                self.m.actuator_ctrlrange[:, 1]))
        self._frac = 0.0
        self.angvel_samples: list[float] = []
        # start in the calibrated neutral stance and let it settle
        self.set_pwm(s.ch_center_lift, p["neutral_height"])
        self.set_pwm(s.ch_port_drive, p["neutral_port"])
        self.set_pwm(s.ch_star_drive, p["neutral_star"])
        self.sleep(0.8)
        self.angvel_samples.clear()

    @staticmethod
    def _linear(pwm_a, target_a, pwm_b, target_b):
        slope = (target_b - target_a) / (pwm_b - pwm_a)
        return lambda pwm: target_a + (pwm - pwm_a) * slope

    # ---- ServoDriver interface ----

    def set_pwm(self, channel: int, value: int):
        aid = self._actuators.get(channel)
        if aid is None:
            return  # arm channels don't exist in the sim
        lo, hi = self._ranges[aid]
        target = self._maps[channel](value)
        if lo < hi:  # 0,0 means unlimited in MJCF
            target = max(lo, min(hi, target))
        self.d.ctrl[aid] = target

    def relax(self, channel: int):
        pass

    def sleep(self, seconds: float):
        """Advance physics by the requested gait-pacing time."""
        self._frac += seconds
        steps = int(self._frac / self.m.opt.timestep)
        self._frac -= steps * self.m.opt.timestep
        for i in range(steps):
            self._mujoco.mj_step(self.m, self.d)
            if i % 10 == 0:
                self.angvel_samples.append(
                    math.degrees(math.hypot(*self.d.qvel[3:6])))

    # ---- episode metrics ----

    @property
    def torso_x(self) -> float:
        return float(self.d.qpos[0])

    @property
    def upright(self) -> bool:
        """zz element of the torso rotation matrix: 1 = vertical, 0 = flat."""
        return float(self.d.xmat[1].reshape(3, 3)[2, 2]) > 0.5

    def mean_wobble(self) -> float:
        """Mean angular speed (deg/s) sampled while the gait ran."""
        if not self.angvel_samples:
            return 0.0
        return sum(self.angvel_samples) / len(self.angvel_samples)
