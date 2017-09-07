#!/bin/bash
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

#==========================================
# delete unnneded files and directories
#------------------------------------------
rm -rf /usr/lib/python*
rm -rf /usr/src
rm -rf /usr/share/X11
rm -rf /usr/share/man
rm -rf /usr/share/zoneinfo
rm -rf /usr/lib/syslinux
rm -rf /usr/share/fonts/truetype
rm -rf /usr/share/mime
rm -rf /usr/share/doc
rm -rf /lib/lsb
rm -rf /lib/crda
rm -rf /var/lib/apt
rm -rf /var/lib/dpkg
rm -rf /usr/share/icons

mv /usr/share/locale /tmp
mv /usr/share/grub* /tmp
rm -rf /usr/share/*
mv /tmp/locale /usr/share/
mv /tmp/grub* /usr/share/

#======================================
# Umount kernel filesystems
#--------------------------------------
baseCleanMount

exit 0
