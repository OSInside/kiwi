#!/bin/bash
# shellcheck disable=SC1091
test -f /.kconfig && . /.kconfig

declare kiwi_iname=${kiwi_iname}

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [${kiwi_iname}]..."

#======================================
# Activate services
#--------------------------------------
baseInsertService dbus-broker
baseInsertService NetworkManager

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
