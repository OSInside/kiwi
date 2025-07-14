#!/bin/bash

set -ex

declare kiwi_install_volid=${kiwi_install_volid}
declare kiwi_iname=${kiwi_iname}

label=${kiwi_install_volid:-$kiwi_iname}

#======================================
# Import repo keys
#--------------------------------------
rpm --import /tmp/systemsmanagement_key.gpg
rpm --import /usr/lib/rpm/gnupg/keys/*.asc
rm /tmp/systemsmanagement_key.gpg

#======================================
# Enable services
#--------------------------------------
systemctl enable sshd.service
systemctl enable NetworkManager.service
systemctl enable avahi-daemon.service
systemctl enable agama.service
systemctl enable agama-web-server.service
systemctl enable agama-auto.service
systemctl enable agama-hostname.service
systemctl enable agama-proxy-setup.service
systemctl enable agama-certificate-issue.path
systemctl enable agama-certificate-wait.service
systemctl enable agama-welcome-issue.service
systemctl enable agama-avahi-issue.service
systemctl enable agama-ssh-issue.service
systemctl enable agama-self-update.service
systemctl enable live-password-cmdline.service
systemctl enable live-password-dialog.service
systemctl enable live-password-iso.service
systemctl enable live-password-random.service
systemctl enable live-password-systemd.service
systemctl enable x11-autologin.service
systemctl enable spice-vdagentd.service
systemctl enable zramswap

#======================================
# Default target
#--------------------------------------
systemctl set-default graphical.target

#======================================
# disable snapshot cleanup
#--------------------------------------
systemctl disable snapper-cleanup.timer
systemctl disable snapper-timeline.timer

#======================================
# disable unused services
#--------------------------------------
systemctl disable YaST2-Firstboot.service
systemctl disable YaST2-Second-Stage.service
systemctl -f disable purge-kernels

#======================================
# setup dracut for live system
#--------------------------------------
echo "Setting default live root: live:LABEL=$label"
mkdir -p /etc/cmdline.d
echo "root=live:LABEL=$label" > \
    /etc/cmdline.d/10-liveroot.conf
echo "root_disk=live:LABEL=$label" >> \
    /etc/cmdline.d/10-liveroot.conf
echo 'install_items+=" /etc/cmdline.d/10-liveroot.conf "' > \
    /etc/dracut.conf.d/10-liveroot-file.conf
echo 'add_dracutmodules+=" dracut-menu "' >> \
    /etc/dracut.conf.d/10-liveroot-file.conf
echo 'add_drivers+=" brd "' >> \
    /etc/dracut.conf.d/10-liveroot-file.conf

#======================================
# replace the @@LIVE_MEDIUM_LABEL@@
#--------------------------------------
sed -i -e "s/@@LIVE_MEDIUM_LABEL@@/$label/g" /usr/bin/live-password
