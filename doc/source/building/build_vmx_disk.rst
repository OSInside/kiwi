Build a Virtual Disk Image
==========================

.. hint::

   Make sure you have checked out the example image descriptions
   For details see :ref:`example-descriptions`

The following example shows how to build and run a simple system
disk image based on SUSE Leap

.. code:: bash

    $ sudo kiwi-ng --type vmx system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.raw` below :file:`/tmp/myimage`.
For testing the disk image a virtual machine with the disk image attached
can be used. The following example shows how to use the Qemu system to
run the image:

.. code:: bash

    $ qemu \
        -drive file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio \
        -m 4096
