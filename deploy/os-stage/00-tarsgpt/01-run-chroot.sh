#!/bin/bash -e
# TarsGPT OS: preinstall the runtime so the robot is ready on first boot.
on_chroot << EOF
set -e
cd /home/pi
git clone --depth 1 https://github.com/metaforismo/TarsGPT
cd TarsGPT
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install . numpy vosk sounddevice adafruit-circuitpython-pca9685 evdev
cp .env.example .env
chown -R 1000:1000 /home/pi/TarsGPT

# autostart on boot
cp deploy/tars.service /etc/systemd/system/tars.service
systemctl enable tars

# I2C for the PCA9685 and the IMU
CONFIG=/boot/firmware/config.txt
[ -f "\$CONFIG" ] || CONFIG=/boot/config.txt
grep -q "^dtparam=i2c_arm=on" "\$CONFIG" || echo "dtparam=i2c_arm=on" >> "\$CONFIG"
EOF
