#!/bin/bash

declare root=${root}

case "${root}" in
    live:/dev/*)
    {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-live-root %s"\n' \
            "${root#live:/dev/}" "${root#live:}"
        printf 'SYMLINK=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-live-root %s"\n' \
            "${root#live:/dev/}" "${root#live:}"
    } >> /etc/udev/rules.d/99-live-kiwi.rules
    wait_for_dev -n "${root#live:}"
    ;;
esac
