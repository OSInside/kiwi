#!/bin/bash
set -ex

#======================================
# Enable lan0 interface
#--------------------------------------
netctl enable ethernet-dhcp

#======================================
# Enable dns resolution
#--------------------------------------
systemctl enable systemd-resolved

#======================================
# Enable first mirror in mirrorlist
#--------------------------------------
sed -ie '0,/#Server/s/#Server/Server/' /etc/pacman.d/mirrorlist

#======================================
# Generate system locale and configure it
#--------------------------------------
sed -ie '0,/#en_US.UTF-8/s/#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
