"""PCA9685 servo driver wrapper with a simulation fallback.

Works with either the legacy Adafruit_PCA9685 library or the current
adafruit-circuitpython-pca9685 stack. Without hardware (or with TARS_SIM=1)
it logs movements instead, so the whole app can be developed off-robot.

Drivers expose set_pwm/relax/sleep and a `parallel_safe` flag; the physics
driver in tars.learn duck-types this interface, which is how the exact same
Gaits code drives both the metal and the simulator.
"""
import logging
import time

log = logging.getLogger("tars.servo")


class ServoDriver:
    parallel_safe = True  # concurrent sweeps from threads are fine on hardware

    def __init__(self, frequency: int = 60, sim: bool = False):
        self.sim = sim
        self._pca = None
        self._legacy = False
        if not sim:
            self._connect(frequency)
        if self._pca is None:
            self.sim = True
            log.warning("No PCA9685 found - running in simulation mode")

    def _connect(self, frequency: int):
        try:  # legacy library (python-pi builds)
            import Adafruit_PCA9685
            self._pca = Adafruit_PCA9685.PCA9685()
            self._pca.set_pwm_freq(frequency)
            self._legacy = True
            return
        except Exception:
            pass
        try:  # current CircuitPython stack
            import board
            import busio
            from adafruit_pca9685 import PCA9685
            self._pca = PCA9685(busio.I2C(board.SCL, board.SDA))
            self._pca.frequency = frequency
        except Exception:
            self._pca = None

    def set_pwm(self, channel: int, value: int):
        """Set a raw 12-bit PWM 'off' tick (0-4095) on a channel."""
        if self.sim:
            log.debug("sim: ch%-2d -> %d", channel, value)
            return
        if self._legacy:
            self._pca.set_pwm(channel, 0, value)
        else:
            # CircuitPython expects a 16-bit duty cycle
            self._pca.channels[channel].duty_cycle = (value << 4) & 0xFFFF

    def relax(self, channel: int):
        """Stop driving a channel (servo goes limp)."""
        if not self.sim:
            self.set_pwm(channel, 0)

    def sleep(self, seconds: float):
        """Gait pacing. Real time here; the physics driver advances the
        simulation clock instead."""
        time.sleep(seconds)
