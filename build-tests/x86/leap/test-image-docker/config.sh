#!/bin/bash
set -ex

#======================================
# Create ssh machine keys
#--------------------------------------
/usr/sbin/sshd-gen-keys-start

#======================================
# Drop locales
#--------------------------------------
find /usr/share/locale -name "*.mo" -delete
