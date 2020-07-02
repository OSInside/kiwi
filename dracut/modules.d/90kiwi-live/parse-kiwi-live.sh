#!/bin/bash
# live images are specified with
# root=live:CDLABEL=label
# root=live:AOEINTERFACE=name

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "live" ] ; then
    liveroot=${root}
fi

[ "${liveroot%%:*}" = "live" ] || return 1

modprobe -q loop

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

[ "$rootok" = "1" ] || return 1

info "root was ${liveroot}, is now ${root}"

# make sure that init doesn't complain
[ -z "${root}" ] && root="live"

wait_for_dev -n /run/rootfsbase
wait_for_dev -n /run/overlayfs/rw
wait_for_dev -n /run/overlayfs/work

return 0
