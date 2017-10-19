#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2015 SUSE LLC. All rights reserved
#               :
# AUTHOR        : Robert Schweikert <rjschwei@suse.com>
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

#======================================
# Setup the build keys
#--------------------------------------
suseImportBuildKey

#=========================================
# Set sysconfig options
#-----------------------------------------
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME no
baseUpdateSysConfig /etc/sysconfig/network/dhcp WRITE_HOSTNAME_TO_HOSTS no

baseUpdateSysConfig /etc/sysconfig/security POLKIT_DEFAULT_PRIVS restrictive

baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_LOAD_MODULES "nf_conntrack_netbios_ns"
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_DEV_EXT "any eth0"
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_LOG_DROP_CRIT yes
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_LOG_DROP_ALL no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_LOG_ACCEPT_CRIT yes
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_LOG_ACCEPT_ALL no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_ALLOW_FW_BROADCAST_EXT no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_ALLOW_FW_BROADCAST_INT no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_ALLOW_FW_BROADCAST_DMZ no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_IGNORE_FW_BROADCAST_INT no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_IGNORE_FW_BROADCAST_DMZ no
baseUpdateSysConfig /etc/sysconfig/SuSEfirewall2 FW_IPSEC_TRUST no

baseUpdateSysConfig /etc/sysconfig/windowmanager X_MOUSE_CURSOR ""
baseUpdateSysConfig /etc/sysconfig/windowmanager DEFAULT_WM ""

# Setup Hardware clock
echo 'DEFAULT_TIMEZONE="UTC"' >> /etc/sysconfig/clock

# Setup policy kit
[ -x /sbin/set_polkit_default_privs ] && /sbin/set_polkit_default_privs

# Setup secure tty for Xen console log
egrep -q '^xvc0$' /etc/securetty || echo xvc0 >> /etc/securetty

# Setup loading of unsupported modules
[ -f /etc/modprobe.d/unsupported-modules ] && sed -i -r -e 's/^(allow_unsupported_modules[[:space:]]*).*/\10/' /etc/modprobe.d/unsupported-modules

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config

# Remove the password for root
# Note the string matches the password set in the config file
sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

#======================================
# Activate services
#--------------------------------------
suseInsertService boot.device-mapper
suseInsertService cloud-init-local
suseInsertService cloud-init
suseInsertService cloud-config
suseInsertService cloud-final
suseInsertService haveged
suseInsertService sshd
suseRemoveService boot.efivars
suseRemoveService boot.lvm
suseRemoveService boot.md
suseRemoveService boot.multipath
suseRemoveService kbd
suseRemoveService acpid 

#======================================
# Umount kernel filesystems
#--------------------------------------
baseCleanMount

exit 0
