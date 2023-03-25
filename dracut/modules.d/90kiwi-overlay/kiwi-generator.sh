#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type getOverlayBaseDirectory >/dev/null 2>&1 || . /lib/kiwi-filesystem-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "overlay" ] ; then
    overlayroot=${root}
fi

# Generate sysroot unit only if overlay is requested
[ "${overlayroot%%:*}" = "overlay" ] || exit 0

GENERATOR_DIR="$2"
[ -z "$GENERATOR_DIR" ] && exit 1
[ -d "$GENERATOR_DIR" ] || mkdir "$GENERATOR_DIR"

if getargbool 0 rd.root.overlay.readonly; then
    case "${overlayroot}" in
        overlay:PARTUUID=*|PARTUUID=*) \
            root="${root#overlay:}"
            root="${root//\//\\x2f}"
            root="block:/dev/disk/by-partuuid/${root#PARTUUID=}"
        ;;
        overlay:PARTLABEL=*|PARTLABEL=*) \
            root="${root#overlay:}"
            root="${root//\//\\x2f}"
            root="block:/dev/disk/by-partlabel/${root#PARTLABEL=}"
        ;;
        overlay:UNIXNODE=*|UNIXNODE=*) \
            root="${root#overlay:}"
            root="${root//\//\\x2f}"
            root="block:/dev/${root#UNIXNODE=}"
        ;;
    esac
    {
        echo "[Unit]"
        echo "Before=initrd-root-fs.target"
        echo "DefaultDependencies=no"
        echo "[Mount]"
        echo "Where=/sysroot"
        echo "What=${root#block:}"
        echo "Type=squashfs"
        _dev=ReadOnlyOS_rootfs
    } > "$GENERATOR_DIR"/sysroot.mount
else
    OVERLAY_BASE="$(getOverlayBaseDirectory)"
    ROOTFLAGS="$(getarg rootflags)"
    {
        echo "[Unit]"
        echo "Before=initrd-root-fs.target"
        echo "DefaultDependencies=no"
        echo "[Mount]"
        echo "Where=/sysroot"
        echo "What=OverlayOS_rootfs"
        echo "Options=${ROOTFLAGS},lowerdir=${OVERLAY_BASE}/rootfsbase,upperdir=${OVERLAY_BASE}/overlayfs/rw,workdir=${OVERLAY_BASE}/overlayfs/work"
        echo "Type=overlay"
        _dev=OverlayOS_rootfs
    } > "$GENERATOR_DIR"/sysroot.mount
fi

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
