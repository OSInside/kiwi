#!/bin/bash
set -ex

#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [${kiwi_iname}]..."

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
