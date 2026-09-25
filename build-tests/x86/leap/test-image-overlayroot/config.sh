#!/bin/bash
set -ex

declare kiwi_profiles=${kiwi_profiles}

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

# for some reason systemd automount unit wants to mount the
# ESP to /efi instead of /boot/efi.
mkdir -p /efi

#======================================
# kernel links
#--------------------------------------
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "grub_verity_erofs" ]; then
        # For image tests with an extra boot partition the
        # kernel must not be a symlink to another area of
        # the filesystem. Latest changes on SUSE changed the
        # layout of the kernel which breaks every image with
        # an extra boot partition
        #
        # All of the following is more than a hack and I
        # don't like it all
        #
        # Complains and discussions about this please with
        # the SUSE kernel team as we in kiwi can just live
        # with the consequences of this change
        #
        pushd /

        for file in /boot/* /boot/.*; do
            if [ -L "${file}" ];then
                link_target=$(readlink "${file}")
                if [[ ${link_target} =~ usr/lib/modules ]];then
                    mv "${link_target}" "${file}"
                fi
            fi
        done
    fi
    if [ "${profile}" = "sdboot_uki_verity_erofs" ];then
        # systemd remount doesn't like overlays on read-only (/)
        systemctl mask systemd-remount-fs.service

        # following directories are created by services and must
        # exist prior read-only
        mkdir -p /var/lib/private/systemd/timesync
        mkdir -p /var/lib/systemd/timesync
        mkdir -p /var/lib/systemd/linger
        mkdir -p /etc/lvm/devices

        # ssh host keys must exist prior read-only
        /usr/sbin/sshd-gen-keys-start

        # we want home on the persistent storage if present
        cat >/usr/lib/systemd/system/home.mount <<-EOF
		[Unit]
		DefaultDependencies=no
		[Mount]
		Where=/home
		Options=lowerdir=/run/overlay/rootfsbase/home,upperdir=/run/overlay/overlayfs/home/rw,workdir=/run/overlay/overlayfs/home/work
		What=overlay
		Type=overlay
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
		EOF
        systemctl enable home.mount

        # we want root home to be 128M in memory
        cat >/usr/lib/systemd/system/run-overlay-overlayfs-root.mount <<-EOF
		[Unit]
		DefaultDependencies=no
		[Mount]
		Where=/run/overlay/overlayfs/root
		What=tmpfs
		Options=size=128M
		Type=tmpfs
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
		EOF
        cat >/usr/lib/systemd/system/root.mount <<-EOF
		[Unit]
		DefaultDependencies=no
		Requires=run-overlay-overlayfs-root.mount
        After=run-overlay-overlayfs-root.mount
		[Mount]
		Where=/root
		Options=lowerdir=/run/overlay/rootfsbase/root,upperdir=/run/overlay/overlayfs/root/rw,workdir=/run/overlay/overlayfs/root/work
		What=overlay
		Type=overlay
		DirectoryMode=0755
		[Install]
		WantedBy=multi-user.target
		EOF
        systemctl enable run-overlay-overlayfs-root.mount
        systemctl enable root.mount

        # required write areas on a read-only (/)
        for target in \
            etc/lvm/devices \
            tmp \
            var/tmp \
            var/log \
            var/lib/private/systemd/timesync \
            var/lib/systemd/timesync \
            var/lib/systemd/linger;
        do
            name=$(echo "${target}" | tr / -)
            cat >/usr/lib/systemd/system/"${name}".mount <<-EOF
			[Unit]
			DefaultDependencies=no
			[Mount]
			Where=/${target}
			What=tmpfs
			Type=tmpfs
			DirectoryMode=0755
			[Install]
			WantedBy=multi-user.target
			EOF
            systemctl enable "${name}".mount
        done
    fi
done

#======================================
# Include erofs module
#--------------------------------------
# remove from blacklist
rm -f /usr/lib/modprobe.d/60-blacklist_fs-erofs.conf
