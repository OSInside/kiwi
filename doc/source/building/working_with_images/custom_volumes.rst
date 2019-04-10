.. _custom_volumes:

Custom Disk Volumes
===================

.. sidebar:: Abstract

   This page provides high level explanations on how to handle volumes or
   subvolumes definitions for disk images using KIWI.

KIWI supports defining custom volumes by using the logical volume manager
(LVM) for the Linux kernel or by setting volumes at filesystem level when
filesystem supports it, like Btrfs.

Volumes are defined inside the KIWI description file, :file:`config.xml`,
under the `type` element by setting a `systemdisk` section. The
`systemdisk` element can include `volume` child elements.

Additional non-root volumes are created for each `volume` element. Volume
details can be defined by setting the following `volume` attributes:

  * `name`: Required attribute representing a volume's name. In
    addition this attribute is understood as the mountpoint path if
    `mountpoint` attribute is not used.

  * `mountpoint`: Optional attribute that specifies the mountpoint path.

  * `size`: Optional attribute to set the size of the volume. If no suffix
    (`M` or `G`) is used the value is considered to be in megabytes.

    .. note:: Special name for root

       In case defining some specific size attributes for the root volume is
       required one can use the `@root` name to refer to the volume mounted
       at root, `/`. For instance

       .. code:: xml

          <volume name="@root" size="4G"/>

  * `freespace`: Optional attribute to set the additional size added to the
    volume. If no suffix (`M` or `G`)is used the value is considered to be
    in megabytes.

  * `label`: Optional attribute to set filesystem label name of the volume.

  * `copy_on_write`: Optional attribute to apply the filesystem
    copy-on-write attribute for this volume.

Note that size attribute for filesystem volumes, as in Btrfs, are ignored
and have no effect.

This is a configuration example including a couple of additional volumes
definition and some additional empty space for the root volume:

.. code:: xml

   <type>
     <systemdisk name="vgroup-name">
       <volume name="@root" freespace="5G"/>
       <volume name="home" size="40G"/>
       <volume name="tmp" size="1024"/>
     </systemdisk>
   </type>
