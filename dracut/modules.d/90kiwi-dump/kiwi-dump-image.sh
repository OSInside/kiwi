#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type setup_debug >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type run_dialog >/dev/null 2>&1 || . /lib/kiwi-dialog-lib.sh
type get_block_device_kbsize >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh
type fetch_file >/dev/null 2>&1 || . /lib/kiwi-net-lib.sh

#======================================
# Functions
#--------------------------------------
function initialize {
    local profile=/.profile

    test -f ${profile} || \
        kiwi_die "No profile setup found"

    import_file ${profile}
}

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
    local disk_id="by-id"
    local disk_size
    local disk_device
    local disk_device_by_id
    local disk_meta
    local item_status=on
    local list_items
    local blk_opts="-p -n -r -o NAME,SIZE,TYPE"
    if [ ! -z "${kiwi_devicepersistency}" ];then
        disk_id=${kiwi_devicepersistency}
    fi
    if getargbool 0 rd.kiwi.ramdisk; then
        # target should be a ramdisk on request. Thus actively
        # load the ramdisk block driver and support custom sizes
        local rd_size
        local modfile=/etc/modprobe.d/99-brd.conf
        rd_size=$(getarg ramdisk_size=)
        if [ ! -z "${rd_size}" ];then
            echo "options brd rd_size=${rd_size}" > ${modfile}
        fi
        modprobe brd
        udev_pending
        # target should be a ramdisk on request. Thus instruct
        # lsblk to list only ramdisk devices (Major=1)
        blk_opts="-I 1 ${blk_opts}"
    elif [ ! -z "${kiwi_oemmultipath_scan}" ];then
        scan_multipath_devices
    fi
    for disk_meta in $(
        eval lsblk "${blk_opts}" | grep disk | tr ' ' ":"
    );do
        disk_device="$(echo "${disk_meta}" | cut -f1 -d:)"
        if [ "$(blkid "${disk_device}" -s LABEL -o value)" = \
            "${kiwi_install_volid}" ]
        then
            # ignore install source device
            continue
        fi
        disk_size=$(echo "${disk_meta}" | cut -f2 -d:)
        disk_device_by_id=$(
            get_persistent_device_from_unix_node "${disk_device}" "${disk_id}"
        )
        if [ ! -z "${disk_device_by_id}" ];then
            disk_device=${disk_device_by_id}
        fi
        # check for static filter rules
        if [[ ${disk_device} =~ ^/dev/fd ]];then
            # ignore floppy disk devices
            continue
        fi
        # check for custom filter rule
        if [ ! -z "${kiwi_oemdevicefilter}" ];then
            if [[ ${disk_device} =~ ${kiwi_oemdevicefilter} ]];then
                info "${disk_device} filtered out by: ${kiwi_oemdevicefilter}"
                continue
            fi
        fi
        list_items="${list_items} ${disk_device} ${disk_size} ${item_status}"
        item_status=off
    done
    if [ -z "${list_items}" ];then
        local no_device_text="No device(s) for installation found"
        run_dialog --msgbox "\"${no_device_text}\"" 5 60
        kiwi_die "${no_device_text}"
    fi
    echo "${list_items}"
}

function get_selected_disk {
    declare kiwi_oemunattended=${kiwi_oemunattended}
    declare kiwi_oemunattended_id=${kiwi_oemunattended_id}
    local disk_list
    local device_array
    disk_list=$(get_disk_list)
    if [ ! -z "${disk_list}" ];then
        local count=0
        local device_index=0
        for entry in ${disk_list};do
            if [ $((count % 3)) -eq 0 ];then
                device_array[${device_index}]=${entry}
                device_index=$((device_index + 1))
            fi
            count=$((count + 1))
        done
        if [ "${device_index}" -eq 1 ];then
            # one single disk device found, use it
            echo "${device_array[0]}"
        elif [ ! -z "${kiwi_oemunattended}" ];then
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
                --radiolist "\"Select Installation Disk\"" 20 75 15 \
                "$(get_disk_list)"
            then
                kiwi_die "System installation canceled"
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
        kiwi_die "Reading ${meta_file} failed"
    fi
    echo "Image checksum: ${checksum}"
    echo "Image blocks: ${blocks} / blocksize: ${blocksize}"
    if [ ! -z "${zblocks}" ];then
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
        kiwi_die "Not enough space available for this image"
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
    image_source="$(echo "${image_source_files}" | cut -f1 -d\|)"
    image_basename=$(basename "${image_source}")
    local progress=/dev/install_progress
    local load_text="Loading ${image_basename}..."
    local title_text="Installation..."
    local dump

    if [ ! -z "${image_from_remote}" ];then
        dump=dump_remote_image
    else
        dump=dump_local_image
    fi

    check_image_fits_target "${image_target}"

    if [ -z "${kiwi_oemunattended}" ];then
        local ack_dump_text="Destroying ALL data on ${image_target}, continue ?"
        if ! run_dialog --yesno "\"${ack_dump_text}\"" 7 80; then
            local install_cancel_text="System installation canceled"
            run_dialog --msgbox "\"${install_cancel_text}\"" 5 60
            kiwi_die "${install_cancel_text}"
        fi
    fi

    echo "${load_text} [${image_target}]..."
    if command -v pv &>/dev/null && [ -z "${kiwi_oemsilentinstall}" ];then
        # dump with dialog based progress information
        setup_progress_fifo ${progress}
        eval "${dump}" "${image_source}" "${image_target}" "${progress}" &
        run_progress_dialog "${load_text}" "${title_text}"
    else
        # dump with silently blocked console
        if ! eval "${dump}" "${image_source}" "${image_target}"; then
            kiwi_die "Failed to install image"
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
    if [ ! -z "${kiwi_oemskipverify}" ];then
        # no verification wanted
        return
    fi
    if command -v pv &>/dev/null && [ -z "${kiwi_oemsilentverify}" ];then
        # verify with dialog based progress information
        setup_progress_fifo ${progress}
        run_progress_dialog "${verify_text}" "${title_text}" &
        (
            pv --size $((blocks * blocksize)) --stop-at-size \
            -n "${image_target}" | md5sum - > ${verify_result}
        ) 2>${progress}
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
        kiwi_die "Image checksum test failed"
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
        kiwi_die "Failed to mount install ISO device"
    fi
    mkdir -m 0755 -p "${image_mount_point}"
    if ! mount -n "${iso_mount_point}"/*.squashfs ${image_mount_point};then
        kiwi_die "Failed to mount install image squashfs filesystem"
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
    image_md5_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".md5", $1); print $1 }'
    )
    image_initrd_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".initrd", $1); print $1 }'
    )
    image_kernel_uri=$(
        echo "${image_uri}" | awk '{ gsub("\\.xz",".kernel", $1); print $1 }'
    )

    if ! ifup lan0 &>/tmp/net.info;then
        kiwi_die "Network setup failed, see /tmp/net.info"
    fi

    if ! fetch_file "${image_md5_uri}" > "${image_md5}";then
        kiwi_die "Failed to fetch ${image_md5_uri}, see /tmp/fetch.info"
    fi

    if ! fetch_file "${image_kernel_uri}" > "${metadata_dir}/linux";then
        kiwi_die "Failed to fetch ${image_kernel_uri}, see /tmp/fetch.info"
    fi

    if ! fetch_file "${image_initrd_uri}" > "${install_dir}/initrd.system_image"
    then
        kiwi_die "Failed to fetch ${image_initrd_uri}, see /tmp/fetch.info"
    fi

    echo "${image_uri}|${image_md5}"
}

function boot_installed_system {
    local boot_options
    boot_options="$(cat /config.bootoptions)"
    if getargbool 0 rd.kiwi.debug; then
        boot_options="${boot_options} rd.kiwi.debug"
    fi
    kexec -l /run/install/boot/*/loader/linux \
        --initrd /run/install/initrd.system_image \
        --command-line "${boot_options}"
    if ! kexec -e; then
        kiwi_die "Failed to boot system"
    fi
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

if getargbool 0 rd.kiwi.ramdisk; then
    # For ramdisk deployment a kexec boot is not possible as it
    # will wipe the contents of the ramdisk. Therefore we prepare
    # the switch_root from this deployment initrd. Also see the
    # unit generator: dracut-kiwi-ramdisk-generator
    kpartx -s -a "${image_target}"
else
    # Standard deployment will use kexec to activate and boot the
    # deployed system
    boot_installed_system
fi
