.. _clone_partitions:

Partition Clones
================

.. sidebar:: Abstract

   This page provides details about the partition clone feature
   and its use cases

{kiwi} allows to create block level clones of certain partitions
used in the image. Clones can be created from the `root`, `boot`
and any other partition listed in the `<partitions>` element.

A partition clone is a simple byte dump from one
block storage device to another. However, this would cause conflicts
during boot of the system because all unique identifiers like
the UUID of a filesystem will no longer be unique. The clone
feature of {kiwi} takes care of this part and re-creates the
relevant unique identifiers per cloned partition. {kiwi} allows
this also for complex partitions like LVM, LUKS or RAID.

The partition clone(s) will always appear first in the partition table,
followed by the origin partition. The origin partition is the one
whose identifier will be referenced and used by the system. By default
no cloned partition will be mounted or used by the system at boot time.

Let's take a look at the following example:

.. code:: xml

   <type image="oem" root_clone="1" boot_clone="1" firmware="uefi" filesystem="xfs" bootpartition="true" bootfilesystem="ext4">
       <partitions>
           <partition name="home" size="10" mountpoint="/home" filesystem="ext3" clone="2"/>
       </partitions>
       <oemconfig>
           <oem-systemsize>2048</oem-systemsize>
           <oem-resize>false</oem-resize>
       </oemconfig>
       <size unit="G">100</size>
   </type>

With the above setup {kiwi} will create a disk image that
contains the following partition table:

.. code::

   Number  Start (sector)    End (sector)  Size       Code  Name
      1            2048            6143   2.0 MiB     EF02  p.legacy
      2            6144           47103   20.0 MiB    EF00  p.UEFI
      3           47104          661503   300.0 MiB   8300  p.lxbootclone1
      4          661504         1275903   300.0 MiB   8300  p.lxboot
      5         1275904         1296383   10.0 MiB    8300  p.lxhomeclone1
      6         1296384         1316863   10.0 MiB    8300  p.lxhomeclone2
      7         1316864         1337343   10.0 MiB    8300  p.lxhome
      8         1337344         3864575   2 GiB       8300  p.lxrootclone1
      9         3864576         6287326   2 GiB       8300  p.lxroot

When booting the system only the origin partitions `p.lxboot`, `p.lxroot`
and `p.lxhome` will be mounted and visible in e.g. :file:`/etc/fstab`,
the bootloader or the initrd. Thus partition clones are present as a data
source but are not relevant for the operating system from a functional
perspective.

As shown in the above example there is one clone request for root and boot
and a two clone requests for the home partition. {kiwi} does not sanity-
check the provided number of clones (e.g. whether your partition table
can hold that many partitions).

.. warning::

   There is a limit how many partitions a partition table can hold.
   This also limits how many clones can be created.

It's important when using the `root_clone` attribute to specify a size for
the part of the system that represents the root partition. As of today {kiwi}
does not automatically divide the root partition into two identical pieces.
In order to create a clone of the partition a size specification is required.
In the above example the size for root is provided via the `oem-systemsize`
element. Using a root clone and fixed size values has the following consequences:

1. The resize capability must be disabled. This is done via `oem-resize`
   element. The reason is that only the last partition in the partition
   table can be resized without destroying data. If there is a clone of
   the root partition it should never be resized because then the two
   partitions will be different in size and no longer clones of each other

2. There can be unpartitioned space left. In the above example the overall
   disk size is set to 100G. The sum of all partition sizes will be smaller
   than this value and there is no resize available anymore. Depending
   on the overall size setup for the disk this will leave unpartitioned
   space free on the disk.

Use Case
--------

Potential use cases for which a clone of one or more partitions
is useful include among others:

Factory Resets:
  Creating an image with the option to rollback to the
  state of the system at deployment time can be very helpful
  for disaster recovery

System Updates with Rollbacks e.g A/B:
  Creating an image which holds extra space allowing to rollback
  modified data can make a system more robust. For example
  in a simple A/B update concept, partition A would get updated
  but would flip to B if A is considered broken after applying the
  update.

.. note::

   Most probably any use case based on partition clones requires
   additional software to manage them. {kiwi} provides the
   option to create the clone layout but it does not provide
   the software to implement the actual use case for which the
   partition clones are needed.

Developers writing applications based on a clone layout created
with {kiwi} can leverage the metadata file :file:`/config.partids`.
This file is created at build time and contains the mapping between
the partition `name` and the actual partition number in the partition
table. For partition clones, the following naming convention applies:

.. code::

   kiwi_(name)PartClone(id)="(partition_number)"

The `(name)` is either taken from the `name` attribute
of the `<partition>` element or it is a fixed name assigned by {kiwi}.
There are the following reserved partition names for which cloning
is supported:

* root
* readonly
* boot

For the mentioned example this will result in the
following :file:`/config.partids`:

.. code::

   kiwi_BiosGrub="1"
   kiwi_EfiPart="2"
   kiwi_bootPartClone1="3"
   kiwi_BootPart="4"
   kiwi_homePartClone1="5"
   kiwi_homePartClone2="6"
   kiwi_HomePart="7"
   kiwi_rootPartClone1="8"
   kiwi_RootPart="9"
