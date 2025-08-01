#!/bin/bash

# called by dracut
check() {
    return 255
}

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
    test -f /config.partids && inst_simple /config.partids
    test -f /.profile && inst_simple /.profile
    inst_hook pre-mount 20 "${moddir}/kiwi-repart-disk.sh"
    dracut_need_initqueue
}
