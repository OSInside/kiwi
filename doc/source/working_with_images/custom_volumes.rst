.. _custom_volumes:

Custom Disk Volumes
===================

.. sidebar:: Abstract

   This chapter provides high level explanations on how to handle volumes
   or subvolumes definitions for disk images using {kiwi}.

{kiwi} supports defining custom volumes by using the logical volume manager
(LVM) for the Linux kernel or by setting volumes at filesystem level when
filesystem supports it (e.g. btrfs).

Volumes are defined in the {kiwi} description file :file:`config.xml`,
using `systemdisk`. This element is a child of the `type`.
Volumes themselves are added via (multiple) `volume` child
elements of the `systemdisk` element:

.. code:: xml

   <image schemaversion="{schema_version}" name="openSUSE-Leap-15.1">
     <type image="oem" filesystem="btrfs" preferlvm="true">
       <systemdisk name="vgroup">
         <volume name="usr/lib" size="1G" label="library"/>
         <volume name="@root" freespace="500M"/>
         <volume name="etc_volume" mountpoint="etc" copy_on_write="false"/>
         <volume name="bin_volume" size="all" mountpoint="/usr/bin"/>
       </systemdisk>
     </type>
   </image>

Additional non-root volumes are created for each `volume`
element. Volume details can be defined by setting the following `volume`
attributes:

- `name`: Required attribute representing the volume's name. Additionally, this
  attribute is interpreted as the mountpoint if the `mountpoint` attribute
  is not used.

- `mountpoint`: Optional attribute that specifies the mountpoint of this
  volume.

- `size`: Optional attribute to set the size of the volume. If no suffix
  (`M` or `G`) is used, then the value is considered to be in megabytes.

  .. note:: Special name for the root volume

     One can use the `@root` name to refer to the volume mounted at `/`, in
     case some specific size attributes for the root volume have to be
     defined. For instance:

     .. code:: xml

        <volume name="@root" size="4G"/>

     In addition to the custom size of the root volume it's also possible
     to setup the name of the root volume as follows:

     .. code:: xml

        <volume name="@root=rootlv" size="4G"/>

     If no name for the root volume is specified the
     default name: **LVRoot** applies.

- `freespace`: Optional attribute defining the additional free space added
  to the volume. If no suffix (`M` or `G`) is used, the value is considered
  to be in megabytes.

- `label`: Optional attribute to set filesystem label of the volume.

- `copy_on_write`: Optional attribute to set the filesystem copy-on-write
  attribute for this volume.

- `filesystem_check`: Optional attribute to indicate that this
  filesystem should perform the validation to become filesystem checked.
  The actual constraints if the check is performed or not depends on
  systemd and filesystem specific components. If not set or set to
  `false` no system component will be triggered to run an eventual
  filesystem check, which results in this filesystem to be never checked.
  The latter is the default.

.. warning::
   The size attributes for filesystem volumes, as for btrfs, are
   ignored and have no effect.


The `systemdisk` element additionally supports the following optional
attributes:

- `name`: The volume group name, by default `kiwiVG` is used. This setting
  is only relevant for LVM volumes.

- `preferlvm`: Boolean value instructing {kiwi} to prefer LVM even if the
  used filesystem has its own volume management system.
