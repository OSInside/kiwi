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
    echo network rootfs-block dm
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop aoe iso9660 overlay
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    declare dracutbasedir=${dracutbasedir}
    local dmsquashdir=
    inst_multiple -o checkmedia
    inst_multiple \
        umount dmsetup partx blkid lsblk dd losetup \
        grep cut partprobe find wc fdisk tail mkfs.ext4 mkfs.xfs \
        dialog cat mountpoint

    dmsquashdir=$(find "${dracutbasedir}/modules.d" -name "*dmsquash-live")
    if [ -n "${dmsquashdir}" ] && \
        [ -f "${dmsquashdir}/parse-iso-scan.sh" ] && \
        [ -f "${dmsquashdir}/iso-scan.sh" ]; then
        inst_hook cmdline 31 "${dmsquashdir}/parse-iso-scan.sh"
        inst_script "${dmsquashdir}/iso-scan.sh" "/sbin/iso-scan"
    fi

    inst_hook cmdline 30 "${moddir}/parse-kiwi-live.sh"
    inst_hook pre-udev 30 "${moddir}/kiwi-live-genrules.sh"
    inst_hook pre-udev 60 "${moddir}/kiwi-live-net-genrules.sh"
    inst_hook pre-mount 30 "${moddir}/kiwi-live-checkmedia.sh"
    inst_script "${moddir}/kiwi-live-root.sh" "/sbin/kiwi-live-root"
    inst_script "${moddir}/kiwi-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-generator"
    inst_simple "${moddir}/kiwi-live-lib.sh" "/lib/kiwi-live-lib.sh"
    inst_rules 60-cdrom_id.rules
    dracut_need_initqueue
}
