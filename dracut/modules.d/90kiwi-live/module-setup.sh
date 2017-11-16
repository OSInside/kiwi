#!/bin/bash

# called by dracut
check() {
    # a live host-only image doesn't really make a lot of sense
    declare hostonly=${hostonly}
    [[ ${hostonly} ]] && return 1
    return 255
}

# called by dracut
depends() {
    echo rootfs-block dm
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop iso9660 overlay
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    inst_multiple \
        umount dmsetup blockdev blkid lsblk dd losetup \
        isoinfo grep cut partprobe find wc fdisk tail mkfs.ext4 mkfs.xfs \
        checkmedia dialog
    inst_hook cmdline 30 "${moddir}/parse-kiwi-live.sh"
    inst_hook pre-udev 30 "${moddir}/kiwi-live-genrules.sh"
    inst_hook pre-mount 30 "${moddir}/kiwi-live-checkmedia.sh"
    inst_script "${moddir}/kiwi-live-root.sh" "/sbin/kiwi-live-root"
    inst_script "${moddir}/kiwi-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-generator"
    inst_simple "${moddir}/kiwi-live-lib.sh" "/lib/kiwi-live-lib.sh"
    inst_rules 60-cdrom_id.rules
    dracut_need_initqueue
}
