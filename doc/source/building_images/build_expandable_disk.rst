.. _expandable_disk:

Build an Expandable Disk Image
==============================

.. sidebar:: Abstract

   This page explains how to build an expandable disk image.
   It covers the following topics:

   * build an expandable disk image
   * deploy an expandable disk image
   * run the deployed system

An expandable disk represents the system disk with the capability to automatically
expand the disk and its filesystem to a custom disk geometry. This
allows deploying the same disk image on target systems with different
hardware setups.

The following example shows how to build and deploy an expandable disk image
based on openSUSE Leap using a QEMU virtual machine as a target
system:

1. Make sure you have checked out the example image descriptions (see :ref:`example-descriptions`).

2. Build an image with {kiwi}:

   .. code:: bash

       $ sudo kiwi-ng --type oem system build \
           --description kiwi/build-tests/{exc_description_disk} \
           --set-repo {exc_repo_leap} \
           --target-dir /tmp/myimage

   The resulting image is saved in :file:`/tmp/myimage`.

   * The disk image with the suffix :file:`.raw` is an expandable
     virtual disk. It can expand itself to a custom disk geometry.

   * The installation image with the suffix :file:`install.iso` is a
     hybrid installation system which contains the disk image and is
     capable to install this image on any target disk.

.. _deployment_methods:

Deployment Methods
------------------

The goal of an expandable disk image is to provide the virtual
disk data for OEM vendors to support easy deployment of the system to
physical storage media.

Basic deployment strategies are as follows:

1. :ref:`deploy_manually`

   Manually deploy the disk image onto the target disk.

2. :ref:`deploy_from_iso`

   Boot the installation image and let {kiwi}'s installer
   deploy the disk image from CD/DVD or USB stick onto the target disk.

3. :ref:`deploy_from_network`

   PXE boot the target system and let {kiwi}'s installer
   deploy the disk image from the network onto the target disk.

.. _deploy_manually:

Manual Deployment
-----------------

The manual deployment method can be tested using virtualization software
like QEMU and an additional virtual a large-size target disk.
To do this, follow the steps below.

1. Create a target disk:

   .. code:: bash

       $ qemu-img create target_disk 20g

   .. note:: Retaining the Disk Geometry

       If the target disk geometry is less than or equals to the geometry of
       the disk image itself, the disk expansion that is performed on a physical
       disk install during the boot workflow is skipped and the
       original disk geometry stays unchanged.

2. Dump disk image on target disk:

   .. code:: bash

       $ dd if={exc_image_base_name_disk}.x86_64-{exc_image_version}.raw of=target_disk conv=notrunc

3. Boot the target disk:

   .. code:: bash

       $ sudo qemu -hda target_disk -m 4096 -serial stdio


   On first boot of the target_disk, the system is expanded to the
   configured storage layout. By default, the system root partition
   and filesystem are resized to the maximum free space available.

.. _deploy_from_iso:

CD/DVD Deployment
-----------------

The deployment from CD/DVD via an installation image can
also be tested using virtualization software such as QEMU.
To do this, follow the steps below.

1. Create a target disk:

   Follow the steps above to create a virtual target disk

2. Boot the installation image as CD/DVD with the
   target disk attached.

   .. code:: bash

       $ sudo qemu -cdrom \
             {exc_image_base_name_disk}.x86_64-{exc_image_version}.install.iso -hda target_disk \
             -boot d -m 4096 -serial stdio

   .. note:: USB Stick Deployment

       Like any other ISO image built with {kiwi}, the installation
       image is also a hybrid image. Thus, it can also be used on USB stick and
       serve as installation media as explained in
       :ref:`hybrid_iso`

.. _deploy_from_network:

Network Deployment
------------------

The process of deployment from the network downloads the disk image from a
PXE boot server. This requires a PXE network boot server to be setup
as described in :ref:`network-boot-server`

If the PXE server is running, the following steps show how to test the
deployment process over the network using a QEMU virtual machine as
a target system:

1. Create an installation PXE TAR archive along with your
   disk image by replacing the following configuration in
   kiwi/build-tests/{exc_description_disk}/appliance.kiwi

   Find the line below:

   .. code:: xml

       <type image="oem" installiso="true"/>

   Modify the line as follows:

   .. code:: xml

       <type image="oem" installpxe="true"/>


2. Rebuild the image, unpack the resulting
   :file:`{exc_image_base_name_disk}.x86_64-{exc_image_version}.install.tar.xz`
   file to a temporary directory, and copy the initrd and kernel images to
   the PXE server.

   a) Unpack installation tarball:

      .. code:: bash

          mkdir /tmp/pxe && cd /tmp/pxe
          tar -xf {exc_image_base_name_disk}.x86_64-{exc_image_version}.install.tar.xz

   b) Copy kernel and initrd used for PXE boot:

      .. code:: bash

          scp pxeboot.{exc_image_base_name_disk}.x86_64-{exc_image_version}.initrd PXE_SERVER_IP:/srv/tftpboot/boot/initrd
          scp pxeboot.{exc_image_base_name_disk}.x86_64-{exc_image_version}.kernel PXE_SERVER_IP:/srv/tftpboot/boot/linux

3. Copy the disk image, MD5 file, system kernel, initrd and bootoptions to
   the PXE boot server.

   Activation of the deployed system is done via `kexec` of the kernel
   and initrd provided here.

   a) Copy system image and MD5 checksum:

      .. code:: bash

          scp {exc_image_base_name_disk}.x86_64-{exc_image_version}.xz PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name_disk}.x86_64-{exc_image_version}.md5 PXE_SERVER_IP:/srv/tftpboot/image/

   b) Copy kernel, initrd and bootoptions used for booting the system via kexec:

      .. code:: bash

          scp {exc_image_base_name_disk}.x86_64-{exc_image_version}.initrd PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name_disk}.x86_64-{exc_image_version}.kernel PXE_SERVER_IP:/srv/tftpboot/image/
          scp {exc_image_base_name_disk}.x86_64-{exc_image_version}.config.bootoptions PXE_SERVER_IP:/srv/tftpboot/image/

      .. note::

         The config.bootoptions file is used with kexec to boot the previously
         dumped image. This file specifies the root of the dumped image, and the
         file can include other boot options. The file provided with the {kiwi}
         built image connected to the image present in the PXE TAR archive. If
         other images are deployed, the file must be modified to match the
         correct root reference.

4. Add/Update the kernel command line parameters.

   Edit your PXE configuration (for example :file:`pxelinux.cfg/default`) on
   the PXE server, and add the following parameters to the append line similar to shown below:

   .. code:: bash

       append initrd=boot/initrd rd.kiwi.install.pxe rd.kiwi.install.image=tftp://192.168.100.16/image/{exc_image_base_name_disk}.x86_64-{exc_image_version}.xz

   The location of the image is specified as a source URI that can point
   to any location supported by the `curl` command. {kiwi} uses `curl` to fetch
   the data from this URI. This means that the image, MD5 file, system kernel
   and initrd can be fetched from any server, and they do not need to be stored
   on the `PXE_SERVER`.

   By default {kiwi} does not use specific `curl` options or flags. But it is
   possible to specify desired options by adding the
   `rd.kiwi.install.pxe.curl_options` flag to the kernel command line (`curl`
   options are passed as comma-separated values), for example:

   .. code:: bash

       rd.kiwi.install.pxe.curl_options=--retry,3,--retry-delay,3,--speed-limit,2048

   The above instructs {kiwi} to run `curl` as follows:

   .. code:: bash

       curl --retry 3 --retry-delay 3 --speed-limit 2048 -f <url>

   This can be particularly useful when the deployment infrastructure requires
   specific download configuration. For example, setting more robust retries
   over an unstable network connection.

   .. note::

      {kiwi} replaces commas with spaces and appends the result to the `curl`
      command. Keep that in mind, because command-line options that include
      commas break the command.

   .. note::

      The initrd and Linux Kernel for PXE boot are always loaded via TFTP
      from the `PXE_SERVER`.

4. Create a target disk.

   Follow the steps above to create a virtual target disk.

5. Connect the client to the network and boot QEMU with the target disk
   attached to the virtual machine:

   .. code:: bash

      $ sudo qemu -boot n -hda target_disk -m 4096

   .. note:: QEMU bridged networking

      To connect QEMU to the network, we recommend to
      setup a network bridge on the host system and connect QEMU
      to it via a custom /etc/qemu-ifup configuration. For details, see
      https://en.wikibooks.org/wiki/QEMU/Networking

.. _oem_customize:

OEM Customization
-----------------

The deployment process of an OEM image can be customized using
the `oemconfig` element. This element is a child section of the `type`
element, for example:

.. code:: xml

   <oemconfig>
     <oem-swapsize>512</oem-swapsize>
   </oemconfig>


Below is a losr list of optional `oem` element settings.

oemconfig.oem-resize
  Determines if the disk has the capability to expand itself to
  a new disk geometry or not. By default, this feature is activated.
  The implementation of the resize capability is done in a dracut
  module packaged as `dracut-kiwi-oem-repart`. If `oem-resize` is
  set to false, the installation of the corresponding dracut package
  can be skipped as well.

oemconfig.oem-boot-title
  By default, the string OEM is used as the boot manager menu
  entry when KIWI creates the GRUB configuration during deployment.
  The `oem-boot-title` element allows you to set a custom name for the
  grub menu entry. This value is represented by the
  ``kiwi_oemtitle`` variable in the initrd.

oemconfig.oem-bootwait
  Determines if the system waits for user interaction before
  continuing the boot process after the disk image has been dumped to
  the designated storage device (default value is false). This value
  is represented by the ``kiwi_oembootwait`` variable in the initrd.

oemconfig.oem-reboot
  When enabled, the system is rebooted after the disk image has
  been deployed to the designated storage device (default value is
  false). This value is represented by the ``kiwi_oemreboot``
  variable in the initrd.

oemconfig.oem-reboot-interactive
  When enabled, the system is rebooted after the disk image has
  been deployed to the designated storage device (default value is
  false). Before the reboot, a message is displayed, and it and must be
  acknowledged by the user for the system to reboot. This
  value is represented by the ``kiwi_oemrebootinteractive`` variable
  in the initrd.

oemconfig.oem-silent-boot
  Determines if the system boots in silent mode after the disk
  image has been deployed to the designated storage device (default
  value is false). This value is represented by the
  ``kiwi_oemsilentboot`` variable in the initrd.

oemconfig.oem-shutdown
  Determines if the system is powered down after the disk image
  has been deployed to the designated storage device (default value
  is false). This value is represented by the ``kiwi_oemshutdown``
  variable in the initrd.

oemconfig.oem-shutdown-interactive
  Determines if the system is powered down after the disk image
  has been deployed to the designated storage device (default value
  is false). Before the shutdown a message is displayed, and it must be
  acknowledged by the user for the system to power off.
  This value is represented by the ``kiwi_oemshutdowninteractive``
  variable in the initrd

oemconfig.oem-swap
  Determines if a swap partition is be created. By default, no
  swap partition is created. This value is represented
  by the ``kiwi_oemswap`` variable in the initrd.

oemconfig.oem-swapname
  Specifies the name of the swap space. By default, the name is set to
  ``LVSwap``. The default indicates that this setting is only useful in
  combination with the LVM volume manager. In this case, the swapspace is
  configured as a volume in the volume group, and every volume requires a name.
  The name specified in `oemconfig.oem-swapname` here is used as a name of the
  swap volume.

oemconfig.oem-swapsize
  Specifies the size of the swap partition. If a swap partition is created while
  the size of the swap partition is not specified, KIWI calculates the size of
  the swap partition, and creates a swap partition at initial boot time. In this
  case, the swap partition size equals the double amount of RAM of the system.
  This value is represented by the ``kiwi_oemswapMB`` variable in the initrd.

oemconfig.oem-systemsize
  Specifies the size the operating system is allowed to occupy on the target
  disk. The size limit does not include any swap space or recovery partition
  considerations. In a setup *without* the systemdisk element, this value
  specifies the size of the root partition. In a setup that *includes* the
  systemdisk element, this value specifies the size of the LVM partition that
  contains all specified volumes. This means that the sum of all specified
  volume sizes plus the sum of the specified freespace for each volume must be
  smaller than or equal to the size specified with the `oem-systemsize` element. This
  value is represented by the variable ``kiwi_oemrootMB`` in the initrd.

oemconfig.oem-unattended
  The installation of the image to the target system occurs
  automatically without requiring user interaction. If multiple
  possible target devices are discovered, the image is deployed to
  the first device. ``kiwi_oemunattended`` in the initrd.

oemconfig.oem-unattended-id
  Selects a target disk device for the installation according to the
  specified device ID. The device ID corresponds to the name of the device for
  the configured `devicepersistency`. By default, it is the `by-uuid` device
  name. If no representation exists, for example for ramdisk devices, the UNIX
  device node can be used to select one. The given name must be present in the
  device list detected by KIWI.

oemconfig.oem-skip-verify
  Disables the checksum verification process after installing of the image to
  the target disk. The verification process computes the checksum of the image
  installed to the target. This value is then compared to the initrd embedded
  checksum generated at build time of the image. Depending on the size of the
  image and machine power, computing the checksum may take time.

.. _installmedia_customize:

Installation Media Customization
--------------------------------

The installation media created for OEM network or CD/DVD deployments can
be customized with the `installmedia` section. It is a child section of the `type`
element, for example:

.. code:: xml

   <installmedia>
     <initrd action="omit">
       <dracut module="network-legacy"/>
     </initrd>
   </installmedia>

The `installmedia` is only available for OEM image types that include the
request to create an installation media.

The `initrd` child element of `installmedia` lists dracut modules. The element's
`action` attribute determines whether the dracut module is omitted
(`action="omit"`) or added (`action="add"`). Use `action="set"` to use only the
listed modules and nothing else (that is, none of the dracut modules included by
default).