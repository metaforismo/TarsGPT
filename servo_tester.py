#!/usr/bin/env python3
"""Interactive servo calibration tool.

Run this BEFORE the first full start: find each servo's safe min/neutral/max
PWM ticks, then copy the values into data/settings.json (key "pwm") or
tars/config.py defaults.

Commands:
  <channel>            select a servo channel (0-15)
  <value>              drive the selected channel to a PWM tick (150-650 typical)
  +10 / -10            nudge the current position
  r                    relax (stop driving) the channel
  q                    quit
"""
from tars.config import settings
from tars.movement.driver import ServoDriver

SAFE_MIN, SAFE_MAX = 130, 680


def main():
    driver = ServoDriver(settings.pwm_frequency, sim=settings.sim_mode)
    channel, position = 0, 350
    print(__doc__)
    while True:
        try:
            cmd = input(f"[ch{channel} @ {position}] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if cmd == "q":
            break
        elif cmd == "r":
            driver.relax(channel)
            print(f"channel {channel} relaxed")
        elif cmd.startswith(("+", "-")) and cmd[1:].isdigit():
            position = max(SAFE_MIN, min(SAFE_MAX, position + int(cmd)))
            driver.set_pwm(channel, position)
        elif cmd.isdigit():
            n = int(cmd)
            if n <= 15:
                channel = n
                print(f"selected channel {channel}")
            elif SAFE_MIN <= n <= SAFE_MAX:
                position = n
                driver.set_pwm(channel, position)
            else:
                print(f"PWM out of safe range {SAFE_MIN}-{SAFE_MAX}")
        elif cmd:
            print("unknown command - see header for usage")


if __name__ == "__main__":
    main()
