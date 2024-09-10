Boxbuild Tweaks
===============

.. note:: Abstract

   This document describes a few ways to modify
   box build VMs for testing/debugging.

Increase Box Build Image Size
-----------------------------

In particularly large builds, you may find that the 
upstream build boxes aren't quite large enough, and
fail to build during the final few steps. While it 
is a bit of a kludge, it is possible to increase the
size of the build box.

To do so, follow these steps:

.. note:: For this example, we will assume the box increase
   question is an Ubuntu box, located in ~/.kiwi_boxes/ubuntu

1. While the VM is offline, locate the VM you want to modify
   and resize with `qemu-img`. Here we will increase the size 
   by 20G. The VM will have to be told to utilize this space in
   the following steps.
   
.. code:: bash
  
  $ qemu-img resize Ubuntu-Box.x86_64-1.22.04-System-BuildBox.qcow2 +20G

2. When relaunching your `kiwi` box build, make sure you use `--no-snapshot`
   and `--box-debug` options within your build command/script. Example:
   
.. code:: bash

   $ kiwi --debug --profile="Disk" --type oem system boxbuild --no-snapshot \
   --box-memory=32G --box-smp-cpus=16 --box-debug --box ubuntu -- \ 
   --description ./ubuntu-jammy --target-dir /build/kiwi/outputs/
  
3. When the build fails and drops you into the VM console, you will
   need to extend the partition of the VM rootfs, then resize with
   `resize2fs`. In this example, `parted` was used and the partition
   in question was /dev/vda3.
   
.. code:: bash

   $ parted
   # Can run parted print to check for relevant partitions if needed.
   (parted) $ print
   (parted) $ resizepart 3 100%
   # Exit from parted
   (parted) $ quit
   # Run resize2fs to grow the filesystem to fill the space
   $ resize2fs /dev/vda3

4. From this point, depending on where your build failed, it may be
   possible to continue your build from inside the box, using the 
   existing 9p mount points defined by your build command. Using the
   command above as an example, `/result` within the box maps up to 
   `/build/kiwi/outputs` on the host, and it's possible to run 
   
.. code:: bash

   $ kiwi-ng --profile="Disk" --type oem  system create \
   --root=/result/build/image-root/ --target-dir=/result

5. If the rebuild from within was successful, you can copy the files
   from `/result` to `/bundle`, from within the VM, where `/bundle`
   maps to your `target-dir` on the host.

