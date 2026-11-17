#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type setup_debug >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type run_dialog >/dev/null 2>&1 || . /lib/kiwi-dialog-lib.sh
type get_block_device_kbsize >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh
type fetch_file >/dev/null 2>&1 || . /lib/kiwi-net-lib.sh

#======================================
# Functions
#--------------------------------------
function scan_multipath_devices {
    # """
    # starts multipath daemon from multipath module
    # """
    systemctl start multipathd
}

function find_disk_entry {
    # """
    # lookup disk entry by name and echo the
    # associated entry parameter (size) when found
    # """
    local list_items=$1
    local search=$2
    local count=0
    local found=
    for entry in ${list_items};do
        if [ -n "${found}" ];then
            echo "${entry}"
            return
        fi
        if [ $((count % 2)) -eq 0 ];then
            if [ "${entry}" = "${search}" ];then
                found=1
            fi
        fi
        count=$((count + 1))
    done
}

function sort_disk_entries {
    # """
    # sort the disk entry names
    # """
    local list_items=$1
    local count=0
    local device_index=0
    local device_array
    local list_items_sorted
    for entry in ${list_items};do
        if [ $((count % 2)) -eq 0 ];then
            device_array[${device_index}]=${entry}
            device_index=$((device_index + 1))
        fi
        count=$((count + 1))
    done
    printf '%s\0' "${device_array[@]}" | sort -z > list_items_sorted.txt
    readarray -td '' list_items_sorted < list_items_sorted.txt
    echo "${list_items_sorted[*]}"
}

function load_ramdisk_driver {
    declare kiwi_oemramdisksize=${kiwi_oemramdisksize}
    local rd_size
    local custom_rd_size
    local modfile=/etc/modprobe.d/99-brd.conf
    custom_rd_size=$(getarg ramdisk_size=)
    if [ -n "${custom_rd_size}" ];then
        rd_size="${custom_rd_size}"
    elif [ -n "${kiwi_oemramdisksize}" ];then
        rd_size="${kiwi_oemramdisksize}"
    fi
    mkdir -p /etc/modprobe.d
    if [ -n "${rd_size}" ];then
        echo "options brd rd_size=${rd_size}" > ${modfile}
    fi
    modprobe brd
    udev_pending
}

function get_disk_list {
    declare kiwi_oemdevicefilter=${kiwi_oemdevicefilter}
    declare kiwi_oemmultipath_scan=${kiwi_oemmultipath_scan}
    declare kiwi_devicepersistency=${kiwi_devicepersistency}
    declare kiwi_install_volid=${kiwi_install_volid}
    declare kiwi_oemunattended=${kiwi_oemunattended}
    declare kiwi_oemunattended_id=${kiwi_oemunattended_id}
    local disk_id="by-id"
    local disk_size
    local disk_device
    local disk_device_by_id
    local disk_trans
    local disk_meta
    local list_items
    local list_items_sorted
    local max_disk
    local kiwi_oem_maxdisk
    local blk_opts="-p -n -r --sort NAME -o NAME,SIZE,TYPE,TRAN"
    local message
    local blk_opts_plus_label="${blk_opts},LABEL"
    local kiwi_install_disk_part

    if [ -n "${kiwi_devicepersistency}" ];then
        disk_id=${kiwi_devicepersistency}
    fi
    max_disk=0
    kiwi_install_devicepersistency=$(getarg rd.kiwi.install.devicepersistency=)
    kiwi_oemmultipath_scan=$(bool "${kiwi_oemmultipath_scan}")
    kiwi_oem_maxdisk=$(getarg rd.kiwi.oem.maxdisk=)
    kiwi_oem_installdevice=$(getarg rd.kiwi.oem.installdevice=)

    # Check for smallest disk parameter
    # - Configure lsblk options based on the selection mode
    if getargbool 0 rd.kiwi.oem.smallest_disk; then
        # Sort by SIZE (ascending), include TRAN to identify USBs
        blk_opts="-p -n -r --sort SIZE -o NAME,SIZE,TYPE,TRAN"
        blk_opts_plus_label="${blk_opts},LABEL"
    fi

    if [ -n "${kiwi_install_devicepersistency}" ];then
        disk_id=${kiwi_install_devicepersistency}
    fi
    if [ -n "${kiwi_oem_maxdisk}" ]; then
        max_disk=$(binsize_to_bytesize "${kiwi_oem_maxdisk}") || max_disk=0
    fi
    if getargbool 0 rd.kiwi.ramdisk; then
        # target should be a ramdisk on request. Thus actively
        # load the ramdisk block driver and support custom sizes
        load_ramdisk_driver
        # target should be a ramdisk on request. Thus instruct
        # lsblk to list only ramdisk devices (Major=1)
        blk_opts="-I 1 ${blk_opts}"
    elif [ "${kiwi_oemmultipath_scan}" = "true" ];then
        scan_multipath_devices
    fi
    kiwi_install_disk_part=$(
        eval lsblk "${blk_opts_plus_label}" | \
        tr -s ' ' ":" | \
        grep ":${kiwi_install_volid}$" | \
        cut -f1 -d:
    )
    for disk_meta in $(
        eval lsblk "${blk_opts}" | grep -E "disk|raid" | tr ' ' ":"
    );do
        disk_device="$(echo "${disk_meta}" | cut -f1 -d:)"
        if [[ "${kiwi_install_disk_part}" == "${disk_device}"* ]]; then
            # ignore install source device
            continue
        fi
        disk_mpath_child=$(
            eval lsblk "${blk_opts}" "${disk_device}" | grep mpath | \
            tr ' ' ":"
        )
        if [[ -n "${disk_mpath_child}" ]];then
          # use mpath device instead of parent device for multipath
          disk_device="$(echo "${disk_mpath_child}" | cut -f1 -d:)"
        fi

        # Filter USBs if smallest disk is requested
        disk_trans=$(echo "${disk_meta}" | cut -f4 -d:)
        if getargbool 0 rd.kiwi.oem.smallest_disk; then
            if [[ "${disk_trans}" == "usb" ]]; then
                continue
            fi
        fi

        disk_size=$(echo "${disk_meta}" | cut -f2 -d:)
        if [ "${max_disk}" -gt 0 ]; then
            local disk_size_bytes
            disk_size_bytes=$(binsize_to_bytesize "${disk_size}") || \
                disk_size_bytes=0
            if [ "${disk_size_bytes}" -gt "${max_disk}" ]; then
                message="${disk_device} filtered out by"
                message="${message} rd.kiwi.oem.maxdisk=${kiwi_oem_maxdisk}"
                message="${message} (disk size is: ${disk_size})"
                info "${message}" >&2
                continue
            fi
        fi
        disk_device_by_id=$(
            get_persistent_device_from_unix_node "${disk_device}" "${disk_id}"
        )
        if [ -n "${disk_device_by_id}" ];then
            disk_device=${disk_device_by_id}
        fi
        # check for static filter rules
        if [[ ${disk_device} =~ ^/dev/fd ]];then
            # ignore floppy disk devices
            continue
        fi
        # check for custom filter rule
        if [ -n "${kiwi_oemdevicefilter}" ];then
            if [[ ${disk_device} =~ ${kiwi_oemdevicefilter} ]];then
                message="${disk_device} filtered out by rule:"
                message="${message} ${kiwi_oemdevicefilter}"
                info "${message}" >&2
                continue
            fi
        fi
        if [[ "${list_items}" == *"${disk_device}"* ]];then
           # device already in the list, can happen in multipath systems
           continue
        fi
        list_items="${list_items} ${disk_device} ${disk_size}"
    done
    if [ -n "${kiwi_oem_installdevice}" ];then
        # install device overwritten by cmdline.
        local device=${kiwi_oem_installdevice}
        local device_meta
        local device_size
        if [ ! -e "${device}" ];then
            local no_dev="Given device ${device} does not exist"
            report_and_quit "${no_dev}"
        fi
        if [ ! -b "${device}" ];then
            local no_block_dev="Given device ${device} is not a block special"
            report_and_quit "${no_block_dev}"
        fi
        device_meta=$(
            eval lsblk "${blk_opts}" "${device}" |\
            grep -E "disk|raid|mpath" | tr ' ' ":"
        )
        device_size=$(echo "${device_meta}" | cut -f2 -d:)
        list_items="${device} ${device_size}"
    fi
    if [ -z "${list_items}" ];then
        local no_device_text="No device(s) for installation found"
        report_and_quit "${no_device_text}"
    fi

    # Conditional Sorting
    if getargbool 0 rd.kiwi.oem.smallest_disk; then
        # If looking for smallest disk, preserve the lsblk size-sort order
        echo "${list_items}"
    else
        # Default behavior:
        # apply final alphabetical sorting for the used disk_device names
        list_items_sorted=$(sort_disk_entries "${list_items}")
        for entry in ${list_items_sorted[*]}; do
            echo -n "${entry} $(find_disk_entry "${list_items}" "${entry}") "
        done
        echo
    fi
}


function validate_disk_selection {
    local selected=$1
    local disk_list
    local entry
    local count=0
    disk_list=$(get_disk_list)
    for entry in ${disk_list};do
        if [ $((count % 2)) -eq 0 ];then
            if [ ! "${entry}" = "${selected}" ];then
                # check system_identifier for the not selected disk
                # if one of them matches the system_identifier because
                # that would produce a global system inconsistency
                if disk_matches_system_identifier "${entry}";then
                    report_and_quit "Disk ${entry} has the same partition UUID"
                fi
            fi
        fi
        count=$((count + 1))
    done
}

function get_selected_disk {
    declare kiwi_oemunattended=${kiwi_oemunattended}
    declare kiwi_oemunattended_id=${kiwi_oemunattended_id}
    local disk_list
    local device_array
    kiwi_oemunattended=$(bool "${kiwi_oemunattended}")
    disk_list=$(get_disk_list)
    if [ -n "${disk_list}" ];then
        local count=0
        local device_index=0
        for entry in ${disk_list};do
            if [ $((count % 2)) -eq 0 ];then
                device_array[${device_index}]=${entry}
                device_index=$((device_index + 1))
            fi
            count=$((count + 1))
        done
        if [ "${device_index}" -eq 1 ];then
            # one single disk device found, use it
            echo "${device_array[0]}"
        elif [ "${kiwi_oemunattended}" = "true" ];then
            if [ -z "${kiwi_oemunattended_id}" ];then
                # unattended mode requested but no target specifier,
                # thus use first device from list
                echo "${device_array[0]}"
            else
                # unattended mode requested with target specifier
                # use this device if present
                local device
                for device in "${device_array[@]}"; do
                    if [[ ${device} =~ ${kiwi_oemunattended_id} ]];then
                        echo "${device}"
                        return
                    fi
                done
            fi
        else
            # manually select from storage list
            if ! run_dialog \
                --menu "\"Select Installation Disk\"" 20 75 15 "${disk_list}"
            then
                report_and_quit "System installation canceled"
            fi
            get_dialog_result
        fi
    fi
}

function export_image_metadata {
    local image_source_files=$1
    export checksum
    export blocks
    export blocksize
    export zblocks
    export zblocksize
    local meta_file
    meta_file="$(echo "${image_source_files}" | cut -f2 -d\|)"
    if ! read -r checksum blocks blocksize zblocks zblocksize < "${meta_file}"
    then
        report_and_quit "Reading ${meta_file} failed"
    fi
    echo "Image checksum: ${checksum}"
    echo "Image blocks: ${blocks} / blocksize: ${blocksize}"
    if [ -n "${zblocks}" ];then
        echo "Image compressed blocks: ${zblocks} / blocksize: ${zblocksize}"
    fi
}

function check_image_fits_target {
    local image_target=$1
    local need_mbytes
    local have_mbytes
    need_mbytes=$((blocks * blocksize / 1048576))
    have_mbytes=$(($(get_block_device_kbsize "${image_target}") / 1024))
    echo "Have size: ${image_target} -> ${have_mbytes} MB"
    echo "Need size: ${image_source} -> ${need_mbytes} MB"
    if [ ${need_mbytes} -gt ${have_mbytes} ];then
        report_and_quit "Not enough space available for this image"
    fi
}

function check_image_matches_target_blocksize {
    declare kiwi_target_blocksize=${kiwi_target_blocksize}
    local image_blocksize=${kiwi_target_blocksize}
    local target_node
    local target_blocksize
    local message
    target_node="${1}"
    if [ -L "${target_node}" ];then
        target_node="$(readlink "${target_node}")"
    fi
    target_node=$(basename "${target_node}")
    target_blocksize="/sys/block/${target_node}/queue/logical_block_size"
    mountpoint -q /sys || mount -t sysfs sysfs /sys
    if [ -n "${image_blocksize}" ] && [ -e "${target_blocksize}" ];then
        read -r target_blocksize < "${target_blocksize}"
        if [ ! "${target_blocksize}" = "${image_blocksize}" ];then
            message="Target blocksize(${target_blocksize}b) doesn't match"
            message="${message} image blocksize(${image_blocksize}b)"
            report_and_quit "${message}"
        fi
    fi
}

function dump_image {
    declare kiwi_oemsilentinstall=${kiwi_oemsilentinstall}
    declare kiwi_oemunattended=${kiwi_oemunattended}
    local image_source_files=$1
    local image_target=$2
    local image_from_remote=$3
    local image_source
    local image_basename
    kiwi_oemsilentinstall=$(bool "${kiwi_oemsilentinstall}")
    kiwi_oemunattended=$(bool "${kiwi_oemunattended}")
    image_source="$(echo "${image_source_files}" | cut -f1 -d\|)"
    image_basename=$(basename "${image_source}")
    local progress=/dev/install_progress
    local image_source_file=/image.raw
    local load_text="Loading ${image_basename}..."
    local title_text="Installation..."
    local dump
    local copy
    local parttable
    local count_32k
    local image_size
    local count=0
    local block_size=32k
    local retries
    local dump_retries_count
    local progress_fifo

    # can we dump this
    check_image_fits_target "${image_target}"
    check_image_matches_target_blocksize "${image_target}"

    # select dump method
    if [ -n "${image_from_remote}" ];then
        if getargbool 0 rd.kiwi.install.partition_based; then
            copy=dump_remote_image
            dump=dump_local_image_partition_based
        else
            dump=dump_remote_image
        fi
    else
        if getargbool 0 rd.kiwi.install.partition_based; then
            if getargbool 0 rd.kiwi.install.clone_local; then
                copy=dump_local_image
            fi
            dump=dump_local_image_partition_based
        else
            dump=dump_local_image
        fi
    fi

    # preserve pre-dump partition table
    if getargbool 0 rd.kiwi.install.retain_past; then
        fetch_local_partition_table "${image_target}" /tmp/parttable_pre
    fi

    # setup blocks and blocksize to retain last
    if getargbool 0 rd.kiwi.install.retain_last || \
       getargbool 0 rd.kiwi.install.retain_past
    then
        if [ -n "${image_from_remote}" ];then
            image_size=$((blocks * blocksize))
            parttable=$(
                fetch_remote_partition_table "${image_source}" "${image_size}"
            )
        else
            parttable=$(
                fetch_local_partition_table "${image_source}"
            )
        fi
        if compatible_to_retain "${parttable}" "${image_target}"; then
            if getargbool 0 rd.kiwi.install.retain_last; then
                count=$(get_disk_offset_retain_last_partition "${parttable}")
            else
                # retain_past always dumps the complete image
                # the compatible_to_retain check for this image blob
                # has been done and the deployment can happen for
                # all blocks
                count=0
            fi
        fi
        if [ "${count}" -gt 0 ];then
            block_size=$(get_sector_size_from_table_dump "${parttable}")
            count_32k=$(
                optimize_count_for_32k_blocksize "${block_size}" "${count}"
            )
            if [ ! "${count}" = "${count_32k}" ];then
                count="${count_32k}"
                block_size=32k
            fi
        fi
    fi

    # ddrescue is used for local dumps only
    if [ "${dump}" = "dump_local_image" ] || \
        [ "${copy}" = "dump_local_image" ]
    then
        check_ddrescue_available
    fi

    # deploy
    echo "${load_text} [${image_target}]..."
    retries=$(dump_retries)
    # The partition based dump changes the source and target
    # filesystems through the btrfs seed/sprout process, it can
    # not be repeated after a failure
    dump_retries_count="${retries}"
    if [ "${dump}" = "dump_local_image_partition_based" ];then
        dump_retries_count=0
    fi
    # ddrescue keeps the state of a dump in a mapfile, a new
    # installation must not continue from a former state
    rm -f \
        "$(ddrescue_mapfile "${image_source_file}")" \
        "$(ddrescue_mapfile "${image_target}")"
    # The progress of a dump is shown by a gauge dialog, which
    # requires pv. ddrescue reports its status in a format the
    # gauge can not show, a local dump with ddrescue therefore
    # blocks the console like a silent installation
    unset progress_fifo
    if with_progress && [ "${kiwi_oemsilentinstall}" = "false" ]; then
        if ! with_ddrescue || [ -n "${image_from_remote}" ];then
            progress_fifo="${progress}"
        fi
    fi
    # The copy only writes to main memory, it runs prior to the
    # last chance to stop us, such that the partition table of a
    # remote image can be checked against the target beforehand
    if [ -n "${copy}" ];then
        if ! run_dump \
            "${load_text}" "${title_text}" "${retries}" "${progress_fifo}" \
            "${copy}" \
            "${image_source}" \
            "${image_source_file}" \
            "${count}" \
            "${block_size}"
        then
            show_log_and_quit \
                "Failed to copy image ${image_source} to ${image_source_file} after $((retries + 1)) attempts" \
                "$(dump_log)"
        fi
        image_source="${image_source_file}"
    fi

    # check if the image partitions can be installed
    if [ "${dump}" = "dump_local_image_partition_based" ];then
        check_partition_based_target "${image_source}" "${image_target}"
    fi

    # last chance to stop us
    if [ "${kiwi_oemunattended}" = "false" ];then
        local ack_dump_text="Destroying ALL data on ${image_target}, continue ?"
        if [ "${dump}" = "dump_local_image_partition_based" ] && \
            [ -e "$(target_partition_table)" ]
        then
            ack_dump_text="Destroying ALL data on partitions"
            ack_dump_text="${ack_dump_text} $(
                get_partition_ids "$(image_partition_table)" | tr '\n' ' '
            )of ${image_target}, continue ?"
        fi
        if ! run_dialog --yesno "\"${ack_dump_text}\"" 7 80; then
            local install_cancel_text="System installation canceled"
            report_and_quit "${install_cancel_text}"
        fi
    fi

    if ! run_dump \
        "${load_text}" "${title_text}" "${dump_retries_count}" \
        "${progress_fifo}" \
        "${dump}" \
        "${image_source}" \
        "${image_target}" \
        "${count}" \
        "${block_size}"
    then
        show_log_and_quit \
            "Failed to install image ${image_source} to ${image_target} after $((dump_retries_count + 1)) attempts" \
            "$(dump_log)"
    fi

    # grow filesystems installed into bigger partitions
    if [ "${dump}" = "dump_local_image_partition_based" ];then
        grow_partition_based_filesystems "${image_target}"
    fi

    # recreate last partition from pre-dump table
    if getargbool 0 rd.kiwi.install.retain_past && \
        [ ! -e /tmp/retain_not_applicable ]
    then
        recreate_last_partition "${image_target}"
    fi

    # update EFI boot entry for the installed system
    remove_efi_boot_entry
    add_efi_boot_entry "${image_target}"
}

function efi_boot_manager_available {
    # """
    # check if EFI boot entries can be managed on this system
    # """
    if [ ! -d /sys/firmware/efi ];then
        warn "System not booted in EFI mode, skipping EFI boot entry setup"
        return 1
    fi
    if ! command -v efibootmgr &>/dev/null;then
        warn "efibootmgr not found, skipping EFI boot entry setup"
        return 1
    fi
    return 0
}

function get_esp_partition {
    # """
    # lookup the EFI system partition on the given disk
    # by its filesystem label EFI
    # """
    local disk_device=$1
    udev_pending
    lsblk -p -n -r -o NAME,LABEL "${disk_device}" |\
        awk '$2 == "EFI" { print $1; exit }'
}

function get_partition_number {
    # """
    # get the partition number of the given partition device
    # """
    local partition_device=$1
    local partition_node
    local partition_number
    partition_node=$(readlink -f "${partition_device}")
    partition_node=${partition_node##*/}
    if [ -e "/sys/class/block/${partition_node}/partition" ];then
        read -r partition_number \
            < "/sys/class/block/${partition_node}/partition"
    elif [[ "${partition_device}" =~ ([0-9]+)$ ]];then
        # e.g. device mapper partitions created by kpartx
        partition_number=${BASH_REMATCH[1]}
    fi
    echo "${partition_number}"
}

function find_efi_binary {
    # """
    # print the first EFI binary found in the given directories.
    # The name patterns are tried in the given order, each one
    # across all directories before the next pattern is tried
    # """
    local patterns
    local pattern
    local efi_dir
    local candidate
    local candidate_name
    read -r -a patterns <<< "$1"
    shift
    for pattern in "${patterns[@]}";do
        for efi_dir in "$@";do
            # shellcheck disable=SC2231
            for candidate in "${efi_dir}"/${pattern};do
                [ -f "${candidate}" ] || continue
                candidate_name=${candidate##*/}
                # skip MokManager and fallback helpers shipped next to shim
                case "${candidate_name,,}" in
                    mm*|fb*|mokmanager*|fallback*) continue ;;
                esac
                echo "${candidate}"
                return 0
            done
        done
    done
    return 1
}

function get_efi_loader_path {
    # """
    # mount the given ESP read-only and search for an EFI binary.
    # Any directory below EFI except BOOT is a vendor directory
    # and searched first. The EFI/BOOT removable media path is
    # searched last. In both cases shim is preferred over any
    # other loader. The result is printed in EFI path notation,
    # e.g \EFI\opensuse\shim.efi
    # """
    local esp_device=$1
    local esp_mount=/run/kiwi-esp
    local efi_dir
    local efi_dir_name
    local vendor_dirs=()
    local boot_dirs=()
    local loader
    mkdir -p "${esp_mount}"
    if ! mount -o ro "${esp_device}" "${esp_mount}";then
        warn "Failed to mount ESP ${esp_device}"
        rmdir "${esp_mount}"
        return 1
    fi
    # FAT is case insensitive, match the same way
    shopt -s nullglob nocaseglob
    for efi_dir in "${esp_mount}"/[Ee][Ff][Ii]/*/;do
        efi_dir=${efi_dir%/}
        efi_dir_name=${efi_dir##*/}
        if [ "${efi_dir_name,,}" = "boot" ];then
            boot_dirs+=("${efi_dir}")
        else
            vendor_dirs+=("${efi_dir}")
        fi
    done
    if [ ${#vendor_dirs[@]} -gt 0 ];then
        loader=$(
            find_efi_binary "shim*.efi grub*.efi *.efi" "${vendor_dirs[@]}"
        )
    fi
    if [ -z "${loader}" ] && [ ${#boot_dirs[@]} -gt 0 ];then
        loader=$(
            find_efi_binary "shim*.efi boot*.efi *.efi" "${boot_dirs[@]}"
        )
    fi
    shopt -u nullglob nocaseglob
    umount "${esp_mount}"
    rmdir "${esp_mount}"
    if [ -z "${loader}" ];then
        warn "No EFI binary found on ESP ${esp_device}"
        return 1
    fi
    loader=${loader#"${esp_mount}"}
    echo "${loader//\//\\}"
}

function remove_efi_boot_entry {
    # """
    # delete all EFI boot entries labeled with the name given
    # in rd.kiwi.install.efi_display_label
    # """
    local label
    local line
    local bootnum
    local bootnums
    local entry_regex='^Boot([0-9A-Fa-f]{4})[* ] (.*)$'
    label=$(getarg rd.kiwi.install.efi_display_label=)
    if [ -z "${label}" ] || ! efi_boot_manager_available;then
        return
    fi
    while read -r line;do
        if [[ "${line}" =~ ${entry_regex} ]];then
            # newer efibootmgr versions append the device path
            # to the label separated by a tab
            if [ "${BASH_REMATCH[2]%%$'\t'*}" = "${label}" ];then
                bootnums="${bootnums} ${BASH_REMATCH[1]}"
            fi
        fi
    done < <(efibootmgr)
    for bootnum in ${bootnums};do
        info "Removing EFI boot entry Boot${bootnum} (${label})"
        if ! efibootmgr --quiet --bootnum "${bootnum}" --delete-bootnum;then
            warn "Failed to remove EFI boot entry Boot${bootnum}"
        fi
    done
}

function add_efi_boot_entry {
    # """
    # create an EFI boot entry labeled with the name given in
    # rd.kiwi.install.efi_display_label for the ESP on the
    # given disk
    # """
    local disk_device=$1
    local label
    local esp_device
    local esp_partnum
    local loader
    label=$(getarg rd.kiwi.install.efi_display_label=)
    if [ -z "${label}" ] || ! efi_boot_manager_available;then
        return
    fi
    esp_device=$(get_esp_partition "${disk_device}")
    if [ -z "${esp_device}" ];then
        warn "No partition labeled EFI found on ${disk_device}"
        return
    fi
    esp_partnum=$(get_partition_number "${esp_device}")
    if [ -z "${esp_partnum}" ];then
        warn "Failed to get partition number of ESP ${esp_device}"
        return
    fi
    if ! loader=$(get_efi_loader_path "${esp_device}");then
        return
    fi
    info "Adding EFI boot entry ${label}: ${loader} on ${esp_device}"
    if ! efibootmgr --quiet --create \
        --disk "$(readlink -f "${disk_device}")" --part "${esp_partnum}" \
        --label "${label}" --loader "${loader}"
    then
        warn "Failed to add EFI boot entry ${label}"
    fi
}

function with_progress {
    if getargbool 0 rd.debug || ! command -v pv &>/dev/null; then
        return 1
    fi
    return 0
}

function with_ddrescue {
    # """
    # check if a local image is dumped with ddrescue. ddrescue
    # retries unreadable sectors of the source and records the state
    # of each block in a mapfile, which tells if the copy is complete.
    # ddrescue is only used if requested with rd.kiwi.install.dump_rescue
    # and if the tools are present in the initrd. They are optional
    # and only present if the image provides them, e.g. through the
    # gnu_ddrescue package, see check_ddrescue_available
    # """
    getargbool 0 rd.kiwi.install.dump_rescue && ddrescue_available
}

function ddrescue_available {
    command -v ddrescue &>/dev/null && command -v ddrescuelog &>/dev/null
}

function check_ddrescue_available {
    # """
    # stop the installation if rd.kiwi.install.dump_rescue requests
    # ddrescue but the initrd does not provide it. The check runs
    # before the target disk is changed
    # """
    if getargbool 0 rd.kiwi.install.dump_rescue && ! ddrescue_available;then
        report_and_quit \
            "rd.kiwi.install.dump_rescue is set, but ddrescue or ddrescuelog is missing in the initrd"
    fi
}

function dump_retries {
    # """
    # print the number of retries of a failed dump, set with
    # rd.kiwi.install.dump_retries=<number>, 2 by default
    # """
    local retries
    retries=$(getarg rd.kiwi.install.dump_retries=)
    if [[ "${retries}" =~ ^[0-9]+$ ]];then
        echo "${retries}"
    else
        echo 2
    fi
}

function dump_log {
    # """
    # print the log file which collects the error output of a dump
    # """
    echo /tmp/dump.log
}

function block_size_bytes {
    # """
    # print the given dd block size in bytes, the dump uses
    # either 32k or a sector size in bytes
    # """
    local block_size=$1
    if [ "${block_size}" = "32k" ];then
        echo 32768
    else
        echo "${block_size}"
    fi
}

function ddrescue_mapfile {
    # """
    # print the ddrescue mapfile for the given dump target
    # """
    local image_target=$1
    echo "/tmp/dump.$(basename "${image_target}").map"
}

function progress_filter {
    # """
    # pass the progress numbers of pv -n read from stdin to stdout
    # and append all other lines, the error messages of pv, to the
    # given log file
    # """
    local log_file=$1
    local line
    while IFS= read -r line; do
        if [[ "${line}" =~ ^[0-9]+$ ]];then
            echo "${line}"
        else
            echo "${line}" >> "${log_file}"
        fi
    done
}

function run_dump {
    # """
    # run the given dump command with its arguments and retry it
    # if it fails, up to the given number of retries. With a
    # progress fifo, the command runs in the background with a
    # gauge dialog showing its progress, and the fifo is passed
    # as last argument. The error output of each attempt is
    # collected in the dump log
    # """
    local text=$1
    local title=$2
    local retries=$3
    local progress=$4
    shift 4
    local attempt=0
    local dump_pid
    while true; do
        : > "$(dump_log)"
        if [ -n "${progress}" ];then
            setup_progress_fifo "${progress}"
            (
                # The gauge dialog reads the fifo until all writers
                # closed it. If the command failed before it opened
                # the fifo, the dialog would wait forever. The fifo
                # is therefore kept open for writing until the
                # command finished. Opening it blocks until the
                # dialog opened it for reading
                exec 3>"${progress}"
                "$@" "${progress}"
                result=$?
                exec 3>&-
                exit "${result}"
            ) &
            dump_pid=$!
            run_progress_dialog "${text}" "${title}"
            if wait "${dump_pid}";then
                return 0
            fi
        elif "$@";then
            return 0
        fi
        if [ "${attempt}" -ge "${retries}" ];then
            return 1
        fi
        attempt=$((attempt + 1))
        warn "${text} failed, retry ${attempt} of ${retries}..."
        sleep 5
    done
}

function fetch_local_partition_table {
    local image_source=$1
    local parttable=$2
    if [ -z "${parttable}" ];then
        parttable=/tmp/parttable
    fi
    sfdisk -d "${image_source}" > "${parttable}" 2>/dev/null
    echo "${parttable}"
}

function recreate_last_partition {
    # recreate last partition as it existed prior dump
    local image_target=$1
    local table_type
    table_type=$(get_partition_table_type "${image_target}")
    if [ "${table_type}" = "gpt" ];then
        relocate_gpt_at_end_of_disk "${image_target}"
    fi
    # parttable after image dump, the OS
    sfdisk -d "${image_target}" > /tmp/parttable_1 2>/dev/null
    # last partition of table as it existed prior dump
    tail -n 1 /tmp/parttable_pre > /tmp/parttable_2
    # combine table snippets. Please note there can now be a gap
    # between the end of the OS table and the start of the last
    # partition of the table prior dump. Please also note, if the
    # table prior dump had more partitions than only the last
    # one to retain, this table concat will not retain those.
    # and the OS dump might have overwritten them. A more
    # sophisticated concat procedure would be needed to support
    # this case here in this code and also in the
    # compatible_to_retain() method
    cat /tmp/parttable_1 /tmp/parttable_2 > /tmp/parttable
    set_device_lock "${image_target}" \
        sfdisk -f "${image_target}" < /tmp/parttable
}

function fetch_remote_partition_table {
    local image_source=$1
    local image_size=$2
    local parttable=/tmp/parttable
    dd if=/dev/zero of=/tmp/table bs=1 count=0 seek="${image_size}" &>/dev/null
    fetch_file "${image_source}" 2>/dev/null | dd of=/tmp/table bs=512 count=1 conv=notrunc &>/dev/null
    sfdisk -d /tmp/table > "${parttable}" 2>/dev/null
    echo "${parttable}"
}

function get_sector_size_from_table_dump {
    local parttable=$1
    sector_size=$(grep sector-size: "${parttable}" | cut -f2 -d:)
    echo "${sector_size}"
}

function compatible_to_retain {
    local parttable=$1
    local image_target=$2
    local source_start
    local target_start
    source_start=$(
        tail -n 1 "${parttable}" | cut -f2 -d= | cut -f1 -d,
    )
    target_start=$(
        sfdisk -d "${image_target}" 2>/dev/null |\
        tail -n 1 | cut -f2 -d= | cut -f1 -d,
    )
    if [ -z "${source_start}" ] || [ -z "${target_start}" ];then
        # no partition information for either source or target
        # broken or net new deployment on empty disk
        touch /tmp/retain_not_applicable
        return 1
    fi
    if getargbool 0 rd.kiwi.install.retain_last; then
        if [ ! "${source_start}" = "${target_start}" ];then
            report_and_quit "Cannot retain partition, start address mismatch"
        fi
    elif getargbool 0 rd.kiwi.install.retain_past; then
        if [ "${source_start}" -gt "${target_start}" ];then
            report_and_quit "Cannot retain partition, image overlaps"
        fi
    fi
    return 0
}

function get_disk_offset_retain_last_partition {
    local parttable=$1
    local next_to_last
    local start
    local size
    local offset
    next_to_last=$(tail -n 2 "${parttable}" | head -n 1)
    if [ -n "${next_to_last}" ];then
        start=$(echo "${next_to_last}" | cut -f2 -d= | cut -f1 -d,)
        size=$(echo "${next_to_last}" | cut -f3 -d= | cut -f1 -d,)
        offset=$((start + size))
        echo "${offset}"
    else
        echo 0
    fi
}

function optimize_count_for_32k_blocksize {
    local block_size=$1
    local count=$2
    local dump_bytes
    dump_bytes=$((block_size * count))
    if [ $((dump_bytes % 32768)) -eq 0 ];then
        # dump_bytes is a multiple of 32k, use it for better I/O performance
        count=$((dump_bytes / 32768))
    fi
    echo "${count}"
}

function dump_local_image {
    # """
    # dump the local image source to the target. A read error on
    # the source or a write error on the target fails the dump, the
    # error messages are appended to the dump log
    # """
    local image_source=$1
    local image_target=$2
    local count=$3
    local block_size=$4
    local progress=$5
    local dump_log
    dump_log=$(dump_log)
    if with_ddrescue;then
        dump_local_image_ddrescue \
            "${image_source}" "${image_target}" "${count}" "${block_size}"
        return
    fi
    if [ "${count}" -gt 0 ];then
        count="count=${count}"
    else
        unset count
    fi
    # The dump log is only appended to, never read in the pipe (SC2094)
    # shellcheck disable=SC2086,SC2094
    if [ -e "${progress}" ];then
        (
            # Without pipefail a read error of pv would end the
            # pipe like the regular end of the image, and dd would
            # report success for the truncated dump
            set -o pipefail
            pv -n "${image_source}" 2> >(progress_filter "${dump_log}" >&2) |\
            dd bs="${block_size}" ${count} of="${image_target}" \
                2>>"${dump_log}" >/dev/null
        ) 2>"${progress}"
    else
        dd \
            if="${image_source}" bs="${block_size}" ${count} \
            of="${image_target}" 2>>"${dump_log}" >/dev/null
    fi
}

function dump_local_image_ddrescue {
    # """
    # dump the local image source to the target with ddrescue, which
    # retries unreadable sectors up to five times and gives up if no
    # read succeeded for one minute. ddrescue does not fail for
    # sectors it could not read, it leaves them unwritten. The dump
    # is therefore only complete if the mapfile reports all blocks
    # as done. The mapfile is kept across retries of the dump, such
    # that a retry continues with the blocks not yet read
    # """
    local image_source=$1
    local image_target=$2
    local count=$3
    local block_size=$4
    local mapfile
    local size_option
    local dump_log
    dump_log=$(dump_log)
    mapfile=$(ddrescue_mapfile "${image_target}")
    if [ "${count}" -gt 0 ];then
        size_option="--size=$((count * $(block_size_bytes "${block_size}")))"
    fi
    # ddrescue writes its status display to stdout, which is not
    # suitable for the dump log, and errors to stderr
    # shellcheck disable=SC2086
    if ! ddrescue \
        --force --retry-passes=5 --timeout=1m --cluster-size=32768 \
        ${size_option} "${image_source}" "${image_target}" "${mapfile}" \
        2>>"${dump_log}" >/dev/null
    then
        return 1
    fi
    if ! ddrescuelog --done-status "${mapfile}" 2>>"${dump_log}";then
        {
            echo "Not all blocks of ${image_source} could be read:"
            ddrescuelog --show-status "${mapfile}"
        } >>"${dump_log}" 2>&1
        return 1
    fi
}

function image_partition_table {
    # """
    # print the sfdisk dump file of the image partition table,
    # written by check_partition_based_target
    # """
    echo /tmp/parttable_image
}

function target_partition_table {
    # """
    # print the sfdisk dump file of the partition table which
    # existed on the target prior the installation. The file only
    # exists if the target has a partition table, written by
    # check_partition_based_target
    # """
    echo /tmp/parttable_target
}

function get_partition_entry {
    # """
    # print number, start and size of the given partition from
    # the given sfdisk dump, followed by its attributes, e.g.
    # ", type=83, bootable". Returns 1 if there is no such
    # partition. Without a partition number, all partitions are
    # printed, one per line. Extended partitions of an msdos
    # table are only containers of the logical partitions, which
    # are listed on their own. They hold no data and are skipped
    # """
    local parttable=$1
    local partid=$2
    local line
    local number
    local start
    local size
    local attributes
    local found=1
    local entry='^.*[^0-9]([0-9]+)[[:space:]]*:[[:space:]]*'
    entry="${entry}start=[[:space:]]*([0-9]+),[[:space:]]*"
    entry="${entry}size=[[:space:]]*([0-9]+)(.*)$"
    local extended='type=(5|f|85)(,|$)'
    while IFS= read -r line;do
        if [[ "${line}" =~ ${entry} ]];then
            number=${BASH_REMATCH[1]}
            start=${BASH_REMATCH[2]}
            size=${BASH_REMATCH[3]}
            attributes=${BASH_REMATCH[4]}
            if [[ "${attributes}" =~ ${extended} ]];then
                continue
            fi
            if [ -z "${partid}" ] || [ "${number}" = "${partid}" ];then
                echo "${number} ${start} ${size}${attributes}"
                found=0
            fi
        fi
    done < "${parttable}"
    return "${found}"
}

function get_partition_ids {
    # """
    # print the numbers of all data partitions of the given sfdisk dump
    # """
    local parttable=$1
    local partid
    local rest
    while read -r partid rest;do
        echo "${partid}"
    done < <(get_partition_entry "${parttable}")
}

function get_last_partition_id_from_table_dump {
    # """
    # print the highest partition number of the given sfdisk dump
    # """
    local parttable=$1
    local partid
    local last=0
    for partid in $(get_partition_ids "${parttable}");do
        if [ "${partid}" -gt "${last}" ];then
            last=${partid}
        fi
    done
    echo "${last}"
}

function get_first_partition_start_from_table_dump {
    # """
    # print the lowest start sector of all partitions of the given
    # sfdisk dump, including the extended partition of msdos tables
    # """
    local parttable=$1
    local line
    local start
    local first=
    while IFS= read -r line;do
        if [[ "${line}" =~ :[[:space:]]*start=[[:space:]]*([0-9]+), ]];then
            start=${BASH_REMATCH[1]}
            if [ -z "${first}" ] || [ "${start}" -lt "${first}" ];then
                first=${start}
            fi
        fi
    done < "${parttable}"
    echo "${first}"
}

function get_table_value_from_table_dump {
    # """
    # print the value of the given header key of the given sfdisk
    # dump, e.g. label or label-id
    # """
    local parttable=$1
    local key=$2
    local line
    while IFS= read -r line;do
        if [[ "${line}" =~ ^${key}:[[:space:]]*(.*)$ ]];then
            echo "${BASH_REMATCH[1]}"
            return
        fi
    done < "${parttable}"
}

function get_partition_bytes {
    # """
    # print the size in bytes of the given partition entry as
    # printed by get_partition_entry
    # """
    local entry=$1
    local sector_size=$2
    local partid
    local start
    local size
    read -r partid start size <<< "${entry}"
    size=${size%%,*}
    echo $((size * sector_size))
}

function get_partition_start_bytes {
    # """
    # print the start in bytes of the given partition entry as
    # printed by get_partition_entry
    # """
    local entry=$1
    local sector_size=$2
    local partid
    local start
    read -r partid start _ <<< "${entry}"
    echo $((start * sector_size))
}

function merge_partition_table {
    # """
    # print the partition table of the target with the attributes
    # of the image partitions applied to the target partitions of
    # the same number, e.g. type, uuid, name and the bootable flag.
    # The geometry of the target partitions is kept. The label-id
    # of the image is applied too, such that the partition UUIDs
    # of the installed system match with the ones of the image,
    # as it is the case if the image partition table gets cloned.
    # This is required e.g. for root=PARTUUID or for the check of
    # oem-resize-once on first boot
    # """
    local image_table=$1
    local target_table=$2
    local line
    local label_id
    local node
    local partid
    local start
    local size
    local image_entry
    local image_attributes
    local entry='^(.*[^0-9])([0-9]+)[[:space:]]*:[[:space:]]*'
    entry="${entry}start=[[:space:]]*([0-9]+),[[:space:]]*"
    entry="${entry}size=[[:space:]]*([0-9]+)"
    label_id=$(get_table_value_from_table_dump "${image_table}" label-id)
    while IFS= read -r line;do
        if [[ "${line}" =~ ^label-id: ]] && [ -n "${label_id}" ];then
            echo "label-id: ${label_id}"
            continue
        fi
        if [[ "${line}" =~ ${entry} ]];then
            node="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
            partid=${BASH_REMATCH[2]}
            start=${BASH_REMATCH[3]}
            size=${BASH_REMATCH[4]}
            if image_entry=$(get_partition_entry "${image_table}" "${partid}")
            then
                image_attributes=${image_entry#* * *,}
                echo "${node} : start=${start}, size=${size},${image_attributes}"
                continue
            fi
        fi
        echo "${line}"
    done < "${target_table}"
}

function dump_boot_code {
    # """
    # dump the boot code of the image to the target, which is
    # the MBR boot code in front of the partition table and for
    # msdos tables the area between the MBR and the first
    # partition. On msdos tables the boot loader embeds its core
    # image into this area, which is loaded by the MBR boot code.
    # On GPT tables this area holds the partition table itself
    # and the boot loader uses a BIOS boot partition instead,
    # which is installed like any other partition. The partition
    # table of the target is not changed
    # """
    local image_source=$1
    local image_target=$2
    local image_table
    local sector_size
    local first_start
    image_table=$(image_partition_table)
    # MBR boot code
    dd if="${image_source}" of="${image_target}" \
        bs=446 count=1 conv=notrunc || return 1
    # boot loader embedding area
    if [ "$(get_table_value_from_table_dump "${image_table}" label)" = "dos" ]
    then
        sector_size=$(get_sector_size_from_table_dump "${image_table}")
        first_start=$(get_first_partition_start_from_table_dump "${image_table}")
        if [ -n "${first_start}" ] && [ "${first_start}" -gt 1 ];then
            dd if="${image_source}" of="${image_target}" \
                bs="${sector_size// /}" skip=1 seek=1 \
                count=$((first_start - 1)) conv=notrunc || return 1
        fi
    fi
}

function clone_partition_table {
    # """
    # clone the partition table and the boot code of the image
    # to the target, used if the target has no partition table
    # """
    local image_source=$1
    local image_target=$2
    sfdisk "${image_target}" < "$(image_partition_table)" || return 1
    dump_boot_code "${image_source}" "${image_target}" || return 1
    partx -u "${image_target}" || return 1
    udev_pending
}

function update_partition_table {
    # """
    # apply the attributes of the image partitions to the existing
    # partition table of the target and dump the boot code of the
    # image, used if the target has a partition table
    # """
    local image_source=$1
    local image_target=$2
    local merged_table=/tmp/parttable_merged
    merge_partition_table \
        "$(image_partition_table)" "$(target_partition_table)" \
        > "${merged_table}"
    echo "Updating partition table of ${image_target}:"
    cat "${merged_table}"
    sfdisk "${image_target}" < "${merged_table}" || return 1
    dump_boot_code "${image_source}" "${image_target}" || return 1
    partx -u "${image_target}" || return 1
    udev_pending
}

function check_partition_based_target {
    # """
    # read the partition table of the image and of the target.
    # If the target has no partition table, the one of the image
    # is cloned to the target. Otherwise the image partitions are
    # installed into the existing partitions of the same number.
    # This is only possible if the table types match, if there is
    # a target partition for each image partition which is at
    # least as big as the image partition and if the boot code
    # fits in front of the first target partition. If not, the
    # installation stops before anything is written to the target
    # """
    local image_source=$1
    local image_target=$2
    local image_table
    local target_table
    local check_log=/tmp/partition_check.log
    local image_label
    local target_label
    local image_sector_size
    local target_sector_size
    local image_entry
    local target_entry
    local image_bytes
    local target_bytes
    local image_first_start
    local target_first_start
    local partid
    local failed=0
    image_table=$(image_partition_table)
    target_table=$(target_partition_table)
    rm -f "${image_table}" "${target_table}"
    : > "${check_log}"
    if ! sfdisk -d "${image_source}" > "${image_table}" 2>>"${check_log}"
    then
        show_log_and_quit \
            "Failed to read partition table of ${image_source}" "${check_log}"
    fi
    if ! sfdisk -d "${image_target}" > "${target_table}" 2>/dev/null;then
        rm -f "${target_table}"
        if [ -n "$(blkid -p -s PTTYPE -o value "${image_target}")" ];then
            report_and_quit \
                "Partition table of ${image_target} exists but can't be read"
        fi
        echo "No partition table on ${image_target}, cloning the image table"
        return
    fi
    echo "Partition table on ${image_target}, installing into its partitions"
    image_label=$(get_table_value_from_table_dump "${image_table}" label)
    target_label=$(get_table_value_from_table_dump "${target_table}" label)
    if [ ! "${image_label}" = "${target_label}" ];then
        report_and_quit \
            "Table type of image(${image_label}) and ${image_target}(${target_label}) differ"
    fi
    if [[ ! "${target_label}" =~ ^(dos|gpt)$ ]];then
        report_and_quit \
            "Table type ${target_label} of ${image_target} not supported"
    fi
    image_sector_size=$(get_sector_size_from_table_dump "${image_table}")
    target_sector_size=$(get_sector_size_from_table_dump "${target_table}")
    for partid in $(get_partition_ids "${image_table}");do
        image_entry=$(get_partition_entry "${image_table}" "${partid}")
        image_bytes=$(
            get_partition_bytes "${image_entry}" "${image_sector_size}"
        )
        if ! target_entry=$(get_partition_entry "${target_table}" "${partid}")
        then
            echo "Partition ${partid}: missing on ${image_target}," \
                "need $((image_bytes / 1048576)) MB" >> "${check_log}"
            failed=1
            continue
        fi
        target_bytes=$(
            get_partition_bytes "${target_entry}" "${target_sector_size}"
        )
        if [ "${image_bytes}" -gt "${target_bytes}" ];then
            echo "Partition ${partid}: too small on ${image_target}," \
                "need $((image_bytes / 1048576)) MB," \
                "have $((target_bytes / 1048576)) MB" >> "${check_log}"
            failed=1
            continue
        fi
        echo "Partition ${partid}: OK," \
            "need $((image_bytes / 1048576)) MB," \
            "have $((target_bytes / 1048576)) MB" >> "${check_log}"
        # The BIOS boot code of the image refers to the absolute
        # position of the BIOS boot partition in the image
        if [[ "${image_entry}" =~ type=21686148-6449-6E6F-744E-656564454649 ]]
        then
            if [ ! "$(get_partition_start_bytes "${image_entry}" "${image_sector_size}")" = \
                "$(get_partition_start_bytes "${target_entry}" "${target_sector_size}")" ]
            then
                warn "BIOS boot partition ${partid} starts at another position on ${image_target}"
                warn "Legacy BIOS boot will fail, EFI boot is not affected"
            fi
        fi
    done
    if [ "${image_label}" = "dos" ];then
        image_first_start=$(
            get_first_partition_start_from_table_dump "${image_table}"
        )
        target_first_start=$(
            get_first_partition_start_from_table_dump "${target_table}"
        )
        if [ -n "${target_first_start}" ] && \
            [ $((target_first_start * target_sector_size)) -lt \
              $((image_first_start * image_sector_size)) ]
        then
            echo "Boot code: needs the space up to sector" \
                "${image_first_start}, first partition on" \
                "${image_target} starts at sector ${target_first_start}" \
                >> "${check_log}"
            failed=1
        fi
    fi
    cat "${check_log}"
    if [ "${failed}" -ne 0 ];then
        show_log_and_quit \
            "Image partitions don't fit into partitions of ${image_target}" \
            "${check_log}"
    fi
}

function grow_filesystem {
    # """
    # grow the filesystem on the given partition to the size of
    # the partition, if the filesystem supports it. Returns 1 if
    # the resize failed, a filesystem which can't be resized is
    # skipped with a message
    # """
    local device=$1
    local mpoint=/fs-grow
    local fstype
    local uuid
    local label
    local result
    fstype=$(blkid -p -s TYPE -o value "${device}")
    case ${fstype} in
    ext2|ext3|ext4)
        e2fsck -p -f "${device}"
        result=$?
        # 1: errors corrected, 2: errors corrected, reboot required
        if [ "${result}" -gt 2 ];then
            return 1
        fi
        resize2fs -f "${device}" || return 1
    ;;
    xfs|btrfs)
        if [ "${fstype}" = "btrfs" ] && \
            btrfs inspect-internal dump-super "${device}" | grep -q SEEDING
        then
            info "${device}: btrfs seeding device is read-only, resize skipped"
            return 0
        fi
        mkdir -p "${mpoint}"
        mount "${device}" "${mpoint}" || return 1
        if [ "${fstype}" = "btrfs" ];then
            btrfs filesystem resize max "${mpoint}"
        else
            xfs_growfs "${mpoint}"
        fi
        result=$?
        umount "${mpoint}" || return 1
        return "${result}"
    ;;
    swap)
        uuid=$(blkid -p -s UUID -o value "${device}")
        label=$(blkid -p -s LABEL -o value "${device}")
        mkswap ${uuid:+-U "${uuid}"} ${label:+-L "${label}"} "${device}" \
            || return 1
    ;;
    *)
        info "${device}: resize of ${fstype:-unknown} filesystem not supported, skipped"
    ;;
    esac
}

function grow_partition_based_filesystems {
    # """
    # grow the filesystems of the image partitions which were
    # installed into bigger partitions of an existing partition
    # table to the size of the partition. The last partition of
    # the image is not resized, this is up to the kiwi resizer
    # on first boot or to any other resizer. A failed resize is
    # reported but does not stop the installation, the
    # filesystem stays usable in its original size
    # """
    local image_target=$1
    local image_table
    local target_table
    local resize_log=/tmp/fs_resize.log
    local image_sector_size
    local target_sector_size
    local image_entry
    local target_entry
    local last_partid
    local partid
    local device
    image_table=$(image_partition_table)
    target_table=$(target_partition_table)
    if [ ! -e "${target_table}" ];then
        # image partition table was cloned, partition sizes match
        return
    fi
    image_sector_size=$(get_sector_size_from_table_dump "${image_table}")
    target_sector_size=$(get_sector_size_from_table_dump "${target_table}")
    last_partid=$(get_last_partition_id_from_table_dump "${image_table}")
    for partid in $(get_partition_ids "${image_table}");do
        if [ "${partid}" = "${last_partid}" ];then
            continue
        fi
        image_entry=$(get_partition_entry "${image_table}" "${partid}")
        target_entry=$(get_partition_entry "${target_table}" "${partid}")
        if [ ! "$(get_partition_bytes "${image_entry}" "${image_sector_size}")" -lt \
            "$(get_partition_bytes "${target_entry}" "${target_sector_size}")" ]
        then
            continue
        fi
        if ! device=$(get_partition_node_name "${image_target}" "${partid}")
        then
            warn "Partition ${partid} of ${image_target} not found, resize skipped"
            continue
        fi
        info "Resizing filesystem on ${device} to the partition size..."
        if ! grow_filesystem "${device}" >>"${resize_log}" 2>&1;then
            warn "Failed to resize filesystem on ${device}, see ${resize_log}"
        fi
    done
}

function btrfs_seed_device_on_target {
    local source_device=$1
    local target_device=$2
    local seed=/seed
    if [ -n "${source_device}" ]; then
        mkdir -p "${seed}"
        if getargbool 0 rd.kiwi.install.clone_local; then
            btrfstune -S 1 "${source_device}" || return 1
        fi
        mount "${source_device}" "${seed}" || return 1
        if ! btrfs device add "${target_device}" "${seed}"; then
            umount "${seed}"
            return 1
        fi
        umount "${seed}" || return 1
        mount "${target_device}" "${seed}" || return 1
        if ! btrfs device delete "${source_device}" "${seed}"; then
            umount "${seed}"
            return 1
        fi
        umount "${seed}" || return 1
    fi
}

function btrfs_replay_uuid {
    local target_device=$1
    local uuid=$2
    if [ -n "${uuid}" ];then
        btrfstune -f -U "${uuid}" "${target_device}"
    fi
}

function check_partition_based_compatibility {
    # partition based mode clones the complete partition table of
    # the image to a target without partition table or installs all
    # image partitions into the existing partitions of the target,
    # both would wipe out the partition to retain
    if getargbool 0 rd.kiwi.install.partition_based; then
        if getargbool 0 rd.kiwi.install.retain_last || \
           getargbool 0 rd.kiwi.install.retain_past
        then
            report_and_quit \
                "rd.kiwi.install.partition_based can't be combined with retain_last|retain_past"
        fi
    fi
}

function clean_partition_map {
    local source_disk=$1
    kpartx -d "${source_disk}" && losetup -d "${source_disk}"
}

function dump_local_image_partition_based {
    local image_source=$1
    local image_target=$2
    local count=$3
    local block_size=$4
    local progress=$5
    local source_disk
    local device_index=0
    local source_device_array
    local target_device_array
    local btrfs_source_device_array
    local btrfs_target_device_array
    local btrfs_source_uuid_array
    local filesystem
    local partid
    local source_part
    local target_part
    local dump_log
    dump_log=$(dump_log)
    # no partial dump in partition based mode
    unset count

    # Create the partition table on the target only if it has none,
    # otherwise install into the existing partitions, which were
    # checked to fit by check_partition_based_target
    if [ -e "$(target_partition_table)" ];then
        if ! update_partition_table \
            "${image_source}" "${image_target}" >>"${dump_log}" 2>&1
        then
            echo "Failed to update partition table of ${image_target}" \
                >>"${dump_log}"
            return 1
        fi
    elif ! clone_partition_table \
        "${image_source}" "${image_target}" >>"${dump_log}" 2>&1
    then
        echo "Failed to clone partition table to ${image_target}" \
            >>"${dump_log}"
        return 1
    fi

    # map source image partitions
    if ! source_disk=$(losetup --show --find "${image_source}" 2>>"${dump_log}")
    then
        echo "Failed to set up loop device for ${image_source}" \
            >>"${dump_log}"
        return 1
    fi
    if ! kpartx -a "${source_disk}" >>"${dump_log}" 2>&1;then
        echo "Failed to map partitions of ${image_source}" >>"${dump_log}"
        losetup -d "${source_disk}"
        return 1
    fi

    # walk through the image partitions and store them together
    # with the target partition of the same number. kpartx names
    # the partition maps of the loop device <loop>p<number>
    for partid in $(get_partition_ids "$(image_partition_table)");do
        source_part="/dev/mapper/$(basename "${source_disk}")p${partid}"
        if [ ! -b "${source_part}" ];then
            echo "Partition ${partid} of ${image_source} not mapped" \
                >>"${dump_log}"
            clean_partition_map "${source_disk}" &>/dev/null
            return 1
        fi
        if ! target_part=$(
            get_partition_node_name "${image_target}" "${partid}"
        );then
            echo "Partition ${partid} of ${image_target} not found" \
                >>"${dump_log}"
            clean_partition_map "${source_disk}" &>/dev/null
            return 1
        fi
        filesystem=$(blkid "${source_part}" -s TYPE -o value)
        uuid=$(blkid "${source_part}" -s UUID -o value)
        if [ "${filesystem}" = "btrfs" ];then
            btrfs_source_device_array[device_index]=${source_part}
            btrfs_source_uuid_array[device_index]=${uuid}
            btrfs_target_device_array[device_index]=${target_part}
        else
            source_device_array[device_index]=${source_part}
            target_device_array[device_index]=${target_part}
        fi
        device_index=$((device_index + 1))
    done

    # seed/sprout for btrfs based partitions
    for ((index=0; index<device_index; index++)); do
        if ! (
            btrfs_seed_device_on_target \
                "${btrfs_source_device_array[${index}]}" \
                "${btrfs_target_device_array[${index}]}"
        ) 2>>/seed.log
        then
            {
                echo "btrfs seed/sprout to" \
                    "${btrfs_target_device_array[${index}]} failed," \
                    "falling back to a block copy of the partition:"
                cat /seed.log
            } >>"${dump_log}"
            warn "btrfs seed/sprout to ${btrfs_target_device_array[${index}]} failed, copying the partition block by block"
            # The failed attempt might have left the source or the
            # target mounted, the target must not be in use for the
            # block copy
            if mountpoint -q /seed && ! umount /seed >>"${dump_log}" 2>&1
            then
                echo "Failed to unmount /seed, no block copy possible" \
                    >>"${dump_log}"
                clean_partition_map "${source_disk}" &>/dev/null
                return 1
            fi
            # A seed device is never written by btrfs, the source
            # partition is therefore still intact and gets copied
            # with the standard partitions. The block copy keeps the
            # filesystem UUID of the source, it is therefore taken
            # out of the UUID replay for the seed/sprout partitions
            source_device_array[index]=${btrfs_source_device_array[${index}]}
            target_device_array[index]=${btrfs_target_device_array[${index}]}
            unset "btrfs_source_device_array[${index}]"
            unset "btrfs_target_device_array[${index}]"
            unset "btrfs_source_uuid_array[${index}]"
        fi
    done

    # dump standard partitions...
    if [ -e "${progress}" ];then
        (
            # see dump_local_image why pipefail is required
            set -o pipefail
            for ((index=0; index<device_index; index++)); do
                if [ -n "${source_device_array[${index}]}" ];then
                    # The dump log is only appended to (SC2094)
                    # shellcheck disable=SC2094
                    if ! pv -n "${source_device_array[${index}]}" \
                        2> >(progress_filter "${dump_log}" >&2) |\
                        dd \
                        bs="${block_size}" \
                        of="${target_device_array[${index}]}" \
                        2>>"${dump_log}" >/dev/null
                    then
                        clean_partition_map "${source_disk}" &>/dev/null
                        exit 1
                    fi
                fi
            done
        ) 2>"${progress}" || return 1
    else
        for ((index=0; index<device_index; index++)); do
            if [ -n "${source_device_array[${index}]}" ];then
                if ! dd \
                    if="${source_device_array[${index}]}" bs="${block_size}" \
                    of="${target_device_array[${index}]}" \
                    2>>"${dump_log}" >/dev/null
                then
                    clean_partition_map "${source_disk}" &>/dev/null
                    return 1
                fi
            fi
        done
    fi
    clean_partition_map "${source_disk}" &>/dev/null
    for ((index=0; index<device_index; index++)); do
        if ! btrfs_replay_uuid \
            "${btrfs_target_device_array[${index}]}" \
            "${btrfs_source_uuid_array[${index}]}" >>"${dump_log}" 2>&1
        then
            echo "Failed to restore the btrfs UUID on" \
                "${btrfs_target_device_array[${index}]}" >>"${dump_log}"
            return 1
        fi
    done
}

function dump_remote_image {
    local image_source=$1
    local image_target=$2
    local count=$3
    local block_size=$4
    local progress=$5
    local image_size
    local dump_log
    local result
    dump_log=$(dump_log)
    image_size=$((blocks * blocksize))
    if [ "${count}" -gt 0 ];then
        count="count=${count}"
    else
        unset count
    fi
    # Without pipefail a failed download would end the pipe like
    # the regular end of the image, and dd would report success
    # for the truncated dump
    # shellcheck disable=SC2086
    if [ -e "${progress}" ];then
        (
            set -o pipefail
            fetch_file "${image_source}" "${image_size}" |\
                dd bs="${block_size}" ${count} of="${image_target}" \
                2>>"${dump_log}" >/dev/null
        ) 2>"${progress}"
    else
        (
            set -o pipefail
            fetch_file "${image_source}" |\
                dd bs="${block_size}" ${count} of="${image_target}" \
                2>>"${dump_log}" >/dev/null
        )
    fi
    result=$?
    if [ "${result}" -ne 0 ] && [ -s /tmp/fetch.info ];then
        cat /tmp/fetch.info >>"${dump_log}"
    fi
    return "${result}"
}

function check_image_integrity {
    declare kiwi_oemskipverify=${kiwi_oemskipverify}
    declare kiwi_oemsilentverify=${kiwi_oemsilentverify}
    local image_target=$1
    local progress=/dev/install_verify_progress
    local verify_text="Verifying ${image_target}"
    local title_text="Installation..."
    local verify_result
    local verify_pid
    local shasum
    local sha_extension
    kiwi_oemskipverify=$(bool "${kiwi_oemskipverify}")
    kiwi_oemsilentverify=$(bool "${kiwi_oemsilentverify}")
    shasum=$(shasum_tool)
    sha_extension=$(shasum_extension)
    verify_result=/dumped_image."${sha_extension}"
    if [ "${kiwi_oemskipverify}" = "true" ];then
        # no verification wanted
        return
    fi
    if getargbool 0 rd.kiwi.install.retain_last || \
       getargbool 0 rd.kiwi.install.retain_past
    then
        if [ ! -e /tmp/retain_not_applicable ];then
            # no verification possible as only a portion of
            # the image got deployed intentionally (retain_last)
            # or parts of the former partition table got
            # restored (retain_past)
            return
        fi
    fi
    if with_progress && [ "${kiwi_oemsilentverify}" = "false" ]; then
        # verify with dialog based progress information
        setup_progress_fifo ${progress}
        (
            pv --size $((blocks * blocksize)) --stop-at-size \
            -n "${image_target}" | "${shasum}" - > "${verify_result}"
        ) 2>${progress} &
        verify_pid=$!
        run_progress_dialog "${verify_text}" "${title_text}"
        # The dialog ends when pv closed the fifo, the checksum
        # might not yet be written at this point
        wait "${verify_pid}"
    else
        # verify with silently blocked console
        head --bytes=$((blocks * blocksize)) "${image_target}" |\
        "${shasum}" - > "${verify_result}"
    fi
    local checksum_dumped_image
    local checksum_fileref
    read -r checksum_dumped_image checksum_fileref < "${verify_result}"
    echo "Dumped Image checksum: ${checksum_dumped_image}/${checksum_fileref}"
    if [ "${checksum}" != "${checksum_dumped_image}" ];then
        report_and_quit "Image checksum test failed"
    fi
}

function get_isoscan_devices {
    # """
    # print the kernel names of the block device stack, e.g.
    # partition, LVM, RAID and disk, which holds the filesystem
    # with the ISO file loop mounted via iso-scan/filename
    # """
    local isoscan_device=/run/initramfs/isoscandev
    local device
    if [[ -e "${isoscan_device}" ]];then
        device=$(readlink -f "${isoscan_device}")
        lsblk -p -n -r -s -o KNAME "${device}"
    fi
}

function target_holds_isoscan_file {
    # """
    # check if the given install target disk holds the
    # ISO file loop mounted via iso-scan/filename
    # """
    local target=$1
    local target_device
    local device
    target_device=$(readlink -f "${target}")
    for device in $(get_isoscan_devices);do
        if [[ "${device}" = "${target_device}" ]];then
            return 0
        fi
    done
    return 1
}

function move_isoscan_file_to_ram {
    # """
    # The install ISO file loop mounted via iso-scan/filename is
    # stored on the install target disk. Dumping the image would
    # overwrite the ISO file while reading from it. Thus copy the
    # ISO file into main memory, release the target disk and
    # continue the installation from the copy
    # """
    declare root=${root}
    local target=$1
    local iso_device="${root#install:}"
    local isoscan_mount=/run/initramfs/isoscan
    local iso_ram_mount=/run/initramfs/isoram
    local iso_ram_file="${iso_ram_mount}/install.iso"
    local iso_file
    local iso_loop
    local iso_size_bytes
    local iso_size_kb
    local mem_available_kb
    local mem_required_kb
    # keep some main memory for the installation process
    local mem_reserve_kb=524288
    local message
    iso_file="${isoscan_mount}/$(getarg iso-scan/filename)"
    iso_loop=$(readlink -f "${iso_device}")
    if [[ ! -f "${iso_file}" ]] || [[ ! "${iso_loop}" =~ ^/dev/loop ]];then
        report_and_quit "Install ISO file not found on ${isoscan_mount}"
    fi
    iso_size_bytes=$(lsblk -n -b -d -o SIZE "${iso_loop}")
    iso_size_kb=$((iso_size_bytes / 1024 + 1024))
    mem_required_kb=$((iso_size_kb + mem_reserve_kb))
    mem_available_kb=$(awk '/^MemAvailable:/ { print $2 }' /proc/meminfo)
    if [[ "${mem_required_kb}" -gt "${mem_available_kb:-0}" ]];then
        message="Install ISO file is stored on target disk ${target}."
        message="${message} Not enough memory to copy it away, required:"
        message="${message} ${mem_required_kb}kB available:"
        message="${message} ${mem_available_kb}kB"
        report_and_quit "${message}"
    fi

    info "Install ISO file is stored on target disk ${target}"
    info "Copying ${iso_file} into main memory..."
    mkdir -p "${iso_ram_mount}"
    if ! mount -t tmpfs -o "size=${iso_size_kb}k,mode=0755" \
        tmpfs "${iso_ram_mount}"
    then
        report_and_quit "Failed to create tmpfs for install ISO copy"
    fi
    if ! cp "${iso_file}" "${iso_ram_file}";then
        report_and_quit "Failed to copy install ISO file into main memory"
    fi

    # release the target disk
    udev_pending
    if ! losetup -d "${iso_loop}";then
        report_and_quit "Failed to detach install ISO loop ${iso_loop}"
    fi
    udev_pending
    if ! umount "${isoscan_mount}";then
        report_and_quit "Failed to release ${isoscan_mount} on ${target}"
    fi
    rm -f /run/initramfs/isoscandev

    # attach the ISO copy, udev recreates the install media label link
    if ! losetup -f -r "${iso_ram_file}";then
        report_and_quit "Failed to attach install ISO copy ${iso_ram_file}"
    fi
    udev_pending
    if [[ ! -e "${iso_device}" ]];then
        report_and_quit "Install ISO device ${iso_device} not found"
    fi
}

function get_local_image_source_files {
    declare root=${root}
    local iso_device="${root#install:}"
    local iso_mount_point=/run/install
    local image_mount_point=/run/image
    local sha_extension
    local image_source
    local image_sha
    local image_container
    sha_extension=$(shasum_extension)
    mkdir -m 0755 -p "${iso_mount_point}"
    if ! mount -n "${iso_device}" "${iso_mount_point}"; then
        report_and_quit "Failed to mount install ISO device"
    fi
    mkdir -m 0755 -p "${image_mount_point}"
    # the disk image is stored in a squashfs or erofs container,
    # see the install_container_filesystem attribute
    for image_container in \
        "${iso_mount_point}"/*.squashfs "${iso_mount_point}"/*.erofs
    do
        [ -e "${image_container}" ] && break
    done
    if ! mount -n "${image_container}" ${image_mount_point};then
        report_and_quit "Failed to mount install image container ${image_container}"
    fi
    image_source="$(echo "${image_mount_point}"/*.raw)"
    image_sha="$(echo "${image_mount_point}"/*."${sha_extension}")"
    echo "${image_source}|${image_sha}"
}

function get_remote_image_source_files {
    local image_uri
    local sha_extension
    local image_sha
    local install_dir=/run/install
    local metadata_dir="${install_dir}/boot/remote/loader"

    sha_extension=$(shasum_extension)

    local image_sha="${install_dir}/image.${sha_extension}"

    mkdir -p "${metadata_dir}"

    image_uri=$(getarg rd.kiwi.install.image=)
    # make sure the protocol type is tftp for metadata files. There is no need for
    # complex protocol types on small files and for standard PXE boot operations
    # only tftp can be guaranteed
    image_sha_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".'"${sha_extension}"'", $1); gsub("dolly:","tftp:", $1); print $1 }'
    )
    image_initrd_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".initrd", $1); gsub("dolly:","tftp:", $1); print $1 }'
    )
    image_kernel_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".kernel", $1); gsub("dolly:","tftp:", $1); print $1 }'
    )
    image_config_uri=$(
        echo "${image_uri}" | \
        awk '{ gsub("\\.xz",".config.bootoptions", $1); gsub("dolly:","tftp:", $1); print $1 }'
    )

    # if we can not access image_sha_uri, maybe network setup
    # by dracut did fail, so collect some additional info
    if ! fetch_file "${image_sha_uri}" > "${image_sha}";then
        {
            echo "--- ip a ---"; ip a
            echo "--- ip r ---"; ip r
        } >> /tmp/fetch.info 2>&1
        show_log_and_quit \
            "Failed to fetch ${image_sha_uri}" /tmp/fetch.info
    fi

    if ! getargbool 0 rd.kiwi.ramdisk; then
        if ! fetch_file "${image_kernel_uri}" > "${metadata_dir}/linux";then
            show_log_and_quit \
                "Failed to fetch ${image_kernel_uri}" /tmp/fetch.info
        fi

        if ! fetch_file "${image_initrd_uri}" > "${install_dir}/initrd.system_image"
        then
            show_log_and_quit \
                "Failed to fetch ${image_initrd_uri}" /tmp/fetch.info
        fi
    fi

    if ! fetch_file "${image_config_uri}" > "/config.bootoptions"
    then
        show_log_and_quit \
            "Failed to fetch ${image_config_uri}" /tmp/fetch.info
    fi

    echo "${image_uri}|${image_sha}"
}

#======================================
# Perform image dump/install operations
#--------------------------------------
setup_debug

lib_initialize

udev_pending

check_partition_based_compatibility

image_target=$(get_selected_disk)

if getargbool 0 rd.kiwi.oem.disk.consistency; then
    validate_disk_selection "${image_target}"
fi

if ! getargbool 0 rd.kiwi.install.pxe && \
    target_holds_isoscan_file "${image_target}"
then
    move_isoscan_file_to_ram "${image_target}"
fi

if getargbool 0 rd.kiwi.install.pxe; then
    image_source_files=$(get_remote_image_source_files)
else
    image_source_files=$(get_local_image_source_files)
fi

export_image_metadata "${image_source_files}"

if getargbool 0 rd.kiwi.install.partition_based; then
    export kiwi_oemskipverify=true
fi

if getargbool 0 rd.kiwi.install.pxe; then
    dump_image "${image_source_files}" "${image_target}" "remote_image"
else
    dump_image "${image_source_files}" "${image_target}"
fi

check_image_integrity "${image_target}"
