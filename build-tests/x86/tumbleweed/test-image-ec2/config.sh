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
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME no
baseUpdateSysConfig /etc/sysconfig/network/dhcp WRITE_HOSTNAME_TO_HOSTS no

baseUpdateSysConfig /etc/sysconfig/security POLKIT_DEFAULT_PRIVS restrictive

baseUpdateSysConfig /etc/sysconfig/windowmanager X_MOUSE_CURSOR ""
baseUpdateSysConfig /etc/sysconfig/windowmanager DEFAULT_WM ""

# Setup Hardware clock
echo 'DEFAULT_TIMEZONE="UTC"' >> /etc/sysconfig/clock

# Setup policy kit
[ -x /sbin/set_polkit_default_privs ] && /sbin/set_polkit_default_privs

# Setup secure tty for Xen console log
grep -E -q '^xvc0$' /etc/securetty || echo xvc0 >> /etc/securetty

# Setup loading of unsupported modules
[ -f /etc/modprobe.d/unsupported-modules ] && sed -i -r -e 's/^(allow_unsupported_modules[[:space:]]*).*/\10/' /etc/modprobe.d/unsupported-modules

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /usr/etc/ssh/sshd_config

# Remove the password for root
# Note the string matches the password set in the config file
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

#======================================
# Activate services
#--------------------------------------
systemctl enable cloud-init-local
systemctl enable cloud-init
systemctl enable cloud-config
systemctl enable cloud-final
systemctl enable haveged
systemctl enable sshd
