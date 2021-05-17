.. _ramdisk_deployment:

Deploy and Run System in a RamDisk
==================================

.. sidebar:: Abstract

   This page provides further information for handling
   oem images built with {kiwi} and references the following
   articles:

   * :ref:`expandable_disk`

If a machine should run the OS completely in memory without
the need for any persistent storage, the approach to deploy
the image into a ramdisk serves this purpose. {kiwi} allows
to create a bootable ISO image which deploys the image
into a ramdisk and activates that image with the following
oem type definition:

.. code:: xml

    <type image="oem" filesystem="ext4" installiso="true" initrd_system="dracut" installboot="install" kernelcmdline="rd.kiwi.ramdisk ramdisk_size=2048000">
        <bootloader name="grub2" timeout="1"/>
        <oemconfig>
            <oem-skip-verify>true</oem-skip-verify>
            <oem-unattended>true</oem-unattended>
            <oem-unattended-id>/dev/ram1</oem-unattended-id>
            <oem-swap>false</oem-swap>
            <oem-multipath-scan>false</oem-multipath-scan>
         </oemconfig>
     </type>

The type specification above builds an installation ISO image
which deploys the System Image into the specified ramdisk
device (/dev/ram1). The setup of the ISO image boots with a
short boot timeout of 1sec and just runs through the process
without asking any questions. In a ramdisk deployment the
optional target verification, swap space and multipath targets
are out of scope and therefore disabled.

The configured size of the ramdisk specifies the size of the
OS disk and must be at least of the size of the System Image.
The disk size can be configured with the following value in
the kernelcmdline attribute:

*  ramdisk_size=kbyte-value"

An image built with the above setup can be tested in QEMU as
follows:

.. code:: bash

    $ sudo qemu -cdrom \
          {exc_image_base_name}.x86_64-{exc_image_version}.install.iso \
          -serial stdio

.. note:: Enough Main Memory

    The machine, no matter if it's a virtual machine like QEMU
    or a real machine, must provide enough RAM to hold the image
    in the ramdisk as well as have enough RAM available to operate
    the OS and its applications. The {kiwi} build image with the
    extension .raw provides the System Image which gets deployed
    into the RAM space. Substract the size of the System Image
    from the RAM space the machine offers and make sure the result
    is still big enough for the use case of the appliance. In
    case of a virtual machine, attach enough main memory to fit
    this calculation. In case of QEMU this can be done with
    the `-m` option

Like all other oem {kiwi} images, also the ramdisk setup supports
all the deployments methods as explained in :ref:`deployment_methods`
This means it's also possible to dump the ISO image on a USB
stick let the system boot from it and unplug the stick from
the machine because the system was deployed into RAM

.. note:: Limitations Of RamDisk Deployments

    Only standard images which can be booted by a simple root mount
    and root switch can be used. Usually {kiwi} calls kexec after deployment
    such that the correct, for the image created dracut initrd, will boot
    the image. In case of a RAM only system kexec does not work because
    it would loose the ramdisk contents. Thus the dracut initrd driving
    the deployment is also the environment to boot the system.
    There are cases where this environment is not suitable to boot
    the system.
