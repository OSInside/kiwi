#!/bin/bash
type initialize >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type report_and_quit >/dev/null 2>&1 || . /lib/kiwi-dump-image.sh
type get_selected_disk >/dev/null 2>&1 || . /lib/kiwi-dump-image.sh
type run_dialog >/dev/null 2>&1 || . /lib/kiwi-dialog-lib.sh

#======================================
# Functions
#--------------------------------------
function boot_installed_system {
    declare kiwi_oemreboot=${kiwi_oemreboot}
    declare kiwi_oemrebootinteractive=${kiwi_oemrebootinteractive}
    declare kiwi_oemshutdown=${kiwi_oemshutdown}
    declare kiwi_oemshutdowninteractive=${kiwi_oemshutdowninteractive}
    local ask_reboot_text="Reboot System ?"
    local ask_shutdown_text="Shutdown System ?"
    local boot_options
    kiwi_oemreboot=$(bool "${kiwi_oemreboot}")
    kiwi_oemrebootinteractive=$(bool "${kiwi_oemrebootinteractive}")
    kiwi_oemshutdown=$(bool "${kiwi_oemshutdown}")
    kiwi_oemshutdowninteractive=$(bool "${kiwi_oemshutdowninteractive}")

    if [ "${kiwi_oemrebootinteractive}" = "true" ];then
        ask_and_reboot "${ask_reboot_text}"
    fi
    if [ "${kiwi_oemreboot}" = "true" ];then
        reboot -f
    fi
    if [ "${kiwi_oemshutdowninteractive}" = "true" ];then
        ask_and_shutdown "${ask_shutdown_text}"
    fi
    if [ "${kiwi_oemshutdown}" = "true" ];then
        systemctl halt
    fi

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
    kexec_options=""
    if kexec --help | grep -q kexec-syscall-auto;then
        # try file based syscall first and fall back to kexec_load
        # syscall if not present. On systems using kexec that does
        # provide --kexec-syscall-auto the assumption is made that
        # neither kexec nor the kernel supports file based syscall
        # and thus no syscall selection is made
        kexec_options="${kexec_options} --kexec-syscall-auto"
    fi
    # shellcheck disable=SC2116,SC2086
    kexec_options=$(echo ${kexec_options}) # strip spaces
    kexec "${kexec_options}" \
        --load /run/install/boot/*/loader/linux \
        --initrd /run/install/initrd.system_image \
        --command-line "${boot_options}"
    if ! kexec -e; then
        report_and_quit "Failed to kexec boot system"
    fi
}

#======================================
# Reboot into system
#--------------------------------------
initialize

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
