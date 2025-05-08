#!/bin/bash
set -ex

declare kiwi_iname=${kiwi_iname}
declare kiwi_profiles=${kiwi_profiles}

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

#======================================
# bootctl writes to read-only area
#--------------------------------------
# systemd bootctl writes to /etc/kernel which is not
# possible on a read-only device. Thus we relink this
# into the ESP
rm -rf /etc/kernel
ln -s /boot/efi /etc/kernel

#======================================
# Include erofs module
#--------------------------------------
# remove from blacklist
rm -f /usr/lib/modprobe.d/60-blacklist_fs-erofs.conf
