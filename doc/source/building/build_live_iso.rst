.. _hybrid_iso:

Build an ISO Hybrid Live Image
==============================

.. sidebar:: Abstract

   This page explains how to build a live image. It contains:

   * how to build an ISO image
   * how to start it with QEMU
   * how to dump the resulting ISO image on an USB stick

In KIWI all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. This works because
the ISO image also has a partition table embedded. With more and more
computers delivered without a CD/DVD drive this becomes important.

The very same ISO image can be copied onto a USB stick and used as a
bootable disk.

The following example shows how to build a live ISO image based on
openSUSE Leap:

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Build the image with KIWI:

   .. code:: bash

      $ sudo kiwi-ng --type iso system build \
           --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
           --target-dir /tmp/myimage

   Find the image with the suffix :file:`.iso` below :file:`/tmp/myimage`.

3. Test the live image with QEMU:

   .. code:: bash

      $ qemu -cdrom LimeJeOS-Leap-42.1.x86_64-1.42.1.iso -m 4096

4. Plug in a USB stick

   Once plugged in, check which Unix device name the stick was assigned
   to. The following command provides an overview about all linux
   storage devices:

   .. code:: bash

      $ lsblk

5. Dump the ISO image on the USB stick:

   .. warning::

      Make sure the selected device really points to your stick because
      the following operation can not be revoked and will destroy all
      data on the selected device

   .. code:: bash

      $ dd if=LimeJeOS-Leap-42.1.x86_64-1.42.1.iso of=/dev/<stickdevice>

6. Start system from USB stick

   Like in the example above use QEMU to start the system, but attach
   the USB stick device as the system disk as follows:

   .. code:: bash

      $ qemu -hda /dev/<stickdevice> -m 4096
