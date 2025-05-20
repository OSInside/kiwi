#!/bin/bash

# shellcheck disable=SC1091
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

declare root=${root}

case "${root}" in
    live:/dev/*)
        {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue %s %s %s"\n' \
            "${root#live:/dev/}" "--settled --onetime --unique" \
            "/sbin/kiwi-live-root" "${root#live:}"
        printf 'SYMLINK=="%s", RUN+="/sbin/initqueue %s %s %s"\n' \
            "${root#live:/dev/}" "--settled --onetime --unique" \
            "/sbin/kiwi-live-root" "${root#live:}"
        } >> /etc/udev/rules.d/99-live-kiwi.rules
        wait_for_dev -n "${root#live:}"
        ;;
    live:aoe:/dev/*)
        {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue %s %s %s"\n' \
            "${root#live:aoe:/dev/}" "--settled --onetime --unique" \
            "/sbin/kiwi-live-root" "${root#live:aoe:}"
        } >> /etc/udev/rules.d/99-live-aoe-kiwi.rules
        wait_for_dev -n "${root#live:aoe:}"
        ;;
    live:net:*)
        system=$(getarg rd.kiwi.live.system=)
        if [ -z "${system}" ];then
            system=/dev/ram0
        fi
        {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue %s %s %s"\n' \
            "${system#/dev/}" "--settled --onetime --unique" \
            "/sbin/kiwi-live-root" "${root}"
        } >> /etc/udev/rules.d/99-live-net-kiwi.rules
        wait_for_dev -n "${system}"
        ;;
esac
