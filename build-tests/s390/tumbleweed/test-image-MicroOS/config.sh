#!/bin/bash
set -euxo pipefail

# shellcheck disable=SC1091
#======================================
# Functions
#--------------------------------------
test -f /.kconfig && . /.kconfig

declare kiwi_profiles=${kiwi_profiles}

#======================================
# Setup Core Services
#--------------------------------------
systemctl enable sshd.service

#======================================
# Setup Cloud Services
#--------------------------------------
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "IBM-Cloud-Standard" ] || [ "${profile}" = "IBM-Cloud-Secure-Execution" ]; then
        for service in \
            cloud-init-local.service \
            cloud-init.service \
            cloud-config.service \
            cloud-final.service \
            systemd-networkd \
            systemd-resolved
        do
            systemctl enable "${service}"
        done
    fi
    if [ "${profile}" = "SUSE-Infra" ]; then
        for service in \
            systemd-networkd \
            systemd-resolved
        do
            systemctl enable "${service}"
        done
    fi
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

for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "IBM-Cloud-Standard" ]; then
        # For image tests with an extra boot partition the
        # kernel must not be a symlink to another area of
        # the filesystem. Latest changes on SUSE changed the
        # layout of the kernel which breaks every image with
        # an extra boot partition
        #
        # All of the following is more than a hack and I
        # don't like it all
        #
        # Complains and discussions about this please with
        # the SUSE kernel team as we in kiwi can just live
        # with the consequences of this change
        #
        pushd /

        for file in /boot/* /boot/.*; do
            if [ -L "${file}" ];then
                link_target=$(readlink "${file}")
                if [[ "${link_target}" =~ usr/lib/modules ]];then
                    mv "${link_target}" "${file}"
                fi
            fi
        done
    fi
done
