.. _custom_partitions:

Custom Disk Partitions
======================

.. sidebar:: Abstract

   This page provides details about the opportunities and limitations
   to customize the partition table in addition to the volume management
   settings from :ref:`custom_volumes`.

{kiwi} has its own partitioning schema which is defined according to several
different user configurations: boot firmware, boot partition,
expandable layouts, etc. Those supported features have an impact on the
partitioning schema.

MBR or GUID partition tables are not flexible, carry limitations and are
tied to some specific disk geometry. Because of that the preferred alternative
to disk layouts based on traditional partition tables is using flexible
approaches like logic volumes.

However, on certain conditions additional entries to the low level
partition table are needed. For this purpose the `<partitions>` section
exists and allows to add custom entries like shown in the following
example:

.. code:: xml

   <partitions>
       <partition name="var" size="100" mountpoint="/var" filesystem="ext3"/>
   </partitions>

Each `<partition>` entry puts a partition of the configured size in the
low level partition table, creates a filesystem on it and includes
it to the system's fstab file. If parts of the root filesystem are
moved into its own partition like it's the case in the above example,
this partition will also contain the data that gets installed during
the image creation process to that area.

The following attributes must/can be set to configured a partition entry:

name="identifier"
  Mandatory name of the partition as handled by {kiwi}.

  .. note::

     There are the following reserved names which cannot be used
     because they are already represented by existing attributes:
     `root`, `readonly`, `boot`, `prep`, `spare`, `swap`, `efi_csm`
     and `efi`.

partition_name="name"
  Optional name of the partition as it appears when listing the
  table contents with tools like `gdisk`. If no name is set
  {kiwi} constructs a name of the form `p.lx(identifier_from_name_attr)`

partition_type="type_identifier"
  Optional partition type identifier as handled by {kiwi}.
  Allowed values are `t.linux` and `t.raid`. If not specified
  `t.linux` is the default.

size="size_string"
  Mandatory size of the partition. A size string can end with `M` or
  `G` to indicate a mega-Byte or giga-Byte value. Without a unit
  specification mega-Byte is used.

mountpoint="path"
  Mandatory mountpoint to mount the partition in the system.

filesystem="btrfs|ext2|ext3|ext4|squashfs|xfs
  Mandatory filesystem configuration to create one of the supported
  filesystems on the partition.

clone="number"
  Optional setting to indicate that this partition should be
  cloned `number` of times. A clone partition is content wise an
  exact byte for byte copy of the origin. However, to avoid conflicts at boot
  time the UUID of any cloned partition will be made unique. In the
  sequence of partitions, the clone(s) will always be created first
  followed by the partition considered the origin. The origin
  partition is the one that will be referenced and used by the
  system

Despite the customization options of the partition table shown above
there are the following limitations:

1. By default the root partition is always the last one

   Disk imags build with {kiwi} are designed to be expandable.
   For this feature to work the partition containing the system
   rootfs must always be the last one. If this is unwanted for
   some reason {kiwi} offers an opportunity for one extra/spare
   partition with the option to be also placed at the end of the
   table. For details lookup `spare_part` in :ref:`image-description-elements`

2. By default there are no gaps in the partition table

   The way partitions are configured is done such that there are no
   gaps in the table of the image. However, leaving some space
   free at the **end** of the partition geometry is possible in the
   following ways:

   * **Deploy with unpartitioned free space.**

     To leave space unpartitioned on first boot of a disk image
     it is possible to configure an `<oem-systemsize>` which is
     smaller than the disk the image gets deployed to. Details
     about this setting can be found in :ref:`image-description-elements`

   * **Build with unpartitioned free space.**

     To leave space unpartitioned at build time of the image it
     is possible to disable `<oem-resize>` and configure an
     `<oem-systemsize>` which is smaller than the kiwi calculated
     disk size or the fixed setting for the disk size via the
     `size>` element.

   * **Build with unpartitioned free space.**

     Setting some unpartitioned free space on the disk can be done using
     the `unpartitioned` attribute of `size` element in type's section.
     For details see :ref:`disk-the-size-element`

   * **Resize built image adding unpartitioned free space.**

     A built image can be resized by using the `kiwi-ng image resize` command
     and set a new extended size for the disk. See {kiwi} commands docs
     :ref:`here <db_kiwi_image_resize>`.
