.. _grub_boot_from_iso:

Booting Live ISO Images from Grub2
====================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with {kiwi} and references the following
   articles:

   * :ref:`hybrid_iso`

In {kiwi}, all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. This works because
the ISO image also has a partition table embedded. With more and more
computers delivered without a CD/DVD drive, this becomes important.

Writing this image to a USB stick will permanently erase all existing
data on the device. Additionally, the stick will no longer be usable for
general data storage. Most USB sticks are pre-formatted with a
FAT32 or exFAT Windows filesystem, and to keep the existing data.

Fortunately, Grub2 supports booting directly from ISO files. It does not matter
whether it is installed on your computer's hard drive or on a USB stick.
The following deployment process copies the ISO image as an additional file
to the USB stick or hard drive. The ability to boot from the disk is configured
through a Grub2 feature that allows you to loopback mount an ISO file and boot the
kernel and initrd directly from the ISO file.

The initrd loaded in this process must also be able to loopback
mount the ISO file to access the root filesystem and boot the
live system. FAT32 is widely supported on USB sticks.
For hard drives, any filesystem supported by grub is also appropriate.

The dracut initrd system used by {kiwi} provides this
feature upstream, called "iso-scan/filename". Therefore, all {kiwi}-generated
live ISO images support this deployment mode.

The following procedure expects an existing Grub2 installation on your
hard drive or USB stick.

1. Copy the ISO image to a folder of your choice on your hard drive.
   For example, create a folder called "iso" in the
   root of your hard drive and copy the ISO image there:

   .. code:: bash

      sudo mkdir /iso
      sudo cp some-kiwi-live.iso /iso/

2. Look up the root filesystem UUID of your current operating system.
   Get this information by running the command:

   .. code:: bash

      findmnt -n -o UUID /

3. Add the following submenu setup to the :file:`grub.cfg` file:

   .. note::

      Verify that the path to the ISO image is correct. Set
      your own menu name. The drive identification for Grub2 can be
      checked at boot time by pressing the 'c' key and typing 'ls'.
      The following example assumes a live ISO image for the x86_64
      architecture. Adjust the paths to kernel and initrd if you
      have a different architecture.

   .. code:: bash

      menuentry "Boot from Live ISO" {
          load_video
          set gfxpayload=keep
          insmod gzio
          insmod part_gpt
          insmod iso9660
          insmod btrfs
          insmod ext2
          insmod xfs
          insmod lvm
          insmod loopback
          search --no-floppy --fs-uuid --set=root UUID_FROM_STEP_2
          set isofile="/iso/some-kiwi-live.iso"
          set kernel="(loop)/boot/x86_64/loader/linux"
          set initrd="(loop)/boot/x86_64/loader/initrd"
          set options="rd.live.image root=live:CDLABEL=CDROM"
          loopback loop $isofile
          linux $kernel iso-scan/filename=$isofile $options
          initrd $initrd
      }

4. Restart your computer and select the added menu entry.

.. note::

   For USB sticks, the procedure is identical. You would install
   Grub2 on the USB drive and follow the steps above. However, it is
   uncommon to have Grub2 already installed on a USB stick. To simplify
   the setup, there are good helper tools such as `MultiOS-USB`.
