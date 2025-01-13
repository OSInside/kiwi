#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2006 SUSE LINUX Products GmbH. All rights reserved
#               :
# AUTHOR        : Marcus Schaefer <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#               :
#               :
# STATUS        : BETA
#----------------
declare kiwi_iname=${kiwi_iname}
declare kiwi_profiles=${kiwi_profiles}

#======================================
# Functions...
#--------------------------------------
# shellcheck disable=SC1091
test -f /.kconfig && . /.kconfig

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3

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
