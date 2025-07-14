#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

#======================================
# SSL Certificates Configuration
#--------------------------------------
echo '** Rehashing SSL Certificates...'
update-ca-certificates

#=====================================
# Enable ntpd if installed
#-------------------------------------
if [ -f /etc/ntp.conf ]; then
	systemctl enable ntpd
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
