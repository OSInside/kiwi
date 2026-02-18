#!/bin/bash
set -euxo pipefail

declare kiwi_profiles=${kiwi_profiles}

# shellcheck disable=SC1091
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

#======================================
# Systemd controls the console font now
#--------------------------------------
echo FONT="eurlatgr.psfu" >> /etc/vconsole.conf

#======================================
# Add data partition mountpoint
#--------------------------------------
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "DataPart" ]; then
        mkdir -p /data
    fi
done

#======================================
# prepare for setting root pw, timezone
#--------------------------------------
echo "** reset machine settings"
rm -f \
    /etc/machine-id \
    /var/lib/zypp/AnonymousUniqueId \
    /var/lib/systemd/random-seed \
    /var/lib/dbus/machine-id

#======================================
# Specify default systemd target
#--------------------------------------
baseSetRunlevel multi-user.target

#======================================
# Set hostname by DHCP
#--------------------------------------
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME yes

#======================================
# Enable DHCP on eth0
#--------------------------------------
cat >/etc/sysconfig/network/ifcfg-eth0 <<EOF
BOOTPROTO='dhcp'
STARTMODE='auto'
EOF

# Add repos from /etc/YaST2/control.xml
if [ -x /usr/sbin/add-yast-repos ]; then
    add-yast-repos
    zypper --non-interactive rm -u live-add-yast-repos
fi

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

# To make x-systemd.growfs work from inside the initrd
cat >/etc/dracut.conf.d/50-microos-growfs.conf <<EOF
install_items+=" /usr/lib/systemd/systemd-growfs "
EOF
