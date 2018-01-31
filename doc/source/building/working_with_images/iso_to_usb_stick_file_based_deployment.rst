.. _iso_as_file_to_usb_stick:

Deploy ISO Image as File on a FAT32 Formated USB Stick
======================================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with KIWI and references the following
   articles:

   * :ref:`hybrid_iso`

In KIWI, all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. The deployment of such
an image onto a disk like an USB stick normally destroys all existing
data on this device. Most USB sticks are pre-formatted with a FAT32
Windows File System and to keep the existing data on the stick untouched
a different deployment needs to be used.

The following deployment process copies the ISO image as an
additional file to the USB stick and makes the USB stick bootable.
The ability to boot from the stick is configured through a GRUB v2
feature which allows to loopback mount an ISO file and boot the
kernel and initrd directly from the ISO file.

The initrd loaded in this process must also be able to loopback
mount the ISO file to access the root filesystem and boot the
live system. The dracut initrd system used by KIWI provides this
feature upstream called as "iso-scan". Therefore all KIWI generated
live ISO images supports this deployment mode.

For copying the ISO file on the USB stick and the setup of the
GRUB v2 bootloader to make use of the "iso-scan" feature an extra tool
named `live-fat-stick` exists. The following procedure shows how
to setup the USB stick with `live-fat-stick`:

1. Install the `live-fat-stick` package:

   The package is available for openSUSE at:
   https://software.opensuse.org/package/live-fat-stick

2. Plug in a USB stick

   Once plugged in, check which Unix device name the stick was assigned
   to. The following command provides an overview about all Linux
   storage devices:

   .. code:: bash

      $ lsblk

3. Call the `live-fat-stick` command as follows:

   .. code:: bash

      $ live-fat-stick LimeJeOS-Leap-42.3.x86_64-1.42.3.iso /dev/<stickdevice>

4. Boot from your USB Stick

   Activate booting from USB in your BIOS/UEFI. As many firmware has different
   procedures on how to do it, look into your user manual.
   Many firmware offers a boot menu which can be activated at boot time.
   Usually this can be reached by :kbd:`Esc` or :kbd:`F12`.
