.. _grub_boot_from_iso:

Booting a Live ISO Images from Grub2
====================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with {kiwi} and references the following
   articles:

   * :ref:`hybrid_iso`

In {kiwi}, all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. This works because
the ISO image also has a partition table embedded. With more and more
computers delivered without a CD/DVD drive this becomes important.
The deployment of such an image onto a disk like an USB stick normally 
destroys all existing data on this device. It is also not possible to use 
USB stick as a data storage device. Most USB sticks are pre-formatted 
with a FAT32 or exFAT Windows File System and to keep the existing data 
on the stick untouched a different deployment needs to be used.

Fortunately Grub2 supports booting directly from ISO files. It does not matter 
whether it is installed on your computer's hard drive or on a USB stick.
The following deployment process copies the ISO image as an additional file 
to the USB stick or hard drive. The ability to boot from the disk is configured 
through a Grub2 feature which allows to loopback mount an ISO file and boot the
kernel and initrd directly from the ISO file.

The initrd loaded in this process must also be able to loopback
mount the ISO file to access the root filesystem and boot the
live system. Almost every Linux distribution supports fat32, 
and more and more of them also support exFAT. For hard drives, 
Linux filesystems are also supported.

The dracut initrd system used by {kiwi} provides this
feature upstream called as "iso-scan/filename". Therefore all {kiwi} generated
live ISO images supports this deployment mode.

The following procedure shows how to setup Grub2 on your hard drive:

1. Copy the ISO image to a folder of your choice on your hard drive.

2. Add the following code to the "grub.cfg" file:

   Be sure to set the path to the ISO image, you can set your own menu name.
   The drive identification for Grub2 can be checked at boot time 
   by pressing the 'c' key and typing 'ls'.

   .. code:: bash

      submenu "Boot from openSUSE ISO" {
	   iso_path="(hd0,gpt2)/path/to/openSUSE.iso"
	   export iso_path
	   loopback loop "$iso_path"
	   root=(loop)
	   source /boot/grub2/loopback.cfg
	   loopback --delete loop
      }

3. Restart your computer and select the added menu.

For USB sticks, the procedure is identical. You would then install 
Grub2 on the USB drive and follow the steps above. 
The use of scripts such as "MultiOS-USB" is strongly recommended.
