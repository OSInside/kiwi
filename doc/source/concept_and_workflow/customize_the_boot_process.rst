.. _working-with-kiwi-customizing-the-boot-process:

Customizing the Boot Process
----------------------------

Most Linux systems use a special boot image to control the system boot process
after BIOS or UEFI hands over control of the hardware to the operating system.
This boot image is a compressed cpio initial RAM disk, and it's called the
:file:`initrd`. The Linux kernel loads the :file:`initrd` into the RAM and
executes :command:`init` or, if present, :command:`linuxrc`.

Depending on the image type, {kiwi} creates the boot image automatically during
the ``create`` step. To create the :file:`initrd`, {kiwi} uses a tool called
`dracut`. dracut-generated initrd archives can be extended with custom modules to
add functionality which is not natively provided by dracut itself. In the scope
of {kiwi}, the following dracut modules are used:

``kiwi-dump``
  Serves as an image installer. It provides the required implementation to
  install a {kiwi} image on a selectable target. This module is required if one
  of the attributes in the image type definition `installiso`, `installstick` or
  `installpxe` is set to `true`.

``kiwi-dump-reboot``
  Serves to boot the system into the installed image after installation is
  completed.

``kiwi-live``
  Boots up a {kiwi} live image. This module is required
  if the `iso` image type is selected.

``kiwi-overlay``
  Allows to boot disk images with the attribute `overlayroot` set to `true`. A
  disk like that has its root partition compressed and readonly. The disk boots up
  using overlayfs for the root filesystem with a separate partition on the same
  disk for persistent data.

``kiwi-repart``
  Resizes an OEM disk image after installation on
  the target disk to meet the size limits configured in the `oemconfig`
  section of the image description. The module takes over the tasks of
  repartitioning the disk, resizing RAID, LVM, LUKS and other layers as well as
  resizing the system filesystems.

``kiwi-lib``
  Provides common functions used by dracut modules.

.. note:: Using Custom Boot Image Support

   In addition to the standard dracut-based creation of the boot image, {kiwi}
   supports the use of custom boot images for the image types ``oem``
   and ``pxe``. The use of a custom boot image is enabled by setting the
   following attribute in the image description:

   .. code:: none

      <type ... initrd_system="kiwi"/>

   Along with this setting, you must provide a reference to
   a boot image description in the ``boot`` attribute as follows:

   .. code:: none

      <type ... boot="{exc_netboot}"/>
    
    While {kiwi} supports this approach, it is recommended using dracut instead.
    Keep also in mind that although {kiwi} supports creation of custom boot
    images, {kiwi} does not include any official boot image descriptions. You
    can find an OEM boot description example at
    https://build.opensuse.org/package/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed/custom-oem-boot-description
    and an PXE boot description example at
    https://build.opensuse.org/package/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed/custom-pxe-boot-description

   The custom boot image descriptions makes it possible to completely customize
   the behavior of the initrd. This concept is mostly used in PXE environments
   that are usually heavily customized and require a specific boot and
   deployment workflow.


Boot Image Hook-Scripts
.......................

The dracut initrd system uses ``systemd`` to implement a predefined workflow
of services documented in the bootup man page:

http://man7.org/linux/man-pages/man7/dracut.bootup.7.html

To hook in a custom boot script to this workflow, it is necessary to provide
a dracut module that dracut picks when {kiwi} calls it.
The module files can be provided either as a package or as part of the
overlay directory in the image description.

The following example shows how to include a custom hook script
before the system rootfs is mounted.

1. Create a subdirectory for the dracut module:

   .. code:: bash

       $ mkdir -p root/usr/lib/dracut/modules.d/90my-module

2. Register the dracut module in the configuration file:

   .. code:: bash

       $ vi root/etc/dracut.conf.d/90-my-module.conf

       add_dracutmodules+=" my-module "

3. Create the hook script:

   .. code:: bash

       $ touch root/usr/lib/dracut/modules.d/90my-module/my-script.sh

4. Create a module setup file in
   :file:`root/usr/lib/dracut/modules.d/90my-module/module-setup.sh` containing the following:

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

.. note:: Declaring Extra Tools for Hook Scripts

   The `install()` function called by dracut can define extra tools required by
   the specified hook script. The `inst_multiple` command and its parameters
   instruct dracut to include these extra tools and items into the initrd.

   The specified tools and items can be files. Normally, they are executables
   and libraries required by the hook script.

   * Each file must be included in the {kiwi} description either in a
     package, archive, or in the root tree of the image description
     directory.

   * The parameters of the `inst_multiple` command are space separated.

   * Each parameter can be a single executable name if it exists in `/bin`,
     `/sbin`, `/usr/bin`, or `/usr/sbin`` directories.

   * Otherwise, a full path to the file is required. This normally applies for
     libraries and other special files.

When {kiwi} calls dracut, the :file:`90my-module` is installed into the
generated initrd. At boot time, systemd calls the scripts as part of the
:file:`dracut-pre-mount.service`.

The dracut system offers many other possibilities to customize the
initrd than shown in the example above. For more information, visit
the `dracut project page <https://dracut.wiki.kernel.org/index.php/Main_Page>`_.


Boot Image Parameters
.....................

A dracut generated initrd in a {kiwi} image build process includes one or
more of the {kiwi} provided dracut modules. The following list documents
the available kernel boot parameters for these modules:

``rd.kiwi.term``
  Exports the TERM variable into the initrd environment. If
  the default value for the terminal emulation is not correct,
  `rd.kiwi.term` can be used to overwrite the default. The
  environment is also passed to the systemd unit that calls
  dialog based programs in {kiwi} dracut code, which means that the
  TERM setting applies there too.

``rd.kiwi.debug``
  Activates the debug log file for the {kiwi} part of
  the boot process in :file:`/run/initramfs/log/boot.kiwi`.

``rd.kiwi.install.pxe``
  Instructs an OEM installation image to lookup the system
  image on a remote location specified in `rd.kiwi.install.image`.

``rd.kiwi.install.image=URI``
  Specifies the remote location of the system image in
  a PXE based OEM installation.

``rd.kiwi.install.pass.bootparam``
  Instructs an OEM installation image to pass an additional
  boot parameters to the kernel used to boot the installed image. This
  can be used, for example, to pass on first boot configuration for a PXE image.
  Note that options starting with `rd.kiwi` are not passed to avoid
  side effects.

``rd.kiwi.oem.maxdisk=size[KMGT]``
  Specifies the maximum disk size an unattended OEM installation uses for image
  deployment. Unattended OEM deployments default to deploying on `/dev/sda` (or
  more precisely, the first device that is not filtered out by
  `oem-device-filter`). With RAID controllers, you may have big JBOD disks along
  with a 480G RAID1 configured for OS deployment. With
  `rd.kiwi.oem.maxdisk=500G`, the deployment is performed on the RAID disk.

``rd.kiwi.oem.force_resize``
  Forces the disk resize process on an OEM disk image. If set, no sanity
  check for unpartitioned/free space is performed and also an eventually
  configured `<oem-resize-once>` configuration from the image description
  will not be taken into account. The disk resize will be started which
  includes re-partition as well as all steps to resize the block layers
  up to the filesystem holding the data. As `rd.kiwi.oem.force_resize`
  bypasses all sanity checks to detect if such a resize process is
  needed or not, it can happen that all program calls of the resize
  process ends without any effect if the disk is already properly
  resized. It's also important to understand that the partition UUIDs
  will change on every resize which might be an unwanted side effect
  of a forced resize.

``rd.kiwi.oem.installdevice``
  Configures the disk device to use in an OEM installation. This overwrites or
  resets any other OEM device-specific settings, such as `oem-device-filter`,
  `oem-unattended-id` or `rd.kiwi.oem.maxdisk`, and continues the installation on
  the given device. The device must exist and must be a block special.

.. note:: Non interactive mode activated by rd.kiwi.oem.installdevice

   When setting `rd.kiwi.oem.installdevice` explicitly through the kernel command line,
   {kiwi} uses the device without prompting for confirmation.

``rd.live.overlay.size``
  Specifies the size for the `tmpfs` filesystem of a live ISO image that is used
  for the `overlayfs` mount process. If the write area of the overlayfs mount
  uses this tmpfs, any new data written during the runtime of the system is
  written in this space. The default value is `50%`, meaning half of the
  available RAM space can be used for writing new data.

``rd.live.overlay.persistent``
  Instructs a live ISO image to prepare a persistent
  write partition.

``rd.live.overlay.cowfs``
  Specifies which filesystem of a live ISO image to use for storing data on the
  persistent write partition.

``rd.live.cowfile.mbsize``
  Specifies the size of the COW file in MB. When using tools like
  `live-grub-stick`, the live ISO image is copied as a file on the target device,
  and a GRUB loopback setup is created there to boot the live system from the
  file. In this case, the persistent write setup that normally creates an extra
  write partition on the target will fail in most situations, because the target
  has no free and unpartitioned space available. To prevent this from happening,
  a COW file (live_system.cow) of a partition is created alongside the live ISO
  image file. The default size of the COW file is 500MB.

``rd.live.cowfile.path``
  Effectively used in isoscan loop mounted live systems. For details on this
  type of live system refer to :ref:`iso_as_file_to_usb_stick`.
  Specifies the path of the COW file below the `/run/initramfs/isoscan` loop
  mount point. If not specified the cowfile is placed at
  `/run/initramfs/isoscan/live_system.cow`.

``rd.live.dir``
  Specifies a directory that contains the live OS root directory. Default is
  `LiveOS`.

``rd.live.squashimg``
  Specifies the name of the squashfs image file which contains the OS root.
  Default is `squashfs.img`.

``rd.kiwi.allow_plymouth``
  By default kiwi stops plymouth if present and active in the
  initrd. Setting rd.kiwi.allow_plymouth will keep plymouth
  active in the initrd including all effects that might have
  to the available consoles.

Boot Debugging
''''''''''''''

If the boot process encounters a fatal error, the default behavior is to
stop the boot process without any possibility to interact with the system.
To prevent this, activate dracut's builtin debug mode in combination
with the {kiwi} debug mode as follows:

.. code:: bash

    rd.debug rd.kiwi.debug

This must be set at the kernel command line. With these parameters activated,
the system enters a limited shell environment when a fatal error occurs
during boot. The shell provides a basic set of tools, and it can be used for inspection using the following command:

.. code:: bash

    less /run/initramfs/log/boot.kiwi
