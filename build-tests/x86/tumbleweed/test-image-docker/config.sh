#!/bin/bash
set -ex

#======================================
# Create ssh machine keys
#--------------------------------------
/usr/sbin/sshd-gen-keys-start

#======================================
# Drop locales
#--------------------------------------
(cd /usr/share/locale && find . -print0 -name "*.mo" | xargs rm)
