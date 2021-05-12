#!/bin/bash
# live images are specified with
# root=live:CDLABEL=label
# root=live:AOEINTERFACE=name
type getOverlayBaseDirectory >/dev/null 2>&1 || . /lib/kiwi-live-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "live" ] ; then
    liveroot=${root}
fi

[ "${liveroot%%:*}" = "live" ] || return 1

modprobe -q loop

need_network=0
if getargbool 0 rd.kiwi.live.pxe; then
    need_network=1
fi

case "${liveroot}" in
    live:CDLABEL=*|CDLABEL=*) \
        root="${root#live:}"
        root="${root//\//\\x2f}"
        root="live:/dev/disk/by-label/${root#CDLABEL=}"
        rootok=1 ;;
    live:AOEINTERFACE=*|AOEINTERFACE=*) \
        modprobe -q aoe
        root="${root#live:}"
        root="${root//\//\\x2f}"
        root="live:aoe:/dev/etherd/${root#AOEINTERFACE=}"
        need_network=1
        rootok=1 ;;
esac

[ "$rootok" = "1" ] || return 1

info "root was ${liveroot}, is now ${root}"

# create network setup if needed
if [ "${need_network}" = "1" ];then
    echo "rd.neednet=1" > /etc/cmdline.d/kiwi-generated.conf
    if ! getarg "ip="; then
        echo "ip=dhcp" >> /etc/cmdline.d/kiwi-generated.conf
    fi
fi

# make sure that init doesn't complain
[ -z "${root}" ] && root="live"

OVERLAY_BASE="$(getOverlayBaseDirectory)"

wait_for_dev -n "${OVERLAY_BASE}/rootfsbase"
wait_for_dev -n "${OVERLAY_BASE}/overlayfs/rw"
wait_for_dev -n "${OVERLAY_BASE}/overlayfs/work"

return 0
