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

function set_swap_map {
    swap_map=$1
    export swap_map
}

function get_root_map {
    echo "${root_map}"
}

function get_swap_map {
    echo "${swap_map}"
}

function lookup_disk_device_from_root {
    declare root=${root}
    local root_device=${root#block:}
    local disk_device
    local disk_matches=0
    local wwn
    if [ -z "${root_device}" ];then
        die "No root device found"
    fi
    if [ -L "${root_device}" ];then
        root_device=/dev/$(basename "$(readlink "${root_device}")")
    fi
    for disk_device in $(
        lsblk -p -n -r -s -o NAME,TYPE "${root_device}" |\
            grep disk | cut -f1 -d ' '
    ); do
        disk_matches=$((disk_matches + 1))
    done
    # Check if root_device is managed by multipath. If this
    # is the case prefer the multipath mapped device because
    # directly accessing the mapped devices is no longer
    # possible
    if type multipath &> /dev/null; then
        for wwn in $(multipath -l -v1 "${disk_device}");do
            if [ -e "/dev/mapper/${wwn}" ];then
                disk_device="/dev/mapper/${wwn}"
                break
            fi
        done
    fi
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
