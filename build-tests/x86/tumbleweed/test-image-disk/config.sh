#!/bin/bash
set -ex

declare kiwi_profiles=${kiwi_profiles}

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd
systemctl enable grub_config
systemctl enable dracut_hostonly

# Just in case the kiwi resizer is disabled in the system and
# gets dropped from the initrd by the customer for some reason
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "RetainLast" ]; then
        cat > /etc/fstab.script <<-EOF
		sed -ie "s@/home ext4 defaults@/home ext4 x-systemd.growfs,defaults@" /etc/fstab
        rm /etc/fstabe
		EOF
    fi
done
