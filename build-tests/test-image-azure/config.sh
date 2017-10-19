#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2013 SUSE LINUX Products GmbH. All rights reserved
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
# These are all set by YaST but not by KIWI
baseUpdateSysConfig /etc/sysconfig/clock HWCLOCK "-u"
baseUpdateSysConfig /etc/sysconfig/clock TIMEZONE UTC

baseUpdateSysConfig /etc/sysconfig/console CONSOLE_FONT "lat9w-16.psfu"
baseUpdateSysConfig /etc/sysconfig/console CONSOLE_SCREENMAP trivial

baseUpdateSysConfig /etc/sysconfig/kernel INITRD_MODULES "processor jbd ext4"
baseUpdateSysConfig /etc/sysconfig/kernel MODULES_LOADED_ON_BOOT "acpiphp"

baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME yes
baseUpdateSysConfig /etc/sysconfig/network/dhcp WRITE_HOSTNAME_TO_HOSTS no

baseUpdateSysConfig /etc/sysconfig/security POLKIT_DEFAULT_PRIVS restrictive

baseUpdateSysConfig /etc/sysconfig/storage USED_FS_LIST ext4

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

# Set the keep alive interval
sed -i 's/#ClientAliveInterval 0/ClientAliveInterval 180/' /etc/ssh/sshd_config

# Disable default targetpw directive
sed -i -e '/^Defaults targetpw/,/^$/ s/^/#/' /etc/sudoers

# WALinuxAgent configuration settings
# Disable agent auto-update
sed -i -e 's/AutoUpdate.Enabled=y/AutoUpdate.Enabled=n/' /etc/waagent.conf

# Remove the password for root
# Note the string matches the password set in the config file
sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Implement password policy
# Length: 6-72 characters long
# Contain any combination of 3 of the following:
#   - a lowercase character
#   - an uppercase character
#   - a number
#   - a special character
sed -i 's/pam_cracklib.so/pam_cracklib.so minlen=6 dcredit=1 ucredit=1 lcredit=1 ocredit=1 minclass=3/' /etc/pam.d/common-password-pc

# Delete resolv.conf
rm /etc/resolv.conf

# Do not use delta rpms in the cloud
sed -i 's/# download.use_deltarpm = true/download.use_deltarpm = false/' /etc/zypp/zypp.conf

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService haveged
suseInsertService waagent
suseRemoveService boot.lvm
suseRemoveService boot.md
suseRemoveService display-manager
suseRemoveService kbd
suseRemoveService smartd

#======================================
# Umount kernel filesystems
#--------------------------------------
baseCleanMount

exit 0
