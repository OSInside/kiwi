#!/bin/bash
set -ex

#======================================
# Set hostname via dhcp
#--------------------------------------
sed -i 's/DHCLIENT_SET_HOSTNAME="no"/DHCLIENT_SET_HOSTNAME="yes"/g' /etc/sysconfig/network/dhcp

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd
systemctl enable network

#======================================
# setup dracut for live system
#--------------------------------------
echo 'add_drivers+=" brd "' >> \
    /etc/dracut.conf.d/10-liveroot-file.conf
