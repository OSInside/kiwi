.. _quick-start:

Quick Start
===========

.. hint:: **Abstract**

   This document describes how to start with KIWI, an OS appliance builder.
   This description applies for version |version|.

Before you start
----------------

Make sure you have installed KIWI and the example collection as
explained in :ref:`kiwi-installation`

Build your first image
----------------------

Your first image will be a simple system disk image which can run
in any full virtualization system like for example QEMU. Call the following
KIWI command in order to build it

.. code:: bash

    $ sudo kiwi-ng --type vmx system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.raw` below :file:`/tmp/myimage`.

Run your image
--------------

Running an image actually means booting the operating system. In order
to do that attach the disk image to a virtual system, in our case QEMU
is used, and boot it as follows:

.. code:: bash

    $ qemu \
        -boot c
        -drive file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio \
        -m 4096
