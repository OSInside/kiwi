#!/bin/sh
set -ex

#======================================
# Delete auto relabel trigger
#--------------------------------------
rm -f /.autorelabel

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd
