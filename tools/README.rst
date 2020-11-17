KIWI - tools
============

this directory contains helper scripts and programs around
the kiwi image technology. If you need them in your image
just set the package kiwi-tools in your config.xml file

* /usr/bin/utimer
  run a timer process like the kernel

* /usr/bin/dcounter
  a small program to count bytes on a transfer so that you
  can show a progress information about the transfer

* /usr/bin/isconsole
  a small program sending the KDGETMODE ioctl to /dev/console
  in order to check if we can fbiterm on that console
