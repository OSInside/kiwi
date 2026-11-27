.. _reproducible_builds:

Reproducible Builds
===================

.. sidebar:: Abstract

   This page describes how to create bit identical images from the
   same root tree with {kiwi}, which parts of an image {kiwi} makes
   deterministic, and which differences remain for technical reasons.

When {kiwi} creates an image twice from the exact same root tree, for
example with `kiwi-ng system build` followed by `kiwi-ng system create`
on the resulting root tree, the two images are by default not bit
identical. The data files inside the image are the same, but many tools
involved in creating the image add data that changes with every call:
timestamps, randomly generated UUIDs, random salts or the order of
directory entries.

Enabling Reproducible Builds
----------------------------

{kiwi} follows the `SOURCE_DATE_EPOCH specification
<https://reproducible-builds.org/specs/source-date-epoch/>`_. If the
environment variable `SOURCE_DATE_EPOCH` is set to a UNIX timestamp,
{kiwi} and the tools it calls use this value instead of the current
time, and derive identifiers from it instead of creating random ones.
If the variable is not set, nothing changes.

Set the variable for every {kiwi} call that creates image data. Note
that `sudo` removes environment variables by default:

.. code:: shell-session

   $ export SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)
   $ sudo --preserve-env=SOURCE_DATE_EPOCH kiwi-ng system build \
         --description <description> --target-dir <target>
   $ sudo --preserve-env=SOURCE_DATE_EPOCH kiwi-ng system create \
         --root <target>/build/image-root --target-dir <target2>

To find the remaining differences between two images, use a tool like
`diffoscope <https://diffoscope.org/>`_.

.. warning::

   Without `SOURCE_DATE_EPOCH`, {kiwi} creates random identifiers on
   purpose, such that two images never share them. With
   `SOURCE_DATE_EPOCH` set, identifiers like filesystem UUIDs and GPT
   partition GUIDs only depend on the value of `SOURCE_DATE_EPOCH` and
   on names like the filesystem label. Two different images built with
   the same `SOURCE_DATE_EPOCH` value and the same labels share these
   identifiers. Do not attach such images to the same system at the
   same time, or use different `SOURCE_DATE_EPOCH` values for them.

What {kiwi} Makes Deterministic
-----------------------------------

With `SOURCE_DATE_EPOCH` set, the following parts of an image no
longer change from build to build:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Handling
   * - Filesystem UUIDs
     - Derived from `SOURCE_DATE_EPOCH` and the filesystem label for
       ext2, ext3, ext4, XFS, Btrfs, FAT, EROFS and swap.
   * - ext2, ext3, ext4
     - The seed of the directory hash is set to the filesystem UUID
       with `mke2fs -E hash_seed=...`.
   * - FAT
     - The volume ID is derived from the filesystem UUID. `mkdosfs`
       is called with `--invariant`, because `mkdosfs` up to version
       4.2 ignores `SOURCE_DATE_EPOCH` and sets the timestamp of the
       volume label to the current time.
   * - GPT partition table
     - The disk GUID and the unique partition GUIDs are derived from
       `SOURCE_DATE_EPOCH` and the partition number.
   * - MBR disk identifier
     - The disk identifier, also written to the `mbrid` file of the
       image, is derived from `SOURCE_DATE_EPOCH`.
   * - dm-verity
     - The salt and the UUID of the verity hash data are derived from
       `SOURCE_DATE_EPOCH`. This makes the root hash deterministic.
   * - SquashFS
     - `mksquashfs` uses `SOURCE_DATE_EPOCH` as the filesystem
       creation time and clamps newer file timestamps to it.
   * - EROFS
     - `mkfs.erofs` uses `SOURCE_DATE_EPOCH` for the timestamps.
       {kiwi} sets the UUID, which is otherwise random.
   * - ISO 9660
     - `xorriso` uses `SOURCE_DATE_EPOCH` for the volume timestamps
       and the GPT disk GUID of hybrid images. Before calling
       `xorriso`, {kiwi} sets the modification time of all files on
       the media that are newer than `SOURCE_DATE_EPOCH`, for example
       the bootloader configuration, to `SOURCE_DATE_EPOCH`.
   * - EFI FAT image of ISO media (`grub2` bootloader)
     - Created like FAT filesystems above. `mcopy` uses
       `SOURCE_DATE_EPOCH` for the timestamps of the copied files.
   * - initrd
     - `dracut` is always called with `--reproducible`, which uses
       `SOURCE_DATE_EPOCH` if it is set.
   * - tar archives
     - Archive members are sorted by name, modification times newer
       than `SOURCE_DATE_EPOCH` are clamped to it, and the access and
       change times are not stored. Requires tar 1.29 or later.
   * - cpio archives
     - Archive members are sorted by name, and inode and device
       numbers of the build host are not stored. Requires cpio 2.12
       or later.
   * - gzip compressed files
     - The original file name and timestamp are not stored.
   * - xz compressed files
     - `xz` writes a different result in single and multi threaded
       mode. {kiwi} calls `xz` with `--threads=0` by default, which
       uses the multi threaded mode on every build host since xz 5.4.
       With older `xz` versions, {kiwi} replaces `--threads=0` by an
       explicit number of threads, at least two, such that the result
       does not depend on the number of CPUs of the build host. This
       also applies to `--threads=0` set in the `options` of the `xz`
       section in the :ref:`runtime_config`.
   * - OCI and Docker containers
     - With the default `umoci` container tool, the creation date and
       the history entries use `SOURCE_DATE_EPOCH`. If `buildah` is set
       as `archive_tool` in the `oci` section of the
       :ref:`runtime_config`, {kiwi} passes `SOURCE_DATE_EPOCH` to
       `buildah commit`. With buildah 1.40 or later, it sets the
       creation date and the history entries, and timestamps of the
       container content newer than `SOURCE_DATE_EPOCH` are clamped to
       it. Older buildah versions set the creation date, the history
       entries and the timestamps of all container content to
       `SOURCE_DATE_EPOCH`.
       `skopeo`, which exports the container, stores the time of the
       export for all members of an OCI archive. {kiwi} clamps these
       times to `SOURCE_DATE_EPOCH`.

Known Limitations
-----------------

The following differences remain even with `SOURCE_DATE_EPOCH` set.
{kiwi} cannot remove them, because they are caused by the Linux kernel
or by the tools {kiwi} calls, or because they exist on purpose.

Filesystems that are populated through a mount
   For disk images, {kiwi} creates the ext2, ext3, ext4, XFS, Btrfs and
   FAT filesystems on a loop device, mounts them and copies the root
   tree into them. The kernel then writes the current time into the
   inode change time of every file and, for some filesystems, into the
   file creation time. It also records the mount and write times in the
   superblock and writes journal or log data. The placement of data
   blocks and inodes is decided by the kernel and can differ from run
   to run. Disk images with such filesystems are therefore not bit
   identical, even if all identifiers match. The same applies to the
   EFI system partition image created for the `systemd-boot`
   bootloader, which is mounted to install the bootloader.

   If a bit identical disk image is required, create it with
   `systemd-repart`, which populates the filesystems without a mount,
   see :ref:`disk_builder_repart`. This requires mkfs tools on the
   build host that support `SOURCE_DATE_EPOCH`: e2fsprogs 1.47.1,
   btrfs-progs 7.3 and xfsprogs 6.18 or newer. Alternatively, use a read-only root
   filesystem that is created from the root tree without a mount:
   SquashFS or EROFS, for example with `overlayroot="true"` for disk
   images or the `iso` image type.

Files created in the create step
   Files that {kiwi} writes into the root tree in the create step, like
   the bootloader configuration, carry the current time as their
   modification time. SquashFS, EROFS, ISO 9660 and tar archives clamp
   these times to `SOURCE_DATE_EPOCH`. The systemd-repart disk builder
   clamps them in its staging directory as well. Filesystems populated
   through a mount and cpio archives keep them.

LUKS encryption
   `cryptsetup` creates a random volume key, random key slot salts and
   a random UUID. This is required for the security of the encryption,
   so encrypted images are never reproducible.

LVM
   LVM creates random UUIDs for physical volumes, volume groups and
   logical volumes, and stores the creation time and the host name in
   its metadata.

Software RAID
   `mdadm` creates a random array UUID and stores timestamps in the
   RAID superblock.

dm-integrity
   {kiwi} does not set any identifiers for `integritysetup`. It has
   not been verified whether its result is deterministic.

Disk formats created with `qemu-img`
   The `vmdk` format, also used in `ova` images and VirtualBox
   Vagrant boxes, contains a random content ID. The `vhd` and
   `vhd-fixed` formats contain the creation time and a random UUID.
   The `vhdx` and `vdi` formats contain random UUIDs. The `qcow2`
   format and the raw disk image are not affected.

xz compression
   The output of `xz` depends on the version of `xz` and the caller
   options with regards to thread usage. {kiwi} makes explicit `xz`
   calls in the build deterministic but tools which compress data
   themselves, use their own `xz` settings. {kiwi} covers this
   for known tools in the process like `dracut` or `mksquashfs`.
   Should there be other tools part of the build process running
   a `xz` based compression task, this will make the build no
   longer deterministic.

Order of directory entries in the EFI FAT image
   `mcopy` copies files in the order the filesystem of the build host
   returns them. Building on hosts with different filesystems can
   result in a different order of the entries in the EFI FAT image.

Versions of the build tools
   Different versions of the tools on the build host, like `mkfs.*`,
   `xorriso`, `mksquashfs`, `grub2-mkimage` or the compressors, create
   different results. Use the same build host environment, for example
   a container or the `boxbuild` command described in
   :ref:`build_methods`, for builds that must be
   compared. With tar older than 1.29 or cpio older than 2.12, {kiwi}
   prints a warning and creates the archives without the reproducible
   options.
