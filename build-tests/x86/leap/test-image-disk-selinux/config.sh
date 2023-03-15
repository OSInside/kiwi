#!/bin/sh
# shellcheck disable=SC1091
test -f /.kconfig && . /.kconfig

set -ex

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Delete auto relabel trigger
#--------------------------------------
rm -f /.autorelabel

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3
