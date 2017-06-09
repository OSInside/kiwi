.. _build_pxe:

Build a PXE Root File System Image
==================================

.. _PXE: https://en.wikipedia.org/wiki/Preboot_Execution_Environment
.. _TFTP: https://en.wikipedia.org/wiki/Trivial_File_Transfer_Protocol
.. _NBD: https://en.wikipedia.org/wiki/Network_block_device
.. _AoE: https://en.wikipedia.org/wiki/ATA_over_Ethernet


.. sidebar:: Abstract

   This page explains how to build a file system image for use with
   KIWI's PXE boot infrastructure. It contains:

   * how to build a PXE file system image
   * how to setup the PXE file system image on the PXE server
   * how to run it with QEMU

`PXE`_ is a network boot protocol that is shipped with most BIOS
implementations. The protocol sends a DHCP request to get an IP
address. When an IP address is assigned, it uses the `TFTP`_ protocol
to download a Kernel and boot instructions. Contrary to other images
built with KIWI, a PXE image consists of separate boot, kernel and root
filesystem images, since those images need to be made available in
different locations on the PXE boot server.

A root filesystem image which can be deployed via KIWI’s PXE
netboot infrastructure represents the system rootfs in a linux
filesystem. A user could loop mount the image and access the
contents of the root filesystem. The image does not contain
any information about the system disk its partitions or the
bootloader setup. All of these information is provided by a
client configuration file on the PXE server which controlls
how the root filesystem image should be deployed.

Many different deployment strategies are possible, e.g root over
`NBD`_ (network block device), `AoE`_ (ATA over Ethernet), or
NFS for diskless and diskfull clients. This particular
example shows how to build an overlayfs-based union system based
on openSUSE Leap for a diskless client which receives the squashfs
compressed root file system image in a ramdisk overlayed via
overlayfs and writes new data into another ramdisk on the same
system. As diskless client, a QEMU virtual machine is used.

.. compound:: **Things to know before**

   * To use the image, all image parts need to be copied to the PXE boot
     server. If you have not set up such a server, refer to
     :ref:`pxe-boot-server` for instructions.

   * The following example assumes you will create the PXE image
     on the PXE boot server itself (if not, use :command:`scp` to copy the files
     on the remote host).

   * To let QEMU connect to the network, we recommend to
     setup a network bridge on the host system and let QEMU connect
     to it via a custom :file:`/etc/qemu-ifup`. For details, see
     https://en.wikibooks.org/wiki/QEMU/Networking


1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Build the image with KIWI:

    .. code:: bash

        $ sudo kiwi-ng --profile netboot --type pxe system build \
            --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
            --target-dir /tmp/mypxe-result

3. Change into the build directory:

    .. code:: bash

        $ cd /tmp/mypxe-result

4. Copy the initrd and the kernel to :file:`/srv/tftpboot/boot`:

    .. code:: bash

        $ cp initrd-netboot-suse-*.gz /srv/tftpboot/boot/initrd
        $ cp initrd-netboot-suse-*.kernel /srv/tftpboot/boot/linux

5. Copy the system image and its MD5 sum to :file:`/srv/tftpboot/image`:

    .. code:: bash

        $ cp LimeJeOS-Leap-42.1.x86_64-1.42.1 /srv/tftpboot/image
        $ cp LimeJeOS-Leap-42.1.x86_64-1.42.1.md5 /srv/tftpboot/image

6. Adjust the PXE configuration file.
   The configuration file controls which kernel and initrd is
   loaded and which kernel parameters are set. A template has been installed
   at :file:`/srv/tftpboot/pxelinux.cfg/default` from the ``kiwi-pxeboot`` package.
   The minimal configuration required to boot the example image looks
   like to following:

    .. code:: bash

        DEFAULT KIWI-Boot

        LABEL KIWI-Boot
            kernel boot/linux
            append initrd=boot/initrd
            IPAPPEND 2

    Additional configuration files can be found at :ref:`pxe_client_config`.

7. Create the image client configuration file:

    .. code:: bash

        $ vi /srv/tftpboot/KIWI/config.default

        IMAGE=/dev/ram1;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096
        UNIONFS_CONFIG=/dev/ram2,/dev/ram1,overlay

   All PXE boot based deployment methods are controlled by a client
   configuration file. The above configuration tells the client where
   to find the image and how to activate it. In this case the image
   will be deployed into a ramdisk (ram1) and overlay mounted such
   that all write operations will land in another ramdisk (ram2).
   KIWI supports a variety of different deployment strategies based
   on the rootfs image created beforehand. For details, refer
   to :ref:`pxe_client_config`

8. Connect the client to the network and boot. This can also be done
   in a virtualized environment using QEMU as follows:

    .. code:: bash

        $ qemu -boot n -m 4096
