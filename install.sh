#!/usr/bin/env bash
# TARS installer for Raspberry Pi OS (64-bit). Also works on any Debian/Ubuntu
# machine for development (servos will run in simulation mode).
set -e
cd "$(dirname "$0")"

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev portaudio19-dev \
    espeak-ng mpv alsa-utils i2c-tools ffmpeg

echo "==> Creating virtualenv"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Hardware extras only on a Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "==> Raspberry Pi detected: installing hardware drivers"
    pip install adafruit-circuitpython-pca9685 evdev
    echo "==> Remember to enable I2C: sudo raspi-config -> Interface Options -> I2C"
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env - add your OPENAI_API_KEY before launching"
fi

echo
echo "Done. Launch with:"
echo "  source .venv/bin/activate && python -m tars.app        # on the robot"
echo "  source .venv/bin/activate && python -m tars.app --sim  # on a laptop"
