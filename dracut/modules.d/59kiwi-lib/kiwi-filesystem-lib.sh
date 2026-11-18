#!/bin/bash

# shellcheck disable=SC1091
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function getOverlayBaseDirectory {
    # initialize and print overlay base directory below which
    # the overlayfs based mountpoints are managed
    local overlay_base=/run/overlay
    local unit_name
    local overlay_size
    mkdir -p "${overlay_base}"
    if ! mountpoint -q "${overlay_base}";then
        overlay_size=$(getarg rd.root.overlay.size)
        [ -z "${overlay_size}" ] && overlay_size="50%"
        unit_name=$(echo "${overlay_base}" | cut -c 2- | tr / -)
        cat >/run/systemd/system/"${unit_name}".mount <<-EOF
		[Unit]
		Before=initrd-root-fs.target
		DefaultDependencies=no
		[Mount]
		Where=$overlay_base
		What=tmpfs
		Type=tmpfs
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
		EOF
        systemctl start "${unit_name}".mount
    fi
    echo "${overlay_base}"
}

function resize_filesystem {
    # """
    # grow the filesystem on the given device to the size of the
    # device, see grow_filesystem. Stops the boot process if the
    # resize failed
    # """
    if ! grow_filesystem "$1"; then
        die "Failed to resize filesystem"
    fi
}

function grow_filesystem {
    # """
    # grow the filesystem on the given device to the size of the
    # device. A filesystem which can't be resized is skipped with
    # a message. Returns 1 if the check or the resize failed
    # """
    local device=$1
    test -n "${device}" || return 0
    local mpoint=/fs-resize
    local fstype
    local uuid
    local label
    local result
    fstype=$(probe_filesystem "${device}")
    case ${fstype} in
    ext2|ext3|ext4|xfs|swap)
    ;;
    btrfs)
        if _is_btrfs_seeding_device "${device}";then
            # a seeding device can only be mounted read-only
            warn "btrfs seeding device ${device} can't be resized... skipped"
            return 0
        fi
    ;;
    *)
        # don't know how to resize this filesystem
        warn "Don't know how to resize ${fstype}... skipped"
        return 0
    ;;
    esac
    if ! _is_ramdisk_device "${device}"; then
        if [ ! "${fstype}" = "btrfs" ];then
            # btrfs reports the free space cache to be outdated/corrupt
            # after kiwi has resized the partition table. This is an
            # expected condition prior resize of the filesystem and
            # should not prevent the following resize. As such the
            # filesystem check is not applied for btrfs prior resize
            fsck_filesystem "${device}" || return 1
        fi
    fi
    info "Resizing ${fstype} filesystem on ${device}..."
    case ${fstype} in
    ext2|ext3|ext4)
        set_device_lock "${device}" resize2fs -f -p "${device}"
    ;;
    btrfs|xfs)
        mkdir -p "${mpoint}" || return 1
        mount "${device}" "${mpoint}" || return 1
        if [ "${fstype}" = "btrfs" ];then
            set_device_lock "${device}" \
                btrfs filesystem resize max "${mpoint}"
        else
            set_device_lock "${device}" xfs_growfs "${mpoint}"
        fi
        result=$?
        umount "${mpoint}" && rmdir "${mpoint}" || return 1
        return "${result}"
    ;;
    swap)
        # keep the identity of the swap space, which might be
        # referenced e.g. in fstab
        uuid=$(blkid "${device}" -s UUID -o value)
        label=$(blkid "${device}" -s LABEL -o value)
        set_device_lock "${device}" \
            mkswap ${uuid:+-U "${uuid}"} --label "${label:-SWAP}" "${device}"
    ;;
    esac
}

function check_filesystem {
    # """
    # check the filesystem on the given device, see fsck_filesystem.
    # Stops the boot process if the check failed
    # """
    if ! fsck_filesystem "$1"; then
        die "Failed to check filesystem"
    fi
}

function fsck_filesystem {
    # """
    # check the filesystem on the given device. A filesystem which
    # can't be checked is skipped with a message. Returns 1 if the
    # check failed
    # """
    local device=$1
    test -n "${device}" || return 0
    local fstype
    local result
    fstype=$(probe_filesystem "${device}")
    case ${fstype} in
    ext2|ext3|ext4|btrfs)
    ;;
    xfs)
        # xfs_repair can be used to check the filesystem. However
        # for subsequent xfs_growfs no check is needed. Thus for
        # xfs we skip the checking
        return 0
    ;;
    *)
        # don't know how to check this filesystem
        warn "Don't know how to check ${fstype}... skipped"
        return 0
    ;;
    esac
    info "Checking ${fstype} filesystem on ${device}..."
    if [ "${fstype}" = "btrfs" ];then
        # btrfs check returns a zero exit status if it succeeds.
        # Non zero is returned in case of failure.
        set_device_lock "${device}" btrfsck "${device}"
        return
    fi
    # The exit code by e2fsck is the sum of the following conditions:
    # 0    - No errors
    # 1    - File system errors corrected
    # 2    - File system errors corrected, system should be rebooted
    # 4    - File system errors left uncorrected
    # 8    - Operational error
    # 16   - Usage or syntax error
    # 32   - E2fsck canceled by user request
    # 128  - Shared library error
    set_device_lock "${device}" e2fsck -p -f "${device}"
    result=$?
    test "${result}" -le 2
}

function clear_btrfs_seeding_flag {
    # """
    # clear the seeding flag of the given unmounted btrfs filesystem.
    # kiwi flags the root filesystem of the disk image as seeding
    # device for the partition based installation, see
    # rd.kiwi.install.partition_based, in which it is the source of
    # the btrfs seed/sprout process. On the installed system or when
    # the disk image boots as system directly, the flag must be
    # cleared, as a seeding device can only be mounted read-only.
    # The device is the filesystem itself, also if it is located
    # inside of LUKS or RAID. Filesystems which are not btrfs or not
    # flagged are not changed, btrfstune fails for a filesystem
    # without the flag
    # """
    local device=$1
    test -n "${device}" || return
    if [ ! "$(probe_filesystem "${device}")" = "btrfs" ];then
        return
    fi
    if ! _is_btrfs_seeding_device "${device}";then
        return
    fi
    info "Clearing btrfs seeding flag on ${device}..."
    if ! set_device_lock "${device}" btrfstune -f -S 0 "${device}"; then
        die "Failed to clear btrfs seeding flag on ${device}"
    fi
}

function probe_filesystem {
    local device=$1
    test -n "${device}" || return
    local fstype
    fstype=$(blkid "${device}" -s TYPE -o value)
    if [ -z "${fstype}" ];then
        fstype=unknown
    fi
    if [ "${fstype}" = "crypto_LUKS" ];then
        fstype=luks
    fi
    echo "${fstype}"
}

#======================================
# Methods considered private
#--------------------------------------
function _is_ramdisk_device {
    echo "$1" | grep -qi "/dev/ram"
}

function _is_btrfs_seeding_device {
    btrfs inspect-internal dump-super "$1" | grep -q "SEEDING"
}
