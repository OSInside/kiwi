#!/bin/bash
#======================================
# Helpers
#--------------------------------------
# shellcheck disable=SC1091
test -f /.kconfig && . /.kconfig

set -ex

declare kiwi_iname

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Fix kernel-install
#--------------------------------------
# patch sent upstream and merged. This patching here can
# be deleted as soon as the main distro has an update for
# systemd available
patch -p0 < kernel-install.patch
rm -f kernel-install.patch

#======================================
# Activate services
#--------------------------------------
baseInsertService dbus-broker
baseInsertService NetworkManager

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
