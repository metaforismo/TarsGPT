"""Optional MPU-6050 IMU (~3 EUR, I2C address 0x68): orientation and fall
detection. Shares the I2C bus with the PCA9685 - wire VCC/GND/SDA/SCL in
parallel. Degrades gracefully: without the sensor (or smbus2) every reading
is None and `available` is False.
"""
import logging

log = logging.getLogger("tars.imu")

MPU_ADDRESS = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_SCALE = 16384.0  # LSB per g at the default +/-2g range


class Imu:
    def __init__(self, address: int = MPU_ADDRESS, upright_axis: str = "z"):
        """upright_axis: which accelerometer axis gravity points along when
        TARS stands ('z', '-z', 'x', '-x', 'y', '-y') - depends on how the
        board is mounted in the chassis."""
        self.address = address
        self.upright_axis = upright_axis
        self._bus = None
        try:
            import smbus2
            self._bus = smbus2.SMBus(1)
            self._bus.write_byte_data(address, PWR_MGMT_1, 0)  # wake from sleep
            log.info("MPU-6050 found at 0x%02x", address)
        except Exception as e:
            self._bus = None
            log.debug("no IMU available (%s)", e)

    @property
    def available(self) -> bool:
        return self._bus is not None

    def read_accel(self) -> tuple[float, float, float] | None:
        """Acceleration in g, or None without a sensor."""
        if self._bus is None:
            return None
        try:
            raw = self._bus.read_i2c_block_data(self.address, ACCEL_XOUT_H, 6)
        except OSError as e:
            log.warning("IMU read failed: %s", e)
            return None

        def word(hi, lo):
            value = (raw[hi] << 8) | raw[lo]
            return value - 65536 if value > 32767 else value

        return (word(0, 1) / ACCEL_SCALE,
                word(2, 3) / ACCEL_SCALE,
                word(4, 5) / ACCEL_SCALE)

    def is_upright(self, tolerance: float = 0.6) -> bool | None:
        """True if gravity points along the configured upright axis (i.e.
        TARS is standing), False if it fell over, None without a sensor.
        tolerance is the minimum g-component required (1.0 = perfectly
        vertical; 0.6 allows ~50 degrees of lean)."""
        accel = self.read_accel()
        if accel is None:
            return None
        axis = self.upright_axis.lstrip("-")
        component = dict(x=accel[0], y=accel[1], z=accel[2])[axis]
        if self.upright_axis.startswith("-"):
            component = -component
        return component >= tolerance


_imu: Imu | None = None


def get_imu() -> Imu:
    """Process-wide lazy singleton (one SMBus handle)."""
    global _imu
    if _imu is None:
        _imu = Imu()
    return _imu
