#!/bin/bash

# called by dracut
check() {
    return 255
}

# called by dracut
depends() {
    echo network rootfs-block dm kiwi-lib kiwi-dump
    return 0
}

# called by dracut
installkernel() {
    return 0
}

# called by dracut
install() {
    declare moddir=${moddir}

    inst_hook pre-mount 40 "${moddir}/kiwi-dump-reboot-system.sh"
}
