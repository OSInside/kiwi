#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "overlay" ] ; then
    overlayroot=${root}
fi

[ "${overlayroot%%:*}" = "overlay" ] || exit 0

case "${overlayroot}" in
    overlay:UUID=*|UUID=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-uuid/${root#UUID=}"
        rootok=1 ;;
esac

[ "${rootok}" != "1" ] && exit 0

GENERATOR_DIR="$2"
[ -z "$GENERATOR_DIR" ] && exit 1
[ -d "$GENERATOR_DIR" ] || mkdir "$GENERATOR_DIR"

ROOTFLAGS="$(getarg rootflags)"
{
    echo "[Unit]"
    echo "Before=initrd-root-fs.target"
    echo "DefaultDependencies=no"
    echo "[Mount]"
    echo "Where=/sysroot"
    echo "What=OverlayOS_rootfs"
    echo "Options=${ROOTFLAGS},lowerdir=/run/rootfsbase,upperdir=/run/overlayfs/rw,workdir=/run/overlayfs/work"
    echo "Type=overlay"
    _dev=OverlayOS_rootfs
} > "$GENERATOR_DIR"/sysroot.mount

if [ ! -e "$GENERATOR_DIR/initrd-root-fs.target.requires/sysroot.mount" ]; then
    mkdir -p "$GENERATOR_DIR"/initrd-root-fs.target.requires
    ln -s "$GENERATOR_DIR"/sysroot.mount \
        "$GENERATOR_DIR"/initrd-root-fs.target.requires/sysroot.mount
fi

mkdir -p "$GENERATOR_DIR/$_dev.device.d"
{
    echo "[Unit]"
    echo "JobTimeoutSec=3000"
} > "$GENERATOR_DIR/$_dev.device.d/timeout.conf"
