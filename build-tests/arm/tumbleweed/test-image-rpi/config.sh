#!/bin/bash
set -ex

declare kiwi_btrfs_root_is_snapshot=${kiwi_btrfs_root_is_snapshot}

# shellcheck disable=SC1091
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

#======================================
# init reconfig system startup
#--------------------------------------
mkdir /var/lib/misc/reconfig_system

#======================================
# add missing fonts
#--------------------------------------
CONSOLE_FONT="eurlatgr.psfu"

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

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

touch /var/log/zypper.log

#======================================
# Import trusted rpm keys
#--------------------------------------
for i in /usr/lib/rpm/gnupg/keys/gpg-pubkey*asc; do
    # importing can fail if it already exists
    rpm --import "$i" || true
done

#=====================================
# Configure snapper
#-------------------------------------
if [ "${kiwi_btrfs_root_is_snapshot-false}" = 'true' ]; then
    echo "creating initial snapper config ..."
    cp /usr/share/snapper/config-templates/default /etc/snapper/configs/root
    baseUpdateSysConfig /etc/sysconfig/snapper SNAPPER_CONFIGS root

    # Adjust parameters
    sed -i'' 's/^TIMELINE_CREATE=.*$/TIMELINE_CREATE="no"/g' \
        /etc/snapper/configs/root
    sed -i'' 's/^NUMBER_LIMIT=.*$/NUMBER_LIMIT="2-10"/g' \
        /etc/snapper/configs/root
    sed -i'' 's/^NUMBER_LIMIT_IMPORTANT=.*$/NUMBER_LIMIT_IMPORTANT="4-10"/g' \
        /etc/snapper/configs/root
fi

#=====================================
# Enable chrony if installed
#-------------------------------------
if [ -f /etc/chrony.conf ]; then
    systemctl enable chronyd
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
