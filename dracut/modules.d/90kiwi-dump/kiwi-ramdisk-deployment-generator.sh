#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

GENERATOR_DIR="$1"
[ -z "${GENERATOR_DIR}" ] && exit 1
[ -d "${GENERATOR_DIR}" ] || mkdir -p "${GENERATOR_DIR}"

[ -e /config.bootoptions ] || exit 1

root_uuid=$(
    while read -r -d ' ' opt; do echo "${opt}";done < /config.bootoptions |\
    grep root= | cut -f2- -d=
)

[ -z "${root_uuid}" ] && exit 1

{
    echo "[Unit]"
    echo "Before=initrd-root-fs.target"
    echo "[Mount]"
    echo "Where=/sysroot"
    echo "What=${root_uuid}"
    _dev=RamDisk_rootfs
} > "$GENERATOR_DIR"/sysroot.mount

if [ ! -e "$GENERATOR_DIR/initrd-root-fs.target.requires/sysroot.mount" ]; then
    mkdir -p "$GENERATOR_DIR"/initrd-root-fs.target.requires
    ln -s "$GENERATOR_DIR"/sysroot.mount \
        "$GENERATOR_DIR"/initrd-root-fs.target.requires/sysroot.mount
fi

mkdir -p "$GENERATOR_DIR/$_dev.device.d"
{
    echo "[Unit]"
    echo "JobTimeoutSec=60"
} > "$GENERATOR_DIR/$_dev.device.d/timeout.conf"
