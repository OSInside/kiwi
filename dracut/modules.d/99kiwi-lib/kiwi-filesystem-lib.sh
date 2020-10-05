type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function getOverlayBaseDirectory {
    # initialize and print overlay base directory below which
    # the overlayfs based mountpoints are managed
    local overlay_base=/run/overlay
    local overlay_size
    mkdir -p "${overlay_base}"
    if ! mountpoint -q "${overlay_base}";then
        overlay_size=$(getarg rd.root.overlay.size)
        [ -z "${overlay_size}" ] && overlay_size="50%"
        mount -t tmpfs -o "size=${overlay_size}" tmpfs "${overlay_base}"
    fi
    echo "${overlay_base}"
}

function resize_filesystem {
    local device=$1
    test -n "${device}" || return
    local resize_fs
    local mpoint=/fs-resize
    local fstype
    fstype=$(probe_filesystem "${device}")
    case ${fstype} in
    ext2|ext3|ext4)
        resize_fs="resize2fs -f -p ${device}"
    ;;
    btrfs)
        resize_fs="mkdir -p ${mpoint} && mount ${device} ${mpoint} &&"
        resize_fs="${resize_fs} btrfs filesystem resize max ${mpoint}"
        resize_fs="${resize_fs};umount ${mpoint} && rmdir ${mpoint}"
    ;;
    xfs)
        resize_fs="mkdir -p ${mpoint} && mount ${device} ${mpoint} &&"
        resize_fs="${resize_fs} xfs_growfs ${mpoint}"
        resize_fs="${resize_fs};umount ${mpoint} && rmdir ${mpoint}"
    ;;
    swap)
        resize_fs="mkswap ${device} --label SWAP"
    ;;
    *)
        # don't know how to resize this filesystem
        warn "Don't know how to resize ${fstype}... skipped"
        return
    ;;
    esac
    if ! _is_ramdisk_device "${device}"; then
        check_filesystem "${device}"
    fi
    info "Resizing ${fstype} filesystem on ${device}..."
    if ! eval "${resize_fs}"; then
        die "Failed to resize filesystem"
    fi
}

function check_filesystem {
    local device=$1
    test -n "${device}" || return
    local check_fs
    local check_fs_return_ok
    local fstype
    fstype=$(probe_filesystem "${device}")
    case ${fstype} in
    ext2|ext3|ext4)
        # The exit code by e2fsck is the sum of the following conditions:
        # 0    - No errors
        # 1    - File system errors corrected
        # 2    - File system errors corrected, system should be rebooted
        # 4    - File system errors left uncorrected
        # 8    - Operational error
        # 16   - Usage or syntax error
        # 32   - E2fsck canceled by user request
        # 128  - Shared library error
        check_fs="e2fsck -p -f ${device}"
        check_fs_return_ok="test \$? -le 2"
    ;;
    btrfs)
        # btrfs check returns a zero exit status if it succeeds.
        # Non zero is returned in case of failure.
        check_fs="btrfsck ${device}"
        check_fs_return_ok="test \$? -eq 0"
    ;;
    xfs)
        # xfs_repair can be used to check the filesystem. However
        # for subsequent xfs_growfs no check is needed. Thus for
        # xfs we skip the checking
        return
    ;;
    *)
        # don't know how to check this filesystem
        warn "Don't know how to check ${fstype}... skipped"
        return
    ;;
    esac
    info "Checking ${fstype} filesystem on ${device}..."
    eval "${check_fs}"
    if ! eval "${check_fs_return_ok}"; then
        die "Failed to check filesystem"
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
    echo ${fstype}
}

#======================================
# Methods considered private
#--------------------------------------
function _is_ramdisk_device {
    echo "$1" | grep -qi "/dev/ram"
}
