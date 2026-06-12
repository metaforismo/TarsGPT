#!/bin/bash -e
# Install the first-boot configurator into the image (runs outside chroot;
# pi-gen executes this with CWD = this directory and ROOTFS_DIR set).
install -m 755 files/tars-firstboot.sh "${ROOTFS_DIR}/usr/local/sbin/tars-firstboot.sh"
install -m 644 files/tars-firstboot.service "${ROOTFS_DIR}/etc/systemd/system/tars-firstboot.service"
install -m 644 files/motd "${ROOTFS_DIR}/etc/motd"
on_chroot << EOF
systemctl enable tars-firstboot
systemctl enable ssh
EOF
