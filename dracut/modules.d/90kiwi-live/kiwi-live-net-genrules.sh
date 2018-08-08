#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

if getargbool 0 rd.kiwi.live.pxe; then
    {
        echo -n "SUBSYSTEM==\"net\", ACTION==\"add\", "
        echo -n "DRIVERS==\"?*\", ATTR{address}==\"?*\", "
        echo -n "ATTR{dev_id}==\"0x0\", ATTR{type}==\"1\", "
        echo -n "KERNEL==\"?*\", NAME=\"lan0\""
        echo
    } > /etc/udev/rules.d/90-net.rules
fi
