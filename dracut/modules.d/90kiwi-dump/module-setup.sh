#!/bin/bash

# called by dracut
check() {
    return 255
}

# called by dracut
depends() {
    echo network rootfs-block dm kiwi-lib
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop iso9660
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    inst_multiple \
        tr lsblk dd md5sum head pv kexec basename awk kpartx

    inst_hook pre-udev 30 "${moddir}/kiwi-installer-genrules.sh"

    inst_script "${moddir}/kiwi-installer-device.sh" \
        "/sbin/kiwi-installer-device"

    inst_hook cmdline 30 "${moddir}/parse-kiwi-install.sh"
    inst_hook pre-mount 30 "${moddir}/kiwi-dump-image.sh"
    inst_hook mount 30 "${moddir}/kiwi-mount-ramdisk.sh" 

    inst_script "${moddir}/kiwi-ramdisk-deployment-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-ramdisk-generator"

    inst_rules 60-cdrom_id.rules
    dracut_need_initqueue
}
