#!/bin/bash

# called by dracut
check() {
    return 255
}

# called by dracut
depends() {
    echo udev-rules crypt bash
    return 0
}

# called by dracut
install() {
    declare moddir=${moddir}
    inst_multiple \
        blkid blockdev dd mkdir rmdir env \
        grep cut tail head tr bc true false mountpoint \
        basename sfdisk sgdisk mkswap readlink lsblk \
        btrfs xfs_growfs resize2fs \
        e2fsck btrfsck xfs_repair \
        vgs vgchange lvextend lvcreate lvresize pvresize \
        mdadm cryptsetup dialog \
        pv curl xz \
        dmsetup
    inst_multiple -o dolly
    if type partx &> /dev/null;then
        inst_multiple partx
    elif type partprobe &> /dev/null;then
        inst_multiple partprobe
    else
        dfatal "Either partx or partprobe is required"
        exit 1
    fi
    if [[ "$(uname -m)" =~ s390 ]];then
        inst_multiple fdasd parted partprobe
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
