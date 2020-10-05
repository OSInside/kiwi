.. _working-with-kiwi-customizing-the-boot-process:

Customizing the Boot Process
----------------------------

Most Linux systems use a special boot image to control the system boot process
after the system firmware, BIOS or UEFI, hands control of the hardware to the
operating system. This boot image is called the :file:`initrd`. The Linux kernel
loads the :file:`initrd`, a compressed cpio initial RAM disk, into the RAM and
executes :command:`init` or, if present, :command:`linuxrc`.

Depending on the image type, {kiwi} creates the boot image automatically during
the ``create`` step. It uses a tool called `dracut` to create this initrd.
Dracut generated initrd archives can be extended by custom modules to add
functionality which is not natively provided by dracut itself. In the scope
of {kiwi} the following dracut modules are used:

``kiwi-dump``
  Serves as an image installer. It provides the
  required implementation to install a {kiwi} image on a selectable target.
  This module is required if one of the attributes `installiso`, `installstick`
  or `installpxe` is set to `true` in the image type definition

``kiwi-dump-reboot``
  Serves to boot the system into the installed image after installation is
  completed.

``kiwi-live``
  Boots up a {kiwi} live image. This module is required
  if the `iso` image type is selected

``kiwi-overlay``
  Allows to boot disk images configured with the
  attribute `overlayroot` set to `true`. Such a disk has its root partition
  compressed and readonly and boots up using overlayfs for the root filesystem
  using an extra partition on the same disk for persistent data.

``kiwi-repart``
  Resizes an OEM disk image after installation onto
  the target disk to meet the size constraints configured in the `oemconfig`
  section of the image description. The module takes over the tasks to
  repartition the disk, resizing of RAID, LVM, LUKS and other layers and
  resizing of the system filesystems.

``kiwi-lib``
  Provides functions of general use and serves
  as a library usable by other dracut modules. As the name implies, its
  main purpose is to function as library for the above mentioned kiwi
  dracut modules.

.. note:: Using Custom Boot Image Support

   Apart from the standard dracut based creation of the boot image, {kiwi}
   supports the use of custom boot images for the image types ``oem``
   and ``pxe``. The use of a custom boot image is activated by setting the
   following attribute in the image description:

   .. code:: none

      <type ... initrd_system="kiwi"/>

   Along with this setting it is now mandatory to provide a reference to
   a boot image description in the ``boot`` attribute like in the
   following example:

   .. code:: none

      <type ... boot="{exc_netboot}"/>

   Such boot descriptions for the OEM and PXE types are currently still
   provided by the {kiwi} packages but will be moved into its own repository
   and package soon.

   The custom boot image descriptions allows a user to completely customize
   what and how the initrd behaves by its own implementation. This concept
   is mostly used in PXE environments which are usually highly customized
   and requires a specific boot and deployment workflow.


Boot Image Hook-Scripts
.......................

The dracut initrd system uses ``systemd`` to implement a predefined workflow
of services which are documented in the bootup man page at:

http://man7.org/linux/man-pages/man7/dracut.bootup.7.html

To hook in a custom boot script into this workflow it's required to provide
a dracut module which is picked up by dracut at the time {kiwi} calls it.
The module files can be either provided as a package or as part of the
overlay directory in your image description

The following example demonstrates how to include a custom hook script
right before the system rootfs gets mounted.

1. Create a subdirectory for the dracut module:

   .. code:: bash

       $ mkdir -p root/usr/lib/dracut/modules.d/90my-module

2. Register the dracut module in a configuration file:

   .. code:: bash

       $ vi root/etc/dracut.conf.d/90-my-module.conf

       add_dracutmodules+=" my-module "

3. Create the hook script:

   .. code:: bash

       $ touch root/usr/lib/dracut/modules.d/90my-module/my-script.sh

4. Create a module setup file in :file:`root/usr/lib/dracut/modules.d/90my-module/module-setup.sh` with the following content:

   .. code:: bash


       #!/bin/bash

       # called by dracut
       check() {
           # check module integrity
       }

       # called by dracut
       depends() {
           # return list of modules depending on this one
       }

       # called by dracut
       installkernel() {
           # load required kernel modules when needed
           instmods _kernel_module_list_
       }

       # called by dracut
       install() {
           declare moddir=${moddir}
           inst_multiple _tools_my_module_script_needs_

           inst_hook pre-mount 30 "${moddir}/my-script.sh"
       }

That's it! At the time {kiwi} calls dracut the :file:`90my-module` will be taken
into account and is installed into the generated initrd. At boot time
systemd calls the scripts as part of the :file:`dracut-pre-mount.service`.

The dracut system offers a lot more possibilities to customize the
initrd than shown in the example above. For more information, visit
the `dracut project page <http://people.redhat.com/harald/dracut.html>`_.


Boot Image Parameters
.....................

A dracut generated initrd in a {kiwi} image build process includes one or
more of the {kiwi} provided dracut modules. The following list documents
the available kernel boot parameters for this modules:

``rd.kiwi.debug``
  Activates the debug log file for the {kiwi} part of
  the boot process at :file:`/run/initramfs/log/boot.kiwi`.

``rd.kiwi.install.pxe``
  Tells an OEM installation image to lookup the system
  image on a remote location specified in `rd.kiwi.install.image`.

``rd.kiwi.install.image=URI``
  Specifies the remote location of the system image in
  a PXE based OEM installation

``rd.kiwi.install.pass.bootparam``
  Tells an OEM installation image to pass an additional
  boot parameters to the kernel used to boot the installed image. This
  can be used e.g. to pass on first boot configuration for a PXE image.
  Note, that options starting with `rd.kiwi` are not passed on to avoid
  side effects.

``rd.kiwi.oem.maxdisk=size[KMGT]``
  Configures the maximum disk size an unattended OEM
  installation should consider for image deployment. Unattended OEM
  deployments default to deploying on `/dev/sda` (more exactly, the first
  device not filtered out by `oem-device-filter`). With RAID
  controllers, it can happen that your buch of big JBOD disks is for
  example `/dev/sda` to `/dev/sdi` and the 480G RAID1 configured for
  OS deployment is `/dev/sdj`. With `rd.kiwi.oem.maxdisk=500G` the
  deployment will land on that RAID disk.

``rd.live.overlay.size``
  Tells a live ISO image the size for the `tmpfs` filesystem that is used
  for the `overlayfs` mount process. If the write area of the overlayfs
  mount uses this tmpfs, any new data written during the runtime of
  the system will fillup this space. The default value used is set
  to `50%` which means one half of the available RAM space can be used
  for writing new data.

``rd.live.overlay.persistent``
  Tells a live ISO image to prepare a persistent
  write partition.

``rd.live.overlay.cowfs``
  Tells a live ISO image which filesystem should be
  used to store data on the persistent write partition.

``rd.live.cowfile.mbsize``
  Tells a live ISO image the size of the COW file in MB.
  When using tools like `live-grub-stick` the live ISO will be copied
  as a file on the target device and a GRUB loopback setup is created
  there to boot the live system from file. In such a case the
  persistent write setup, which usually creates an extra write
  partition on the target, will fail in almost all cases because
  the target has no free and unpartitioned space available.
  Because of that a cow file(live_system.cow) instead of a partition
  is created. The cow file will be created in the same directory
  the live iso image file was read from by grub and takes the
  configured size or the default size of 500MB.

``rd.live.dir``
  Tells a live ISO image the directory which contains
  the live OS root directory. Defaults to `LiveOS`.

``rd.live.squashimg``
  Tells a live ISO image the name of the squashfs
  image file which holds the OS root. Defaults to `squashfs.img`.

Boot Debugging
''''''''''''''

If the boot process encounters a fatal error, the default behavior is to
stop the boot process without any possibility to interact with the system.
Prevent this behavior by activating dracut's builtin debug mode in combination
with the kiwi debug mode as follows:

.. code:: bash

    rd.debug rd.kiwi.debug

This should be set at the Kernel command line. With those parameters activated,
the system will enter a limited shell environment in case of a fatal error
during boot. The shell contains a basic set of commands and allows for a closer
look to:

.. code:: bash

    less /run/initramfs/log/boot.kiwi
