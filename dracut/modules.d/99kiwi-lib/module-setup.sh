#!/bin/bash

# called by dracut
check() {
    return 0
}

# called by dracut
depends() {
    echo udev-rules
    return 0
}

# called by dracut
install() {
    declare moddir=${moddir}
    inst_multiple \
        blkid blockdev parted dd mkdir grep cut tail head tr bc \
        basename partprobe sgdisk mkswap readlink lsblk \
        btrfs xfs_growfs resize2fs \
        e2fsck btrfsck xfs_repair \
        vgs vgchange lvextend lvcreate lvresize pvresize \
        mdadm cryptsetup dialog \
        pv curl xz \
        dmsetup
    if [[ "$(uname -m)" =~ s390 ]];then
        inst_multiple fdasd
    fi
    inst_simple \
        "${moddir}/kiwi-lib.sh" "/lib/kiwi-lib.sh"
    inst_simple \
        "${moddir}/kiwi-partitions-lib.sh" "/lib/kiwi-partitions-lib.sh"
    inst_simple \
        "${moddir}/kiwi-filesystem-lib.sh" "/lib/kiwi-filesystem-lib.sh"
    inst_simple \
        "${moddir}/kiwi-dialog-lib.sh" "/lib/kiwi-dialog-lib.sh"
    inst_simple \
        "${moddir}/kiwi-mdraid-lib.sh" "/lib/kiwi-mdraid-lib.sh"
    inst_simple \
        "${moddir}/kiwi-lvm-lib.sh" "/lib/kiwi-lvm-lib.sh"
    inst_simple \
        "${moddir}/kiwi-luks-lib.sh" "/lib/kiwi-luks-lib.sh"
    inst_simple \
        "${moddir}/kiwi-net-lib.sh" "/lib/kiwi-net-lib.sh"
}
