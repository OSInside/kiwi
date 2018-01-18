#!/bin/bash

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
    inst_multiple \
        tr lsblk dd md5sum head pv kexec basename awk

    inst_hook pre-udev 60 "${moddir}/kiwi-dump-net-genrules.sh"

    inst_hook cmdline 30 "${moddir}/parse-kiwi-install.sh"
    inst_hook pre-mount 30 "${moddir}/kiwi-dump-image.sh"
    inst_rules 60-cdrom_id.rules
    dracut_need_initqueue
}
