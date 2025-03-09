# shellcheck shell=bash
set -x

# image_fs=$1

root_partnum=$2

is_kpartx=false

# shellcheck disable=SC2125
root_device=/dev/loop*p${root_partnum}
# shellcheck disable=SC2086
if [ ! -e ${root_device} ];then
    # shellcheck disable=SC2125
    root_device=/dev/mapper/loop*p${root_partnum}
    is_kpartx=true
fi

# shellcheck disable=SC2086
loop_name=$(basename $root_device | cut -f 1-2 -d'p')

disk_device=/dev/"${loop_name}"

sgdisk --delete=4 "$disk_device" || exit 1

# /var 100MB
sgdisk --new=4:0:+100M "$disk_device" || exit 1

# /var/log 100MB
sgdisk --new=6:0:+100M "$disk_device" || exit 1

# /var/audit rest of spare (500 - 200 = 300MB)
sgdisk --new=7:0:0 "$disk_device" || exit 1

# reread partition changes
partprobe "$disk_device" || exit 1

# recreate partition maps
if [ "${is_kpartx}" = "false" ];then
    partx --delete "$disk_device" || exit 1
    partx --add "$disk_device" || exit 1
else
    kpartx -d "$disk_device" || exit 1
    kpartx -a "$disk_device" || exit 1
fi

# create filesystems on partitions, use labels
if [ "${is_kpartx}" = "false" ];then
    mkfs.ext4 -L var /dev/"${loop_name}"p4 || exit 1
    mkfs.ext4 -L log /dev/"${loop_name}"p6 || exit 1
    mkfs.ext4 -L audit /dev/"${loop_name}"p7 || exit 1
else
    mkfs.ext4 -L var /dev/mapper/"${loop_name}"p4 || exit 1
    mkfs.ext4 -L log /dev/mapper/"${loop_name}"p6 || exit 1
    mkfs.ext4 -L audit /dev/mapper/"${loop_name}"p7 || exit 1
fi

# order partitions
sgdisk --sort "$disk_device"
