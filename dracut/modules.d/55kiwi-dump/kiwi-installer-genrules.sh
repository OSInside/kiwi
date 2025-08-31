#!/bin/bash

declare root=${root}

case "${root}" in
    install:/dev/*)
    {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-installer-device %s"\n' \
            "${root#install:/dev/}" "${root#install:}"
        printf 'SYMLINK=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/kiwi-installer-device %s"\n' \
            "${root#install:/dev/}" "${root#install:}"
    } >> /etc/udev/rules.d/99-installer-kiwi.rules
    wait_for_dev -n "${root#install:}"
    ;;
esac
