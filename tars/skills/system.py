"""System skills: vitals (battery, CPU, uptime, disk) and volume control."""
import shutil
import subprocess
import time
from . import skill

_BOOT = time.monotonic()


def read_cpu_temp() -> float | None:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def read_battery() -> dict | None:
    """Voltage/current/power from an INA260 on I2C, if present."""
    try:
        import board
        import adafruit_ina260
        sensor = adafruit_ina260.INA260(board.I2C())
        return {"voltage": round(sensor.voltage, 2),
                "current_ma": round(sensor.current, 0),
                "power_mw": round(sensor.power, 0)}
    except Exception:
        return None


def battery_percent(voltage: float, cells: int = 3) -> int:
    """Rough Li-ion state of charge from pack voltage (3.0-4.2 V per cell)."""
    per_cell = voltage / cells
    return max(0, min(100, round((per_cell - 3.0) / (4.2 - 3.0) * 100)))


@skill("system_status",
       "Report your own vitals: battery, CPU temperature, uptime and disk space.")
def system_status(ctx):
    parts = []
    battery = read_battery()
    if battery:
        pct = battery_percent(battery["voltage"])
        parts.append(f"battery {pct}% ({battery['voltage']} V, {battery['current_ma']} mA)")
    else:
        parts.append("battery sensor not installed")
    temp = read_cpu_temp()
    if temp is not None:
        parts.append(f"CPU {temp} C")
    up = int(time.monotonic() - _BOOT)
    parts.append(f"runtime up {up // 3600}h{(up % 3600) // 60:02d}m")
    du = shutil.disk_usage("/")
    parts.append(f"disk {du.free // 2**30} GiB free of {du.total // 2**30}")
    return "; ".join(parts)


@skill("set_volume",
       "Set your speaker volume, 0-100 percent.",
       {"type": "object", "properties": {
           "percent": {"type": "integer", "minimum": 0, "maximum": 100}},
        "required": ["percent"]})
def set_volume(ctx, percent):
    pct = max(0, min(100, int(percent)))
    if shutil.which("amixer"):
        r = subprocess.run(["amixer", "-M", "sset", "Master", f"{pct}%"],
                           capture_output=True)
        if r.returncode == 0:
            return f"ok: volume set to {pct}%"
    if shutil.which("pactl"):
        r = subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
                           capture_output=True)
        if r.returncode == 0:
            return f"ok: volume set to {pct}%"
    return "error: no mixer available (install alsa-utils)"
