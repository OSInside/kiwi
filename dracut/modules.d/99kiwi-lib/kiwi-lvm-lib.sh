type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type udev_pending >/dev/null 2>&1 || . /lib/kiwi-lib.sh

function lvm_system {
    declare kiwi_lvm=${kiwi_lvm}
    if [ "${kiwi_lvm}" = "true" ];then
        return 0
    fi
    return 1
}

function setup_lvm_config {
    mkdir -p /etc/lvm
    cat > /etc/lvm/lvm.conf <<- EOF
		global {
		    locking_type = 0
		    use_lvmetad = 0
		}
	EOF
}

function activate_volume_group {
    declare kiwi_lvmgroup=${kiwi_lvmgroup}
    local vg_count=0
    local vg_name
    if lvm_system;then
        for vg_name in $(vgs --noheadings -o vg_name 2>/dev/null);do
            if [ "${vg_name}" = "${kiwi_lvmgroup}" ];then
                vg_count=$((vg_count + 1))
            fi
        done
        if [ ${vg_count} -gt 1 ];then
            die "Duplicate VolumeGroup name ${kiwi_lvmgroup} found !"
        fi
        vgchange -a y "${kiwi_lvmgroup}"
        udev_pending
    fi
}

function deactivate_volume_group {
    declare kiwi_lvmgroup=${kiwi_lvmgroup}
    vgchange -a n "${kiwi_lvmgroup}"
    udev_pending
}

function create_volume {
    declare kiwi_lvmgroup=${kiwi_lvmgroup}
    local volume_name=$1
    local volume_mb_size=$2
    if [ ! -f "$(get_volume_path_for_volume "${volume_name}")" ];then
        lvcreate --yes --wipesignatures y \
            --size "${volume_mb_size}M" -n "${volume_name}" "${kiwi_lvmgroup}"
    fi
}

function get_volume_path_for_volume {
    declare kiwi_lvmgroup=${kiwi_lvmgroup}
    echo "/dev/${kiwi_lvmgroup}/$1"
}

function resize_pyhiscal_volumes {
    pvresize "$(get_root_map)"
}

function resize_lvm_volumes_and_filesystems {
    declare kiwi_lvmgroup=${kiwi_lvmgroup}
    local volume_name
    local resize_mode
    local resize_prefix
    local volume_size
    local volspec
    local all_free_volume
    for volspec in $(read_volume_setup "/.profile" "skip_all_free_volume");do
        resize_prefix=''
        volume_name=$(get_volume_name "${volspec}")
        resize_mode=$(get_volume_size_mode "${volspec}")
        volume_size=$(get_volume_size "${volspec}")
        info "Resizing volume ${volume_name}..."
        if [ ! "${resize_mode}" = "size" ];then
            resize_prefix=+
        fi
        if lvextend -L "${resize_prefix}${volume_size}M" \
            "/dev/${kiwi_lvmgroup}/${volume_name}"
        then
            resize_filesystem "/dev/${kiwi_lvmgroup}/${volume_name}"
        else
            warn "Warning: requested size cannot be reached !"
        fi
    done
    all_free_volume=$(get_all_free_volume)
    if [ -n "${all_free_volume}" ];then
        if lvextend -l +100%FREE "/dev/${kiwi_lvmgroup}/${all_free_volume}";then
            resize_filesystem "/dev/${kiwi_lvmgroup}/${all_free_volume}"
        fi
    fi
}

function read_volume_setup {
    # """
    # read the volume setup from the profile file and return
    # a list with the following values:
    #
    # volume_name,resize_mode,requested_size,mount_point ...
    # """
    local profile=$1
    local skip_all_free_volume=$2
    local volume
    local name
    local mode
    local size
    local mpoint
    local result
    local volspec
    result=$(
        while read -r volspec;do
            if ! [[ "${volspec}" =~ "kiwi_Volume_" ]];then
                continue
            fi
            volume=$(echo "${volspec}" | cut -f2 -d= | tr -d \' | tr -d \")
            size=$(echo "${volume}" | cut -f2 -d\| | cut -f2 -d:)
            if [ "${size}" = "all" ] && [ -n "${skip_all_free_volume}" ];then
                continue
            fi
            mode=$(echo "${volume}" | cut -f2 -d\| | cut -f1 -d:)
            name=$(echo "${volume}" | cut -f1 -d\|)
            mpoint=$(echo "${volume}" | cut -f3 -d\|)
            if [ -z "${mpoint}" ];then
                mpoint=noop
            fi
            echo "${name},${mode},${size},${mpoint}"
        done < "${profile}"
    )
    echo "${result}"
}

function read_volume_setup_all_free {
    # """
    # read the volume setup from the profile file and
    # lookup the volume that should take the rest space
    # available in the volume group.
    #
    # return a list with the following values:
    #
    # volume_name,mount_point
    #
    # If no @root volume is configured in the kiwi XML
    # description the default LVRoot volume will be used
    # to take the rest space.
    # """
    local profile=$1
    local size
    local volume
    local name
    local mpoint
    while read -r volspec;do
        if ! [[ "${volspec}" =~ "kiwi_Volume_" ]];then
            continue
        fi
        volume=$(echo "${volspec}" | cut -f2 -d= | tr -d \' | tr -d \")
        size=$(echo "${volume}" | cut -f2 -d\| | cut -f2 -d:)
        name=$(echo "${volume}" | cut -f1 -d\|)
        if [ "${size}" = "all" ];then
            mpoint=$(echo "${volume}" | cut -f3 -d\|)
            echo "${name},${mpoint}"
            return
        fi
    done < "${profile}"
}

function get_all_free_volume {
    read_volume_setup_all_free "/.profile" | cut -f1 -d,
}

function get_volume_name {
    echo "$1" | cut -f1 -d,
}

function get_volume_mount_point {
    echo "$1" | cut -f4 -d,
}

function get_volume_size_mode {
    echo "$1" | cut -f2 -d,
}

function get_volume_size {
    echo "$1" | cut -f3 -d,
}
