#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2018 SUSE LINUX Products GmbH. All rights reserved
#               :
# AUTHOR        : Marcus Schaefer <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#               :
#               :
# STATUS        : BETA
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
baseUpdateSysConfig /etc/sysconfig/clock HWCLOCK "-u"
baseUpdateSysConfig /etc/sysconfig/clock TIMEZONE UTC
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME yes
baseUpdateSysConfig /etc/sysconfig/network/dhcp WRITE_HOSTNAME_TO_HOSTS no
baseUpdateSysConfig /etc/sysconfig/security POLKIT_DEFAULT_PRIVS restrictive
baseUpdateSysConfig /etc/sysconfig/storage USED_FS_LIST ext3

# Set up ntp server
sed -i 's/server 127/#server 127/' /etc/ntp.conf
sed -i 's/fudge  127/#fudge  127/' /etc/ntp.conf
sed -i 's/keys/#keys/' /etc/ntp.conf
sed -i 's/trustedkey/#trustedkey/' /etc/ntp.conf
sed -i 's/requestkey/#requestkey/' /etc/ntp.conf
echo "server metadata.google.internal iburst" >> /etc/ntp.conf

# replace HOSTNAME file with link to file being created by Google startup code
rm /etc/HOSTNAME
ln -s /etc/hostname /etc/HOSTNAME

# Setup policy kit
[ -x /sbin/set_polkit_default_privs ] && /sbin/set_polkit_default_privs

if [ -f /etc/modprobe.d/unsupported-modules ];then
    sed -i -r -e 's/^(allow_unsupported_modules[[:space:]]*).*/\10/' \
        /etc/modprobe.d/unsupported-modules
fi

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config

# Remove the password for root
# Note the string matches the password set in the config file
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Create the boto config file
echo  '[Boto]
ca_certificates_file = system' >> /etc/boto.cfg

# gsutil clobbers boto.cfg create the template file and hope for the best
echo  '[Boto]
ca_certificates_file = system' >> /etc/boto.cfg.template

# Speed up name resolution for the metadata server
echo '169.254.169.254 metadata.google.internal metadata.google.internal' \
    >> /etc/hosts
echo '' >> /etc/hosts

# Do not use delta rpms in the cloud
sed -i 's/# download.use_deltarpm = true/download.use_deltarpm = false/' \
    /etc/zypp/zypp.conf

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService google-accounts-daemon
suseInsertService google-clock-skew-daemon
suseInsertService google-instance-setup
suseInsertService google-network-daemon
suseInsertService google-shutdown-scripts
suseInsertService google-startup-scripts
suseInsertService haveged
suseInsertService ntpd
suseInsertService rootgrow
suseRemoveService boot.lvm
suseRemoveService boot.md
suseRemoveService display-manager
suseRemoveService kbd
