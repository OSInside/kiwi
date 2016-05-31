# KIWI - tools

this directory contains helper scripts and programs around
the kiwi image technology. If you need them in your image
just set the package kiwi-tools in your config.xml file

* /usr/bin/startshell

  small tool to run a shell on a specified console. Most often
  used in initrd images for providing shell access while init
  is not called

* /usr/bin/setctsid

  set controlling terminal in rescue shell for systems without
  systemd

* /usr/bin/utimer

  run a timer process like the kernel

* /usr/bin/kversion

  extract kernel version information from kernel image

* /usr/bin/driveready

  small tool to check the sense code of a CD/DVD drive. The tool
  can be used to wait for the drive to be ready for mounting

* /usr/bin/dcounter

  a small program to count bytes on a transfer so that you
  can show a progress information about the transfer

* /usr/bin/isconsole

  a small program sending the KDGETMODE ioctl to /dev/console
  in order to check if we can fbiterm on that console

* /usr/bin/livestick

  a script to create a livestick from a kiwi generated iso image.
  The advantage of livestick compared to a simple dd of the iso
  to the stick is, that livestick preserves the data on the stick
  and does not destroy existing infrastructure. livestick is installed
  as part of the kiwi main package and is not part of the
  kiwi-tools package

* /usr/bin/kiwicompat

  Allows to call kiwi using the commandline syntax of the
  kiwi v7 version
