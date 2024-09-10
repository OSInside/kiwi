#!/bin/bash

set -ex

declare kiwi_iname=${kiwi_iname}

echo "Configure image: [${kiwi_iname}]..."

#======================================
# Setup services
#--------------------------------------
for service in nitro-enclave-alive sshd;do
    systemctl enable "${service}"
done

#======================================
# Allow ssh root login
#--------------------------------------
echo "PermitRootLogin yes" > /etc/ssh/sshd_config.d/root.conf

#======================================
# load virtio_mmio
#--------------------------------------
echo virtio_mmio > /etc/modules-load.d/virtio-mmio.conf
