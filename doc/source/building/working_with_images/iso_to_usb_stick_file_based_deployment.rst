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
The ability to boot from the stick is configured through a SYSLINUX
feature which allows to loopback mount an ISO file and boot the
kernel and initrd directly from the ISO file.

The initrd loaded in this process must also be able to loopback
mount the ISO file to access the root filesystem and boot the
live system. The dracut initrd system used by KIWI provides this
feature upstream called as "iso-scan". Therefore all KIWI generated
live ISO images supports this deployment mode.

For copying the ISO file on the USB stick and the setup of the
SYSLINUX bootloader to make use of the "iso-scan" feature an extra tool
named `live-fat-stick` exists. The following procedure shows how
to setup the USB stick with `live-fat-stick`:

1. Install the `live-fat-stick` package:

   The package is available for openSUSE at:
   https://software.opensuse.org/package/live-fat-stick

2. Plug in a USB stick

   Once plugged in, check which Unix device name the FAT32 partition
   was assigned to. The following command provides an overview about all
   storage devices and their filesystems:

   .. code:: bash

      $ sudo lsblk --fs

3. Call the `live-fat-stick` command as follows:

   Assuming "/dev/sdz1" was the FAT32 partition selected from the
   output of the `lsblk` command:

   .. code:: bash

      $ sudo live-fat-stick LimeJeOS-Leap-42.3.x86_64-1.42.3.iso /dev/sdz1

4. Update the SYSLINUX configuration on the USB Stick

   By default, the SYSLINUX configuration does not use the "iso-scan"
   feature. Thus this information needs to be added as follows:

   1. Mount the FAT32 partition of the USB Stick. This must be the
      same device as used in the `live-fat-stick` command call:

      .. code:: bash

          $ sudo mount /dev/sdz1 /mnt

   #. Edit the file :file:`/mnt/boot/syslinux/syslinux.cfg` and include the
      following parameters to the existing **append** line:

      .. code:: bash

          iso-scan/filename=/LimeJeOS-Leap-42.3.x86_64-1.42.3.iso root=live:CDLABEL=CDROM

   #. Unmount the FAT32 partition:

      .. code:: bash

          $ sudo umount /mnt

5. Boot from your USB Stick

   Activate booting from USB in your BIOS/UEFI. As many firmware has different
   procedures on how to do it, look into your user manual.
   Many firmware offers a boot menu which can be activated at boot time.
   Usually this can be reached by pressing the :kbd:`Esc` or :kbd:`F12` keys.
