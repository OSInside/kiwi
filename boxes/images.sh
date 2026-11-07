#!/bin/bash

run_kiwi=/usr/local/bin/run_kiwi

tail -n +9 "$0" >"${run_kiwi}" && chmod 755 "${run_kiwi}"

exit $?
# The code of interest starts here
#!/bin/bash

set -x

function is_container {
    test -e /container.cmdline
}

if ! is_container; then
    exec &>/dev/console
fi

function get_cmdline_file {
    if is_container; then
        echo "/container.cmdline"
    else
        echo "/proc/cmdline"
    fi
}

function run_build {
    # """
    # Run kiwi and the bundler
    # """
    local options
    local logfile=/bundle/result.log
    local exit_code_file=/bundle/result.code
    local cmdline_file
    cmdline_file=$(get_cmdline_file)
    if type setenforce &>/dev/null; then
        # for SELinux managed systems the enforcing rule
        # set does not allow to e.g create a new rpm database.
        # Also other restrictions drives us crazy when building
        # images. Therefore in the boxes we don't need this
        # sort of security
        setenforce 0
    fi
    echo 1 > "${exit_code_file}"
    options=$(cut -f2 -d\" "${cmdline_file}")
    if is_container; then
        # directly create all target image files in the shared
        # volume path. Do not call the bundler later
        rm -rf /bundle/*
        options="${options} --description /description --target-dir /bundle"
    else
        # keep target files inside the VM because I/O between
        # guest and host is expensive. Call the bundler later
        rm -rf /result
        options="${options} --description /description --target-dir /result"
    fi
    export PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin
    # shellcheck disable=SC2086
    if kiwi-ng --logfile "${logfile}" ${options}; then
        echo 0 > "${exit_code_file}"
        if ! is_container; then
            kiwi-ng result bundle --id 0 --target-dir /result --bundle-dir /bundle
            echo $? > "${exit_code_file}"
        fi
    fi
}

function wait_network {
    # """
    # even though this program is called in a systemd unit that
    # requires the network-online target there could be a delay
    # in the network online status between the host and the guest.
    # This means the guest could be online while the host/guest
    # network negotiation is still not done.
    # """
    local sleep_timeout=2
    local retry_count=5
    local check=0
    echo "Waiting for link up on lan0..."
    while true;do
        if ip link ls lan0 | grep -qi "state UP"; then
            # interface link is up
            break
        fi
        if [ "${check}" -eq "${retry_count}" ];then
            # interface link did not came up
            exit 1
        fi
        echo "Waiting for link up on lan0..."
        check=$((check + 1))
        sleep "${sleep_timeout}"
    done
    if [ -e /run/systemd/resolve/stub-resolv.conf ];then
        ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    fi
}

function mount_shared_path {
    # """
    # mount shared host path identified by given mount tag
    # """
    local path=$1
    local tag=$2
    local ssh_host_path
    declare sharing_backend=${sharing_backend}
    declare host_kiwidescription=${host_kiwidescription}
    declare host_kiwibundle=${host_kiwibundle}
    declare host_custompath=${host_custompath}
    if mountpoint -q "${path}"; then
        return
    fi
    mkdir -p "${path}"
    if [ "${sharing_backend}" = "virtiofs" ];then
        mount -t virtiofs "${tag}" "${path}"
    elif [ "${sharing_backend}" = "sshfs" ];then
        # The kiwi boxbuild code forwards the host ssh port
        # here to port HOST_SSH_PORT_FORWARDED_TO_BOX(10000)
        if waitport 10000; then
            if [ "${tag}" = "kiwidescription" ];then
                ssh_host_path=${host_kiwidescription}
            fi
            if [ "${tag}" = "kiwibundle" ];then
                ssh_host_path=${host_kiwibundle}
            fi
            if [ "${tag}" = "custompath" ];then
                ssh_host_path=${host_custompath}
            fi
            # Without the box pubkey added to the authorized_keys
            # file on the host, the following call will be
            # interactively asking for credentials.
            while ! sshfs -p 10000 \
                -o "idmap=user" \
                -o "StrictHostKeyChecking=accept-new" \
            "${ssh_host_path}" "${path}"; do
                sleep 2
            done
        fi
    else
        mount -t 9p -o "trans=virtio,version=9p2000.L" "${tag}" "${path}"
    fi
}

function import_box_overlay_files {
    # """
    # Import optional boxroot overlay tree into box system
    # Also make sure there is .gnupg directory for the root
    # user created
    # """
    if [ -d /description/boxroot ];then
        rsync -zav /description/boxroot/ /
    fi
    # make sure it's possible to create a GPG keyring
    # used for apt repo keys as an example
    mkdir -p /root/.gnupg
    chmod 700 /root/.gnupg
}

function import_box_environment {
    # """
    # Import optional etc/boxprofile into runtime environment
    # """
    if [ -e /etc/boxprofile ];then
        # shellcheck disable=SC1091
        source /etc/boxprofile
    fi
}

function import_box_variables {
    # """
    # Box variables are those which uses the =_*_ notation
    # """
    # shellcheck disable=SC2002,SC2046
    eval export $(
        cat "$(get_cmdline_file)" | \
        tr " " "\n" | grep "=_" | sed -e "s@=_@=@" | sed -e "s@_\$@@"
    )
}

function import_ssh_pub_key {
    rm -f /run/nologin
    declare ssh_key=${ssh_key}
    declare ssh_key_type=${ssh_key_type}
    if [ -n "${ssh_key}" ];then
        mkdir -p /root/.ssh
        echo "${ssh_key_type} ${ssh_key}" >> /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
    fi
}

function waitport {
    # shellcheck disable=SC2086
    while ! nc -z localhost $1 ; do sleep 1 ; done
}

function install_kiwi_from_git {
    # """
    # Clone, build and install kiwi from the given git repository
    # and optional branch. The build and install steps follow the
    # instructions from package/python-kiwi-spec-template. KIWI
    # gets installed into a staging root first and is then synced
    # into the box system, replacing the box installed KIWI files.
    # """
    local source_dir=/var/tmp/kiwi-git
    local install_root=/var/tmp/kiwi-git-root
    local bindir
    local site_dir
    local staged_site_dir
    declare kiwi_git_repo=${kiwi_git_repo}
    declare kiwi_git_branch=${kiwi_git_branch}
    rm -rf "${source_dir}" "${install_root}"
    if [ -n "${kiwi_git_branch}" ]; then
        git clone --depth 1 --branch "${kiwi_git_branch}" \
            "${kiwi_git_repo}" "${source_dir}" || return 1
    else
        git clone --depth 1 \
            "${kiwi_git_repo}" "${source_dir}" || return 1
    fi
    pushd "${source_dir}" || return 1

    # Drop shebang for kiwi/xml_parse.py, as we don't intend to use it
    # as an independent script
    sed -e "s|#!/usr/bin/env python||" -i kiwi/xml_parse.py || return 1

    # Build application wheel
    python3 -m build --no-isolation --wheel || return 1

    # Install application
    python3 -m installer --destdir "${install_root}" dist/*.whl || return 1

    # Fix where files were installed. The default python install
    # scheme might point to a location which is not part of the
    # python search path, e.g. /usr/local on SUSE or the versioned
    # python path on Debian. Thus move the kiwi python modules to
    # the location of the box installed kiwi
    site_dir=$(
        cd / && python3 -I -c \
        'import os,kiwi; print(os.path.dirname(os.path.dirname(kiwi.__file__)))'
    ) || return 1
    staged_site_dir=$(
        dirname "$(find "${install_root}" -type d -path '*-packages/kiwi')"
    )
    if [ "${staged_site_dir}" != "${install_root}${site_dir}" ];then
        mkdir -p "${install_root}${site_dir}" || return 1
        mv "${staged_site_dir}"/* "${install_root}${site_dir}" || return 1
    fi

    # Install completion and kiwi default configuration
    # (make install, without the manual pages)
    install -d -m 755 \
        "${install_root}"/usr/share/bash-completion/completions || return 1
    install -m 644 completions/bash-completion \
        "${install_root}"/usr/share/bash-completion/completions/kiwi-ng || \
        return 1
    install -d -m 755 "${install_root}"/usr/share/kiwi/kiwi.yml.d || return 1
    install -d -m 755 "${install_root}"/etc/kiwi.yml.d || return 1
    install -m 644 kiwi.yml \
        "${install_root}"/usr/share/kiwi/kiwi.yml.example || return 1
    cp -a helper/xsl_to_v74 "${install_root}"/usr/share/kiwi/ || return 1

    # Install dracut modules
    make buildroot="${install_root}"/ python=python3 install_dracut || \
        return 1

    # Create symlinks for correct binaries. Depending on the python
    # install scheme of the distribution kiwi-ng was installed to
    # /usr/bin or /usr/local/bin, both are part of PATH
    for bindir in "${install_root}"/usr/bin "${install_root}"/usr/local/bin;do
        if [ -e "${bindir}/kiwi-ng" ];then
            ln -sfr "${bindir}/kiwi-ng" "${bindir}/kiwi" || return 1
            ln -sfr "${bindir}/kiwi-ng" "${bindir}/kiwi-ng-3" || return 1
        fi
    done
    popd || return 1

    # Delete the box installed kiwi python modules and metadata such
    # that no stale modules or entry points of the former version exist
    rm -rf "${site_dir}"/kiwi "${site_dir}"/kiwi-*-info || return 1

    # Sync into the box system, keep attributes of existing
    # directories and directory symlinks (merged /usr) as they are
    tar -C "${install_root}" -cf - . | \
        tar -C / -xf - --no-overwrite-dir --keep-directory-symlink
}

function finish {
    if ! grep -q kiwi-no-halt "$(get_cmdline_file)"; then
        if ! is_container; then
            halt -p
        else
            reboot -f
        fi
    fi
}

# main
declare custom_mount=${custom_mount}
declare kiwi_version=${kiwi_version}
declare kiwi_git_repo=${kiwi_git_repo}

trap finish EXIT

import_box_variables

import_ssh_pub_key

wait_network

if ! is_container; then
    if ! mount_shared_path "/description" "kiwidescription"; then
        exit 1
    fi

    if ! mount_shared_path "/bundle" "kiwibundle"; then
        exit 1
    fi

    if [ -n "${custom_mount}" ]; then
        if ! mount_shared_path "${custom_mount}" "custompath"; then
            exit 1
        fi
    fi
fi

import_box_overlay_files

import_box_environment

# Mark the build as failed until run_build reports otherwise, so a
# failed KIWI installation below is not reported as successful build
echo 1 > /bundle/result.code

if [ -n "${kiwi_version}" ]; then
    if ! pip3 install --break-system-packages kiwi=="${kiwi_version}"; then
        exit 1
    fi
elif [ -n "${kiwi_git_repo}" ]; then
    if ! install_kiwi_from_git; then
        exit 1
    fi
fi

run_build
