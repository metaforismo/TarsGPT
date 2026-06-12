#!/bin/bash
# TarsGPT first-boot configurator.
#
# After flashing the image, the FAT boot partition is editable from any
# computer. Drop these files there and they are applied on next boot:
#
#   tarsgpt.env   copied to the robot's .env (API keys, language, ...)
#   wifi.txt      line 1: network name (SSID), line 2: password
#
# Applied files are renamed *.applied so secrets don't linger in plain
# sight and the service stays idempotent. Paths are overridable for tests.
set -e
BOOT_DIR="${BOOT_DIR:-/boot/firmware}"
TARS_DIR="${TARS_DIR:-/home/pi/TarsGPT}"
WIFI_DIR="${WIFI_DIR:-/etc/NetworkManager/system-connections}"
TARS_UID="${TARS_UID:-1000}"

[ -d "$BOOT_DIR" ] || BOOT_DIR=/boot

if [ -f "$BOOT_DIR/tarsgpt.env" ]; then
    install -m 600 "$BOOT_DIR/tarsgpt.env" "$TARS_DIR/.env"
    chown "$TARS_UID:$TARS_UID" "$TARS_DIR/.env" 2>/dev/null || true
    mv "$BOOT_DIR/tarsgpt.env" "$BOOT_DIR/tarsgpt.env.applied"
    echo "tars-firstboot: .env installed"
fi

if [ -f "$BOOT_DIR/wifi.txt" ]; then
    SSID=$(sed -n 1p "$BOOT_DIR/wifi.txt" | tr -d '\r')
    PSK=$(sed -n 2p "$BOOT_DIR/wifi.txt" | tr -d '\r')
    if [ -n "$SSID" ]; then
        mkdir -p "$WIFI_DIR"
        CONN="$WIFI_DIR/tarsgpt-wifi.nmconnection"
        {
            echo "[connection]"
            echo "id=tarsgpt-wifi"
            echo "type=wifi"
            echo "[wifi]"
            echo "ssid=$SSID"
            if [ -n "$PSK" ]; then
                echo "[wifi-security]"
                echo "key-mgmt=wpa-psk"
                echo "psk=$PSK"
            fi
            echo "[ipv4]"
            echo "method=auto"
            echo "[ipv6]"
            echo "method=auto"
        } > "$CONN"
        chmod 600 "$CONN"
        command -v nmcli >/dev/null && nmcli connection reload || true
        echo "tars-firstboot: wifi '$SSID' configured"
    fi
    mv "$BOOT_DIR/wifi.txt" "$BOOT_DIR/wifi.txt.applied"
fi
exit 0
