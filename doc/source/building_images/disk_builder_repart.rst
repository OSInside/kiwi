.. _disk_builder_repart:

Building Disk Images with systemd-repart
========================================

.. sidebar:: Abstract

   This page describes how {kiwi} creates `oem` disk images with
   `systemd-repart` instead of loop devices and mounts, which
   image descriptions are supported, and how the result differs from
   a disk image created the default way.

By default, {kiwi} creates a disk image on a loop device: it partitions
the device, creates the filesystems on the partitions, mounts them and
copies the root tree into them. This requires loop devices and mount
privileges on the build host, and the kernel writes data like
timestamps into the filesystems that changes with every build.

`systemd-repart` creates the partition table and the filesystems
including their content directly in the image file. The `mkfs` tools
are called in a mode that populates the new filesystem from a
directory, for example `mkfs.ext4 -d`. No loop devices and no mounts
are used.

Enabling systemd-repart
-----------------------

Set the `disk_builder` attribute of the `oem` type:

.. code:: xml

   <type image="oem" filesystem="ext4" firmware="uefi"
         bootloader="systemd_boot" disk_builder="systemd-repart"/>

The build host needs `systemd-repart` with support for the `--offline`
option, which is available since systemd version 254, and the `mkfs`
tools of the used filesystems (`mkfs.vfat` for the EFI partition).
The image needs the `systemd-boot` EFI binaries, which are part of the
`systemd-boot` package on most distributions, or the `grub2` EFI
binaries if `bootloader="grub2"` is used, see :ref:`repart_grub2`.

Supported Image Descriptions
----------------------------

The systemd-repart disk builder supports a subset of the `oem` type
features. {kiwi} stops with an error that lists all unsupported
features of an image description before it starts to build. Supported
are:

* EFI firmware (`firmware="efi"` or `firmware="uefi"`) with a GPT
  partition table. Legacy BIOS boot is not supported, an EFI CSM
  partition is not created.
* The `systemd_boot` bootloader, with loader entries or with an UKI
  if `<dracut uefi="true"/>` is set.
* The `grub2` bootloader for EFI only, with a menu entry for each
  kernel flavor or with an UKI if `<dracut uefi="true"/>` is set.
  Legacy BIOS boot is not supported, therefore `eficsm="false"` must
  be set on x86, see :ref:`repart_grub2`.
* The `dracut` initrd system.
* An `ext2`, `ext3`, `ext4`, `xfs` or `btrfs` root filesystem.
* Btrfs volumes, defined in the `<systemdisk>` section with
  `filesystem="btrfs"`, including the root subvolume, the snapper
  snapshot layout and the read-only root snapshot, see
  :ref:`repart_btrfs_volumes`.
* A swap partition, requested with `<oem-swap>` and `<oem-swapsize>`
  in the `<oemconfig>` section.
* The `disk.sh`, `pre_disk_sync.sh` and `editbootconfig` scripts.
* Disk formats like `qcow2`, which are converted from the raw disk
  image.

Not supported are LVM volume management, Btrfs quota groups
(`btrfs_quota_groups` and the `quota` volume attribute), volumes
with `copy_on_write="false"`, software RAID, LUKS encryption,
dm-integrity, dm-verity, `overlayroot`, custom and spare partitions,
an extra boot partition, partition clones, filesystem create options,
an unpartitioned area and the `editbootinstall` script.

How the Disk Is Created
-----------------------

The disk image contains the following partitions, in this order:

#. The EFI system partition, label `EFI`, mounted at :file:`/boot/efi`
#. The swap partition, label `SWAP`, if requested
#. The root partition, label as set by `rootfs_label` or `ROOT`. It
   uses the remaining space of the disk. With `apply_dps_codes="true"`
   the partition gets the root partition type of the Discoverable
   Partitions Specification, otherwise the generic Linux type.

The GPT partition names are the same as the labels.

The steps that run in the mounted disk image with the default disk
builder run in a staging directory instead:

#. {kiwi} writes the metadata and the initrd into the root tree as
   with the default disk builder.
#. {kiwi} copies the root tree into a staging directory below the
   target directory. The staging directory needs as much space as the
   root tree.
#. `disk.sh` runs chrooted in the staging directory, then the SELinux
   labels are set. Unlike with the default disk builder, the staging
   directory is not bind mounted onto itself.
#. {kiwi} installs `systemd-boot`, the loader configuration and the
   loader entries into :file:`boot/efi` of the staging directory.
   `bootctl` is not used, because it requires a mounted EFI system
   partition. {kiwi} copies the `systemd-boot` EFI binary to
   :file:`EFI/systemd/` and :file:`EFI/BOOT/` and writes the entry
   token, like `bootctl install` does. With `bootloader="grub2"`
   {kiwi} sets up grub2 instead, see :ref:`repart_grub2`.
#. `systemd-repart` creates the disk image: the EFI system partition
   from :file:`boot/efi` of the staging directory, the root
   partition from the rest of the staging directory.

The root tree itself is not changed by these steps. The initrd is
still created with `dracut` in a chroot of the root tree, which bind
mounts :file:`/dev` and :file:`/proc` as for every image type.

Filesystem UUIDs
----------------

`systemd-repart` derives the filesystem UUIDs from the partition UUIDs
when it creates the filesystems. {kiwi} writes :file:`/etc/fstab` and
the `root=` kernel parameter before that, thus it references the
partitions by their partition UUID, `PARTUUID=...`, instead of the
filesystem UUID. With `devicepersistency="by-label"` the filesystem
labels are used.

The grub2 setup needs the filesystem UUIDs in advance.
`systemd-repart` calculates the UUID of a filesystem as HMAC-SHA256
of the string `file-system-uuid`, keyed by the partition UUID. The
first half of the result is used as version 4 UUID, for `vfat` the
first 32 bits are the volume ID. {kiwi} calculates the filesystem
UUIDs the same way. After `systemd-repart` has created the disk,
{kiwi} reads the filesystem UUIDs with `blkid`. If they don't match
the calculated ones, {kiwi} stops with an error instead of producing
an image that doesn't boot.

.. _repart_btrfs_volumes:

Btrfs Volumes
-------------

With the btrfs volume manager, `systemd-repart` creates the volumes
as subvolumes of the root filesystem while it creates the filesystem.
It uses the `Subvolumes=` setting, which `systemd-repart` implements
by the `--subvol` option of `mkfs.btrfs`:

.. code:: xml

   <type image="oem" filesystem="btrfs" firmware="uefi"
         btrfs_root_is_subvolume="true"
         btrfs_root_is_snapper_snapshot="true"
         disk_builder="systemd-repart">
       <bootloader name="grub2"/>
       <systemdisk>
           <volume name="home"/>
           <volume name="var"/>
       </systemdisk>
   </type>

The build host needs `systemd-repart` with support for `Subvolumes=`,
which is available since systemd version 257, and a `mkfs.btrfs`
that supports the `--subvol` option with subvolume types like
`default-ro:`, as for example btrfs-progs version 6.14 does.

`systemd-repart` passes the flags of a subvolume as suffix to
`mkfs.btrfs`, for example `--subvol path:ro,default`, while
`mkfs.btrfs` expects the subvolume type as prefix, for example
`--subvol default-ro:path`. Therefore {kiwi} does not use the `:ro`
flag of `Subvolumes=` and the `DefaultSubvolume=` setting. Instead
it passes the read-only and the default subvolume to `mkfs.btrfs`
through the `SYSTEMD_REPART_MKFS_OPTIONS_BTRFS` environment
variable. Options already set in this variable are kept.

The subvolume layout is the same as the one the default disk builder
creates:

* With `btrfs_root_is_subvolume="true"` the root tree is stored in
  the root subvolume, :file:`/@` by default, or the name set by
  `<volume name="@root=name"/>`. Otherwise the root tree is stored
  in the toplevel of the filesystem.
* With `btrfs_root_is_snapper_snapshot="true"` the root tree is
  stored in the first snapper snapshot
  :file:`/@/.snapshots/1/snapshot`, and :file:`/@/.snapshots` is
  mounted at :file:`/.snapshots`. With
  `btrfs_root_is_readonly_snapshot="true"` the snapshot is created
  read-only and the root filesystem is mounted read-only.
* Each volume is a subvolume below its parent, which is the root
  subvolume if the `parent` attribute is not set. The data of a
  volume is copied into its subvolume. If the subvolume is not stored
  below the location of the root tree, for example with a snapshot
  or with `parent="/"`, its data is excluded from the copy of the
  root tree and only the empty mount point directory is kept there.
* The root subvolume is the default subvolume unless
  `btrfs_set_default_volume="false"` is set. In that case
  :file:`/etc/fstab` and the kernel command line mount the root
  subvolume by the `subvol=` and `rootflags=subvol=` options. A
  snapshot is always the default subvolume.
* :file:`/etc/fstab` mounts each volume by the `subvol=` option,
  using the same device reference as the root filesystem. The
  `filesystem_check` volume attribute enables the filesystem check
  of the volume.

`snapper` requires a mounted btrfs filesystem and can't be used to
setup the first snapshot. Instead {kiwi} writes the
:file:`/.snapshots/1/info.xml` file of the first snapshot, with the
date taken from `SOURCE_DATE_EPOCH` if set, and creates the
:file:`/etc/snapper/configs/root` configuration from the snapper
configuration template if snapper is installed in the image.

grub2 looks up its files from the toplevel of a btrfs filesystem,
unless the `btrfs_relative_path` lookup is used, which is the case
with `btrfs_set_default_volume="true"` or a snapper snapshot. Without
it {kiwi} writes the paths of the grub2 configuration, the kernel and
the initrd as they are located in the filesystem, for example
:file:`/@/boot/grub2/grub.cfg`.

.. _repart_grub2:

EFI Boot with grub2
-------------------

With `bootloader="grub2"` the systemd-repart disk builder sets up
grub2 for EFI only:

.. code:: xml

   <type image="oem" filesystem="ext4" firmware="uefi" eficsm="false"
         disk_builder="systemd-repart">
       <bootloader name="grub2"/>
   </type>

The kernel, the initrd and the grub2 configuration stay on the root
filesystem, as with the default disk builder. The EFI system
partition contains the EFI binaries and an early boot configuration.
The setup in the staging directory works as follows:

#. With `firmware="efi"` {kiwi} uses the unsigned grub2 EFI image of
   the distribution if there is one. Otherwise {kiwi} creates it with
   `grub2-mkimage`, chrooted in the staging directory. With
   `firmware="uefi"` {kiwi} copies the shim, the signed grub2 EFI
   image and the MOK manager of the distribution into
   :file:`EFI/BOOT/`. `shim-install` and `grub2-install` are not used,
   because they require access to the disk device.
#. The early boot configuration in the EFI system partition searches
   the root filesystem by its UUID, see above, and loads
   :file:`/boot/grub2/grub.cfg` from it. With `<dracut uefi="true"/>`
   it chainloads the UKI from :file:`EFI/Linux/` of the EFI system
   partition instead.
#. `grub2-mkconfig` can't be used, because it looks up the root
   device from the mounted root filesystem. {kiwi} writes
   :file:`/boot/grub2/grub.cfg` from a template. It contains a menu
   entry for the kernel of each kernel flavor, and a failsafe entry
   if requested. The timeout, the console, the graphics mode and the
   theme are set as configured in the `<bootloader>` section. The
   first kernel flavor is the default entry.
#. {kiwi} writes :file:`/etc/default/grub` as with the default disk
   builder. A `grub2-mkconfig` call on the booted system, for example
   at a kernel update, creates the grub2 configuration from it.

With `SOURCE_DATE_EPOCH` set, the partition UUIDs and the seed for all
other identifiers `systemd-repart` creates are derived from
`SOURCE_DATE_EPOCH`, see :ref:`reproducible_builds`.
