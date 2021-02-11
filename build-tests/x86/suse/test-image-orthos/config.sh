#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2006 SUSE LINUX Products GmbH. All rights reserved
#               :
# AUTHOR        : Marcus Schaefer <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#               :
#               :
# STATUS        : BETA
#----------------
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
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Set hostname via dhcp
#--------------------------------------
sed -i 's/DHCLIENT_SET_HOSTNAME="no"/DHCLIENT_SET_HOSTNAME="yes"/g' /etc/sysconfig/network/dhcp

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService network

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
