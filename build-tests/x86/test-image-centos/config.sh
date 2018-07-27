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
# Activate services
#--------------------------------------
baseInsertService dracut_hostonly

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3

exit 0
