.. _schema-docs:

Schema Documentation 6.5
=========================

.. hint:: **Element quantifiers**

    * **Optional** elements are qualified with _`[?]`
    * Elements that occur **one or more** times are qualified with _`[+]`
    * Elements that occur **zero or more** times are qualified with _`[*]`
    * Required elements are not qualified

.. _k.image:

image
-----

The root element of the configuration file   

Children:
   The following elements occur in ``image``: :ref:`description <k.image.description>` , :ref:`preferences <k.image.preferences>` `[+]`_, :ref:`profiles <k.image.profiles>` `[?]`_, :ref:`users <k.image.users>` `[*]`_, :ref:`drivers <k.image.drivers>` `[*]`_, :ref:`strip <k.image.strip>` `[*]`_, :ref:`repository <k.image.repository>` `[*]`_, :ref:`packages <k.image.packages>` `[*]`_, :ref:`extension <k.image.extension>` `[?]`_

List of attributes for ``image``:

* ``name`` : An image name without / and spaces
* ``displayname`` `[?]`_: A friendly display name. Used in the boot menu for isolinux and grub
* ``kiwirevision`` `[?]`_: A kiwi git revision number which is known to build a working image from this description. If the kiwi git revision doesn't match the installed kiwi revision the process will exit.
* ``id`` `[?]`_: An identification number which is represented in a file named /etc/ImageID
* ``schemaversion`` : The allowed Schema version (fixed value)
* ``xsi:noNamespaceSchemaLocation`` `[?]`_: The location of the XSD Schema (not relevant for RELAX NG or DTD)
* ``xsi:schemaLocation`` `[?]`_: A pair of URI references: First is a namespace name, second the location of the XSD Schema (not relevant for RELAX NG or DTD)

.. _k.image.description:

description
___________

A Short Description

Parents:
   These elements contain ``description``: :ref:`k.image`

Children:
   The following elements occur in ``description``: :ref:`author <k.image.description.author>` , :ref:`contact <k.image.description.contact>` `[+]`_, :ref:`specification <k.image.description.specification>` 

List of attributes for ``description``:

* ``type`` : Kiwi distinguishes between two basic image description types which uses the same format but one is created and provided by the kiwi developers and the other is created by the users of kiwi. The type=boot specifies a boot image (initrd) which should be provided by the kiwi developers wheras type=system specifies a standard image description created by a kiwi user.

.. _k.image.description.author:

author
......

Author of the image

Parents:
   These elements contain ``author``: :ref:`k.image.description`


.. _k.image.description.contact:

contact
.......

Contact Information from the Author, like Email etc.

Parents:
   These elements contain ``contact``: :ref:`k.image.description`


.. _k.image.description.specification:

specification
.............

A Detailed Description

Parents:
   These elements contain ``specification``: :ref:`k.image.description`


.. _k.image.preferences:

preferences
___________

Configuration Information Needed for Logical Extend All elements are optional since the combination of appropriate preference sections based on profiles combine to create on vaild definition

Parents:
   These elements contain ``preferences``: :ref:`k.image`

Children:
   The following elements occur in ``preferences``: :ref:`bootsplash-theme <k.image.preferences.bootsplash-theme>` `[?]`_, :ref:`bootloader-theme <k.image.preferences.bootloader-theme>` `[?]`_, :ref:`defaultdestination <k.image.preferences.defaultdestination>` `[?]`_, :ref:`defaultprebuilt <k.image.preferences.defaultprebuilt>` `[?]`_, :ref:`defaultroot <k.image.preferences.defaultroot>` `[?]`_, :ref:`hwclock <k.image.preferences.hwclock>` `[?]`_, :ref:`keytable <k.image.preferences.keytable>` `[?]`_, :ref:`locale <k.image.preferences.locale>` `[?]`_, :ref:`packagemanager <k.image.preferences.packagemanager>` `[?]`_, :ref:`partitioner <k.image.preferences.partitioner>` `[?]`_, :ref:`rpm-check-signatures <k.image.preferences.rpm-check-signatures>` `[?]`_, :ref:`rpm-excludedocs <k.image.preferences.rpm-excludedocs>` `[?]`_, :ref:`rpm-force <k.image.preferences.rpm-force>` `[?]`_, :ref:`showlicense <k.image.preferences.showlicense>` `[*]`_, :ref:`timezone <k.image.preferences.timezone>` `[?]`_, :ref:`type <k.image.preferences.type>` `[*]`_, :ref:`version <k.image.preferences.version>` `[?]`_

List of attributes for ``preferences``:

* ``profiles`` `[?]`_: A profile name which binds the section to this name

.. _k.image.preferences.bootsplash-theme:

bootsplash-theme
................

Image bootsplash theme setup.

Parents:
   These elements contain ``bootsplash-theme``: :ref:`k.image.preferences`


.. _k.image.preferences.bootloader-theme:

bootloader-theme
................

Image bootloader theme setup.

Parents:
   These elements contain ``bootloader-theme``: :ref:`k.image.preferences`


.. _k.image.preferences.defaultdestination:

defaultdestination
..................

Default Path if destdir Otion is Not Specified

Parents:
   These elements contain ``defaultdestination``: :ref:`k.image.preferences`


.. _k.image.preferences.defaultprebuilt:

defaultprebuilt
...............

Default directory name for pre-built boot images, used if the directory is not specified on the command line

Parents:
   These elements contain ``defaultprebuilt``: :ref:`k.image.preferences`


.. _k.image.preferences.defaultroot:

defaultroot
...........

Default Root Directory Name if root Option is Not Specified

Parents:
   These elements contain ``defaultroot``: :ref:`k.image.preferences`


.. _k.image.preferences.hwclock:

hwclock
.......

Setup Image harware clock setup, either utc or localtime

Parents:
   These elements contain ``hwclock``: :ref:`k.image.preferences`


.. _k.image.preferences.keytable:

keytable
........

Image keytable setup.

Parents:
   These elements contain ``keytable``: :ref:`k.image.preferences`


.. _k.image.preferences.locale:

locale
......

Image locale setup.

Parents:
   These elements contain ``locale``: :ref:`k.image.preferences`


.. _k.image.preferences.packagemanager:

packagemanager
..............

Name of the Package Manager

Parents:
   These elements contain ``packagemanager``: :ref:`k.image.preferences`


.. _k.image.preferences.partitioner:

partitioner
...........

Name of the Partitioner used for any disk partition tasks

Parents:
   These elements contain ``partitioner``: :ref:`k.image.preferences`


.. _k.image.preferences.rpm-check-signatures:

rpm-check-signatures
....................

Setup a Package Signature

Parents:
   These elements contain ``rpm-check-signatures``: :ref:`k.image.preferences`


.. _k.image.preferences.rpm-excludedocs:

rpm-excludedocs
...............

Do not install files marked as documentation in the package

Parents:
   These elements contain ``rpm-excludedocs``: :ref:`k.image.preferences`


.. _k.image.preferences.rpm-force:

rpm-force
.........

Force the Installation of a Package

Parents:
   These elements contain ``rpm-force``: :ref:`k.image.preferences`


.. _k.image.preferences.showlicense:

showlicense
...........

Setup showlicense

Parents:
   These elements contain ``showlicense``: :ref:`k.image.preferences`


.. _k.image.preferences.timezone:

timezone
........

Setup Image Timezone setup

Parents:
   These elements contain ``timezone``: :ref:`k.image.preferences`


.. _k.image.preferences.type:

type
....

The Image Type of the Logical Extend

Parents:
   These elements contain ``type``: :ref:`k.image.preferences`

Children:
   The following elements occur in ``type``: :ref:`containerconfig <k.image.preferences.type.containerconfig>` `[?]`_, :ref:`machine <k.image.preferences.type.machine>` `[?]`_, :ref:`oemconfig <k.image.preferences.type.oemconfig>` `[?]`_, :ref:`pxedeploy <k.image.preferences.type.pxedeploy>` `[?]`_, :ref:`size <k.image.preferences.type.size>` `[?]`_, :ref:`systemdisk <k.image.preferences.type.systemdisk>` `[?]`_, :ref:`vagrantconfig <k.image.preferences.type.vagrantconfig>` `[*]`_

List of attributes for ``type``:

* ``boot`` `[?]`_: Specifies the path of the boot image (initrd), relative to /usr/share/kiwi/image
* ``bootfilesystem`` `[?]`_: if an extra boot partition is required this attribute specify which filesystem should be used for it. The type of the bootloader might overwrite this setting e.g for the syslinux loader fat is required
* ``firmware`` `[?]`_: Specifies the boot firmware of the system. Most systems uses a standard BIOS but there are also other firmware systems like efi, coreboot, etc.. This attribute is used to differentiate the image according to the firmware which boots up the system. It mostly has an impact on the disk layout and the partition table type. By default the standard x86 bios firmware setup is used
* ``bootkernel`` `[?]`_: Specifies the kernel boot profile defined in the boot image description. When kiwi builds the boot image the information is passed as add-profile option
* ``bootloader`` `[?]`_: Specifies the bootloader used for booting the image. At the moment grub2, zipl and the combination of zipl plus userspace grub2 are supported. The special custom entry allows to skip the bootloader configuration and installation and leaves this up to the user which can be done by using the editbootinstall and editbootconfig custom scripts
* ``bootloader_console`` `[?]`_: Specifies the bootloader console. The value only has an effect for the grub bootloader. By default a graphics console setup is used
* ``zipl_targettype`` `[?]`_: The device type of the disk zipl should boot. On zFCP devices use SCSI, on DASD devices use CDL or LDL on emulated DASD devices use FBA
* ``bootpartition`` `[?]`_: specify if an extra boot partition should be used or not. This will overwrite kiwi's default layout
* ``bootpartsize`` `[?]`_: For images with a separate boot partition this attribute specifies the size in MB. If not set the min bootpart size is set to 200 MB
* ``efipartsize`` `[?]`_: For images with an EFI fat partition this attribute specifies the size in MB. If not set the min efipart size is set to 20 MB
* ``bootprofile`` `[?]`_: Specifies the boot profile defined in the boot image description. When kiwi builds the boot image the information is passed as add-profile option
* ``boottimeout`` `[?]`_: Specifies the boot timeout in seconds prior to launching the default boot option. the unit for the timeout value is seconds if GRUB is used as the boot loader and 1/10 seconds if syslinux is used
* ``btrfs_root_is_snapshot`` `[?]`_: Tell kiwi to install the system into a btrfs snapshot The snapshot layout is compatible with the snapper management toolkit. By default no snapshots are used
* ``btrfs_root_is_readonly_snapshot`` `[?]`_: Tell kiwi to set the btrfs root filesystem snapshot read-only Once all data has been placed to the root filesystem snapshot it will be turned into read-only mode if this option is set to true. The option is only effective if btrfs_root_is_snapshot is also set to true. By default the root filesystem snapshot is writable
* ``checkprebuilt`` `[?]`_: Activates whether KIWI should search for a prebuild boot image or not. Obsolete attribute since KIWI v8
* ``compressed`` `[?]`_: Specifies whether the image output file should be compressed or not. This makes only sense for filesystem only images respectively for the pxe or cpio type
* ``devicepersistency`` `[?]`_: Specifies which method to use in order to get persistent storage device names. By default by-uuid is used.
* ``editbootconfig`` `[?]`_: Specifies the path to a script which is called right before the bootloader is installed. The script runs relative to the directory which contains the image structure
* ``editbootinstall`` `[?]`_: Specifies the path to a script which is called right after the bootloader is installed. The script runs relative to the directory which contains the image structure
* ``filesystem`` `[?]`_: Specifies the root filesystem type
* ``flags`` `[?]`_: Specifies flags for the image type. This could be compressed or clic and applies to the iso type only
* ``format`` `[?]`_: Specifies the format of the virtual disk. The ec2 value is deprecated and no longer supported It remains in the schema to allow us to print a better Error message than we receive from the parser. To be remove from here by the end of 2014
* ``formatoptions`` `[?]`_: Specifies additional format options passed on to qemu-img formatoptions is a comma separated list of format specific options in a name=value format like qemu-img expects it. kiwi will take the information and pass it as parameter to the -o option in the qemu-img call
* ``fsnocheck`` `[?]`_: Turn off periodic filesystem checks on ext2/3/4. Obsolete attribute since KIWI v8
* ``fsmountoptions`` `[?]`_: Specifies the filesystem mount options which also ends up in fstab The string given here is passed as value to the -o option of mount
* ``gcelicense`` `[?]`_: Specifies the license tag in a GCE format
* ``hybrid`` `[?]`_: Specifies that the image file should be turned into a hybrid image file. It's required to use the vmxboot boot image to boot that image though
* ``hybridpersistent`` `[?]`_: Will trigger the creation of a partition for a COW file to keep data persistent over a reboot
* ``hybridpersistent_filesystem`` `[?]`_: Set the filesystem to use for persistent writing if a hybrid image is used as disk on e.g a USB Stick. By default the btrfs filesystem is used
* ``gpt_hybrid_mbr`` `[?]`_: for gpt disk types only: create a hybrid GPT/MBR partition table
* ``force_mbr`` `[?]`_: Force use of MBR (msdos table) partition table even if the use of the GPT would be the natural choice. On e.g some arm systems an EFI partition layout is required but must not be stored in a GPT. For those rare cases this attribute allows to force the use of the msdos table including all its restrictions in max partition size and amount of partitions
* ``initrd_system`` `[?]`_: specify which initrd builder to use, default is kiwi's builtin architecture. Be aware that the dracut initrd system does not support all features of the kiwi initrd
* ``image`` : Specifies the image type
* ``installboot`` `[?]`_: Specifies the bootloader default boot entry for the" initial boot of a kiwi install image. This value is" only evaluated for grub and ext|syslinux"
* ``installprovidefailsafe`` `[?]`_: Specifies if the bootloader menu should provide an" failsafe entry with special kernel parameters or not"
* ``installiso`` `[?]`_: Specifies if a install iso should be created (oem only)
* ``installstick`` `[?]`_: Specifies if a install stick should be created (oem only)
* ``installpxe`` `[?]`_: Specifies if all data for a pxe network installation should be created (oem only)
* ``kernelcmdline`` `[?]`_: 
* ``luks`` `[?]`_: Setup cryptographic volume along with the given filesystem using the LUKS extension. The value of this attribute represents the password string used to be able to mount that filesystem while booting
* ``luksOS`` `[?]`_: With the luksOS value a predefined set of ciper, keysize and hash format options is passed to the cryptsetup call in order to create a format compatible to the specified distribution
* ``mdraid`` `[?]`_: Setup software raid in degraded mode with one disk Thus only mirroring and striping is possible
* ``overlayroot`` `[?]`_: Specifies to use an overlay root system consisting out of a squashfs compressed read-only root system overlayed using the overlayfs filesystem into an extra read-write partition. Available for the disk image types, vmx and oem
* ``primary`` `[?]`_: Specifies the primary type (choose KIWI option type)
* ``ramonly`` `[?]`_: for use with overlay filesystems only: will force any COW action to happen in RAM
* ``rootfs_label`` `[?]`_: label to set for the root filesystem. By default ROOT is used
* ``spare_part`` `[?]`_: Request a spare partition right before the root partition of the requested size. The attribute takes a size value and allows a unit in MB or GB, e.g 200M. If no unit is given the value is considered to be mbytes. A spare partition can only be configured for the disk image types oem and vmx
* ``target_blocksize`` `[?]`_: Specifies the image blocksize in bytes which has to match the logical (SSZ) blocksize of the target storage device. By default 512 byte is used which works on many disks However 4096 byte disks are coming. You can check the desired target by calling: blockdev --report device
* ``target_removable`` `[?]`_: Indicate if the target disk for oem images is deployed to a removable device e.g a USB stick or not. This only affects the EFI setup if requested and in the end avoids the creation of a custom boot menu entry in the firmware of the target machine. By default the target disk is expected to be non-removable
* ``vga`` `[?]`_: Specifies the kernel framebuffer mode. More information about the possible values can be found by calling hwinfo --framebuffer or in /usr/src/linux/Documentation/fb/vesafb.txt
* ``vhdfixedtag`` `[?]`_: Specifies the GUID in a fixed format VHD
* ``volid`` `[?]`_: for the iso type only: Specifies the volume ID (volume name or label) to be written into the master block. There is space for 32 characters.
* ``wwid_wait_timeout`` `[?]`_: Specifies the wait period in seconds after launching the multipath daemon to wait until all presented devices are available on the host. Default timeout is 3 seconds
* ``derived_from`` `[?]`_: Specifies the image URI of the container image. The image created by KIWI will use the specified container as the base root to work on.

.. _k.image.preferences.type.containerconfig:

containerconfig
,,,,,,,,,,,,,,,

Provides metadata information for containers

Parents:
   These elements contain ``containerconfig``: :ref:`k.image.preferences.type`

Children:
   The following elements occur in ``containerconfig``: :ref:`entrypoint <k.image.preferences.type.containerconfig.entrypoint>` `[?]`_, :ref:`subcommand <k.image.preferences.type.containerconfig.subcommand>` `[?]`_, :ref:`expose <k.image.preferences.type.containerconfig.expose>` `[?]`_, :ref:`volumes <k.image.preferences.type.containerconfig.volumes>` `[?]`_, :ref:`environment <k.image.preferences.type.containerconfig.environment>` `[?]`_, :ref:`labels <k.image.preferences.type.containerconfig.labels>` `[?]`_

List of attributes for ``containerconfig``:

* ``name`` : Specifies a name for the container. This is usually the the repository name of the container as read if the container image is imported via the docker load command
* ``tag`` `[?]`_: Specifies a tag for the container. This is usually the the tag name of the container as read if the container image is imported via the docker load command
* ``maintainer`` `[?]`_: Specifies a maintainer for the container.
* ``user`` `[?]`_: Specifies a user for the container.
* ``workingdir`` `[?]`_: Specifies the default working directory of the container

.. _k.image.preferences.type.containerconfig.entrypoint:

entrypoint
::::::::::

Provides details for the entry point command. This includes the execution name and its parameters. Arguments can be optionally specified

Parents:
   These elements contain ``entrypoint``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``entrypoint``: :ref:`argument <k.image.preferences.type.containerconfig.entrypoint.argument>` `[*]`_

List of attributes for ``entrypoint``:

* ``execute`` : Specifies the entry point program name to execute

.. _k.image.preferences.type.containerconfig.entrypoint.argument:

argument
;;;;;;;;

Provides details about a command argument

Parents:
   These elements contain ``argument``: :ref:`k.image.preferences.type.containerconfig.entrypoint`, :ref:`k.image.preferences.type.containerconfig.subcommand`

List of attributes for ``argument``:

* ``name`` : Specifies a command argument name

.. _k.image.preferences.type.containerconfig.subcommand:

subcommand
::::::::::

Provides details for the subcommand command. This includes the execution name and its parameters. Arguments can be optionally specified. The subcommand is appended the command information from the entrypoint. It is in the responsibility of the author to make sure the combination of entrypoint and subcommand forms a valid execution command

Parents:
   These elements contain ``subcommand``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``subcommand``: :ref:`argument <k.image.preferences.type.containerconfig.subcommand.argument>` `[*]`_

List of attributes for ``subcommand``:

* ``execute`` : Specifies the subcommand program name to execute

.. _k.image.preferences.type.containerconfig.subcommand.argument:

argument
;;;;;;;;

Provides details about a command argument

Parents:
   These elements contain ``argument``: :ref:`k.image.preferences.type.containerconfig.entrypoint`, :ref:`k.image.preferences.type.containerconfig.subcommand`

List of attributes for ``argument``:

* ``name`` : Specifies a command argument name

.. _k.image.preferences.type.containerconfig.expose:

expose
::::::

Provides details about network ports which should be exposed from the container. At least one port must be configured

Parents:
   These elements contain ``expose``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``expose``: :ref:`port <k.image.preferences.type.containerconfig.expose.port>` `[+]`_


.. _k.image.preferences.type.containerconfig.expose.port:

port
;;;;

Provides details about an exposed port.

Parents:
   These elements contain ``port``: :ref:`k.image.preferences.type.containerconfig.expose`

List of attributes for ``port``:

* ``number`` : Specifies the port number to expose

.. _k.image.preferences.type.containerconfig.volumes:

volumes
:::::::

Provides details about storage volumes in the container At least one volume must be configured

Parents:
   These elements contain ``volumes``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``volumes``: :ref:`volume <k.image.preferences.type.containerconfig.volumes.volume>` `[+]`_


.. _k.image.preferences.type.containerconfig.volumes.volume:

volume
;;;;;;

Specify which parts of the filesystem should be on an extra volume.

Parents:
   These elements contain ``volume``: :ref:`k.image.preferences.type.containerconfig.volumes`, :ref:`k.image.preferences.type.systemdisk`

List of attributes for ``volume``:

* ``copy_on_write`` `[?]`_: Apply the filesystem copy-on-write attribute for this volume
* ``freespace`` `[?]`_: free space to be added to this volume. The value is used as MB by default but you can add "M" and/or "G" as postfix
* ``mountpoint`` `[?]`_: volume path. The mountpoint specifies a path which has to exist inside the root directory.
* ``name`` : volume name. The name of the volume. if mountpoint is not specified the name specifies a path which has to exist inside the root directory.
* ``size`` `[?]`_: absolute size of the volume. If the size value is too small to store all data kiwi will exit. The value is used as MB by default but you can add "M" and/or "G" as postfix

.. _k.image.preferences.type.containerconfig.environment:

environment
:::::::::::

Provides details about the container environment variables At least one environment variable must be configured

Parents:
   These elements contain ``environment``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``environment``: :ref:`env <k.image.preferences.type.containerconfig.environment.env>` `[+]`_


.. _k.image.preferences.type.containerconfig.environment.env:

env
;;;

Provides details about an environment variable

Parents:
   These elements contain ``env``: :ref:`k.image.preferences.type.containerconfig.environment`

List of attributes for ``env``:

* ``name`` : Specifies the environment variable name
* ``value`` : Specifies the environment variable value

.. _k.image.preferences.type.containerconfig.labels:

labels
::::::

Provides details about container labels At least one label must be configured

Parents:
   These elements contain ``labels``: :ref:`k.image.preferences.type.containerconfig`

Children:
   The following elements occur in ``labels``: :ref:`label <k.image.preferences.type.containerconfig.labels.label>` `[+]`_


.. _k.image.preferences.type.containerconfig.labels.label:

label
;;;;;

Provides details about a container label

Parents:
   These elements contain ``label``: :ref:`k.image.preferences.type.containerconfig.labels`

List of attributes for ``label``:

* ``name`` : Specifies the label name
* ``value`` : Specifies the label value

.. _k.image.preferences.type.machine:

machine
,,,,,,,

specifies the VM configuration sections

Parents:
   These elements contain ``machine``: :ref:`k.image.preferences.type`

Children:
   The following elements occur in ``machine``: :ref:`vmconfig-entry <k.image.preferences.type.machine.vmconfig-entry>` `[*]`_, :ref:`vmdisk <k.image.preferences.type.machine.vmdisk>` , :ref:`vmdvd <k.image.preferences.type.machine.vmdvd>` `[?]`_, :ref:`vmnic <k.image.preferences.type.machine.vmnic>` `[*]`_

List of attributes for ``machine``:

* ``min_memory`` `[?]`_: The virtual machine min memory in MB (ovf only)
* ``max_memory`` `[?]`_: The virtual machine max memory in MB (ovf only)
* ``min_cpu`` `[?]`_: The virtual machine min CPU count (ovf only)
* ``max_cpu`` `[?]`_: The virtual machine max CPU count (ovf only)
* ``ovftype`` `[?]`_: The OVF configuration type
* ``HWversion`` `[?]`_: The virtual HW version number for the VM configuration (vmdk and ovf)
* ``arch`` `[?]`_: the VM architecture type (vmdk only)
* ``domain`` `[?]`_: The domain setup for the VM (xen only)
* ``guestOS`` `[?]`_: The virtual guestOS identification string for the VM (vmdk and ovf, note the name designation is different for the two formats)
* ``memory`` `[?]`_: The memory, in MB, setup for the guest VM (all formats)
* ``ncpus`` `[?]`_: The number of virtual cpus for the guest VM (all formats)

.. _k.image.preferences.type.machine.vmconfig-entry:

vmconfig-entry
::::::::::::::

An entry for the VM configuration file

Parents:
   These elements contain ``vmconfig-entry``: :ref:`k.image.preferences.type.machine`


.. _k.image.preferences.type.machine.vmdisk:

vmdisk
::::::

The VM disk definition.

Parents:
   These elements contain ``vmdisk``: :ref:`k.image.preferences.type.machine`

List of attributes for ``vmdisk``:

* ``disktype`` `[?]`_: The type of the disk as it is internally handled by the VM (ovf only)
* ``controller`` `[?]`_: The disk controller used for the VM guest (vmdk only)
* ``id`` `[?]`_: The disk ID / device for the VM disk (vmdk only)
* ``device`` `[?]`_: The disk device to appear in the guest (xen only)
* ``diskmode`` `[?]`_: The disk mode (vmdk only)

.. _k.image.preferences.type.machine.vmdvd:

vmdvd
:::::

The VM CD/DVD drive definition. You can setup either a scsi CD or an ide CD drive

Parents:
   These elements contain ``vmdvd``: :ref:`k.image.preferences.type.machine`

List of attributes for ``vmdvd``:

* ``controller`` : The CD/DVD controller used for the VM guest
* ``id`` : The CD/DVD ID for the VM CD rom drive

.. _k.image.preferences.type.machine.vmnic:

vmnic
:::::

The VM network interface definition

Parents:
   These elements contain ``vmnic``: :ref:`k.image.preferences.type.machine`

List of attributes for ``vmnic``:

* ``driver`` `[?]`_: The driver used for the VM network interface
* ``interface`` : The interface ID for the VM network interface
* ``mode`` `[?]`_: The VM network mode
* ``mac`` `[?]`_: The VM mac address

.. _k.image.preferences.type.oemconfig:

oemconfig
,,,,,,,,,

Specifies the OEM configuration section

Parents:
   These elements contain ``oemconfig``: :ref:`k.image.preferences.type`

Children:
   The following elements occur in ``oemconfig``: :ref:`oem-ataraid-scan <k.image.preferences.type.oemconfig.oem-ataraid-scan>` `[?]`_, :ref:`oem-boot-title <k.image.preferences.type.oemconfig.oem-boot-title>` `[?]`_, :ref:`oem-bootwait <k.image.preferences.type.oemconfig.oem-bootwait>` `[?]`_, :ref:`oem-device-filter <k.image.preferences.type.oemconfig.oem-device-filter>` `[?]`_, :ref:`oem-inplace-recovery <k.image.preferences.type.oemconfig.oem-inplace-recovery>` `[?]`_, :ref:`oem-kiwi-initrd <k.image.preferences.type.oemconfig.oem-kiwi-initrd>` `[?]`_, :ref:`oem-multipath-scan <k.image.preferences.type.oemconfig.oem-multipath-scan>` `[?]`_, :ref:`oem-vmcp-parmfile <k.image.preferences.type.oemconfig.oem-vmcp-parmfile>` `[?]`_, :ref:`oem-partition-install <k.image.preferences.type.oemconfig.oem-partition-install>` `[?]`_, :ref:`oem-reboot <k.image.preferences.type.oemconfig.oem-reboot>` `[?]`_, :ref:`oem-reboot-interactive <k.image.preferences.type.oemconfig.oem-reboot-interactive>` `[?]`_, :ref:`oem-recovery <k.image.preferences.type.oemconfig.oem-recovery>` `[?]`_, :ref:`oem-recoveryID <k.image.preferences.type.oemconfig.oem-recoveryID>` `[?]`_, :ref:`oem-recovery-part-size <k.image.preferences.type.oemconfig.oem-recovery-part-size>` `[?]`_, :ref:`oem-shutdown <k.image.preferences.type.oemconfig.oem-shutdown>` `[?]`_, :ref:`oem-shutdown-interactive <k.image.preferences.type.oemconfig.oem-shutdown-interactive>` `[?]`_, :ref:`oem-silent-boot <k.image.preferences.type.oemconfig.oem-silent-boot>` `[?]`_, :ref:`oem-silent-install <k.image.preferences.type.oemconfig.oem-silent-install>` `[?]`_, :ref:`oem-silent-verify <k.image.preferences.type.oemconfig.oem-silent-verify>` `[?]`_, :ref:`oem-skip-verify <k.image.preferences.type.oemconfig.oem-skip-verify>` `[?]`_, :ref:`oem-swap <k.image.preferences.type.oemconfig.oem-swap>` `[?]`_, :ref:`oem-swapsize <k.image.preferences.type.oemconfig.oem-swapsize>` `[?]`_, :ref:`oem-systemsize <k.image.preferences.type.oemconfig.oem-systemsize>` `[?]`_, :ref:`oem-unattended <k.image.preferences.type.oemconfig.oem-unattended>` `[?]`_, :ref:`oem-unattended-id <k.image.preferences.type.oemconfig.oem-unattended-id>` `[?]`_


.. _k.image.preferences.type.oemconfig.oem-ataraid-scan:

oem-ataraid-scan
::::::::::::::::

For oemboot driven images: turn on or off the search for ata raid devices (aka fake raid controllers) true/false (default is true)

Parents:
   These elements contain ``oem-ataraid-scan``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-boot-title:

oem-boot-title
::::::::::::::

For oemboot driven images: setup of the boot menu text displayed within the square brackets after first reboot of the OEM image

Parents:
   These elements contain ``oem-boot-title``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-bootwait:

oem-bootwait
::::::::::::

For oemboot driven images: halt system after image dump true/false

Parents:
   These elements contain ``oem-bootwait``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-device-filter:

oem-device-filter
:::::::::::::::::

For oemboot driven images: filter install devices by given regular expression. The expression is handled by the bash regexp operator

Parents:
   These elements contain ``oem-device-filter``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-inplace-recovery:

oem-inplace-recovery
::::::::::::::::::::

For oemboot driven images: Specify whether the recovery archive should be stored as part of the image or not. If it's not stored it's created during install of the oem image

Parents:
   These elements contain ``oem-inplace-recovery``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-kiwi-initrd:

oem-kiwi-initrd
:::::::::::::::

For oemboot driven images: use kiwi initrd in any case and don't replace it with mkinitrd created initrd

Parents:
   These elements contain ``oem-kiwi-initrd``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-multipath-scan:

oem-multipath-scan
::::::::::::::::::

For oemboot driven images: turn on or off the search for multipath devices: true/false (default is true)

Parents:
   These elements contain ``oem-multipath-scan``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-vmcp-parmfile:

oem-vmcp-parmfile
:::::::::::::::::

For oemboot driven images: provide the name of a parmfile which is loaded via cmsfscat on s390 systems. Default value is set to: PARM-S11

Parents:
   These elements contain ``oem-vmcp-parmfile``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-partition-install:

oem-partition-install
:::::::::::::::::::::

For oemboot driven images: install the system not as disk but into a free partition. If this option is set all other oem-* options concerning the partition table will not have any effect

Parents:
   These elements contain ``oem-partition-install``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-reboot:

oem-reboot
::::::::::

For oemboot driven images: reboot after first deployment true/false

Parents:
   These elements contain ``oem-reboot``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-reboot-interactive:

oem-reboot-interactive
::::::::::::::::::::::

For oemboot driven images: reboot after first deployment true/false

Parents:
   These elements contain ``oem-reboot-interactive``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-recovery:

oem-recovery
::::::::::::

For oemboot driven images: create a recovery archive yes/no

Parents:
   These elements contain ``oem-recovery``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-recoveryID:

oem-recoveryID
::::::::::::::

For oemboot driven images: Set the partition ID of recovery partition. Default value is 83 (Linux)

Parents:
   These elements contain ``oem-recoveryID``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-recovery-part-size:

oem-recovery-part-size
::::::::::::::::::::::

For oemboot driven images: Set the size of the recovery partition. Value is interpreted as MB

Parents:
   These elements contain ``oem-recovery-part-size``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-shutdown:

oem-shutdown
::::::::::::

For oemboot driven images: shutdown after first deployment  true/false

Parents:
   These elements contain ``oem-shutdown``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-shutdown-interactive:

oem-shutdown-interactive
::::::::::::::::::::::::

For oemboot driven images: shutdown after first deployment  true/false

Parents:
   These elements contain ``oem-shutdown-interactive``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-silent-boot:

oem-silent-boot
:::::::::::::::

For oemboot driven images: boot silently during the initial boot true/false

Parents:
   These elements contain ``oem-silent-boot``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-silent-install:

oem-silent-install
::::::::::::::::::

For oemboot driven images: do not show progress of the image dump process, true/false

Parents:
   These elements contain ``oem-silent-install``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-silent-verify:

oem-silent-verify
:::::::::::::::::

For oemboot driven images: do not show progress of the image verification process, true/false

Parents:
   These elements contain ``oem-silent-verify``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-skip-verify:

oem-skip-verify
:::::::::::::::

For oemboot driven images: do not perform the md5 verification process, true/false

Parents:
   These elements contain ``oem-skip-verify``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-swap:

oem-swap
::::::::

For oemboot driven images: use a swap partition yes/no

Parents:
   These elements contain ``oem-swap``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-swapsize:

oem-swapsize
::::::::::::

For oemboot driven images: Set the size of the swap partition in MB

Parents:
   These elements contain ``oem-swapsize``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-systemsize:

oem-systemsize
::::::::::::::

For oemboot driven images: Set the size of the system (root) partition in MB

Parents:
   These elements contain ``oem-systemsize``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-unattended:

oem-unattended
::::::::::::::

For oemboot driven images: don't ask questions if possible true/false

Parents:
   These elements contain ``oem-unattended``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.oemconfig.oem-unattended-id:

oem-unattended-id
:::::::::::::::::

For oemboot driven images: use the specified disk id the device is looked up in /dev/disk/by-* and /dev/mapper/*

Parents:
   These elements contain ``oem-unattended-id``: :ref:`k.image.preferences.type.oemconfig`


.. _k.image.preferences.type.pxedeploy:

pxedeploy
,,,,,,,,,

Controls the Image Deploy Process

Parents:
   These elements contain ``pxedeploy``: :ref:`k.image.preferences.type`

Children:
   The following elements occur in ``pxedeploy``: :ref:`timeout <k.image.preferences.type.pxedeploy.timeout>` `[?]`_, :ref:`kernel <k.image.preferences.type.pxedeploy.kernel>` `[?]`_, :ref:`initrd <k.image.preferences.type.pxedeploy.initrd>` `[?]`_, :ref:`partitions <k.image.preferences.type.pxedeploy.partitions>` `[?]`_, :ref:`union <k.image.preferences.type.pxedeploy.union>` `[?]`_, :ref:`configuration <k.image.preferences.type.pxedeploy.configuration>` `[*]`_

List of attributes for ``pxedeploy``:

* ``server`` `[?]`_: Name or IP Address of server for downloading the data
* ``blocksize`` `[?]`_: Blocksize value used for atftp downloads

.. _k.image.preferences.type.pxedeploy.timeout:

timeout
:::::::

Specifies an ATFTP Download Timeout

Parents:
   These elements contain ``timeout``: :ref:`k.image.preferences.type.pxedeploy`


.. _k.image.preferences.type.pxedeploy.kernel:

kernel
::::::

Specifies Where to Find the Boot Kernel

Parents:
   These elements contain ``kernel``: :ref:`k.image.preferences.type.pxedeploy`


.. _k.image.preferences.type.pxedeploy.initrd:

initrd
::::::

Specifies where the Boot Image can be Found

Parents:
   These elements contain ``initrd``: :ref:`k.image.preferences.type.pxedeploy`


.. _k.image.preferences.type.pxedeploy.partitions:

partitions
::::::::::

A List of Partitions

Parents:
   These elements contain ``partitions``: :ref:`k.image.preferences.type.pxedeploy`

Children:
   The following elements occur in ``partitions``: :ref:`partition <k.image.preferences.type.pxedeploy.partitions.partition>` `[+]`_

List of attributes for ``partitions``:

* ``device`` `[?]`_: As part of the network deploy configuration this section specifies the disk device name

.. _k.image.preferences.type.pxedeploy.partitions.partition:

partition
;;;;;;;;;

A Partition

Parents:
   These elements contain ``partition``: :ref:`k.image.preferences.type.pxedeploy.partitions`

List of attributes for ``partition``:

* ``type`` : Partition Type identifier, see parted for details
* ``number`` : Partition ID
* ``size`` `[?]`_: A partition size or optional image size
* ``mountpoint`` `[?]`_: Mount path for this partition
* ``target`` `[?]`_: Is a real target or not which means is part of the /etc/fstab file or not

.. _k.image.preferences.type.pxedeploy.union:

union
:::::

Specifies the Overlay Filesystem

Parents:
   These elements contain ``union``: :ref:`k.image.preferences.type.pxedeploy`

List of attributes for ``union``:

* ``ro`` : Device only for read-only 
* ``rw`` : Device for Read-Write
* ``type`` : 

.. _k.image.preferences.type.pxedeploy.configuration:

configuration
:::::::::::::

Specifies Configuration files

Parents:
   These elements contain ``configuration``: :ref:`k.image.preferences.type.pxedeploy`

List of attributes for ``configuration``:

* ``source`` : A source location where a package or configuration file can be found
* ``dest`` : Destination of a resource
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.preferences.type.size:

size
,,,,

Specifies the Size of an Image in (M)egabyte or (G)igabyte If the attribute additive is set the value will be added to the required size of the image

Parents:
   These elements contain ``size``: :ref:`k.image.preferences.type`

List of attributes for ``size``:

* ``unit`` `[?]`_: The unit of the image
* ``additive`` `[?]`_: 

.. _k.image.preferences.type.systemdisk:

systemdisk
,,,,,,,,,,

Specify volumes and size attributes

Parents:
   These elements contain ``systemdisk``: :ref:`k.image.preferences.type`

Children:
   The following elements occur in ``systemdisk``: :ref:`volume <k.image.preferences.type.systemdisk.volume>` `[*]`_

List of attributes for ``systemdisk``:

* ``name`` `[?]`_: Specify Volume group name, default is kiwiVG. This information is only used if the LVM volume management is used
* ``preferlvm`` `[?]`_: Prefer LVM even if the used filesystem has its own volume management system

.. _k.image.preferences.type.systemdisk.volume:

volume
::::::

Specify which parts of the filesystem should be on an extra volume.

Parents:
   These elements contain ``volume``: :ref:`k.image.preferences.type.containerconfig.volumes`, :ref:`k.image.preferences.type.systemdisk`

List of attributes for ``volume``:

* ``copy_on_write`` `[?]`_: Apply the filesystem copy-on-write attribute for this volume
* ``freespace`` `[?]`_: free space to be added to this volume. The value is used as MB by default but you can add "M" and/or "G" as postfix
* ``mountpoint`` `[?]`_: volume path. The mountpoint specifies a path which has to exist inside the root directory.
* ``name`` : volume name. The name of the volume. if mountpoint is not specified the name specifies a path which has to exist inside the root directory.
* ``size`` `[?]`_: absolute size of the volume. If the size value is too small to store all data kiwi will exit. The value is used as MB by default but you can add "M" and/or "G" as postfix

.. _k.image.preferences.type.vagrantconfig:

vagrantconfig
,,,,,,,,,,,,,

Specifies the Vagrant configuration section

Parents:
   These elements contain ``vagrantconfig``: :ref:`k.image.preferences.type`

List of attributes for ``vagrantconfig``:

* ``provider`` : The vagrant provider for this box
* ``virtualsize`` : The vagrant virtual image size in GB
* ``boxname`` `[?]`_: The boxname as it's written into the json file If not specified the image name is used

.. _k.image.preferences.version:

version
.......

A Version Number for the Image, Consists of Major.Minor.Release 

Parents:
   These elements contain ``version``: :ref:`k.image.preferences`


.. _k.image.profiles:

profiles
________

Creates Namespace Section for Drivers

Parents:
   These elements contain ``profiles``: :ref:`k.image`

Children:
   The following elements occur in ``profiles``: :ref:`profile <k.image.profiles.profile>` `[+]`_


.. _k.image.profiles.profile:

profile
.......

Creates Profiles

Parents:
   These elements contain ``profile``: :ref:`k.image.profiles`

List of attributes for ``profile``:

* ``name`` : A name
* ``description`` : Description of how this profiles influences the image
* ``import`` `[?]`_: Import profile by default if no profile was set on the command line

.. _k.image.users:

users
_____

A List of Users

Parents:
   These elements contain ``users``: :ref:`k.image`

Children:
   The following elements occur in ``users``: :ref:`user <k.image.users.user>` `[+]`_

List of attributes for ``users``:

* ``profiles`` `[?]`_: A profile name which binds the section to this name

.. _k.image.users.user:

user
....

A User with Name, Password, Path to Its Home And Shell

Parents:
   These elements contain ``user``: :ref:`k.image.users`

List of attributes for ``user``:

* ``groups`` `[?]`_: The list of groups that he user belongs to. The frist item in the list is used as the login group. If 'groups' is not present a default group is assigned to the user according to he specifing toolchain behaviour.
* ``home`` : The home directory for this user
* ``id`` `[?]`_: The user ID for this user
* ``name`` : A name
* ``password`` `[?]`_: The password
* ``pwdformat`` `[?]`_: Format of the given password, encrypted is the default
* ``realname`` `[?]`_: The name of an user
* ``shell`` `[?]`_: The shell for this user

.. _k.image.drivers:

drivers
_______

A Collection of Driver Files 

Parents:
   These elements contain ``drivers``: :ref:`k.image`

Children:
   The following elements occur in ``drivers``: :ref:`file <k.image.drivers.file>` `[+]`_

List of attributes for ``drivers``:

* ``profiles`` `[?]`_: A profile name which binds the section to this name

.. _k.image.drivers.file:

file
....

A Pointer to a File

Parents:
   These elements contain ``file``: :ref:`k.image.drivers`, :ref:`k.image.strip`

List of attributes for ``file``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.strip:

strip
_____

A Collection of files to strip

Parents:
   These elements contain ``strip``: :ref:`k.image`

Children:
   The following elements occur in ``strip``: :ref:`file <k.image.strip.file>` `[+]`_

List of attributes for ``strip``:

* ``type`` : 
* ``profiles`` `[?]`_: A profile name which binds the section to this name

.. _k.image.strip.file:

file
....

A Pointer to a File

Parents:
   These elements contain ``file``: :ref:`k.image.drivers`, :ref:`k.image.strip`

List of attributes for ``file``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.repository:

repository
__________

The Name of the Repository

Parents:
   These elements contain ``repository``: :ref:`k.image`

Children:
   The following elements occur in ``repository``: :ref:`source <k.image.repository.source>` 

List of attributes for ``repository``:

* ``type`` `[?]`_: Type of repository
* ``profiles`` `[?]`_: A profile name which binds the section to this name
* ``status`` `[?]`_: Specifies the status of the repository. This can be replaceable or if not specified it's a must have repository
* ``alias`` `[?]`_: Alias name to be used for this repository. This is an optional free form text. If not set the source attribute value is used and builds the alias name by replacing each '/' with a '_'. An alias name should be set if the source argument doesn't really explain what this repository contains
* ``components`` `[?]`_: Distribution components, used for deb repositories. If not set it defaults to main
* ``distribution`` `[?]`_: Distribution name information, used for deb repositories
* ``imageinclude`` `[?]`_: Specify whether or not this repository should be configured in the resulting image. Boolean value true or false, the default is false.
* ``prefer-license`` `[?]`_: Use the license found in this repository, if any, as the license installed in the image
* ``priority`` `[?]`_: Channel priority assigned to all packages available in this channel (0 if not set). If the exact same package is available in more than one channel, the highest priority is used
* ``password`` `[?]`_: The password
* ``username`` `[?]`_: A name of a user

.. _k.image.repository.source:

source
......

A Pointer to a data source. This can be a remote location as well as a path specification

Parents:
   These elements contain ``source``: :ref:`k.image.repository`

List of attributes for ``source``:

* ``path`` : A path

.. _k.image.packages:

packages
________

Specifies Packages/Patterns Used in Different Stages

Parents:
   These elements contain ``packages``: :ref:`k.image`

Children:
   The following elements occur in ``packages``: :ref:`archive <k.image.packages.archive>` `[*]`_, :ref:`ignore <k.image.packages.ignore>` `[*]`_, :ref:`namedCollection <k.image.packages.namedCollection>` `[*]`_, :ref:`product <k.image.packages.product>` `[*]`_, :ref:`package <k.image.packages.package>` `[*]`_

List of attributes for ``packages``:

* ``type`` : 
* ``profiles`` `[?]`_: A profile name which binds the section to this name
* ``patternType`` `[?]`_: Selection type for patterns. Could be onlyRequired or plusRecommended

.. _k.image.packages.archive:

archive
.......

Name of an image archive file (tarball)

Parents:
   These elements contain ``archive``: :ref:`k.image.packages`

List of attributes for ``archive``:

* ``name`` : A name
* ``bootinclude`` `[?]`_: Indicates that this package should be part of the boot image (initrd) too. This attribute can be used to include for example branding packages specified in the system image description to become part of the boot image also

.. _k.image.packages.ignore:

ignore
......

Ignores a Package

Parents:
   These elements contain ``ignore``: :ref:`k.image.packages`

List of attributes for ``ignore``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.packages.namedCollection:

namedCollection
...............

Name of a Pattern for SUSE or a Group for RH

Parents:
   These elements contain ``namedCollection``: :ref:`k.image.packages`

List of attributes for ``namedCollection``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.packages.product:

product
.......

Name of a Product From openSUSE

Parents:
   These elements contain ``product``: :ref:`k.image.packages`

List of attributes for ``product``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"

.. _k.image.packages.package:

package
.......

Name of an image Package

Parents:
   These elements contain ``package``: :ref:`k.image.packages`

List of attributes for ``package``:

* ``name`` : A name
* ``arch`` `[?]`_: A system architecture name, matching the 'uname -m' information Multiple architectures can be combined as comma separated list e.g arch="x86_64,ix86"
* ``replaces`` `[?]`_: Replace package with some other package
* ``bootdelete`` `[?]`_: Indicates that this package should be removed from the boot image (initrd). the attribute is only evaluated if the bootinclude attribute is specified along with it too
* ``bootinclude`` `[?]`_: Indicates that this package should be part of the boot image (initrd) too. This attribute can be used to include for example branding packages specified in the system image description to become part of the boot image also

.. _k.image.extension:

extension
_________

Define custom XML extensions

Parents:
   These elements contain ``extension``: :ref:`k.image`


