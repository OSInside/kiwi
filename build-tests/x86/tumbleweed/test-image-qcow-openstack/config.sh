#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2019 SUSE LINUX Products GmbH. All rights reserved
#               :
# AUTHOR        : Robert Schweikert <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#               :
#----------------
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
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#=========================================
# Set sysconfig options
#-----------------------------------------
# These are all set by YaST but not by KIWI
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME no
baseUpdateSysConfig /etc/sysconfig/network/dhcp WRITE_HOSTNAME_TO_HOSTS no

# Always get a new lease or booting off a snapshot will not work
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_USE_LAST_LEASE no
baseUpdateSysConfig /etc/sysconfig/security POLKIT_DEFAULT_PRIVS restrictive
baseUpdateSysConfig /etc/sysconfig/storage USED_FS_LIST ext4

if [ -f /etc/modprobe.d/unsupported-modules ];then
    sed -i -r -e 's/^(allow_unsupported_modules[[:space:]]*).*/\10/' \
        /etc/modprobe.d/unsupported-modules
fi

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config

# Remove the password for root
# Note the string matches the password set in the config file
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Setup cloud-init for OpenStack
echo ""  >> /etc/cloud/cloud.cfg
echo "datasource_list: [ NoCloud, ConfigDrive, OpenStack, None ]" \
    >> /etc/cloud/cloud.cfg

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService cloud-init-local
suseInsertService cloud-init
suseInsertService cloud-config
suseInsertService cloud-final
suseInsertService haveged

#======================================
# Deactivate services
#--------------------------------------
suseRemoveService kbd
