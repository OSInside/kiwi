#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable dbus-broker
systemctl enable NetworkManager
systemctl enable sshd
