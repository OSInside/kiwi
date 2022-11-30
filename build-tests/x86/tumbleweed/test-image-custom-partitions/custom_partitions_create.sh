image_fs=$1

root_partnum=$2

root_device=/dev/loop*p${root_partnum}

loop_name=$(basename $root_device | cut -f 1-2 -d'p')

disk_device=/dev/${loop_name}

sgdisk --delete=4 $disk_device || exit 1

# /var 100MB
sgdisk --new=4:0:+100M $disk_device || exit 1

# /var/log 100MB
sgdisk --new=6:0:+100M $disk_device || exit 1

# /var/audit rest of spare (500 - 200 = 300MB)
sgdisk --new=7:0:0 $disk_device || exit 1

# reread partition changes
partprobe $disk_device || exit 1

# recreate partition maps
partx --delete $disk_device || exit 1
partx --add $disk_device || exit 1

# create filesystems on partitions, use labels
mkfs.ext4 -L var /dev/${loop_name}p4 || exit 1
mkfs.ext4 -L log /dev/${loop_name}p6 || exit 1
mkfs.ext4 -L audit /dev/${loop_name}p7 || exit 1

# order partitions
sgdisk --sort $disk_device
