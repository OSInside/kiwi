#!/bin/bash

declare root=${root}

case "${root}" in
    overlay:/dev/*)
    {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-overlay-root %s"\n' \
            "${root#overlay:/dev/}" "${root#overlay:}"
        printf 'SYMLINK=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-overlay-root %s"\n' \
            "${root#overlay:/dev/}" "${root#overlay:}"
    } >> /etc/udev/rules.d/99-overlay-kiwi.rules
    wait_for_dev -n "${root#overlay:}"
    ;;
esac
