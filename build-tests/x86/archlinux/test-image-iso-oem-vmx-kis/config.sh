#!/bin/bash
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3

#======================================
# Enable lan0 interface
#--------------------------------------
netctl enable ethernet-dhcp

#======================================
# Enable dns resolution
#--------------------------------------
baseInsertService systemd-resolved

#======================================
# Enable first mirror in mirrorlist
#--------------------------------------
sed -ie '0,/#Server/s/#Server/Server/' /etc/pacman.d/mirrorlist

exit 0
