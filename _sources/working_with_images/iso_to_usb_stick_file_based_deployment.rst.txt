.. _iso_as_file_to_usb_stick:

Deploy ISO Image as a File on a FAT32 Formatted USB Stick
=========================================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with {kiwi} and references the following
   articles:

   * :ref:`hybrid_iso`

In {kiwi}, all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. The deployment of such
an image onto a disk like a USB stick normally destroys all existing
data on this device. Most USB sticks are pre-formatted with a FAT32
Windows filesystem, and to keep the existing data on the stick untouched,
a different deployment needs to be used.

The following deployment process copies the ISO image as an
additional file to the USB stick and makes the USB stick bootable.
The ability to boot from the stick is configured through a SYSLINUX
feature that allows you to loopback mount an ISO file and boot the
kernel and initrd directly from the ISO file.

The initrd loaded in this process must also be able to loopback
mount the ISO file to access the root filesystem and boot the
live system. The dracut initrd system used by {kiwi} provides this
feature upstream, called "iso-scan". Therefore, all {kiwi}-generated
live ISO images support this deployment mode.

For copying the ISO file to the USB stick and the setup of the
SYSLINUX bootloader to make use of the "iso-scan" feature, an extra tool
named `live-grub-stick` exists. The following procedure shows how
to set up the USB stick with `live-grub-stick`:

1. Install the `live-grub-stick` package from software.opensuse.org.

2. Plug in a USB stick.

   Once plugged in, check which Unix device name the FAT32 partition
   was assigned to. The following command provides an overview of all
   storage devices and their filesystems:

   .. code:: bash

      $ sudo lsblk --fs

3. Call the `live-grub-stick` command as follows:

   Assuming "/dev/sdz1" was the FAT32 partition selected from the
   output of the `lsblk` command:

   .. code:: bash

      $ sudo live-grub-stick {exc_image_base_name}.x86_64-{exc_image_version}.iso /dev/sdz1

4. Boot from your USB Stick.

   Activate booting from USB in your BIOS/UEFI. As many firmwares have different
   procedures on how to do it, look into your user manual.
   EFI booting from an ISO image is not supported at the moment. For EFI booting,
   use the --isohybrid option with live-grub-stick; however, note that all the data
   on the stick will be lost.
   Many firmwares offer a boot menu that can be activated at boot time.
   Usually, this can be reached by pressing the :kbd:`Esc` or :kbd:`F12` keys.
