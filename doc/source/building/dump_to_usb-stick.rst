.. _dump_usb_stick:

Dumping an Image to an USB Stick
================================


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

      $ dd if=LimeJeOS-Leap-42.1.x86_64-1.42.1.iso of=/dev/<stickdevice>

3. Boot from your USB Stick

   Activate booting from USB in your BIOS/UEFI. As many firmware has different
   procedures on how to do it, look into your user manual.
   Many firmware offers a boot menu which can be activated at boot time.
