#!/bin/bash
#======================================
# Helpers
#--------------------------------------
# shellcheck disable=SC1091

test -f /.kconfig && . /.kconfig

declare kiwi_iname

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService dracut_hostonly

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
