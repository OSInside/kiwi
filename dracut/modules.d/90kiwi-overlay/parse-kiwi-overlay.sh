#!/bin/bash
# overlay images are specified with
# root=overlay:UUID=uuid
# root=overlay:nbd=ip:exportname
# root=overlay:aoe=interface

[ -z "${root}" ] && root=$(getarg root=)

if [ "${root%%:*}" = "overlay" ] ; then
    overlayroot=$root
fi

[ "${overlayroot%%:*}" = "overlay" ] || return 1

modprobe -q loop

need_network=0

case "${overlayroot}" in
    overlay:UUID=*|UUID=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-uuid/${root#UUID=}"
    ;;
    overlay:nbd=*) \
        root="block:/dev/nbd0"
        need_network=1
    ;;
    overlay:aoe=*) \
        root="${root#overlay:aoe=}"
        root="block:/dev/etherd/${root}"
        need_network=1
    ;;
esac

if [ "${need_network}" = "1" ];then
    echo "rd.neednet=1" > /etc/cmdline.d/kiwi-generated.conf
    if ! getarg "ip="; then
        echo "ip=dhcp" >> /etc/cmdline.d/kiwi-generated.conf
    fi
fi

# Done, all good!
rootok=1

[ "${rootok}" = "1" ] || return 1

info "root was ${overlayroot}, is now ${root}"

# make sure that init doesn't complain
[ -z "${root}" ] && root="overlay"

wait_for_dev -n "${root#block:}"
