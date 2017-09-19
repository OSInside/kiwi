#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function lookupIsoDiskDevice {
    local disk
    local disk_device
    for disk in $(lsblk -n -r -o NAME,TYPE | grep disk | cut -f1 -d' ');do
        disk_device="/dev/${disk}"
        application_id=$(
            isoinfo -d -i "${disk_device}" 2>/dev/null |\
                grep "Application id:"|cut -f2 -d:
        )
        if [ ! -z "${application_id}" ];then
            echo "${disk_device}"
            return
        fi
    done
}

function setupDebugMode {
    if getargbool 0 rd.live.debug; then
        local log=/run/initramfs/log
        mkdir -p ${log}
        exec > ${log}/boot.kiwi
        exec 2>> ${log}/boot.kiwi
        set -x
    fi
}

function loadKernelModules {
    modprobe squashfs
}

function initGlobalDevices {
    if [ -z "$1" ]; then
        die "No root device for operation given"
    fi
    isodev="$1"
    isodiskdev=$(lookupIsoDiskDevice)
    isofs_type=$(blkid -s TYPE -o value "${isodev}")
    media_check_device=${isodev}
    if [ ! -z "${isodiskdev}" ]; then
        media_check_device=${isodiskdev}
    fi
    export media_check_device
    export isodev
    export isodiskdev
    export isofs_type
}

function initGlobalOptions {
    live_dir=$(getarg rd.live.dir -d live_dir)
    [ -z "${live_dir}" ] && live_dir="LiveOS"

    squash_image=$(getarg rd.live.squashimg)
    [ -z "${squash_image}" ] && squash_image="squashfs.img"

    cow_filesystem=$(getarg rd.live.overlay.cowfs)
    [ -z "${cow_filesystem}" ] && cow_filesystem="ext4"
}

function mountIso {
    ln -s "${isodev}" /run/initramfs/isodev
    local iso_mount_point=/run/initramfs/live
    mkdir -m 0755 -p "${iso_mount_point}"
    if ! mount -n -t "${isofs_type}" "${isodev}" "${iso_mount_point}"; then
        die "Failed to mount live ISO device"
    fi
    echo "${iso_mount_point}"
}

function mountCompressedContainerFromIso {
    local iso_mount_point=$1
    local container_mount_point=/run/initramfs/squashfs_container
    squashfs_container="${iso_mount_point}/${live_dir}/${squash_image}"
    mkdir -m 0755 -p "${container_mount_point}"
    if ! mount -n "${squashfs_container}" "${container_mount_point}";then
        die "Failed to mount live ISO squashfs container"
    fi
    echo "${container_mount_point}"
}

function mountReadOnlyRootImageFromContainer {
    local container_mount_point=$1
    local rootfs_image="${container_mount_point}/LiveOS/rootfs.img"
    local root_mount_point=/run/rootfsbase
    mkdir -m 0755 -p "${root_mount_point}"
    if ! mount -n "${rootfs_image}" "${root_mount_point}"; then
        die "Failed to mount live ISO root filesystem"
    fi
    echo "${root_mount_point}"
}

function prepareTemporaryOverlay {
    mkdir -m 0755 -p /run/overlayfs/rw
    mkdir -m 0755 -p /run/overlayfs/work
}

function preparePersistentOverlay {
    if [ -z "${isodiskdev}" ]; then
        return 1
    fi
    local overlay_mount_point=/run/overlayfs
    mkdir -m 0755 -p "${overlay_mount_point}"
    if ! mount -L cow "${overlay_mount_point}"; then
        echo -e "n\np\n\n\n\nw\nq" | fdisk "${isodiskdev}"
        if ! partprobe "${isodiskdev}"; then
            return 1
        fi
        local write_partition
        write_partition=$(lsblk "${isodiskdev}" -r -n -o NAME | tail -n1)
        if ! mkfs."${cow_filesystem}" -L cow /dev/"${write_partition}"; then
            return 1
        fi
        if ! mount -L cow ${overlay_mount_point}; then
            return 1
        fi
    fi
    mkdir -m 0755 -p ${overlay_mount_point}/rw
    mkdir -m 0755 -p ${overlay_mount_point}/work
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
    local service=/usr/lib/systemd/system/dracut-run-interactive.service
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
        echo "ExecStart=/bin/bash /bin/dracut-interactive"
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
    echo "dialog $*" >/bin/dracut-interactive
    _run_interactive
}
