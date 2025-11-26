#!/bin/bash
set -euxo pipefail

# shellcheck disable=SC1091
declare kiwi_profiles=${kiwi_profiles}

#======================================
# Setup Core Services
#--------------------------------------
systemctl disable network
systemctl enable sshd.service

#======================================
# Setup Cloud Services
#--------------------------------------
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "IBM-Cloud-Secure-Execution" ]; then
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
