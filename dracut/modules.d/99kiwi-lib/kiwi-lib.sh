type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function setup_debug {
    if getargbool 0 rd.kiwi.debug; then
        local log=/run/initramfs/log
        mkdir -p ${log}
        exec >> ${log}/boot.kiwi
        exec 2>> ${log}/boot.kiwi
        set -x
    fi
}

function set_root_map {
    root_map=$1
    export root_map
}

function get_root_map {
    echo "${root_map}"
}

function get_mapped_multipath_disk {
    declare DEVICE_TIMEOUT=${DEVICE_TIMEOUT}
    local disk_device=$1
    local check=0
    local limit=30
    if [[ "${DEVICE_TIMEOUT}" =~ ^[0-9]+$ ]]; then
        limit=$(((DEVICE_TIMEOUT + 1)/ 2))
    fi
    udev_pending &>/dev/null
    while true;do
        for wwn in $(multipath -l -v1 "${disk_device}");do
            if [ -e "/dev/mapper/${wwn}" ];then
                echo "/dev/mapper/${wwn}"
                return
            fi
        done
        if [ "${check}" -eq "${limit}" ]; then
            die "Multipath map for ${disk_device} did not show up"
        fi
        check=$((check + 1))
        sleep 2
    done
}

function lookup_disk_device_from_root {
    declare root=${root}
    declare kiwi_RaidDev=${kiwi_RaidDev}
    declare kiwi_oemmultipath_scan=${kiwi_oemmultipath_scan}
    local root_device=${root#block:}
    local disk_device
    local wwn
    kiwi_oemmultipath_scan=$(bool "${kiwi_oemmultipath_scan}")
    if [ -z "${root_device}" ];then
        die "No root device found"
    fi
    if [ -L "${root_device}" ];then
        root_device=/dev/$(basename "$(readlink "${root_device}")")
    fi
    for disk_device in $(
        lsblk -p -n -r -s -o NAME,TYPE "${root_device}" |\
            grep -E "disk|raid" | cut -f1 -d ' '
    ); do
        # If multipath is requested, set the disk_device to the
        # multipath mapped device
        if [ "${kiwi_oemmultipath_scan}" = "true" ];then
            disk_device=$(get_mapped_multipath_disk "${disk_device}")
        fi
        # Check if root_device is managed by mdadm and that the md raid
        # is not created as part of the kiwi image building process. If
        # this is the case the md raid device comes from a fake raid
        # controller and we need to prefer the md device over the storage
        # disks
        if type mdadm &> /dev/null && [ -z "${kiwi_RaidDev}" ]; then
            if mdadm --detail -Y "${disk_device}" &>/dev/null; then
                echo "${disk_device}"
                return
            fi
        fi
    done
    echo "${disk_device}"
}

function udev_pending {
    declare DEVICE_TIMEOUT=${DEVICE_TIMEOUT}
    local limit=30
    if [[ "${DEVICE_TIMEOUT}" =~ ^[0-9]+$ ]]; then
        limit=$(((DEVICE_TIMEOUT + 1)/ 2))
    fi
    udevadm settle --timeout=${limit}
}

function get_persistent_device_from_unix_node {
    local unix_device=$1
    local schema=$2
    local node
    local persistent_name
    node=$(basename "${unix_device}")
    udev_pending
    for persistent_name in /dev/disk/"${schema}"/*; do
        if [ "$(basename "$(readlink "${persistent_name}")")" = "${node}" ];then
            echo "${persistent_name}"
            return
        fi
    done
    warn "Could not find ${schema} representation of ${node}"
    warn "Using original device ${unix_device}"
    echo "${unix_device}"
}

function deactivate_all_device_maps {
    dmsetup remove_all
}

function import_file {
    # """
    # import file with key=value format. the function
    # will export each entry of the file as variable into
    # the current shell environment
    # """
    local source_format=/tmp/source_file_formatted
    # create clean input, no empty lines and comments
    grep -v '^$' "$1" | grep -v '^[ \t]*#' > ${source_format}
    # remove start/stop quoting from values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=[\"']\(.*\)[\"']#\1=\2#" ${source_format}
    # remove backslash quotes if any
    sed -i -e s"#\\\\\(.\)#\1#g" ${source_format}
    # quote simple quotation marks
    sed -i -e s"#'\+#'\\\\''#g" ${source_format}
    # add '...' quoting to values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=\(.*\)#\1='\2'#" ${source_format}
    source ${source_format} &>/dev/null
    while read -r line;do
        local key
        key=$(echo "${line}" | cut -d '=' -f1)
        eval "export ${key}" &>/dev/null
    done < ${source_format}
}

function binsize_to_bytesize {
    # """
    # converts binary sizes (1024k, 2.4G) to bytes
    # uses awk to handle floating point numbers
    # """
    local sz="$1"
    local bs=${sz:0:-1}
    case ${sz} in
        *K|*k) mult=1024 ;;
        *M) mult=$((1024*1024)) ;;
        *G) mult=$((1024*1024*1024)) ;;
        *T) mult=$((1024*1024*1024*1024)) ;;
        *) bs=${sz}; mult=1 ;;
    esac
    awk "BEGIN {print int(${bs}*${mult})}"
}

function bool {
    # """
    # provides boolean string true|false for given value.
    # Only if value matches true return true, in any other
    # case return false
    # """
    local value=$1
    if [ -n "${value}" ] && [ "${value}" = "true" ] ;then
        echo "true"
    else
        echo "false"
    fi
}
