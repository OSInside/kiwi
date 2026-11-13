.. _working-with-kiwi-customizing-the-boot-process:

Customizing the Boot Process
============================

.. sidebar:: Abstract

   This page describes the initrd {kiwi} creates for an image, the
   {kiwi} modules it contains, how to add own boot code, and the boot
   parameters of the {kiwi} modules.

Most Linux systems boot with an initial RAM disk, the :file:`initrd`,
which the kernel loads after the firmware handed over the control.
Depending on the image type, {kiwi} creates the initrd in the create
step with `dracut`. {kiwi} provides the following dracut modules, which
are added to the initrd as needed:

.. list-table::
   :header-rows: 1
   :widths: 22 50 28

   * - Module
     - Purpose
     - Package
   * - `kiwi-dump`
     - Installs an image onto a selectable target disk. Used by install
       media, the `installiso`, `installstick` or `installpxe`
       attributes.
     - `dracut-kiwi-oem-dump`
   * - `kiwi-dump-reboot`
     - Boots into the installed image after the installation.
     - `dracut-kiwi-oem-dump`
   * - `kiwi-live`
     - Boots a live ISO image, the `iso` image type.
     - `dracut-kiwi-live`
   * - `kiwi-overlay`
     - Boots disk images with `overlayroot="true"`: a compressed,
       read-only root partition with an overlayfs and a separate
       partition for persistent data.
     - `dracut-kiwi-overlay`
   * - `kiwi-repart`
     - Resizes an OEM disk image on first boot to the limits of the
       `oemconfig` section: repartitioning, resizing of RAID, LVM, LUKS
       and the filesystems.
     - `dracut-kiwi-oem-repart`
   * - `kiwi-verity`
     - Sets up dm-verity for images with `verity_blocks` or
       `embed_verity_metadata`, to verify the root device at boot.
     - `dracut-kiwi-verity`
   * - `kiwi-lib`
     - Common functions of the other modules.
     - `dracut-kiwi-lib`

.. note:: Custom boot images

   For the `oem` and `pxe` types, {kiwi} also supports custom boot
   images instead of dracut, with `initrd_system="kiwi"` and a reference
   to a boot image description in the `boot` attribute of the `type`
   element. This is mostly used in heavily customized PXE environments.
   dracut is recommended, and {kiwi} does not ship boot image
   descriptions. There are examples for an `OEM boot description
   <https://build.opensuse.org/package/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed/custom-oem-boot-description>`__
   and a `PXE boot description
   <https://build.opensuse.org/package/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed/custom-pxe-boot-description>`__.

Boot Image Hook-Scripts
-----------------------

dracut boots with a defined sequence of systemd services, see
`dracut.bootup(7)
<http://man7.org/linux/man-pages/man7/dracut.bootup.7.html>`_. Own boot
code is added as a dracut module, provided by a package or by the
overlay tree of the image description. The following example adds a
script which runs before the root filesystem is mounted:

#. Create the directory of the module:

   .. code:: bash

      $ mkdir -p root/usr/lib/dracut/modules.d/90my-module

#. Enable the module in :file:`root/etc/dracut.conf.d/90-my-module.conf`:

   .. code:: bash

      add_dracutmodules+=" my-module "

#. Add the script as
   :file:`root/usr/lib/dracut/modules.d/90my-module/my-script.sh`.

#. Add the module setup
   :file:`root/usr/lib/dracut/modules.d/90my-module/module-setup.sh`:

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

dracut adds the module to the initrd, and systemd calls the script as
part of the :file:`dracut-pre-mount.service`.

`inst_multiple` adds the tools the script needs to the initrd, as a
space-separated list. Tools in :file:`/bin`, :file:`/sbin`,
:file:`/usr/bin` or :file:`/usr/sbin` are given by name, other files,
such as libraries, by their full path. Each of them must be part of the
image, from a package, an archive or the overlay tree. For more ways to
customize the initrd, see the `dracut documentation
<https://dracut.wiki.kernel.org/index.php/Main_Page>`_.

Boot Image Parameters
---------------------

The following kernel parameters control the {kiwi} dracut modules. The
list contains the most commonly used ones.

General
~~~~~~~

``rd.kiwi.debug``
  Writes a debug log of the {kiwi} part of the boot process to
  :file:`/run/initramfs/log/boot.kiwi`.

``rd.kiwi.term``
  Sets the `TERM` variable in the initrd, also for the dialogs of the
  {kiwi} modules, if the default terminal emulation does not fit.

``rd.kiwi.dialog.timeout=seconds|off``
  The timeout of the dialogs of the {kiwi} modules. The default is 60
  seconds, `off` disables the timeout.

``rd.kiwi.allow_plymouth``
  Keeps plymouth running in the initrd. By default, {kiwi} stops it,
  as it can affect the available consoles.

OEM Installation Images
~~~~~~~~~~~~~~~~~~~~~~~

``rd.kiwi.install.devicepersistency=by-*``
  Lists the disks to install to by their `by-*` device names, for
  example `by-path`.

``rd.kiwi.oem.installdevice``
  The disk to install to. It overrides all other settings to select the
  disk, such as `oem-device-filter`, `oem-unattended-id` or
  `rd.kiwi.oem.maxdisk`, and is used without asking for confirmation.
  The device must exist and be a block device.

``rd.kiwi.oem.maxdisk=size[KMGT]``
  The maximum size of the disk an unattended installation installs to.
  By default it installs to the first disk not filtered out by
  `oem-device-filter`. For example, with big JBOD disks and a 480G
  RAID1 for the system, `rd.kiwi.oem.maxdisk=500G` installs to the
  RAID.

``rd.kiwi.oem.smallest_disk``
  An unattended installation installs to the smallest disk instead of
  the first one by name. USB flash drives are not considered. An
  alternative to `rd.kiwi.oem.maxdisk` for big JBOD setups.

``rd.kiwi.oem.disk.consistency``
  Stops the installation if another disk of the system has the same
  partition table UUID as the image, which means that the image is
  already installed on that disk. Two such disks cause device ID
  conflicts.

``rd.kiwi.oem.sha512``
  Expects sha512 instead of sha256 checksums, with the `.sha512` file
  extension.

``rd.kiwi.install.pxe``
  Loads the image from the remote location given in
  `rd.kiwi.install.image`.

``rd.kiwi.install.image=URI``
  The remote location of the image for `rd.kiwi.install.pxe`.

``rd.kiwi.install.pass.bootparam``
  Passes the boot parameters of the installation on to the installed
  image, for example a first boot configuration. Parameters starting
  with `rd.kiwi` are not passed on.

``rd.kiwi.install.efi_display_label=name``
  Creates an EFI boot entry with the given name after the installation,
  on EFI systems. An existing entry with this name is removed first. The
  entry points to the first EFI binary on the partition labeled `EFI`,
  preferring vendor loaders such as `\EFI\opensuse\shim.efi` over
  `\EFI\BOOT`, and shim over other loaders. Requires `efibootmgr` in the
  installation initrd.

``rd.kiwi.install.retain_last``
  Keeps the content of the last partition of the target disk, for
  example a data partition added with the `spare_part` attribute. This
  only works if the partition starts at the same address on the target
  disk as in the image.

``rd.kiwi.install.retain_past``
  Keeps the content of the last partition of the target disk if it
  starts after the end of the image. Unlike
  `rd.kiwi.install.retain_last`, the partition does not need to be part
  of the image.

  .. note:: Limitations

     There are no checks of the partition: {kiwi} takes the last
     partition reported by `sfdisk` before the installation and
     recreates it afterwards. This can leave a gap between the system
     and the kept partition. Of several partitions after the system, only
     the last one is kept. Use with care.

``rd.kiwi.install.partition_based``
  Installs the image partition by partition instead of as one block.
  {kiwi} copies the partition table and the MBR boot code, transfers
  `btrfs` partitions with the `btrfs seed/sprout process
  <https://btrfs.readthedocs.io/en/latest/Seeding-device.html>`_ and
  all other partitions block by block, and restores the filesystem UUID
  of btrfs afterwards. The main purpose is to use seed/sprout for the
  deployment.

  The btrfs root filesystem of the image must be flagged as a seeding
  device at build time. {kiwi} does this only for install images
  (`installiso`, `installstick` or `installpxe`) with the `btrfs`
  volume manager which set the parameter in the `kernelcmdline`
  attribute. Passing it only at boot time is not sufficient:

  .. code:: xml

     <type image="oem" filesystem="btrfs" installiso="true"
           kernelcmdline="console=ttyS0 rd.kiwi.install.partition_based">
       ...
     </type>

  `btrfs` and `btrfstune` must be part of the installation initrd. With
  `rd.kiwi.install.pxe`, the image is first loaded into main memory as
  :file:`/image.raw`, which must fit the complete uncompressed image.

  .. note:: Limitations

     * The result is not bit-identical with the image, the checksum
       verification is therefore skipped.
     * All partitions are installed, the parameter cannot be combined
       with `rd.kiwi.install.retain_last` or
       `rd.kiwi.install.retain_past`. The installation stops before
       writing to the disk if one of them is set.
     * It is not faster than installing the image as one block, and
       slower with `rd.kiwi.install.pxe`.
     * The seed/sprout messages are logged to :file:`/seed.log` in the
       installation initrd.

``rd.kiwi.install.clone_local``
  With `rd.kiwi.install.partition_based`: copies the image from the
  install media into main memory as :file:`/image.raw` first, and flags
  the btrfs filesystems of the copy as seeding devices. This allows a
  partition based installation of images which were not flagged at
  build time. The main memory must fit the complete uncompressed image.
  No effect for PXE installations, which always use a copy in memory.

OEM Disk Images
~~~~~~~~~~~~~~~

``rd.kiwi.oem.force_resize``
  Resizes the disk on boot without checking for free space, also with
  `<oem-resize-once>`. If the disk is already resized, the resize has
  no effect. The partition UUIDs change with every resize.

``rd.kiwi.oem.luks.reencrypt``
  Re-encrypts a LUKS2-encrypted disk before a resize, with a new key
  pool and master key. Recommended if the image file is not protected,
  as its LUKS header allows to decrypt the data otherwise. Runs only if
  the LUKS header still matches the one of the image, and asks for the
  passphrase if the image was built with one.

``rd.kiwi.oem.luks.reencrypt_randompass``
  With `rd.kiwi.oem.luks.reencrypt`: replaces the build time passphrase
  of the `luks` attribute with a random one-time passphrase, stored in
  memory in :file:`/run/.kiwi_reencrypt.keyfile`.

  .. warning::

     The passphrase is lost on reboot. The boot process must store
     retrievable key information for the following boots, for example
     with a TPM.

Live ISO Images
~~~~~~~~~~~~~~~

``rd.live.overlay.size``
  The size of the `tmpfs` which holds the data written at runtime, if
  no persistent write partition is used. The default is `50%` of the
  main memory.

``rd.live.overlay.persistent``
  Creates a persistent write partition.

``rd.live.encrypt``
  Encrypts the persistent write partition. The boot asks for a
  passphrase.

``rd.live.overlay.cowfs``
  The filesystem of the persistent write partition.

``rd.live.cowfile.mbsize``
  The size of the COW file in MB, 500 by default. If the ISO image is
  copied as a file onto a disk and booted with a GRUB loopback setup,
  for example with `live-grub-stick`, there is usually no space for a
  write partition. The data is then written to the COW file
  :file:`live_system.cow` next to the ISO file.

``rd.live.cowfile.path``
  The path of the COW file below the loop mount point
  :file:`/run/initramfs/isoscan`, for live systems booted from an ISO
  file, see :ref:`iso_as_file_to_usb_stick`. The default is
  :file:`/run/initramfs/isoscan/live_system.cow`.

``rd.live.dir``
  The directory which holds the live system. The default is `LiveOS`.

``rd.live.squashimg``
  The name of the squashfs image which holds the root filesystem. The
  default is `squashfs.img`.

Boot Debugging
--------------

By default, the boot stops without a way to interact with the system if
a fatal error occurs. With the following kernel parameters, the boot
opens a limited shell instead:

.. code:: bash

   rd.debug rd.kiwi.debug

The {kiwi} log in the shell is available with:

.. code:: bash

   less /run/initramfs/log/boot.kiwi
