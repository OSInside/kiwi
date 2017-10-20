#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : openSUSE KIWI Image System
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
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Keep UTF-8 locale
#--------------------------------------
baseStripLocales \
    $(for i in $(echo $kiwi_language | tr "," " ");do echo -n "$i.utf8 ";done)
baseStripTranslations kiwi.mo

#======================================
# Umount kernel filesystems
#--------------------------------------
baseCleanMount

exit 0
