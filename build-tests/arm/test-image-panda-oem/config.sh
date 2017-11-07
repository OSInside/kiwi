#!/bin/bash
# vim: sw=4 et
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2006 SUSE LINUX Products GmbH. All rights reserved
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

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService boot.device-mapper
suseInsertService ntpd
suseInsertService NetworkManager
suseRemoveService avahi-dnsconfd
suseRemoveService avahi-daemon

#==========================================
# remove unneeded packages
#------------------------------------------
suseRemovePackagesMarkedForDeletion

#======================================
# Add missing gpg keys to rpm
#--------------------------------------
suseImportBuildKey

#==========================================
# remove package docs
#------------------------------------------
rm -rf /usr/share/doc/packages/*
rm -rf /usr/share/doc/manual/*
rm -rf /opt/kde*

if ! rpmqpack | grep -q vim-enhanced; then
    #======================================
    # only basic version of vim is
    # installed; no syntax highlighting
    #--------------------------------------
    sed -i -e's/^syntax on/" syntax on/' /etc/vimrc
fi

#======================================
# Import GPG Key
#--------------------------------------
t=$(mktemp)
cat - <<EOF > $t
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2.0.15 (GNU/Linux)

mQENBEkUTD8BCADWLy5d5IpJedHQQSXkC1VK/oAZlJEeBVpSZjMCn8LiHaI9Wq3G
3Vp6wvsP1b3kssJGzVFNctdXt5tjvOLxvrEfRJuGfqHTKILByqLzkeyWawbFNfSQ
93/8OunfSTXC1Sx3hgsNXQuOrNVKrDAQUqT620/jj94xNIg09bLSxsjN6EeTvyiO
mtE9H1J03o9tY6meNL/gcQhxBvwuo205np0JojYBP0pOfN8l9hnIOLkA0yu4ZXig
oKOVmf4iTjX4NImIWldT+UaWTO18NWcCrujtgHueytwYLBNV5N0oJIP2VYuLZfSD
VYuPllv7c6O2UEOXJsdbQaVuzU1HLocDyipnABEBAAG0NG9wZW5TVVNFIFByb2pl
Y3QgU2lnbmluZyBLZXkgPG9wZW5zdXNlQG9wZW5zdXNlLm9yZz6JATwEEwECACYC
GwMGCwkIBwMCBBUCCAMEFgIDAQIeAQIXgAUCU2dN1AUJHR8ElQAKCRC4iy/UPb3C
hGQrB/9teCZ3Nt8vHE0SC5NmYMAE1Spcjkzx6M4r4C70AVTMEQh/8BvgmwkKP/qI
CWo2vC1hMXRgLg/TnTtFDq7kW+mHsCXmf5OLh2qOWCKi55Vitlf6bmH7n+h34Sha
Ei8gAObSpZSF8BzPGl6v0QmEaGKM3O1oUbbB3Z8i6w21CTg7dbU5vGR8Yhi9rNtr
hqrPS+q2yftjNbsODagaOUb85ESfQGx/LqoMePD+7MqGpAXjKMZqsEDP0TbxTwSk
4UKnF4zFCYHPLK3y/hSH5SEJwwPY11l6JGdC1Ue8Zzaj7f//axUs/hTC0UZaEE+a
5v4gbqOcigKaFs9Lc3Bj8b/lE10Y
=i2TA
-----END PGP PUBLIC KEY BLOCK-----
EOF
rpm --import $t
rm -f $t

#======================================
# SuSEconfig
#--------------------------------------
suseConfig

#======================================
# Add Factory repo
#--------------------------------------
zypper ar -f \
    http://download.opensuse.org/ports/armv7hl/tumbleweed/repo/oss/ openSUSE-Ports-Tumbleweed-repo-oss

#======================================
# Add xorg config with fbdev
#--------------------------------------
mkdir -p /etc/X11/xorg.conf.d/
cat > /etc/X11/xorg.conf.d/20-fbdev.conf <<EOF
Section "Device"
Identifier "fb gfx"
Driver "fbdev"
Option "fb" "/dev/fb0"
EndSection
EOF

#======================================
# Add tty devices to securetty
#--------------------------------------
cat >> /etc/securetty <<EOF
ttyO0
ttyO2
ttyAMA0
ttyAMA2
ttymxc0
ttymxc1
EOF

#======================================
# Bring up eth device automatically
#--------------------------------------
mkdir -p /etc/sysconfig/network/
case "$kiwi_iname" in
    *)
	cat > /etc/sysconfig/network/ifcfg-eth0 <<-EOF
	BOOTPROTO='dhcp'
	MTU=''
	REMOTE_IPADDR=''
	STARTMODE='onboot'
	EOF
	;;
esac

#======================================
# Configure ntp
#--------------------------------------
# tell e2fsck to ignore the time differences
cat > /etc/e2fsck.conf <<EOF
[options]
broken_system_clock=true
EOF

for i in 0 1 2 3; do
    echo "server $i.opensuse.pool.ntp.org iburst" >> /etc/ntp.conf
done

#======================================
# Load panel-tfp410 before omapdrm
#--------------------------------------
cat > /etc/modprobe.d/50-omapdrm.conf <<EOF
# Ensure that panel-tfp410 is loaded before omapdrm
softdep omapdrm pre: panel-tfp410
EOF

#======================================
# Umount kernel filesystems
#--------------------------------------
baseCleanMount

exit 0
