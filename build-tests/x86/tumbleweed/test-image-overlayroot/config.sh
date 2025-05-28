#!/bin/bash
set -ex

declare kiwi_iname=${kiwi_iname}
declare kiwi_profiles=${kiwi_profiles}

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

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
            if [ -L ${file} ];then
                link_target=$(readlink ${file})
                if [[ ${link_target} =~ usr/lib/modules ]];then
                    mv ${link_target} ${file}
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

		cat >/etc/fstab.append <<- EOF
		# we want home on the persistent storage if present
		overlay /home overlay defaults,lowerdir=/run/overlay/rootfsbase/home,upperdir=/run/overlay/overlayfs/home/rw,workdir=/run/overlay/overlayfs/home/work  0  0

		# we want root home to be 128M in memory
		tmpfs /run/overlay/overlayfs/root tmpfs defaults,size=128M 0 0
		overlay /root overlay defaults,x-systemd.required-by=run-overlay-overlayfs-root.mount,lowerdir=/run/overlay/rootfsbase/root,upperdir=/run/overlay/overlayfs/root/rw,workdir=/run/overlay/overlayfs/root/work  0  0

		# required write areas on a read-only (/)
		tmpfs /etc/lvm/devices tmpfs defaults 0 0
		tmpfs /tmp tmpfs defaults 0 0
		tmpfs /var/tmp tmpfs defaults 0 0
		tmpfs /var/log tmpfs defaults 0 0
		tmpfs /var/lib/private/systemd/timesync tmpfs defaults 0 0
		tmpfs /var/lib/systemd/timesync tmpfs defaults 0 0
		tmpfs /var/lib/systemd/linger tmpfs defaults 0 0
		EOF
    fi
done

#======================================
# Include erofs module
#--------------------------------------
# remove from blacklist
rm -f /usr/lib/modprobe.d/60-blacklist_fs-erofs.conf
