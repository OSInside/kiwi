#!/bin/bash -x

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "live" ] ; then
    liveroot="${root}"
fi

[ "${liveroot%%:*}" = "live" ] || exit 0

case "${liveroot}" in
    live:CDLABEL=*|CDLABEL=*) \
        root="${root#live:}"
        root="${root//\//\\x2f}"
        root="live:/dev/disk/by-label/${root#CDLABEL=}"
        rootok=1 ;;
    live:AOEINTERFACE=*|AOEINTERFACE=*) \
        root="${root#live:}"
        root="${root//\//\\x2f}"
        root="live:aoe:/dev/etherd/${root#AOEINTERFACE=}"
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
    echo "What=LiveOS_rootfs"
    echo "Options=${ROOTFLAGS},lowerdir=/run/rootfsbase,upperdir=/run/overlayfs/rw,workdir=/run/overlayfs/work"
    echo "Type=overlay"
    _dev=LiveOS_rootfs
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
