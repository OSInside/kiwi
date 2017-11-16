#!/bin/bash

# called by dracut
depends() {
    echo rootfs-block dm
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop overlay
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    inst_multiple \
        lsblk losetup grep cut mount
    inst_hook cmdline 30 "${moddir}/parse-kiwi-overlay.sh"
    inst_hook pre-udev 30 "${moddir}/kiwi-overlay-genrules.sh"
    inst_script "${moddir}/kiwi-overlay-root.sh" "/sbin/kiwi-overlay-root"
    inst_script "${moddir}/kiwi-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-generator"
    dracut_need_initqueue
}
