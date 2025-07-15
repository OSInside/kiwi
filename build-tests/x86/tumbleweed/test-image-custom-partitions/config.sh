#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

#======================================
# Create custom parts mount points
#--------------------------------------
mkdir -p var var/log var/audit

#======================================
# Custom partitions moves root
#--------------------------------------
patch -p0 < /config_partids.patch
