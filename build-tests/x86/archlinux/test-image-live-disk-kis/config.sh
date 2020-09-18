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

#======================================
# Generate system locale and configure it
#--------------------------------------
sed -ie '0,/#en_US.UTF-8/s/#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
