#!/bin/bash

# called by dracut
depends() {
    echo rootfs-block dm kiwi-lib
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop
}

# called by dracut
install() {
    declare moddir=${moddir}
    inst_hook pre-mount 20 "${moddir}/kiwi-repart-disk.sh"
    inst_hook pre-pivot 20 "${moddir}/kiwi-update-fstab.sh"
    dracut_need_initqueue
}
