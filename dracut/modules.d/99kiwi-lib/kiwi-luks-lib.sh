#!/bin/bash

# shellcheck disable=SC1091
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type set_root_map >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type wait_for_storage_device >/dev/null 2>&1 || . /lib/kiwi-partitions-lib.sh
type ask_for_password >/dev/null 2>&1 || . /lib/dracut-crypt-lib.sh
type run_progress_dialog >/dev/null 2>&1 || . /lib/kiwi-dialog-lib.sh

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

function reencrypt_luks {
    declare kiwi_RootPart=${kiwi_RootPart}
    local disk=$1
    local keyslot=/root/.luks.slot
    local header_checksum_origin=/root/.luks.header
    local header_checksum_cur=/root/.luks.header.cur
    local keyfile=/root/.root.keyfile
    local new_keyfile=/run/.kiwi_reencrypt.keyfile
    local passphrase_file=/root/.slotpass
    local progress=/dev/install_progress
    local load_text="Reencrypting..."
    local title_text="LUKS"
    local device
    device=$(get_partition_node_name "${disk}" "${kiwi_RootPart}")
    read -r header_checksum_origin < "${header_checksum_origin}"
    read -r keyslot < "${keyslot}"

    # Checksum test if luks header is still the image origin header
    cryptsetup luksHeaderBackup \
        "${device}" --header-backup-file "${header_checksum_cur}"
    header_checksum_cur=$(
        sha256sum "${header_checksum_cur}" |\
        cut -f1 -d" "; rm -f "${header_checksum_cur}"
    )
    if [ "${header_checksum_origin}" == "${header_checksum_cur}" ];then
        if getargbool 0 rd.kiwi.oem.luks.reencrypt_randompass; then
            # reset insecure built time passphrase with a random
            # onetime passphrase that will be stored in memory at $new_keyfile
            # This action require that the boot process uses $new_keyfile
            # and sets a retrievable keyfile information for subsequent
            # boot processes of this system
            (umask 077; touch "${new_keyfile}")
            tr -dc '[:graph:]' 2>/dev/null < /dev/urandom |\
                head -c 32 > "${new_keyfile}"
            chmod 0400 "${new_keyfile}"
            cryptsetup \
                --key-file "${passphrase_file}" \
                --key-slot "${keyslot}" \
            luksChangeKey "${device}" "${new_keyfile}"
            cp "${new_keyfile}" "${passphrase_file}"
            if [ -e "${keyfile}" ]; then
                # if there is a keyfile it's referenced in the crypttab
                # of this initrd instance in memory. Make sure all subsequent
                # tasks e.g. luks resize have permissions to complete while
                # inside of this initrd instance
                cp "${new_keyfile}" "${keyfile}"
            fi
        fi
        # reencrypt
        setup_progress_fifo ${progress}
        (
            # reencrypt, this will overwrite all key slots
            cryptsetup reencrypt \
                --progress-frequency 1 \
                --key-file "${passphrase_file}" \
                --key-slot "${keyslot}" \
            "${device}" 2>&1 | sed -u 's/.* \([0-9]*\)[0-9.]*%.*/\1/'
        ) >"${progress}" &
        run_progress_dialog "${load_text}" "${title_text}"
        if [ -e "${keyfile}" ] && [ ! -e "${new_keyfile}" ];then
            # re-add keyfile if present and no other keyfile was created
            cryptsetup --key-file "${passphrase_file}" luksAddKey \
                "${device}" "${keyfile}"
        fi
    fi
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
        systemctl start systemd-cryptsetup@luks
    fi
    wait_for_storage_device "/dev/mapper/luks"
    set_root_map "/dev/mapper/luks"
}
