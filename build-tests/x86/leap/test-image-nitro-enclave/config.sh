#!/bin/bash
set -ex

#======================================
# Setup services
#--------------------------------------
for service in nitro-enclave-alive sshd vsock_server;do
    systemctl enable "${service}"
done

#======================================
# Allow ssh root login
#--------------------------------------
echo "PermitRootLogin yes" > /etc/ssh/sshd_config.d/root.conf

#======================================
# load virtio_mmio
#--------------------------------------
echo virtio_mmio > /etc/modules-load.d/virtio-mmio.conf

#======================================
# autologin on tty1/serial
#--------------------------------------
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat << EOF > /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/usr/sbin/agetty --autologin root --noclear tty1 $TERM
EOF
systemctl enable getty@tty1
mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d
cat << EOF > /etc/systemd/system/serial-getty@ttyS0.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/usr/sbin/agetty --autologin root --noclear --keep-baud 115200,38400,9600 ttyS0 $TERM
EOF
systemctl enable serial-getty@ttyS0

#======================================
# Masked services
#--------------------------------------
systemctl mask systemd-hwdb-update.service

#======================================
# show vsock_server output
#--------------------------------------
cat << EOF >> /etc/profile
echo "nsm-check output"
/usr/bin/nsm-check
echo "Watching vsock_server output..."
systemctl status vsock_server
journalctl -f -u vsock_server
EOF
