#!/bin/bash
# overlay images are specified with
# root=overlay:UUID=uuid

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "overlay" ] ; then
    overlayroot=$root
fi

[ "${overlayroot%%:*}" = "overlay" ] || return 1

modprobe -q loop

case "${overlayroot}" in
    overlay:UUID=*|UUID=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-uuid/${root#UUID=}"
        rootok=1 ;;
esac

[ "${rootok}" = "1" ] || return 1

info "root was ${overlayroot}, is now ${root}"

# make sure that init doesn't complain
[ -z "${root}" ] && root="overlay"

wait_for_dev -n "${root#block:}"

return 0
