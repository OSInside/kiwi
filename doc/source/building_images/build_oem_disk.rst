.. _oem:

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

2. Build the image with {kiwi}:

   .. code:: bash

       $ sudo kiwi-ng --type oem system build \
           --description kiwi-descriptions/suse/x86_64/{exc_description} \
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

   Boot the OEM installation image and let {kiwi}'s OEM installer
   deploy the OEM disk image from CD/DVD or USB stick onto the target disk

3. :ref:`deploy_from_network`

   PXE boot the target system and let {kiwi}'s OEM installer
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

       $ dd if={exc_image_base_name}.x86_64-{exc_image_version}.raw of=target_disk conv=notrunc

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

       $ qemu -cdrom{exc_image_base_name}.x86_64-{exc_image_version}.install.iso -hda target_disk -boot d -m 4096

   .. note:: USB Stick Deployment

       Like any other iso image built with {kiwi}, also the OEM installation
       image is a hybrid image. Thus it can also be used on USB stick and
       serve as installation stick image like it is explained in
       :ref:`hybrid_iso`

.. _deploy_from_network:

Network Deployment
------------------

The deployment from the network downloads the OEM disk image from a
PXE boot server. This requires a PXE network boot server to be setup
as explained in :ref:`network-boot-server`

If the PXE server is running the following steps shows how to test the
deployment process over the network using a QEMU virtual machine as
target system:

1. Make sure to create an installation PXE TAR archive along with your
   OEM image by replacing the following setup in
   kiwi-descriptions/suse/x86_64/{exc_description}/config.xml

   Instead of

   .. code:: xml

       <type image="oem" installiso="true"/>

   setup

   .. code:: xml

       <type image="oem" installpxe="true"/>


2. Rebuild the image, unpack the resulting
   :file:`{exc_image_base_name}.x86_64-{exc_image_version}.install.tar.xz`
   file to a temporary directory and copy the initrd and kernel images to
   the PXE server:

   a) Unpack installation tarball

      .. code:: bash

          mkdir /tmp/pxe && cd /tmp/pxe
          tar -xf {exc_image_base_name}.x86_64-{exc_image_version}.install.tar.xz

   b) Copy kernel and initrd used for pxe boot

      .. code:: bash

          scp pxeboot.{exc_image_base_name}.x86_64-{exc_image_version}.initrd.xz PXE_SERVER_IP:/srv/tftpboot/boot/initrd
          scp pxeboot.{exc_image_base_name}.x86_64-{exc_image_version}.kernel PXE_SERVER_IP:/srv/tftpboot/boot/linux

3. Copy the OEM disk image, MD5 file, system kernel, initrd and bootoptions to
   the PXE boot server:

   Activation of the deployed system is done via `kexec` of the kernel
   and initrd provided here.

   a) Copy system image and MD5 checksum

      .. code:: bash

          scp {exc_image_base_name}.x86_64-{exc_image_version}.xz PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name}.x86_64-{exc_image_version}.md5 PXE_SERVER_IP:/srv/tftpboot/image/

   b) Copy kernel, initrd and bootoptions used for booting the system via kexec

      .. code:: bash

          scp {exc_image_base_name}.x86_64-{exc_image_version}.initrd PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name}.x86_64-{exc_image_version}.kernel PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name}.x86_64-{exc_image_version}.config.bootoptions PXE_SERVER_IP:/srv/tftpboot/image/

      .. note::

         The config.bootoptions file is used together with kexec to boot the
         previously dumped image. The information in that file references the
         root of the dumped image and can also include any other type of
         boot options. The file provided with the {kiwi} built image is
         by default connected to the image present in the PXE TAR archive.
         If other images got deployed the contents of this file must be
         adapted to match the correct root reference.

4. Add/Update the kernel command line parameters

   Edit your PXE configuration (for example :file:`pxelinux.cfg/default`) on
   the PXE server and add these parameters to the append line, typically
   looking like this:

   .. code:: bash

       append initrd=boot/initrd rd.kiwi.install.pxe rd.kiwi.install.image=tftp://192.168.100.16/image/{exc_image_base_name}.x86_64-{exc_image_version}.xz

   The location of the image is specified as a source URI which can point
   to any location supported by the `curl` command. {kiwi} calls `curl` to fetch
   the data from this URI. This also means your image, MD5 file, system kernel
   and initrd could be fetched from any server and doesn't have to be stored
   on the `PXE_SERVER`.

   By default {kiwi} does not use specific `curl` options or flags. However it
   is possible to add custom ones by adding the 
   `rd.kiwi.install.pxe.curl_options` flag into the kernel command line.
   `curl` options are passed as comma separated values. Consider the following
   example:

   .. code:: bash

       rd.kiwi.install.pxe.curl_options=--retry,3,--retry-delay,3,--speed-limit,2048

   The above tells {kiwi} to call `curl` with:

   .. code:: bash

       curl --retry 3 --retry-delay 3 --speed-limit 2048 -f <url>

   This is specially handy when the deployment infraestructure requires
   some fine tuned download behavior. For example, setting retries to be
   more robust over flaky network connections.

   .. note::

      {kiwi} just replaces commas with spaces and appends it to the
      `curl` call. This is relevant since command line options including
      commas will always fail.

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

.. _oem_customize:

OEM Customization
-----------------

The deployment process of an oem image can be customized through
the `oemconfig` element which is a child section of the `type`
element like the following example shows:

.. code:: xml

   <oemconfig>
     <oem-swapsize>512</oem-swapsize>
   </oemconfig>


The following list of optional oem element settings exists:

oemconfig.oem-boot-title Element
  By default, the string OEM will be used as the boot manager menu
  entry when KIWI creates the GRUB configuration during deployment.
  The oem-boot-title element allows you to set a custom name for the
  grub menu entry. This value is represented by the
  ``kiwi_oemtitle`` variable in the initrd

oemconfig.oem-bootwait Element
  Specify if the system should wait for user interaction prior to
  continuing the boot process after the oem image has been dumped to
  the designated storage device (default value is false). This value
  is represented by the ``kiwi_oembootwait`` variable in the initrd

oemconfig.oem-reboot Element
  Specify if the system is to be rebooted after the oem image has
  been deployed to the designated storage device (default value is
  false). This value is represented by the ``kiwi_oemreboot``
  variable in the initrd

oemconfig.oem-reboot-interactive Element
  Specify if the system is to be rebooted after the oem image has
  been deployed to the designated storage device (default value is
  false). Prior to reboot a message is posted and must be
  acknowledged by the user in order for the system to reboot. This
  value is represented by the ``kiwi_oemrebootinteractive`` variable
  in the initrd

oemconfig.oem-silent-boot Element
  Specify if the system should boot in silent mode after the oem
  image has been deployed to the designated storage device (default
  value is false). This value is represented by the
  ``kiwi_oemsilentboot`` variable in the initrd

oemconfig.oem-shutdown Element
  Specify if the system is to be powered down after the oem image
  has been deployed to the designated storage device (default value
  is false). This value is represented by the ``kiwi_oemshutdown``
  variable in the initrd

oemconfig.oem-shutdown-interactive Element
  Specify if the system is to be powered down after the oem image
  has been deployed to the designated storage device (default value
  is false). Prior to shutdown a message is posted and must be
  acknowledged by the user in order for the system to power off.
  This value is represented by the ``kiwi_oemshutdowninteractive``
  variable in the initrd

oemconfig.oem-swap Element
  Specify if a swap partition should be created. The creation of a
  swap partition is the default behavior. This value is represented
  by the ``kiwi_oemswap`` variable in the initrd

oemconfig.oem-swapsize Element
  Set the size of the swap partition. If a swap partition is to be
  created and the size of the swap partition is not specified with
  this optional element, KIWI will calculate the size of the swap
  partition and create a swap partition equal to two times the RAM
  installed on the system at initial boot time. This value is
  represented by the ``kiwi_oemswapMB`` variable in the initrd

oemconfig.oem-systemsize Element
  Set the size the operating system is allowed to consume on the
  target disk. The size limit does not include any consideration for
  swap space or a recovery partition. In a setup *without* a
  systemdisk element this value specifies the size of the root
  partition. In a setup *including* a systemdisk element this value
  specifies the size of the LVM partition which contains all
  specified volumes. Thus, the sum of all specified volume sizes
  plus the sum of the specified freespace for each volume must be
  smaller or equal to the size specified with the oem-systemsize.
  This value is represented by the variable ``kiwi_oemrootMB`` in
  the initrd

oemconfig.oem-unattended Element
  The installation of the image to the target system occurs
  automatically without requiring user interaction. If multiple
  possible target devices are discovered the image is deployed to
  the first device. ``kiwi_oemunattended`` in the initrd
