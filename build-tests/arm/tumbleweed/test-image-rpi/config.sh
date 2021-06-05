#!/bin/bash
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

mkdir /var/lib/misc/reconfig_system

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]-[$kiwi_profiles]..."

#======================================
# Debug
#--------------------------------------
#systemctl enable debug-shell.service

#======================================
# add missing fonts
#--------------------------------------
CONSOLE_FONT="eurlatgr.psfu"

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Specify default runlevel
#--------------------------------------
baseSetRunlevel 3

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd

#======================================
# Sysconfig Update
#--------------------------------------
# Systemd controls the console font now
echo FONT="$CONSOLE_FONT" >> /etc/vconsole.conf

#======================================
# SSL Certificates Configuration
#--------------------------------------
echo '** Rehashing SSL Certificates...'
update-ca-certificates

if [ ! -s /var/log/zypper.log ]; then
	> /var/log/zypper.log
fi

#======================================
# Import trusted rpm keys
#--------------------------------------
for i in /usr/lib/rpm/gnupg/keys/gpg-pubkey*asc; do
    # importing can fail if it already exists
    rpm --import $i || true
done

#=====================================
# Configure snapper
#-------------------------------------
if [ "$kiwi_btrfs_root_is_snapshot" = 'true' ]; then
        echo "creating initial snapper config ..."
        # we can't call snapper here as the .snapshots subvolume
        # already exists and snapper create-config doens't like
        # that.
        cp /etc/snapper/config-templates/default /etc/snapper/configs/root
        # Change configuration to match SLES12-SP1 values
        sed -i -e '/^TIMELINE_CREATE=/s/yes/no/' /etc/snapper/configs/root
        sed -i -e '/^NUMBER_LIMIT=/s/50/10/'     /etc/snapper/configs/root

        baseUpdateSysConfig /etc/sysconfig/snapper SNAPPER_CONFIGS root
fi

#=====================================
# Enable ntpd if installed
#-------------------------------------
if [ -f /etc/ntp.conf ]; then
	suseInsertService ntpd
	for i in 0 1 2 3; do
	    echo "server $i.opensuse.pool.ntp.org iburst" >> /etc/ntp.conf
	done
fi

#======================================
# Configure Raspberry Pi specifics
#--------------------------------------
# Add necessary kernel modules to initrd (will disappear with bsc#1084272)
echo 'add_drivers+=" bcm2835_dma dwc2 "' \
    > /etc/dracut.conf.d/raspberrypi_modules.conf

# Work around HDMI connector bug and network issues
cat > /etc/modprobe.d/50-rpi3.conf <<-EOF
    # No HDMI hotplug available
    options drm_kms_helper poll=0
    # Prevent too many page allocations (bsc#1012449)
    options smsc95xx turbo_mode=N
EOF

cat > /usr/lib/sysctl.d/50-rpi3.conf <<-EOF
    # Avoid running out of DMA pages for smsc95xx (bsc#1012449)
    vm.min_free_kbytes = 2048
EOF
