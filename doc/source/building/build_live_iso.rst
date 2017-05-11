Build an ISO Hybrid Live Image
==============================

.. hint::

   Make sure you have checked out the example image descriptions
   For details see :ref:`example-descriptions`

The following example shows how to build a live system image
based on SUSE Leap

.. code:: bash

    $ sudo kiwi-ng --type iso system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.iso` below :file:`/tmp/myimage`.
For testing the live system a virtual machine with the iso image attached
as CD/DVD device can be used. The following example shows how to use the
Qemu system to run the image:

.. code:: bash

    $ qemu -cdrom LimeJeOS-Leap-42.1.x86_64-1.42.1.iso -m 4096

.. _hybrid_iso:

Use Live System from USB Stick
------------------------------

In KIWI all generated iso images are created to be hybrid. This means
the image can be used as a CD/DVD or as a disk. This works because
the iso image also has a partition table embedded. With more and more
computers delivered without a CD/DVD drive this becomes important.

As a used the very same iso image can be copied onto a USB stick
and used as a bootable disk. Thus in order to use the above live
system from stick do the following:

1. Plug in a USB stick

   Once plugged in, check which Unix device name the stick was assigned
   to. The following command provides an overview about all linux
   storage devices:

   .. code:: bash

      $ lsblk

2. Dump iso image on the stick

   .. warning::

      Make sure the selected device really points to your stick because
      the following operation can not be revoked and will destroy all
      data on the selected device

   .. code:: bash

      $ dd if=LimeJeOS-Leap-42.1.x86_64-1.42.1.iso of=/dev/<stickdevice>

3. Run system from stick

   Like in the example above use Qemu to run the system, but attach
   the USB stick device as the system disk as follows:

   .. code:: bash

      $ qemu -hda /dev/<stickdevice> -m 4096
