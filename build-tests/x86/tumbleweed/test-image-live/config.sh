#!/bin/bash

set -ex

declare kiwi_profiles=${kiwi_profiles}
declare kiwi_iname=${kiwi_iname}

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup services
#--------------------------------------
for service in \
    sshd \
    systemd-networkd \
    systemd-resolved
do
    systemctl enable "${service}"
done

#======================================
# Include erofs module
#--------------------------------------
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "EroFS" ]; then
        # remove from blacklist
        rm -f /usr/lib/modprobe.d/60-blacklist_fs-erofs.conf
    fi
done
