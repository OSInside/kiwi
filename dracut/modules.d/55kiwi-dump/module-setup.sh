#!/bin/bash

# called by dracut
check() {
    return 255
}

# called by dracut
depends() {
    echo network rootfs-block dm kiwi-lib
    return 0
}

# called by dracut
installkernel() {
    instmods squashfs loop iso9660 vfat nls_cp437 nls_iso8859-1
}

# called by dracut
install() {
    declare moddir=${moddir}
    declare systemdutildir=${systemdutildir}
    declare dracutbasedir=${dracutbasedir}
    local dmsquashdir=
    inst_multiple \
        tr lsblk dd sha256sum sha512sum head pv kexec \
        basename awk kpartx sort mount mountpoint readlink \
        btrfs btrfstune mount umount losetup cp
    inst_multiple -o efibootmgr

    # support booting the install ISO as a file on disk via
    # iso-scan/filename=, e.g. through a grub loopback setup
    dmsquashdir=$(find "${dracutbasedir}/modules.d" -name "*dmsquash-live")
    if [[ -n "${dmsquashdir}" ]] && \
        [[ -f "${dmsquashdir}/parse-iso-scan.sh" ]] && \
        [[ -f "${dmsquashdir}/iso-scan.sh" ]]; then
        inst_hook cmdline 31 "${dmsquashdir}/parse-iso-scan.sh"
        inst_script "${dmsquashdir}/iso-scan.sh" "/sbin/iso-scan"
    fi

    inst_hook pre-udev 30 "${moddir}/kiwi-installer-genrules.sh"

    inst_script "${moddir}/kiwi-installer-device.sh" \
        "/sbin/kiwi-installer-device"

    inst_hook cmdline 30 "${moddir}/parse-kiwi-install.sh"
    inst_hook pre-mount 30 "${moddir}/kiwi-dump-image.sh"
    inst_hook mount 30 "${moddir}/kiwi-mount-ramdisk.sh"

    inst_script "${moddir}/kiwi-ramdisk-deployment-generator.sh" \
        "${systemdutildir}/system-generators/dracut-kiwi-ramdisk-generator"

    inst_rules 60-cdrom_id.rules
    dracut_need_initqueue
}
