#!/bin/bash
# install images are specified with
# root=install:CDLABEL=label
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

[ -z "${root}" ] && root=$(getarg root=)

if getargbool 0 rd.kiwi.install.pxe; then
    root="install:REMOTE"
fi

if [ "${root%%:*}" = "install" ] ; then
    installroot=${root}
fi

[ "${installroot%%:*}" = "install" ] || return 1

modprobe -q loop

case "${installroot}" in
    install:CDLABEL=*|CDLABEL=*) \
        root="${root#install:}"
        root="$(echo "${root}" | sed 's,/,\\x2f,g')"
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
