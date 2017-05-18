.. _vmx:

Build a Virtual Disk Image
==========================

.. sidebar:: Abstract

   This page explains how to build a simple disk image. It contains:

   * how to build a vmx image
   * how to run it with QEMU

A simple disk image represents the system disk, useful for cloud frameworks
like Amazon EC2, Google Compute Engine or Microsoft Azure.

The following example shows how to build a simple disk image based on
openSUSE Leap and ready to run in QEMU:


1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Build the image with KIWI:

   .. code:: bash

      $ sudo kiwi-ng --type vmx system build \
          --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
          --target-dir /tmp/myimage

   Find the image with the suffix :file:`.raw` below :file:`/tmp/myimage`.

3. Test the live image with QEMU:

   .. code:: bash

      $ qemu \
          -drive file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio \
          -m 4096

After the test was successful, the image is complete. For further information
how to setup the image to work within a cloud framework see:

* :ref:`setup_for_ec2`
* :ref:`setup_for_azure`
* :ref:`setup_for_gce`
