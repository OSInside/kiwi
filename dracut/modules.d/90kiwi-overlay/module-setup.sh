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
    instmods squashfs loop overlay nbd aoe
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    inst_multiple \
        lsblk losetup grep cut mount nbd-client
    inst_hook cmdline 30 "${moddir}/parse-kiwi-overlay.sh"
    # kiwi-repart priority pre-mount hook is 20
    # overlay pre-mount needs to happend after any repartition
    inst_hook pre-mount 30 "${moddir}/kiwi-overlay-root.sh"
    inst_script "${moddir}/kiwi-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-generator"
    dracut_need_initqueue
}
