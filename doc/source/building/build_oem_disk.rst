Build an OEM Expandable Disk Image
==================================

.. sidebar:: Abstract

   This page explains how to build an OEM disk image. It contains:

   * how to build an OEM image
   * how to deploy an OEM image
   * how to run the deployed system

An OEM disk represents the system disk with the capability to auto
expand the disk and its filesystem to a custom disk geometry. This
allows deploying the same OEM image on target systems of a different
hardware setup.

The following example shows how to build and deploy an OEM disk image
based on openSUSE Leap using a QEMU virtual machine as OEM target
system:

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Build the image with KIWI:

    .. code:: bash

        $ sudo kiwi-ng --type oem system build \
            --description kiwi-descriptions/suse/x86_64/suse-leap-42.3-JeOS \
            --target-dir /tmp/myimage

    Find the following result images below :file:`/tmp/myimage`.

    * The OEM disk image with the suffix :file:`.raw` is an expandable
      virtual disk. It can expand itself to a custom disk geometry.

    * The OEM installation image with the suffix :file:`install.iso` is a
      hybrid installation system which contains the OEM disk image and is
      capable to install this image on any target disk.

.. _deployment_methods:

Deployment Methods
------------------

The basic idea behind an OEM image is to provide the virtual disk data for
OEM vendors to support easy deployment of the system to physical storage
media.

There are the following basic deployment strategies:

1. :ref:`deploy_manually`

   Manually deploy the OEM disk image onto the target disk

2. :ref:`deploy_from_iso`

   Boot the OEM installation image and let KIWI's OEM installer
   deploy the OEM disk image from CD/DVD or USB stick onto the target disk

3. :ref:`deploy_from_network`

   PXE boot the target system and let KIWI's OEM installer
   deploy the OEM disk image from the network onto the target disk

.. _deploy_manually:

Manual Deployment
-----------------

The manual deployment method can be tested using virtualization software
such as QEMU, and an additional virtual target disk of a larger size.
The following steps shows how to do it:

1. Create a target disk

   .. code:: bash

       $ qemu-img create target_disk 20g

   .. note:: Retaining the Disk Geometry

       If the target disk geometry is less or equal to the geometry of
       the OEM disk image itself, the disk expansion performed for a physical
       disk install during the OEM boot workflow will be skipped and the
       original disk geometry stays untouched.

2. Dump OEM image on target disk

   .. code:: bash

       $ dd if=LimeJeOS-Leap-42.3.x86_64-1.42.3.raw of=target_disk conv=notrunc

3. Boot the target disk

   .. code:: bash

       $ qemu -hda target_disk -m 4096


   At first boot of the target_disk the system is expanded to the
   configured storage layout. By default the system root partition
   and filesystem is resized to the maximum free space available.

.. _deploy_from_iso:

CD/DVD Deployment
-----------------

The deployment from CD/DVD via the installation image can
also be tested using virtualization software such as QEMU.
The following steps shows how to do it:

1. Create a target disk

   Follow the steps above to create a virtual target disk

2. Boot the OEM installation image as CD/DVD with the
   target disk attached

   .. code:: bash

       $ qemu -cdrom LimeJeOS-Leap-42.3.x86_64-1.42.3.install.iso -hda target_disk -boot d -m 4096

   .. note:: USB Stick Deployment

       Like any other iso image built with KIWI, also the OEM installation
       image is a hybrid image. Thus it can also be used on USB stick and
       serve as installation stick image like it is explained in
       :ref:`hybrid_iso`

.. _deploy_from_network:

Network Deployment
------------------

The deployment from the network downloads the OEM disk image from a
PXE boot server. This requires a PXE network boot server to be setup
as explained in :ref:`pxe-boot-server`

If the PXE server is running the following steps shows how to test the
deployment process over the network using a QEMU virtual machine as
target system:

1. Make sure to create an installation PXE TAR archive along with your
   OEM image by replacing the following setup in
   kiwi-descriptions/suse/x86_64/suse-leap-42.3-JeOS/config.xml

   .. code:: xml

       instead of

       <type image="oem" installiso="true" ...

       setup

       <type image="oem" installpxe="true" ...


2. Rebuild the image, unpack the resulting
   :file:`LimeJeOS-Leap-42.3.x86_64-1.42.3.install.tar.xz` file to a temporary
   directory and copy the initrd and kernel images to the PXE server:

   .. code:: bash

       # Unpack installation tarball
       mkdir /tmp/pxe && cd /tmp/pxe
       tar -xf LimeJeOS-Leap-42.3.x86_64-1.42.3.install.tar.xz

       # Copy kernel and initrd used for pxe boot
       scp pxeboot.initrd.xz PXE_SERVER_IP:/srv/tftpboot/boot/initrd
       scp pxeboot.kernel PXE_SERVER_IP:/srv/tftpboot/boot/linux

3. Copy the OEM disk image, MD5 file, system kernel and initrd to
   the PXE boot server:

   Activation of the deployed system is done via `kexec` of the kernel
   and initrd provided here.

   .. code:: bash

       # Copy system image and MD5 checksum
       scp LimeJeOS-Leap-42.3.xz PXE_SERVER_IP:/srv/tftpboot/image/
       scp LimeJeOS-Leap-42.3.md5 PXE_SERVER_IP:/srv/tftpboot/image/

       # Copy kernel and initrd used for booting the system via kexec
       scp LimeJeOS-Leap-42.3.initrd PXE_SERVER_IP:/srv/tftpboot/image/
       scp LimeJeOS-Leap-42.3.kernel PXE_SERVER_IP:/srv/tftpboot/image/

4. Add/Update the kernel command line parameters

   Edit your PXE configuration (for example :file:`pxelinux.cfg/default`) on
   the PXE server and add these parameters to the append line, typically
   looking like this:

   .. code:: bash

       append initrd=boot/initrd rd.kiwi.install.pxe rd.kiwi.install.image=tftp://192.168.100.16/image/LimeJeOS-Leap-42.3.xz

   The location of the image is specified as a source URI which can point
   to any location supported by the `curl` command. KIWI calls `curl` to fetch
   the data from this URI. This also means your image, MD5 file, system kernel
   and initrd could be fetched from any server and doesn't have to be stored
   on the `PXE_SERVER`.

   .. note::

      The initrd and Linux Kernel for pxe boot are always loaded via tftp
      from the `PXE_SERVER`.

4. Create a target disk

   Follow the steps above to create a virtual target disk

5. Connect the client to the network and boot QEMU with the target disk
   attached to the virtual machine.

   .. code:: bash

      $ qemu -boot n -hda target_disk -m 4096

   .. note:: QEMU bridged networking

      In order to let qemu connect to the network we recommend to
      setup a network bridge on the host system and let qemu connect
      to it via a custom /etc/qemu-ifup. For details see
      https://en.wikibooks.org/wiki/QEMU/Networking
