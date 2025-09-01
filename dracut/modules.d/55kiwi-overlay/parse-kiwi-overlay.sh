#!/bin/bash
# overlay images are specified with
# root=overlay:UUID=uuid
# root=overlay:PARTUUID=partuuid
# root=overlay:LABEL=label
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
        rootok=1
    ;;
    overlay:PARTUUID=*|PARTUUID=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-partuuid/${root#PARTUUID=}"
        rootok=1
    ;;
    overlay:PARTLABEL=*|PARTLABEL=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-partlabel/${root#PARTLABEL=}"
        rootok=1
    ;;
    overlay:LABEL=*|LABEL=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/disk/by-label/${root#LABEL=}"
        rootok=1
    ;;
    overlay:UNIXNODE=*|UNIXNODE=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/${root#UNIXNODE=}"
        rootok=1
    ;;
    overlay:MAPPER=*|MAPPER=*) \
        root="${root#overlay:}"
        root="${root//\//\\x2f}"
        root="block:/dev/mapper/${root#MAPPER=}"
        rootok=1
    ;;
    overlay:nbd=*) \
        root="${root#overlay:nbd=}"
        root="block:/dev/nbd0"
        need_network=1
        rootok=1
    ;;
    overlay:aoe=*) \
        root="${root#overlay:aoe=}"
        root="block:/dev/etherd/${root}"
        need_network=1
        rootok=1
    ;;
esac

if [ "${need_network}" = "1" ];then
    echo "rd.neednet=1" > /etc/cmdline.d/kiwi-generated.conf
    if ! getarg "ip="; then
        echo "ip=dhcp" >> /etc/cmdline.d/kiwi-generated.conf
    fi
fi

[ "${rootok}" = "1" ] || return 1

info "root was ${overlayroot}, is now ${root}"

# make sure that init doesn't complain
[ -z "${root}" ] && root="overlay"

wait_for_dev -n "${root#block:}"
