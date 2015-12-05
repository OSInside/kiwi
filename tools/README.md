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
