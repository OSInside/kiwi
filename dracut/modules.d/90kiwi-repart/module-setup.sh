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
    if inst_simple /config.partids; then
        test -f /.profile && inst_simple /.profile
        inst_hook pre-mount 20 "${moddir}/kiwi-repart-disk.sh"
        dracut_need_initqueue
    else
        echo "ERROR: kiwi-repart needs /config.partids; not installing module"
    fi
}
