#!/bin/bash
# install images are specified with
# root=install:CDLABEL=label
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if getargbool 0 rd.kiwi.install.pxe; then
    root="install:REMOTE"
    echo "rd.neednet=1" > /etc/cmdline.d/kiwi-generated.conf
    if ! getarg "ip="; then
        echo "ip=dhcp" >> /etc/cmdline.d/kiwi-generated.conf
    fi
fi

if [ "${root%%:*}" = "install" ] ; then
    installroot=${root}
fi

[ "${installroot%%:*}" = "install" ] || return 1

modprobe -q loop

case "${installroot}" in
    install:CDLABEL=*|CDLABEL=*) \
        root="${root#install:}"
        root="${root//\//\\x2f}"
        root="install:/dev/disk/by-label/${root#CDLABEL=}"
        rootok=1 ;;

    install:REMOTE) \
        rootok=1 ;;
esac

[ "$rootok" = "1" ] || return 1

info "root was ${installroot}, is now ${root}"

# make sure that init doesn't complain
[ -z "${root}" ] && root="install"

return 0
