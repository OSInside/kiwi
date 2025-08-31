#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

if ! getargbool 0 rd.kiwi.ramdisk; then
    # we create a sysroot generator only for the special
    # ramdisk deployment case
    exit 0
fi

root_cmdline=$(getarg root=)
if [ -z "${root_cmdline}" ];then
    # if the root= parameter is missing there is no guarantee
    # that the /config.bootoptions file is present on local
    # storage at the time this generator code is called. This
    # case applies on PXE deployments which serves config.bootoptions
    # from the network. The mount process including config.bootoptions
    # paramters is then handled by the dracut
    # mount hook: kiwi-mount-ramdisk.sh
    exit 0
fi

GENERATOR_DIR="$1"
[ -z "${GENERATOR_DIR}" ] && exit 1
[ -d "${GENERATOR_DIR}" ] || mkdir -p "${GENERATOR_DIR}"

[ -e /config.bootoptions ] || exit 1

root_uuid=$(
    awk '{ for(i=1; i <= NF; i++) {print $i } }' /config.bootoptions |\
    grep root= | cut -f2- -d=
)

[ -z "${root_uuid}" ] && exit 2

{
    echo "[Unit]"
    echo "Before=initrd-root-fs.target"
    echo "DefaultDependencies=no"
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
