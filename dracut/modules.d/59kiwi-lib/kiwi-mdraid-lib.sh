#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type set_root_map >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type wait_for_storage_device >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh

# The functions are called with the md raid device kiwi
# created at build time, see lookup_raid_device_from_root()

function mdraid_system {
    local raid_device=$1
    if [ -n "${raid_device}" ];then
        return 0
    fi
    return 1
}

function deactivate_mdraid {
    local raid_device=$1
    mdadm --stop "${raid_device}"
}

function activate_mdraid {
    local raid_device=$1
    mdadm --assemble --scan "${raid_device}"
    wait_for_storage_device "${raid_device}"
    set_root_map "${raid_device}"
}

function update_devicesize_mdraid {
    local raid_device=$1
    mdadm --assemble --scan "${raid_device}" --update=devicesize
    wait_for_storage_device "${raid_device}"
    deactivate_mdraid "${raid_device}"
}

function resize_mdraid {
    local raid_device=$1
    set_device_lock "${raid_device}" \
        mdadm --grow --size=max "${raid_device}"
}
