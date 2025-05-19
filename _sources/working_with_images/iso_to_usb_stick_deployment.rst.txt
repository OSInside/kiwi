.. _iso_to_usb_stick:

Deploy ISO Image on an USB Stick
================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with {kiwi} and references the following
   articles:

   * :ref:`hybrid_iso`

In {kiwi} all generated ISO images are created to be hybrid. This means,
the image can be used as a CD/DVD or as a disk. This works because
the ISO image also has a partition table embedded. With more and more
computers delivered without a CD/DVD drive this becomes important.

The very same ISO image can be copied onto a USB stick and used as a
bootable disk. The following procedure shows how to do this:

1. Plug in a USB stick

   Once plugged in, check which Unix device name the stick was assigned
   to. The following command provides an overview about all linux
   storage devices:

   .. code:: bash

      $ lsblk

2. Dump the ISO image on the USB stick:

   .. warning::

      Make sure the selected device really points to your stick because
      the following operation can not be revoked and will destroy all
      data on the selected device

   .. code:: bash

      $ dd if={exc_image_base_name}.x86_64-{exc_image_version}.iso of=/dev/<stickdevice>

3. Boot from your USB Stick

   Activate booting from USB in your BIOS/UEFI. As many firmware has different
   procedures on how to do it, look into your user manual.
   Many firmware offers a boot menu which can be activated at boot time.
