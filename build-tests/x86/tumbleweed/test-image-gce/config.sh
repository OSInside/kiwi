#!/bin/bash
set -ex

# shellcheck disable=SC1091
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

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
systemctl enable sshd
systemctl enable google-accounts-daemon
systemctl enable google-clock-skew-daemon
systemctl enable google-instance-setup
systemctl enable google-network-daemon
systemctl enable google-shutdown-scripts
systemctl enable google-startup-scripts
systemctl enable haveged
systemctl enable ntpd
systemctl enable rootgrow
systemctl enable boot.lvm
systemctl enable boot.md
systemctl enable display-manager
systemctl enable kbd
