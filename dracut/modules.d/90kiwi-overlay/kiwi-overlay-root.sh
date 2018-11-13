#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type kiwi_die >/dev/null 2>&1 || . /lib/kiwi-lib.sh

#======================================
# functions
#--------------------------------------
function setupDebugMode {
    if getargbool 0 rd.kiwi.debug; then
        local log=/run/initramfs/log
        mkdir -p ${log}
        exec > ${log}/boot.kiwi
        exec 2>> ${log}/boot.kiwi
        set -x
    fi
}

function loadKernelModules {
    modprobe squashfs
}

function initGlobalDevices {
    if [ -z "$1" ]; then
        kiwi_die "No root device for operation given"
    fi
    write_partition="$1"
    root_disk=$(
        lsblk -p -n -r -s -o NAME,TYPE "${write_partition}" |\
        grep disk | cut -f1 -d ' '
    )
    read_only_partition=$(
        lsblk -p -r --fs -o NAME,FSTYPE "${root_disk}" |\
        grep squashfs | cut -f1 -d ' '
    )
}

function mountReadOnlyRootImage {
    local root_mount_point=/run/rootfsbase
    mkdir -m 0755 -p ${root_mount_point}
    if ! mount -n "${read_only_partition}" "${root_mount_point}"; then
        kiwi_die "Failed to mount overlay(ro) root filesystem"
    fi
    echo "${root_mount_point}"
}

function preparePersistentOverlay {
    local overlay_mount_point=/run/overlayfs
    mkdir -m 0755 -p ${overlay_mount_point}
    if ! mount "${write_partition}" "${overlay_mount_point}"; then
        kiwi_die "Failed to mount overlay(rw) filesystem"
    fi
    mkdir -m 0755 -p ${overlay_mount_point}/rw
    mkdir -m 0755 -p ${overlay_mount_point}/work
}

#======================================
# perform root access preparation
#--------------------------------------
PATH=/usr/sbin:/usr/bin:/sbin:/bin

# init debug log file if wanted
setupDebugMode

# device nodes and types
initGlobalDevices "$1"

# load required kernel modules
loadKernelModules

# mount readonly root filesystem
mountReadOnlyRootImage

# prepare overlay for generated systemd OverlayOS_rootfs service
preparePersistentOverlay

need_shutdown

exit 0
