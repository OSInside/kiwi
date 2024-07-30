#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function getOverlayBaseDirectory {
    # initialize and print overlay base directory below which
    # the iso and overlayfs based mountpoints are managed
    local overlay_base=/run/overlay
    local overlay_size
    mkdir -p "${overlay_base}"
    if ! mountpoint -q "${overlay_base}";then
        overlay_size=$(getarg rd.live.overlay.size)
        [ -z "${overlay_size}" ] && overlay_size="50%"
        mount -t tmpfs -o "size=${overlay_size}" tmpfs "${overlay_base}"
    fi
    echo "${overlay_base}"
}

function lookupIsoDiskDevice {
    local root=$1
    local iso_label=${root#/dev/disk/by-label/}
    local disk
    local mount_point
    local iso_volid
    for disk in $(lsblk -p -n -r -o NAME,TYPE | grep disk | cut -f1 -d' ');do
        if [[ ${disk} =~ ^/dev/fd ]];then
            # ignore floppy disk devices
            continue
        fi
        # 1. Mapping:
        # If the ISO is bootet as disk in hybrid mode the exposed LABEL
        # of the disk device matches the ISO label
        iso_volid=$(blkid -s LABEL -o value "${disk}")
        if [ "${iso_volid}" = "${iso_label}" ];then
            echo "${disk}%disk_boot"
            return
        fi
        # 2. Mapping:
        # If the ISO is booted via grub loopback the partition of the
        # disk device which contains the ISO file and was loopbacked
        # by grub is mounted to /run/initramfs/isoscan
        for mount_point in $(lsblk -p -n -r -o MOUNTPOINT "${disk}");do
            if [ "${mount_point}" = "/run/initramfs/isoscan" ];then
                echo "${disk}%loop_boot"
                return
            fi
        done
    done
}

function setupDebugMode {
    if getargbool 0 rd.kiwi.debug; then
        local log=/run/initramfs/log
        mkdir -p ${log}
        exec > ${log}/boot.kiwi
        exec 2>> ${log}/boot.kiwi
        set -x
    fi
}

function initialize {
    local profile=/.profile
    test -f ${profile} && cat ${profile}
}

function loadKernelModules {
    modprobe squashfs
}

function udev_pending {
    declare DEVICE_TIMEOUT=${DEVICE_TIMEOUT}
    local limit=120
    if [[ "${DEVICE_TIMEOUT}" =~ ^[0-9]+$ ]]; then
        limit="${DEVICE_TIMEOUT}"
    fi
    udevadm settle --timeout="${limit}"
}

function initGlobalDevices {
    if [ -z "$1" ]; then
        die "No root device for operation given"
    fi
    isodev="$1"
    local isodisk
    isodisk=$(lookupIsoDiskDevice "${isodev}")
    isodiskdev=$(echo "${isodisk}" | cut -f1 -d%)
    isodiskmode=$(echo "${isodisk}" | cut -f2 -d%)
    isofs_type=$(blkid -s TYPE -o value "${isodev}")
    media_check_device=${isodev}
    if [ -n "${isodiskdev}" ]; then
        media_check_device=${isodiskdev}
    fi
    export media_check_device
    export isodev
    export isodiskdev
    export isodiskmode
    export isofs_type
}

function initGlobalOptions {
    live_dir=$(getarg rd.live.dir -d live_dir)
    [ -z "${live_dir}" ] && live_dir="LiveOS"

    squash_image=$(getarg rd.live.squashimg)
    [ -z "${squash_image}" ] && squash_image="squashfs.img"

    cow_filesystem=$(getarg rd.live.overlay.cowfs)
    [ -z "${cow_filesystem}" ] && cow_filesystem="ext4"

    cow_file_mbsize=$(getarg rd.live.cowfile.mbsize)
    [ -z "${cow_file_mbsize}" ] && cow_file_mbsize="500"

    cow_file_path=$(getarg rd.live.cowfile.path)
    [ -z "${cow_file_path}" ] && cow_file_path="live_system.cow"
}

function mountIso {
    local overlay_base
    overlay_base=$(getOverlayBaseDirectory)
    ln -s "${isodev}" "${overlay_base}/isodev"
    local iso_mount_point="${overlay_base}/live"
    mkdir -m 0755 -p "${iso_mount_point}"
    if ! mount -o ro -n -t "${isofs_type}" "${isodev}" "${iso_mount_point}"; then
        die "Failed to mount live ISO device"
    fi
    echo "${iso_mount_point}"
}

function mountCompressedContainerFromIso {
    local iso_mount_point=$1
    local overlay_base
    local squashfs_container
    overlay_base=$(getOverlayBaseDirectory)
    local container_mount_point="${overlay_base}/squashfs_container"
    squashfs_container="${iso_mount_point}/${live_dir}/${squash_image}"
    mkdir -m 0755 -p "${container_mount_point}"
    if ! mount -n "${squashfs_container}" "${container_mount_point}";then
        die "Failed to mount live ISO squashfs container"
    fi
    echo "${container_mount_point}"
}

function mountReadOnlyRootImageFromContainer {
    local container_mount_point=$1
    local overlay_base
    overlay_base=$(getOverlayBaseDirectory)
    local rootfs_image="${container_mount_point}/LiveOS/rootfs.img"
    local root_mount_point="${overlay_base}/rootfsbase"
    mkdir -m 0755 -p "${root_mount_point}"

    if ! [ -e "${rootfs_image}" ] && [ -d "${container_mount_point}/proc" ]; then
        # It's the root filesystem directly, just do a bind mount
        mount -n --bind "${container_mount_point}" "${root_mount_point}"
        echo "${root_mount_point}"
        return
    fi

    if ! mount -n "${rootfs_image}" "${root_mount_point}"; then
        die "Failed to mount live ISO root filesystem"
    fi
    echo "${root_mount_point}"
}

function prepareTemporaryOverlay {
    local overlay_base
    overlay_base=$(getOverlayBaseDirectory)
    mkdir -m 0755 -p "${overlay_base}/overlayfs/rw"
    mkdir -m 0755 -p "${overlay_base}/overlayfs/work"
}

function preparePersistentOverlay {
    if [ -z "${isodiskmode}" ] || [ -z "${isodiskdev}" ]; then
        return 1
    fi
    local overlay_base
    overlay_base=$(getOverlayBaseDirectory)
    local overlay_mount_point="${overlay_base}/overlayfs"
    mkdir -m 0755 -p "${overlay_mount_point}"
    if [ "${isodiskmode}" = "disk_boot" ];then
        if ! preparePersistentOverlayDiskBoot "${overlay_mount_point}"; then
            return 1
        fi
    else
        if ! preparePersistentOverlayLoopBoot "${overlay_mount_point}"; then
            return 1
        fi
    fi
    mkdir -m 0755 -p "${overlay_mount_point}/rw"
    mkdir -m 0755 -p "${overlay_mount_point}/work"
}

function preparePersistentOverlayLoopBoot {
    # Create or re-use a cow file on the filesystem the iso
    # was loopback booted from. If the file already exists
    # it will be used as presented. If not it will be created
    # with the custom size configured in rd.live.cowfile.mbsize
    # or the default size of 500MB
    local overlay_mount_point=$1
    local isoscan_loop_mount=/run/initramfs/isoscan
    local cow_file_name="${isoscan_loop_mount}/${cow_file_path}"
    mkdir -m 0755 -p "${overlay_mount_point}"
    if ! mount -o "remount,rw" "${isoscan_loop_mount}"; then
        return 1
    fi
    if ! mount "${cow_file_name}" "${overlay_mount_point}"; then
        if ! dd if=/dev/zero of="${cow_file_name}" \
            count=0 bs=1M seek="${cow_file_mbsize}"; then
            return 1
        fi
        if ! mkfs."${cow_filesystem}" "${cow_file_name}"; then
            return 1
        fi
        if ! mount "${cow_file_name}" "${overlay_mount_point}"; then
            return 1
        fi
    fi
}

function preparePersistentOverlayDiskBoot {
    # Create a write partition and filesystem on the iso
    # disk device with the cow label and mount it. If the
    # disk already populates a cow labeled partition it is
    # used as presented
    local overlay_mount_point=$1
    local partitions_before_cow_part
    mkdir -m 0755 -p "${overlay_mount_point}"
    if ! mount -L cow "${overlay_mount_point}"; then
        partitions_before_cow_part=$(_partition_count)
        echo -e "n\np\n\n\n\nw\nq" | fdisk "${isodiskdev}"
        if type partprobe &> /dev/null;then
            if ! partprobe "${isodiskdev}"; then
                return 1
            fi
        else
            if ! partx -u "${isodiskdev}"; then
                return 1
            fi
        fi
        udev_pending
        if [ "$(_partition_count)" -le "${partitions_before_cow_part}" ];then
            return 1
        fi
        local write_partition
        write_partition=$(lsblk "${isodiskdev}" -p -l -n -o NAME | tail -n1)
        if ! mkfs."${cow_filesystem}" -L cow "${write_partition}"; then
            return 1
        fi
        if ! mount -L cow "${overlay_mount_point}"; then
            return 1
        fi
    fi
}

function runMediaCheck {
    # messages are redirected to stderr because this code is called
    # as part of the pre-mount hook via the dracut-pre-mount.service
    # which only shows messages on stderr to the console and we want
    # to see the check results during boot
    if ! command -v checkmedia &>/dev/null; then
        echo "No mediacheck program installed, mediacheck skipped" 1>&2
        return
    fi
    local timeout=20
    local check_result
    check_result=/run/initramfs/checkmedia.result
    checkmedia "${media_check_device}" &>${check_result}
    local check_status=$?
    if [ ${check_status} != 0 ];then
        echo "ISO check failed" >> ${check_result}
    else
        echo "ISO check passed" >> ${check_result}
    fi
    echo "Press key to continue (waiting ${timeout}sec...)" >> ${check_result}
    _run_dialog --timeout ${timeout} --textbox ${check_result} 20 70
    if [ ${check_status} != 0 ];then
        die "Failed to verify system integrity"
    fi
}

#=========================================
# Methods considered private
#-----------------------------------------
function _setup_interactive_service {
    local service=/run/systemd/system/dracut-run-interactive.service
    mkdir -p /run/systemd/system
    [ -e ${service} ] && return
    {
        echo "[Unit]"
        echo "Description=Dracut Run Interactive"
        echo "DefaultDependencies=no"
        echo "After=systemd-vconsole-setup.service"
        echo "Wants=systemd-vconsole-setup.service"
        echo "Conflicts=emergency.service emergency.target"
        echo "[Service]"
        echo "Environment=HOME=/"
        echo "Environment=DRACUT_SYSTEMD=1"
        echo "Environment=NEWROOT=/sysroot"
        echo "WorkingDirectory=/"
        echo "ExecStart=/bin/bash /run/dracut-interactive"
        echo "Type=oneshot"
        echo "StandardInput=tty-force"
        echo "StandardOutput=inherit"
        echo "StandardError=inherit"
        echo "KillMode=process"
        echo "IgnoreSIGPIPE=no"
        echo "TaskMax=infinity"
        echo "KillSignal=SIGHUP"
    } > ${service}
}

function _run_interactive {
    _setup_interactive_service
    systemctl start dracut-run-interactive.service
}

function _run_dialog {
    echo "dialog $*" >/run/dracut-interactive
    _run_interactive
}

function _partition_count {
    if [ -z "${isodiskdev}" ]; then
        echo 0
    else
        lsblk "${isodiskdev}" -p -r -n -o TYPE | grep -c part
    fi
}
