type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type set_root_map >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type wait_for_storage_device >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh
type ask_for_password >/dev/null 2>&1 || . /lib/dracut-crypt-lib.sh

function luks_system {
    declare kiwi_RootPart=${kiwi_RootPart}
    local disk=$1
    local device
    device=$(get_partition_node_name "${disk}" "${kiwi_RootPart}")
    if cryptsetup isLuks "${device}" &>/dev/null;then
        return 0
    fi
    return 1
}

function deactivate_luks {
    /usr/lib/systemd/systemd-cryptsetup detach luks
}

function resize_luks {
    cryptsetup resize luks
}

function activate_luks {
    declare kiwi_luks_empty_passphrase=${kiwi_luks_empty_passphrase}
    local device=$1
    if [ "${kiwi_luks_empty_passphrase}" = "true" ];then
        # There is no keyfile and kiwi has created the luks pool with
        # an empty key. Therefore it can be opened without interaction
        # but this requires to manually call luksOpen since
        # with systemd-cryptsetup we saw it still asking for
        # a passphrase
        cryptsetup \
            --key-file /dev/zero \
            --keyfile-size 32 \
        luksOpen "${device}" luks
    else
        # There is a keyfile and we need to get prompted to enter the passphrase
        /usr/lib/systemd/systemd-cryptsetup attach luks "${device}"
    fi
    wait_for_storage_device "/dev/mapper/luks"
    set_root_map "/dev/mapper/luks"
}
