#!/bin/bash

set -ex

# shellcheck disable=SC1091
test -f /.kconfig && . /.kconfig

#======================================
# Activate services
#--------------------------------------
baseInsertService dbus-broker
baseInsertService NetworkManager

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
