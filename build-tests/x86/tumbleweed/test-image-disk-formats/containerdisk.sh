#!/bin/bash

set -ex

declare kiwi_profiles=${kiwi_profiles}

# Setup file permissions and ownership requested by the
# target system using the container, kubernetes
for profile in ${kiwi_profiles//,/ }; do
	if [ "${profile}" = "oci_disk" ] || [ "${profile}" = "docker_disk" ];then
        chown 107:107 "$1"
	fi
done
