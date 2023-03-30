type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type udev_pending >/dev/null 2>&1 || . /lib/kiwi-lib.sh

#======================================
# Library Methods
#--------------------------------------
function create_partitions {
    local disk_device=$1
    local partition_setup=$2
    local pt_table_type
    pt_table_type=$(get_partition_table_type "${disk_device}")
    case ${pt_table_type} in
        "dos")
            create_msdos_partitions "${disk_device}" "${partition_setup}"
        ;;
        "gpt")
            create_gpt_partitions "${disk_device}" "${partition_setup}"
        ;;
        "dasd")
            create_parted_partitions "${disk_device}" "${partition_setup}"
        ;;
    esac
    partprobe "${disk_device}"
}

function create_msdos_partitions {
    # """
    # create partitions using sfdisk (msdos table)
    # """
    local disk_device=$1
    local partition_setup=$2
    local partid
    local part_size_end
    local cmd_list
    local start_sector_from
    local cmd

    # put partition setup in a command list(cmd_list)
    for cmd in ${partition_setup};do
        # default values in sfdisk are used if - is provided
        cmd=$(echo "${cmd}" | tr . -)
        cmd_list[$index]=${cmd}
        index=$((index + 1))
    done

    # operate on index based cmd_list
    index=0
    for cmd in ${cmd_list[*]};do
        case ${cmd} in
        "d")
            # delete a partition...
            partid=${cmd_list[$index + 1]}
            start_sector_from[$partid]=$(
                _get_msdos_partition_start_sector "${disk_device}" "${partid}"
            )
            sfdisk --force --delete "${disk_device}" "${partid}"
        ;;
        "n")
            # create a partition...
            partid=${cmd_list[$index + 2]}
            part_size_end=${cmd_list[$index + 4]}
            echo "${start_sector_from[$partid]},${part_size_end}" > /tmp/sfdisk.in
            sfdisk --force -N "${partid}" "${disk_device}" <  /tmp/sfdisk.in
        ;;
        "t")
            # change a partition type...
            part_type=${cmd_list[$index + 2]}
            partid=${cmd_list[$index + 1]}
            sfdisk --force --change-id "${disk_device}" "${partid}" \
                "${part_type}"
        ;;
        esac
        index=$((index + 1))
    done
}

function create_gpt_partitions {
    # """
    # create partitions using sgdisk (gpt table)
    # """
    local disk_device=$1
    local partition_setup=$2
    local partid
    local part_name
    local part_size_start
    local part_size_end
    local cmd_list
    local cmd

    # put partition setup in a command list(cmd_list)
    for cmd in ${partition_setup};do
        # default values in sgdisk are used if 0 is provided
        cmd=$(echo "${cmd}" | tr . 0)
        cmd_list[$index]=${cmd}
        index=$((index + 1))
    done

    # operate on index based cmd_list
    index=0
    for cmd in ${cmd_list[*]};do
        case ${cmd} in
        "d")
            # delete a partition...
            partid=${cmd_list[$index + 1]}
            sgdisk --delete "${partid}" "${disk_device}"
        ;;
        "n")
            # create a partition...
            part_name=$(echo "${cmd_list[$index + 1]}" | tr : .)
            partid=${cmd_list[$index + 2]}
            part_size_start=${cmd_list[$index + 3]}
            part_size_end=${cmd_list[$index + 4]}
            sgdisk --new "${partid}:${part_size_start}:${part_size_end}" \
                "${disk_device}"
            sgdisk --change-name "${partid}:${part_name}" \
                "${disk_device}"
        ;;
        "t")
            # change a partition type...
            part_type=${cmd_list[$index + 2]}
            partid=${cmd_list[$index + 1]}
            sgdisk --typecode "${partid}:$(_to_guid "${part_type}")" \
                "${disk_device}"
        ;;
        esac
        index=$((index + 1))
    done
}

function create_dasd_partitions {
    # """
    # create partitions using fdasd (s390)
    # """
    local disk_device=$1
    local partition_setup=$2
    local partition_setup_file=/run/fdasd.cmds
    local ignore_cmd=0
    local ignore_cmd_once=0
    local cmd
    for cmd in ${partition_setup};do
        if [ "${ignore_cmd}" = 1 ] && echo "${cmd}" | grep -qE '[dntwq]';then
            ignore_cmd=0
        elif [ "${ignore_cmd}" = 1 ];then
            continue
        fi
        if [ "${ignore_cmd_once}" = "1" ];then
            ignore_cmd_once=0
            continue
        fi
        if [ "${cmd}" = "a" ];then
            ignore_cmd=1
            continue
        fi
        if [[ "${cmd}" =~ ^p: ]];then
            ignore_cmd_once=1
            continue
        fi
        if [ "${cmd}" = "83" ] || [ "${cmd}" = "8e" ];then
            cmd=1
        fi
        if [ "${cmd}" = "82" ];then
            cmd=2
        fi
        if [ "${cmd}" = "." ];then
            echo >> ${partition_setup_file}
            continue
        fi
        echo $cmd >> ${partition_setup_file}
    done
    echo "w" >> ${partition_setup_file}
    echo "q" >> ${partition_setup_file}
    fdasd "${disk_device}" < ${partition_setup_file} 1>&2
}

function create_parted_partitions {
    # """
    # create partitions using parted
    # """
    local disk_device=$1
    local partition_setup=$2
    local index=0
    local commands
    local partid
    local part_name
    local part_start_cyl
    local part_stop_cyl
    local part_type
    local cmd_list
    local cmd

    _parted_init "${disk_device}"
    _parted_sector_init "${disk_device}"

    # put partition setup in a command list(cmd_list)
    for cmd in ${partition_setup};do
        cmd_list[$index]=${cmd}
        index=$((index + 1))
    done

    # operate on index based cmd_list
    index=0
    for cmd in ${cmd_list[*]};do
        case ${cmd} in
        "d")
            # delete a partition...
            partid=${cmd_list[$index + 1]}
            partid=$((partid / 1))
            commands="${commands} rm $partid"
            _parted_write "${disk_device}" "${commands}"
            unset commands
        ;;
        "n")
            # create a partition...
            part_name=${cmd_list[$index + 1]}
            partid=${cmd_list[$index + 2]}
            partid=$((partid / 1))
            part_start_cyl=${cmd_list[$index + 3]}
            if [ ! "${partedTableType}" = "gpt" ];then
                part_name=primary
            else
                part_name=$(echo ${part_name} | cut -f2 -d:)
            fi
            if [ "${part_start_cyl}" = "1" ];then
                part_start_cyl=$(echo "${partedStartSectors}" |\
                    cut -f ${partid} -d:
                )
            fi
            if [ "${part_start_cyl}" = "." ];then
                # start is next cylinder according to previous partition
                part_start_cyl=$((partid - 1))
                if [ ${part_start_cyl} -gt 0 ];then
                    part_start_cyl=$(echo "${partedEndSectors}" |\
                        cut -f ${part_start_cyl} -d:
                    )
                else
                    part_start_cyl=$(echo "${partedStartSectors}" |\
                        cut -f ${partid} -d:
                    )
                fi
            fi
            part_stop_cyl=${cmd_list[$index + 4]}
            if [ "${part_stop_cyl}" = "." ];then
                # use rest of the disk for partition end
                part_stop_cyl=${partedCylCount}
            elif echo "${part_stop_cyl}" | grep -qi M;then
                # calculate stopp cylinder from size
                part_stop_cyl=$((partid - 1))
                if [ ${part_stop_cyl} -gt 0 ];then
                    part_stop_cyl=$(_parted_end_cylinder ${part_stop_cyl})
                fi
                local part_size_mbytes
                part_size_mbytes=$(
                    echo "${cmd_list[$index + 4]}" | cut -f1 -dM | tr -d +
                )
                local part_size_cyl
                part_size_cyl=$(
                    _parted_mb_to_cylinder "${part_size_mbytes}"
                )
                part_stop_cyl=$((1 + part_stop_cyl + part_size_cyl))
                if [ "${part_stop_cyl}" -gt "${partedCylCount}" ];then
                    # given size is out of bounds, reduce to end of disk
                    part_stop_cyl=${partedCylCount}
                fi
            fi
            commands="${commands} mkpart ${part_name}"
            commands="${commands} ${part_start_cyl} ${part_stop_cyl}"
            _parted_write "${disk_device}" "${commands}"
            _parted_sector_init "${disk_device}"
            unset commands
        ;;
        "t")
            # change a partition type...
            part_type=${cmd_list[$index + 2]}
            partid=${cmd_list[$index + 1]}
            local flagok=1
            if [ "${part_type}" = "82" ];then
                # parted can not consistently set swap flag.
                # There is no general solution to this issue.
                # Thus swap flag setup is skipped
                flagok=0
            elif [ "${part_type}" = "fd" ];then
                commands="${commands} set ${partid} raid on"
            elif [ "${part_type}" = "8e" ];then
                commands="${commands} set ${partid} lvm on"
            elif [ "${part_type}" = "83" ];then
                # default partition type set by parted is linux(83)
                flagok=0
            fi
            if [ ! "${partedTableType}" = "gpt" ] && [ ${flagok} = 1 ];then
                _parted_write "${disk_device}" "${commands}"
            fi
            unset commands
        ;;
        esac
        index=$((index + 1))
    done
    partprobe "${disk_device}"
}

function get_partition_node_name {
    local disk=$1
    local partid=$2
    local index=1
    local part
    udev_pending
    for partnode in $(
        lsblk -p -l -o NAME,TYPE "${disk}" | grep -E "part|md$" | cut -f1 -d ' '
    );do
        if [ "${index}" = "${partid}" ];then
            echo "${partnode}"
            return 0
        fi
        index=$((index + 1))
    done
    return 1
}

function wait_for_storage_device {
    # """
    # function to check access on a storage device which could be
    # a whole disk or a partition. The function will wait until
    # the size of the storage device could be obtained and is
    # greater than zero or the timeout is reached. Default timeout
    # is set to 60 seconds, however it can be set to different
    # value by setting the DEVICE_TIMEOUT variable on the kernel
    # command line.
    # """
    declare DEVICE_TIMEOUT=${DEVICE_TIMEOUT}
    local device=$1
    local check=0
    local limit=30
    local storage_size=0
    if [[ "${DEVICE_TIMEOUT}" =~ ^[0-9]+$ ]]; then
        limit=$(((DEVICE_TIMEOUT + 1)/ 2))
    fi
    udev_pending
    while true;do
        storage_size=$(get_block_device_kbsize "${device}")
        if [ "${storage_size}" -gt 0 ]; then
            sleep 1; return 0
        fi
        if [ "${check}" -eq "${limit}" ]; then
            die "Storage device ${device} did not appear"
        fi
        info "Waiting for storage device ${device} to settle..."
        check=$((check + 1))
        sleep 2
    done
}

function get_block_device_kbsize {
    local device=$1
    if [ ! -e "${device}" ];then
        echo 0; return 1
    fi
    echo $(($(blockdev --getsize64 "${device}") / 1024))
}

function get_free_disk_bytes {
    local disk=$1
    local pt_table_type
    local disk_bytes
    local max_dos_disk
    pt_table_type=$(get_partition_table_type "${disk}")
    disk_bytes=$(blockdev --getsize64 "${disk}")
    # max msdos table geometry is at 2TB - 512
    max_dos_disk=$((4294967295 * 512))
    if \
        [ "${pt_table_type}" = "dos" ] && \
        [ "${disk_bytes}" -gt "${max_dos_disk}" ]
    then
        warn "msdos table allows a max disk size of 2TB"
        warn "disk expansion will be truncated to 2TB"
        disk_bytes=${max_dos_disk}
    fi
    local rest_bytes
    rest_bytes=${disk_bytes}
    local part_bytes=0
    local part_count=0
    local part_uuids
    udev_pending
    for part in $(
        lsblk -p -l -o NAME,TYPE "${disk}" | grep -E "part|md$" | cut -f1 -d ' '
    );do
        current_part_uuid=$(get_partition_uuid "${part}")
        for part_uuid in ${part_uuids[*]};do
            if [ "${current_part_uuid}" = "${part_uuid}" ];then
                # this partition uuid was already handled. The device
                # node is pointing to the same physical device and
                # should only be taken into account once
                unset part
                break
            fi
        done
        if [ -n "${part}" ]; then
            part_bytes=$((part_bytes + $(blockdev --getsize64 "${part}")))
            part_uuids[${part_count}]=${current_part_uuid}
            part_count=$((part_count + 1))
        fi
    done
    rest_bytes=$((rest_bytes - part_bytes))
    echo ${rest_bytes}
}

function get_partition_table_type {
    case $(basename "$1") in
        # Assume DASD if the device starts with "dasd" blkid does not
        # properly recognize dasd as PTTYPE bsc#1209247
        dasd*)
            echo "dasd"
            ;;
        *)
            blkid -s PTTYPE -o value "$1"
            ;;
    esac
}

function get_partition_uuid {
    blkid -s PARTUUID -o value "$1"
}

function relocate_gpt_at_end_of_disk {
    if ! sgdisk -e "$1";then
        die "Failed to write backup GPT at end of disk"
    fi
}

function disk_has_unallocated_space {
    local disk_device=$1
    local pt_table_type
    pt_table_type=$(get_partition_table_type "${disk_device}")
    if [ "${pt_table_type}" = "gpt" ];then
        # GPT disks store a backup table at the end of the disk
        # if the disk geometry changes the backup table is no
        # longer at the end and this condition can be easily
        # checked and used to detect that there is space
        # unallocated due to a geometry change of the underlying
        # block device layer
        sgdisk --verify "${disk_device}" 2>&1 | grep -q "end of the disk"
    else
        # There is currently no method we could come up with
        # to detect a geometry change for non GPT based disks.
        # Thus we assume it's not fully allocated and allow
        # for resize
        true
    fi
}

function activate_boot_partition {
    local disk_device=$1
    local boot_partition_id=$2
    local pt_table_type
    pt_table_type=$(get_partition_table_type "${disk_device}")
    if [[ "$(uname -m)" =~ i.86|x86_64 ]];then
        if [ "${pt_table_type}" = "dos" ];then
            sfdisk --activate "${disk_device}" "${boot_partition_id}"
        fi
    fi
}

function create_hybrid_gpt {
    local disk_device=$1
    local partition_count
    udev_pending
    partition_count=$(lsblk -r -o NAME,TYPE "${disk_device}" | grep -c part)
    if [ "${partition_count}" -gt 3 ]; then
        # The max number of partitions to embed is 3
        # see man sgdisk for details
        partition_count=3
    fi
    if ! sgdisk -h "$(seq -s : 1 "${partition_count}")" "${disk_device}";then
        die "Failed to create hybrid GPT/MBR !"
    fi
}

function finalize_partition_table {
    # """
    # finalize partition table with flags which
    # could have got lost during repartition
    # """
    declare kiwi_BootPart=${kiwi_BootPart}
    declare kiwi_gpt_hybrid_mbr=${kiwi_gpt_hybrid_mbr}
    local disk_device=$1
    if [ -n "${kiwi_BootPart}" ];then
        activate_boot_partition "${disk_device}" "${kiwi_BootPart}"
    fi
    if [ "${kiwi_gpt_hybrid_mbr}" = "true" ];then
        create_hybrid_gpt "${disk_device}"
    fi
}

function resize_wanted {
    # """
    # check if oem-resize-once was requested in the image
    # description. If not we always try to repart/resize
    # the image according to the configured constraints.
    #
    # If oem-resize-once is set to true we check if the
    # system has been already resized compared to the
    # original image PARTUUID and repart/resize the system
    # only if the PARTUUID is still the original value.
    # After resize a new PARTUUID will be written by the
    # partitioner and that will result in the repart/resize
    # operation to happen only once in the livetime of
    # the image
    #
    # If the resize is wanted the method also checks for
    # a real change in geometry on the block device layer
    # and returns accordingly. Please note geometry change
    # can currently only be detected on GPT disks. In any
    # other case it is assumed the geometry has changed
    # such that a resize can at least be tried
    # """
    declare kiwi_oemresizeonce=${kiwi_oemresizeonce}
    declare kiwi_rootpartuuid=${kiwi_rootpartuuid}
    local current_rootpart_uuid
    local root_device=$1
    local disk_device=$2
    kiwi_oemresizeonce=$(bool "${kiwi_oemresizeonce}")
    if [ "${kiwi_oemresizeonce}" = "true" ];then
        current_rootpart_uuid=$(get_partition_uuid "${root_device}")
        if [ "${current_rootpart_uuid}" == "${kiwi_rootpartuuid}" ];then
            info "System was not yet resized"
        else
            info "System was already resized and oem-resize-once is requested"
            info "Skipping resize operation"
            return 1
        fi
    else
        info "System resize is active on every reboot"
    fi
    if disk_has_unallocated_space "${disk_device}";then
        info "Activating resize operation"
        return 0
    else
        info "Disk geometry did not change"
        info "Skipping resize operation"
        return 1
    fi
}

#======================================
# Global pareted exports
#--------------------------------------
export partedTableType
export partedOutput
export partedCylCount
export partedCylKSize
export partedStartSectors
export partedEndSectors


#======================================
# Methods considered private
#--------------------------------------
function _get_msdos_partition_start_sector {
    # """
    # read start sector from given partition
    # """
    local disk_device=$1
    local partid=$2
    sfdisk --dump "${disk_device}" |\
        grep "${partid} :" | cut -f1 -d, | cut -f2 -d= | tr -d " "
}

function _to_guid {
    # """
    # convert two digit partition id to guid id
    # """
    local partid=$1
    if [ "${partid}" = "83" ];then
        # Linux filesystem
        echo 8300
    elif [ "${partid}" = "8e" ];then
        # Linux LVM
        echo 8e00
    elif [ "${partid}" = "fd" ];then
        # Linux RAID
        echo fd00
    elif [ "${partid}" = "82" ];then
        # Linux swap
        echo 8200
    else
        # Assume Linux filesystem
        echo 8300
    fi
}

function _parted_init {
    # """
    # initialize current partition table output
    # as well as the number of cylinders and the
    # cyliner size in kB for this disk
    # """
    local disk_device=$1
    local IFS=""
    local parted
    local header
    local ccount
    local cksize
    local diskhd
    local plabel
    parted=$(
        parted -m -s "${disk_device}" unit cyl print | grep -v Warning:
    )
    header=$(echo "${parted}" | head -n 3 | tail -n 1)
    ccount=$(
        echo "${parted}" | grep ^"${disk_device}" | cut -f 2 -d: | tr -d cyl
    )
    cksize=$(echo "${header}" | cut -f4 -d: | cut -f1 -dk)
    diskhd=$(echo "${parted}" | head -n 3 | tail -n 2 | head -n 1)
    plabel=$(echo "${diskhd}" | cut -f6 -d:)
    if [[ "${plabel}" =~ gpt ]];then
        plabel=gpt
    fi
    export partedTableType=${plabel}
    export partedOutput=${parted}
    export partedCylCount=${ccount}
    export partedCylKSize=${cksize}
}

function _parted_sector_init {
    # """
    # calculate aligned start/end sectors of
    # the current table.
    #
    # Uses following kiwi profile values if present:
    #
    # kiwi_align
    # kiwi_sectorsize
    # kiwi_startsector
    #
    # """
    declare kiwi_align=${kiwi_align}
    declare kiwi_sectorsize=${kiwi_sectorsize}
    declare kiwi_startsector=${kiwi_startsector}
    local disk_device=$1
    local s_start
    local s_stopp
    local align=1048576
    local sector_size=512
    local sector_start=2048
    local part
    [ -n "${kiwi_align}" ] && align=${kiwi_align}
    [ -n "${kiwi_sectorsize}" ] && sector_size=${kiwi_sectorsize}
    [ -n "${kiwi_startsector}" ] && sector_start=${kiwi_startsector}
    local align=$((align / sector_size))

    unset partedStartSectors
    unset partedEndSectors

    for part in $(
        parted -m -s "${disk_device}" unit s print |\
        grep -E "^[1-9]+:" | cut -f2-3 -d: | tr -d s
    );do
        s_start=$(echo "${part}" | cut -f1 -d:)
        s_stopp=$(echo "${part}" | cut -f2 -d:)
        if [ -z "${partedStartSectors}" ];then
            partedStartSectors=${s_start}s
        else
            partedStartSectors=${partedStartSectors}:${s_start}s
        fi
        if [ -z "${partedEndSectors}" ];then
            partedEndSectors=$((s_stopp/align*align+align))s
        else
            partedEndSectors=${partedEndSectors}:$((s_stopp/align*align+align))s
        fi
    done
    # The default start sector applies for an empty disk
    if [ -z "${partedStartSectors}" ];then
        partedStartSectors=${sector_start}s
    fi
}

function _parted_end_cylinder {
    # """
    # return end cylinder of given partition, next
    # partition must start at return value plus 1
    # """
    local partition_id=$(($1 + 3))
    local IFS=""
    local header
    local ccount
    header=$(echo "${partedOutput}" | head -n "${partition_id}" | tail -n 1)
    ccount=$(echo "${header}" | cut -f3 -d: | tr -d cyl)
    echo "${ccount}"
}

function _parted_mb_to_cylinder {
    # """
    # convert partition size in MB to cylinder count
    # """
    local sizeBytes=$(($1 * 1048576))
    # bc truncates to zero decimal places, which results in
    # a partition that is slightly smaller than the requested
    # size. Add one cylinder to compensate.
    local required_cylinders
    required_cylinders=$(
        echo "scale=0; ${sizeBytes} / (${partedCylKSize} * 1000) + 1" | bc
    )
    echo "${required_cylinders}"
}

function _parted_write {
    # """
    # call parted with current command queue.
    # and reinitialize the new table data
    # """
    local disk_device=$1
    local commands=$2
    if ! parted -a cyl -m -s "${disk_device}" unit cyl "${commands}";then
        die "Failed to create partition table"
    fi
    _parted_init "${disk_device}"
}
