.. _custom_partitions:

Custom Disk Partitions
======================

.. sidebar:: Abstract

   This page provides some details about what {kiwi} supports and does
   not support regarding customization over the partition scheme. It also
   provides some guidance in case the user requires some custom layout
   beyond {kiwi} supported features.

By design, {kiwi} does not support a customized partition table. Alternatively,
{kiwi} supports the definition of user-defined volumes which covers most of
common use cases. See :ref:`Custom Disk Volumes <custom_volumes>` for
further details about that.

{kiwi} has its own partitioning schema which is defined according to several
different user configurations: boot firmware, boot partition,
expandable layouts, etc. Those supported features have an impact on the
partitioning schema. MBR or GUID partition tables are not flexible,
carry limitations and are tied to some specific disk geometry. Because
of that the preferred alternative to disk layouts based on traditional
partition tables is using flexible approaches like logic volumes.

As an example, expandable OEM images is a relevant {kiwi} feature that
is incompatible with the idea of adding user defined partitions on the
system area.

Despite no full customization is supported, some aspects of the partition
schema can be customized. {kiwi} supports:

1. Adding a spare partition *before* the root (`/`) partition.

     It can be achieved by using the `spare_part` type attribute.

2. Leaving some unpartitioned area at the *end* of the disk.

     Setting some unpartitioned free space on the disk can be done using
     the `unpartitioned` attribute of `size` element in type's section. [LINK]

3. Expand built disks to a new size adding unpartitioned free space at
   the *end* of the disk.

     A built image can be resized by using the `kiwi-ng image resize` command
     and set a new extended size for the disk. See {kiwi} commands docs
     :ref:`here <db_kiwi_image_resize>`.

Custom Partitioning at Boot Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding additional partitions at boot time of {kiwi} images is also possible,
however, setting the tools and scripts for doing so needs to be handled by
the user. A possible strategy to add partitions on system area are described
below.

The main idea consists on running a first boot service that creates the
partitions that are needed. Adding custom services is simple, use the
following steps:

1. Create a unit file for a systemd service:

    .. code:: shell

      [Unit]
      Description=Add a data partition
      After=basic.target
      Wants=basic.target

      [Service]
      Type=oneshot
      ExecStart=/bin/bash /usr/local/bin/create_part


    This systemd unit file will run at boot time once systemd reaches the basic
    target. At this stage all basic services are up an running (devices mounted,
    network interfaces up, etc.). In case the service is required to run on
    earlier stages for some reason, default dependencies need to be disabled,
    see `systemd man pages <https://www.freedesktop.org/software/systemd/man/systemd.service.html>`_.

2. Create partitioner shell script matching your specific needs

    Consider the following steps for a partitioner shell script that
    creates a new partition. Following the above unit file example
    the `/usr/local/bin/create_part` script should cover the following
    steps:

    a. Verify partition exists

       Verify the required partition is not mounted neither exists. Exit
       zero (0) if is already there.

       Use tools such `findmnt` to find the root device and `blkid`
       or `lsblk` to find a partition with certain label or similar
       criteria.

    b. Create a new partition

       Create a new partition. On error, exit with non zero.

       Use partitioner tools such as `sgdisk` that can be easily used
       in non interactive scripts. Using `partprobe` to reload partition
       table to make OS aware of the changes is handy.

    c. Make filesystem

       Add the desired filesystem to the new partitions. On error, exit
       with non zero.

       Regular filesystem formatting tools (`mkfs.ext4` just to mention one)
       can be used to apply the desired filesystem to the just created
       new partition. At this stage it is handy to add a label to the
       filesystem for easy recognition on later stages or script reruns.

    d. Update fstab file

       Just echo and append the desired entry in /etc/fstab.

    e. Mount partition

       `mount --all` will try to mount all fstab volumes, it just omits
       any already mounted device.


3. Add additional files into the root overlay tree.

     The above described unit files and partition creation shell script
     need to be included into the overlay tree of the image, thus they should
     be placed into the expected paths in root folder (or in
     :file:`root.tar.gz` tarball).

4. Activate the service in :file:`config.sh`

     The service needs to be enabled during image built time to be
     run during the very first boot. In can be done by adding the following
     snipped inside the :file:`config.sh`.
