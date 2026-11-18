#!/bin/bash
# root=overlay:* was converted into a root=block:/dev/... node
# shellcheck disable=SC1091
type setup_debug >/dev/null 2>&1 || . /lib/kiwi-lib.sh
type getOverlayBaseDirectory >/dev/null 2>&1 || . /lib/kiwi-filesystem-lib.sh

#======================================
# functions
#--------------------------------------
function loadKernelModules {
    modprobe squashfs
}

function initGlobalDevices {
    local nbd_host
    local nbd_export
    if [ -z "$1" ]; then
        die "No root device for operation given"
    fi
    write_partition=$(getarg rd.root.overlay.write=)
    if [[ "${root_cmdline}" =~ "overlay:nbd=" ]];then
        nbd_host=$(echo "${root_cmdline}" | cut -f2 -d= | cut -f1 -d:)
        nbd_export=$(echo "${root_cmdline}" | cut -f3 -d:)
        read_only_partition="/dev/nbd0"
        if ! nbd-client \
            "${nbd_host}" "${read_only_partition}" -name "${nbd_export}"
        then
            die "Failed to setup nbd client for ${root_cmdline}"
        fi
    elif [[ "${root_cmdline}" =~ "overlay:aoe=" ]];then
        read_only_partition="/dev/etherd/$(echo "${root_cmdline}"|cut -f2 -d=)"
    else
        read_only_partition="$1"
    fi
}

function mountReadOnlyRootImage {
    local overlay_base
    local unit_name
    overlay_base=$(getOverlayBaseDirectory)
    local root_mount_point="${overlay_base}/rootfsbase"
    mkdir -m 0755 -p "${root_mount_point}"
    unit_name=$(echo "${root_mount_point}" | cut -c 2- | tr / -)
    cat >/run/systemd/system/"${unit_name}".mount <<-EOF
		[Unit]
		Before=initrd-root-fs.target
		After=run-overlay.mount
		DefaultDependencies=no
		[Mount]
		Where=$root_mount_point
		What=$read_only_partition
		Type=auto
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
	EOF
    if ! systemctl start "${unit_name}".mount;then
        die "Failed to mount overlay(ro) root filesystem"
    fi
    echo "${root_mount_point}"
}

function setupOverlaySELinuxRelabel {
    # The SELinux policy is loaded after switch-root, so everything
    # created in the tmpfs upper layer before has no valid label.
    # Add a service which relabels it early in the booted system
    local upper=$1
    local unit_dir=/run/systemd/system
    local unit_name=kiwi-overlay-selinux-relabel.service
    local service="${unit_dir}/${unit_name}"
    cat >"${service}" <<-EOF
		[Unit]
		Description=Restore SELinux labels of the overlayroot upper layer
		DefaultDependencies=no
		ConditionSecurity=selinux
		ConditionPathExists=!/etc/initrd-release
		After=systemd-remount-fs.service
		Before=local-fs-pre.target sysinit.target
		Before=systemd-tmpfiles-setup.service systemd-journal-flush.service
		Before=systemd-sysusers.service systemd-firstboot.service
		Before=systemd-random-seed.service systemd-udevd.service
		Before=systemd-sysctl.service
		[Service]
		Type=oneshot
		RemainAfterExit=yes
		ExecStartPre=test -d ${upper}
		ExecStart=sh -c 'cd ${upper} && find . -xdev -print0 | (cd / && xargs -0 restorecon -i -F)'
	EOF
    mkdir -p "${unit_dir}/sysinit.target.wants"
    ln -sf "${service}" "${unit_dir}/sysinit.target.wants/${unit_name}"
    info "Added ${unit_name} to restore SELinux labels of ${upper}"
}

function prepareTemporaryOverlay {
    local overlay_base
    overlay_base=$(getOverlayBaseDirectory)
    mkdir -m 0755 -p "${overlay_base}/overlayfs/rw"
    mkdir -m 0755 -p "${overlay_base}/overlayfs/work"
    # a read-only root does not use the upper layer
    if ! getargbool 0 rd.root.overlay.readonly; then
        setupOverlaySELinuxRelabel "${overlay_base}/overlayfs/rw"
    fi
}

function preparePersistentOverlay {
    local overlay_base
    local unit_name
    overlay_base=$(getOverlayBaseDirectory)
    local overlay_mount_point="${overlay_base}/overlayfs"
    mkdir -m 0755 -p "${overlay_mount_point}"
    unit_name=$(echo "${overlay_mount_point}" | cut -c 2- | tr / -)
    cat >/run/systemd/system/"${unit_name}".mount <<-EOF
		[Unit]
		Before=initrd-root-fs.target
		After=run-overlay.mount
		DefaultDependencies=no
		[Mount]
		Where=$overlay_mount_point
		What=$write_partition
		Type=auto
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
	EOF
    if ! systemctl start "${unit_name}".mount; then
        die "Failed to mount overlay(rw) filesystem"
    fi
    mkdir -m 0755 -p "${overlay_mount_point}/rw"
    mkdir -m 0755 -p "${overlay_mount_point}/work"
}

#======================================
# perform root access preparation
#--------------------------------------
PATH=/usr/sbin:/usr/bin:/sbin:/bin

declare root=${root}
declare root_cmdline

root_cmdline=$(getarg root=)

# only run if overlay is requested
if [[ ! "${root_cmdline}" =~ "overlay:" ]];then
    return 0
fi

# init debug log file if wanted
setup_debug

# device nodes and types
initGlobalDevices "${root#block:}"

# load required kernel modules
loadKernelModules

# mount readonly root filesystem
mountReadOnlyRootImage

if [ -z "${write_partition}" ] || getargbool 0 rd.root.overlay.temporary; then
    prepareTemporaryOverlay
else
    preparePersistentOverlay
fi

need_shutdown

return 0
