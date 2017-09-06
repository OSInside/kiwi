#!/bin/sh
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

#======================================
# functions
#--------------------------------------
function lookupIsoDiskDevice {
    local disk
    local disk_device
    for disk in $(lsblk -n -r -o NAME,TYPE | grep disk | cut -f1 -d' ');do
        disk_device="/dev/${disk}"
        application_id=$(
            isoinfo -d -i ${disk_device} 2>/dev/null |\
                grep "Application id:"|cut -f2 -d:
        )
        if [ ! -z "${application_id}" ];then
            echo ${disk_device}
            return
        fi
    done
}

function setupDebugMode {
    if getargbool 0 rd.live.debug; then
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
        die "No root device for operation given"
    fi
    isodev="$1"
    isodiskdev=$(lookupIsoDiskDevice)
    isofs_type=$(blkid -s TYPE -o value ${isodev})
}

function initGlobalOptions {
    live_dir=$(getarg rd.live.dir -d live_dir)
    [ -z "${live_dir}" ] && live_dir="LiveOS"

    squash_image=$(getarg rd.live.squashimg)
    [ -z "${squash_image}" ] && squash_image="squashfs.img"

    cow_filesystem=$(getarg rd.live.overlay.cowfs)
    [ -z "${cow_filesystem}" ] && cow_filesystem="ext4"
}

function mountIso {
    ln -s ${isodev} /run/initramfs/isodev
    local iso_mount_point=/run/initramfs/live
    mkdir -m 0755 -p ${iso_mount_point}
    if ! mount -n -t ${isofs_type} ${isodev} ${iso_mount_point}; then
        die "Failed to mount live ISO device"
    fi
    echo ${iso_mount_point}
}

function mountCompressedContainerFromIso {
    local iso_mount_point=$1
    local container_mount_point=/run/initramfs/squashfs_container
    squashfs_container="${iso_mount_point}/${live_dir}/${squash_image}"
    mkdir -m 0755 -p ${container_mount_point}
    if ! mount -n ${squashfs_container} ${container_mount_point};then
        die "Failed to mount live ISO squashfs container"
    fi
    echo ${container_mount_point}
}

function mountReadOnlyRootImageFromContainer {
    local container_mount_point=$1
    local rootfs_image="${container_mount_point}/LiveOS/rootfs.img"
    local root_mount_point=/run/rootfsbase
    mkdir -m 0755 -p ${root_mount_point}
    if ! mount -n ${rootfs_image} ${root_mount_point}; then
        die "Failed to mount live ISO root filesystem"
    fi
    echo ${root_mount_point}
}

function prepareTemporaryOverlay {
    mkdir -m 0755 -p /run/overlayfs/rw
    mkdir -m 0755 -p /run/overlayfs/work
}

function preparePersistentOverlay {
    if [ -z "${isodiskdev}" ]; then
        return 1
    fi
    local overlay_mount_point=/run/overlayfs
    mkdir -m 0755 -p ${overlay_mount_point}
    if ! mount -L cow ${overlay_mount_point}; then
        echo -e "n\np\n\n\n\nw\nq" | fdisk ${isodiskdev}
        if ! partprobe ${isodiskdev}; then
            return 1
        fi
        local write_partition=$(lsblk ${isodiskdev} -r -n -o NAME | tail -n1)
        if ! mkfs.${cow_filesystem} -L cow /dev/${write_partition}; then
            return 1
        fi
        if ! mount -L cow ${overlay_mount_point}; then
            return 1
        fi
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
initGlobalDevices $1

# live options and their default values
initGlobalOptions

# load required kernel modules
loadKernelModules

# mount ISO device
iso_mount_point=$(mountIso)

# mount squashfs compressed container
container_mount_point=$(
    mountCompressedContainerFromIso ${iso_mount_point}
)

# mount readonly root filesystem from container
mountReadOnlyRootImageFromContainer ${container_mount_point}

# prepare overlay for generated systemd LiveOS_rootfs service
if getargbool 0 rd.live.overlay.persistent && [ ! -z "${isodiskdev}" ]; then
    if ! preparePersistentOverlay; then
        echo "Failed to setup persistent write space !"
        echo "Falling back to temporary overlay"
        prepareTemporaryOverlay
    fi
else
    prepareTemporaryOverlay
fi

need_shutdown

exit 0
