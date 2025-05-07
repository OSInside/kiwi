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

#======================================
# Include erofs module
#--------------------------------------
# remove from blacklist
rm -f /usr/lib/modprobe.d/60-blacklist_fs-erofs.conf

#======================================
# Include systemd-verity to initrd
#--------------------------------------
# for some reason dracut doesn't automatically pick up
# the needed systemd veritysetup generator and tools
# and also the kiwi written /etc/veritytab is not added
# automatically. Thus we do this programatically here.
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "verity" ]; then
        cat >/etc/dracut.conf.d/verity.conf <<- EOF
			dracutmodules+=" systemd-veritysetup "
			install_items+=" /etc/veritytab "
		EOF
    fi
done
