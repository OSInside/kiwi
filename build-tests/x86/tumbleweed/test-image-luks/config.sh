#!/bin/bash
set -ex

declare kiwi_profiles=${kiwi_profiles}

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

#==========================================
# remove package docs
#------------------------------------------
rm -rf /usr/share/doc/packages/*
rm -rf /usr/share/doc/manual/*

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
for profile in ${kiwi_profiles//,/ }; do
    if [ "${profile}" = "ReEncryptExtraBootEmptyPass" ] || [ "${profile}" = "ReEncryptExtraBootWithPass" ]; then
        pushd /

        for file in /boot/* /boot/.*; do
            if [ -L "${file}" ];then
                link_target=$(readlink "${file}")
                if [[ "${link_target}" =~ usr/lib/modules ]];then
                    mv "${link_target}" "${file}"
                fi
            fi
        done
    fi
done
