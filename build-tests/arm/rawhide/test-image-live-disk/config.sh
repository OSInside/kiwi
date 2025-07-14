#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable network
systemctl enable grub_config
