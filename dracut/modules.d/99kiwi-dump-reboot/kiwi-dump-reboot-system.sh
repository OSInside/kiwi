#!/bin/bash
type report_and_quit >/dev/null 2>&1 || . /lib/kiwi-dump-image.sh
type get_selected_disk >/dev/null 2>&1 || . /lib/kiwi-dump-image.sh
type run_dialog >/dev/null 2>&1 || . /lib/kiwi-dialog-lib.sh

#======================================
# Functions
#--------------------------------------
function boot_installed_system {
    local boot_options
    # if rd.kiwi.install.pass.bootparam is given, pass on most
    # boot options to the kexec kernel
    if getargbool 0 rd.kiwi.install.pass.bootparam; then
        local cmdline
        local option
        read -r cmdline < /proc/cmdline
        for option in ${cmdline}; do
            case ${option} in
                rd.kiwi.*) ;; # skip all rd.kiwi options, they might do harm
                *)  boot_options="${boot_options}${option} ";;
            esac
        done
    fi
    boot_options="${boot_options}$(cat /config.bootoptions)"
    if getargbool 0 rd.kiwi.debug; then
        boot_options="${boot_options} rd.kiwi.debug"
    fi
    kexec -l /run/install/boot/*/loader/linux \
        --initrd /run/install/initrd.system_image \
        --command-line "${boot_options}"
    if ! kexec -e; then
        report_and_quit "Failed to kexec boot system"
    fi
}

#======================================
# Reboot into system
#--------------------------------------

if getargbool 0 rd.kiwi.ramdisk; then
    # For ramdisk deployment a kexec boot is not possible as it
    # will wipe the contents of the ramdisk. Therefore we prepare
    # the switch_root from this deployment initrd. See
    # kiwi-mount-ramdisk.sh mount hook for further details.
    image_target=$(get_selected_disk)
    kpartx -s -a "${image_target}"
else
    # Standard deployment will use kexec to activate and boot the
    # deployed system
    boot_installed_system
fi
