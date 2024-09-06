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
    local disk_meta
    local list_items
    local max_disk
    local kiwi_oem_maxdisk
    local blk_opts="-p -n -r --sort NAME -o NAME,SIZE,TYPE"
    local message
    local blk_opts_plus_label="${blk_opts},LABEL"
    local kiwi_install_disk_part
    if [ -n "${kiwi_devicepersistency}" ];then
        disk_id=${kiwi_devicepersistency}
    fi
    max_disk=0
    kiwi_oemmultipath_scan=$(bool "${kiwi_oemmultipath_scan}")
    kiwi_oem_maxdisk=$(getarg rd.kiwi.oem.maxdisk=)
    kiwi_oem_installdevice=$(getarg rd.kiwi.oem.installdevice=)
    if [ -n "${kiwi_oem_maxdisk}" ]; then
        max_disk=$(binsize_to_bytesize "${kiwi_oem_maxdisk}") || max_disk=0
    fi
    if getargbool 0 rd.kiwi.ramdisk; then
        # target should be a ramdisk on request. Thus actively
        # load the ramdisk block driver and support custom sizes
        local rd_size
        local modfile=/etc/modprobe.d/99-brd.conf
        rd_size=$(getarg ramdisk_size=)
        mkdir -p /etc/modprobe.d
        if [ -n "${rd_size}" ];then
            echo "options brd rd_size=${rd_size}" > ${modfile}
        fi
        modprobe brd
        udev_pending
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
            grep -E "disk|raid" | tr ' ' ":"
        )
        device_size=$(echo "${device_meta}" | cut -f2 -d:)
        list_items="${device} ${device_size}"
    fi
    if [ -z "${list_items}" ];then
        local no_device_text="No device(s) for installation found"
        report_and_quit "${no_device_text}"
    fi
    echo "${list_items}"
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
                for device in ${device_array[*]}; do
                    if [[ ${device} =~ ${kiwi_oemunattended_id} ]];then
                        echo "${device}"
                        return
                    fi
                done
            fi
        else
            # manually select from storage list
            if ! run_dialog \
                --menu "\"Select Installation Disk\"" 20 75 15 \
                "$(get_disk_list)"
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
    local load_text="Loading ${image_basename}..."
    local title_text="Installation..."
    local dump

    if [ -n "${image_from_remote}" ];then
        dump=dump_remote_image
    else
        dump=dump_local_image
    fi

    check_image_fits_target "${image_target}"

    if [ "${kiwi_oemunattended}" = "false" ];then
        local ack_dump_text="Destroying ALL data on ${image_target}, continue ?"
        if ! run_dialog --yesno "\"${ack_dump_text}\"" 7 80; then
            local install_cancel_text="System installation canceled"
            report_and_quit "${install_cancel_text}"
        fi
    fi

    echo "${load_text} [${image_target}]..."
    if command -v pv &>/dev/null && [ "${kiwi_oemsilentinstall}" = "false" ]
    then
        # dump with dialog based progress information
        setup_progress_fifo ${progress}
        eval "${dump}" "${image_source}" "${image_target}" "${progress}" &
        run_progress_dialog "${load_text}" "${title_text}"
    else
        # dump with silently blocked console
        if ! eval "${dump}" "${image_source}" "${image_target}"; then
            report_and_quit "Failed to install image"
        fi
    fi
}

function dump_local_image {
    local image_source=$1
    local image_target=$2
    local progress=$3
    if [ -e "${progress}" ];then
        (
            pv -n "${image_source}" | dd bs=32k of="${image_target}" &>/dev/null
        ) 2>"${progress}"
    else
        dd if="${image_source}" bs=32k of="${image_target}" &>/dev/null
    fi
}

function dump_remote_image {
    local image_source=$1
    local image_target=$2
    local progress=$3
    local image_size
    image_size=$((blocks * blocksize))
    if [ -e "${progress}" ];then
        (
            fetch_file "${image_source}" "${image_size}" |\
                dd bs=32k of="${image_target}" &>/dev/null
        ) 2>"${progress}"
    else
        fetch_file "${image_source}" |\
            dd bs=32k of="${image_target}" &>/dev/null
    fi
}

function check_image_integrity {
    declare kiwi_oemskipverify=${kiwi_oemskipverify}
    declare kiwi_oemsilentverify=${kiwi_oemsilentverify}
    local image_target=$1
    local progress=/dev/install_verify_progress
    local verify_text="Verifying ${image_target}"
    local title_text="Installation..."
    local verify_result=/dumped_image.md5
    kiwi_oemskipverify=$(bool "${kiwi_oemskipverify}")
    kiwi_oemsilentverify=$(bool "${kiwi_oemsilentverify}")
    if [ "${kiwi_oemskipverify}" = "true" ];then
        # no verification wanted
        return
    fi
    if command -v pv &>/dev/null && [ "${kiwi_oemsilentverify}" = "false" ]
    then
        # verify with dialog based progress information
        setup_progress_fifo ${progress}
        (
            pv --size $((blocks * blocksize)) --stop-at-size \
            -n "${image_target}" | md5sum - > ${verify_result}
        ) 2>${progress} &
        run_progress_dialog "${verify_text}" "${title_text}"
    else
        # verify with silently blocked console
        head --bytes=$((blocks * blocksize)) "${image_target}" |\
        md5sum - > ${verify_result}
    fi
    local checksum_dumped_image
    local checksum_fileref
    read -r checksum_dumped_image checksum_fileref < ${verify_result}
    echo "Dumped Image checksum: ${checksum_dumped_image}/${checksum_fileref}"
    if [ "${checksum}" != "${checksum_dumped_image}" ];then
        report_and_quit "Image checksum test failed"
    fi
}

function get_local_image_source_files {
    declare root=${root}
    local iso_device="${root#install:}"
    local iso_mount_point=/run/install
    local image_mount_point=/run/image
    local image_source
    local image_md5
    mkdir -m 0755 -p "${iso_mount_point}"
    if ! mount -n "${iso_device}" "${iso_mount_point}"; then
        report_and_quit "Failed to mount install ISO device"
    fi
    mkdir -m 0755 -p "${image_mount_point}"
    if ! mount -n "${iso_mount_point}"/*.squashfs ${image_mount_point};then
        report_and_quit "Failed to mount install image squashfs filesystem"
    fi
    image_source="$(echo "${image_mount_point}"/*.raw)"
    image_md5="$(echo "${image_mount_point}"/*.md5)"
    echo "${image_source}|${image_md5}"
}

function get_remote_image_source_files {
    local image_uri
    local install_dir=/run/install
    local image_md5="${install_dir}/image.md5"
    local metadata_dir="${install_dir}/boot/remote/loader"

    mkdir -p "${metadata_dir}"

    image_uri=$(getarg rd.kiwi.install.image=)
    # make sure the protocol type is tftp for metadata files. There is no need for
    # complex protocol types on small files and for standard PXE boot operations
    # only tftp can be guaranteed
    image_md5_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".md5", $1); gsub("dolly:","tftp:", $1); print $1 }'
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

    # if we can not access image_md5_uri, maybe network setup
    # by dracut did fail, so collect some additional info
    if ! fetch_file "${image_md5_uri}" > "${image_md5}";then
        {
            echo "--- ip a ---"; ip a
            echo "--- ip r ---"; ip r
        } >> /tmp/fetch.info 2>&1
        show_log_and_quit \
            "Failed to fetch ${image_md5_uri}" /tmp/fetch.info
    fi

    if ! fetch_file "${image_kernel_uri}" > "${metadata_dir}/linux";then
        show_log_and_quit \
            "Failed to fetch ${image_kernel_uri}" /tmp/fetch.info
    fi

    if ! fetch_file "${image_initrd_uri}" > "${install_dir}/initrd.system_image"
    then
        show_log_and_quit \
            "Failed to fetch ${image_initrd_uri}" /tmp/fetch.info
    fi

    if ! fetch_file "${image_config_uri}" > "/config.bootoptions"
    then
        show_log_and_quit \
            "Failed to fetch ${image_config_uri}" /tmp/fetch.info
    fi

    echo "${image_uri}|${image_md5}"
}

#======================================
# Perform image dump/install operations
#--------------------------------------
setup_debug

initialize

udev_pending

image_target=$(get_selected_disk)

if getargbool 0 rd.kiwi.install.pxe; then
    image_source_files=$(get_remote_image_source_files)
else
    image_source_files=$(get_local_image_source_files)
fi

export_image_metadata "${image_source_files}"

if getargbool 0 rd.kiwi.install.pxe; then
    dump_image "${image_source_files}" "${image_target}" "remote_image"
else
    dump_image "${image_source_files}" "${image_target}"
fi

check_image_integrity "${image_target}"
