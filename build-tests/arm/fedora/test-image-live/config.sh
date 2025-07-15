#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable systemd-networkd
systemctl enable systemd-resolved
