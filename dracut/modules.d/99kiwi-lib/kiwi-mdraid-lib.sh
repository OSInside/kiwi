#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type set_root_map >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type wait_for_storage_device >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh

function mdraid_system {
    declare kiwi_RaidDev=${kiwi_RaidDev}
    if [ -n "${kiwi_RaidDev}" ];then
        return 0
    fi
    return 1
}

function deactivate_mdraid {
    declare kiwi_RaidDev=${kiwi_RaidDev}
    mdadm --stop "${kiwi_RaidDev}"
}

function activate_mdraid {
    declare kiwi_RaidDev=${kiwi_RaidDev}
    mdadm --assemble --scan "${kiwi_RaidDev}"
    wait_for_storage_device "${kiwi_RaidDev}"
    set_root_map "${kiwi_RaidDev}"
}

function resize_mdraid {
    declare kiwi_RaidDev=${kiwi_RaidDev}
    mdadm --grow --size=max "${kiwi_RaidDev}"
}
