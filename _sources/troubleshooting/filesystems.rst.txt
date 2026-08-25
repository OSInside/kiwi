Incompatible Filesystem Settings on Host vs. Image
==================================================

.. note:: **Abstract**

   This page provides further information on how to solve
   image boot problems if the filesystem toolchain on
   the image build host is incompatible with the
   image's target distribution.

When {kiwi} builds an image that requests the creation of a
filesystem, the required filesystem creation tool, for
example, `mkfs.xfs`, is called from the host on which {kiwi}
is running. It is expected that the generated filesystem
is compatible with the image's target distribution. This
expectation is not always correct and depends on the
compatibility of the filesystem default settings between
build host and image target. We know about the following
settings that cause an incompatible filesystem, which
will not be able to be used on boot:

Ext[2,3,4]
  Check `/etc/mke2fs.conf` on the build host and make sure
  the configured `inode_size` is the same as the setting used
  for the target image. To solve an issue of this type, use
  the following filesystem creation option in your {kiwi}
  image configuration:

  .. code:: xml

      <type fscreateoptions="-I inode-size"/>

XFS
  Check the XFS metadata setup on the build host and make sure
  the settings are compatible with the target image. XFS has the
  default settings compiled-in, thus it might be needed to build
  the image first and use the `xfs_info` tool in a `disk.sh` script
  to fetch the settings at the build time of the image. We know from
  community reports that the setting `sparse=1` will cause issues
  on older versions of grub's xfs module, which does not know how
  to handle this setting properly. To solve an issue of this type,
  use the following filesystem creation option in your
  {kiwi} image configuration:

  .. code:: xml

      <type fscreateoptions="-i sparse=0"/>

btrfs
  btrfs and default page sizes (4k vs 64k). By default, btrfs
  autodetects the sector size according to the used kernel page
  size. If the sector size differs from the page size, the
  created filesystem cannot be mounted by the image's target
  kernel. If there is a different kernel page size between the
  kernel on the system the image is built on and the later
  kernel used for the image, it's required to specify the
  filesystem sector size to match with the kernel page size
  of the kernel used for the image. This can be done as in
  the following example:

  .. code:: xml

      <type fscreateoptions="--sectorsize 4k"/>

.. note::

    There can be more inconsistencies in the area of filesystems
    that we have not listed here. In general, it's advisable to
    build the image in a compatible environment. At best, the
    build host distribution is of the same major Linux version
    as the image target. For this purpose, {kiwi} provides the
    so-called `boxed-plugin`. Further details can be found
    in :ref:`self_contained`
