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

# --robot: turn this machine into a TARS appliance (I2C + autostart)
if [ "${1:-}" = "--robot" ]; then
    echo
    echo "==> Appliance setup (--robot)"
    if command -v raspi-config >/dev/null; then
        sudo raspi-config nonint do_i2c 0 && echo "==> I2C enabled"
    else
        echo "==> raspi-config not found - enable I2C manually if needed"
    fi
    sed -e "s|^User=.*|User=$(whoami)|" \
        -e "s|^WorkingDirectory=.*|WorkingDirectory=$(pwd)|" \
        -e "s|^ExecStart=.*|ExecStart=$(pwd)/.venv/bin/python -m tars.app|" \
        deploy/tars.service | sudo tee /etc/systemd/system/tars.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable tars
    echo "==> TARS will start on every boot (journalctl -u tars -f for logs)."
    echo "==> Add your API key to .env, then: sudo systemctl start tars"
fi
