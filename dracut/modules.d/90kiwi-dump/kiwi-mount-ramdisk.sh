#!/bin/bash
type setup_debug >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

#======================================
# Functions
#--------------------------------------
function mount_ramdisk {
    local root_dev
    local boot_options

    boot_options="/config.bootoptions"

    if [ ! -e "${boot_options}" ]; then
        die "Missing ${boot_options} file"
    fi

    root_dev=$(
        while read -r -d ' ' opt; do echo "${opt}";done < "${boot_options}" |\
        grep root= | cut -f2- -d=
    )

    if [ -z "${root_dev}" ]; then
        die "'root=' argument not found in ${boot_options}"
    fi
    
    mount --options defaults "${root_dev}" /sysroot
}

#======================================
# Mount ramdisk root in /sysroot
#--------------------------------------

setup_debug

if getargbool 0 rd.kiwi.ramdisk; then
    mount_ramdisk
fi
