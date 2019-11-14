.. _xml-description:

The Image Description
=====================

The image description is a XML file that defines properties of the
appliance that will be build by KIWI, for example:

- image type (e.g. QEMU disk image, PXE bootable image, Vagrant box, etc.)
- partition layout
- packages to be installed on the system
- users to be added

The following sections will walk you through the major elements and
attributes of the RELAX NG schema [#f1]_. A complete description of the
schema can be found in :ref:`schema-docs`.

We will follow the standard nomenclature when addressing components of the
XML file:

- An *element* is a XML "tag": `<example/>`, which we address by the name
  *example*.

- Elements can have *attributes* which take values:
  `<example attr1="val1" attr2=val2"/>`.

- Elements can have *children*:

  .. code:: xml

     <element>
       <child/>
     </element>

- Some elements have a *content*:
  `<element_with_content>CONTENT</element_with_content>`, while others are
  *emtpy-element tags*: `<emtpy_element/>`.


The `image` Element
===================

The image description consists of the root element `image` and its
children, for example:

.. code:: xml

   <?xml version="1.0" encoding="utf-8"?>

   <image schemaversion="7.1" name="{exc_image_base_name}">
       <!-- all settings belong here -->
   </image>

The `image` element requires the following two attributes (as shown in the
above example):

- `name`: A name for this image that must not contain spaces or `/`.

- `schemaversion`: The used version of the [KIWI] RNG schema. KIWI will
  automatically convert your image description from an older schema
  version to the most recent one (it will perform this only internally and
  won't modify your :file:`config.xml`).
  If in doubt, use the latest schema version.

The `name` attribute will be used to create the bootloader entry, however
it can be inconvenient to use as it must be POSIX-safe. You can therefore
provide an alternative name that will be displayed in the bootloader via
the attribute `displayName`, which doesn't have the same strict rules as
`name` (it can contain spaces and slashes):

.. code:: xml

   <?xml version="1.0" encoding="utf-8"?>

   <image schemaversion="{schema_version}" name="{exc_image_base_name}" displayName="{exc_image_base_name}">
       <!-- all setting belong here -->
   </image>


The `description` Element
=========================

The `description` element, contains some high level information about the
image:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <description type="system">
           <author>Jane Doe</author>
           <contact>jane@myemaildomain.xyz</contact>
           <specification>
               {exc_image_base_name}, a small image
           </specification>
           <license>GPLv3</license>
       </description>
       <!-- snip -->
   </image>


The `description` element must always contain a `type` attribute. This
attribute accepts the values `system` or `boot`. The value `boot` is used
by the KIWI developers and is not relevant for the end user, thus `type`
should be always set to `system`.

`description` allows the following optional children:

- `author`: The name of the author of this image.

- `contact`: Some means how to contact the author of the image (e.g. an
  email address, an IM nickname and network, etc.)

- `specification`: A detailed description of this image, e.g. its use case.

- `license`: If applicable, you can specify a license for the image.


The `preferences` Element
=========================

The mandatory `preferences` element contains the definition of the various
enabled image types (so-called build types). Each of these build types can
be supplied with attributes specific to that image type, which we described
in the section :ref:`xml-description-build-types`.

The elements that are not image type specific are presented afterwards in
section :ref:`xml-description-preferences-common-elements`.


.. _xml-description-build-types:

Build Types
-----------

A build type defines the type of an appliance that is produced by KIWI, for
instance, a live ISO image or a virtual machine disk.

For example, a live ISO image is specified as follows:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <preferences>
           <type image="iso" primary="true" flags="overlay" hybridpersistent_filesystem="ext4" hybridpersistent="true"/>
           <!-- additional preferences -->
       </preferences>
       <!-- additional image settings -->
   </image>

A build type is defined via a single `type` element whose only required
attribute is `image`, that defines which image type is created. All other
attributes are optional and can be used to customize an image further. In
the above example we created an ISO image, with the an ext4 filesystem
[#f2]_.

It is possible to provide **multiple** `type` elements with **different**
`image` attributes inside the preferences section. The following XML
snippet can be used to create a live image, an OEM installation image, and
a virtual machine disk of the same appliance:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <preferences>
           <!-- Live ISO -->
           <type image="iso" primary="true" flags="overlay" hybridpersistent_filesystem="ext4" hybridpersistent="true"/>

           <!-- Virtual machine -->
           <type image="vmx" filesystem="ext4" bootloader="grub2" kernelcmdline="splash" firmware="efi"/>

           <!-- OEM installation image -->
           <type image="oem" filesystem="ext4" initrd_system="dracut" installiso="true" bootloader="grub2" kernelcmdline="splash" firmware="efi">
               <oemconfig>
                   <oem-systemsize>2048</oem-systemsize>
                   <oem-swap>true</oem-swap>
                   <oem-device-filter>/dev/ram</oem-device-filter>
                   <oem-multipath-scan>false</oem-multipath-scan>
               </oemconfig>
               <machine memory="512" guestOS="suse" HWversion="4"/>
           </type>
           <!-- additional preferences -->
       </preferences>

       <!-- additional image settings -->
   </image>

Note the additional attribute `primary` in the Live ISO image build
type. KIWI will by default build the image which `primary` attribute is set
to `true`.

KIWI supports the following values for the `image` attribute (further
attributes of the `type` element are documented inside the referenced
sections):

- `iso`: a live ISO image, see :ref:`hybrid_iso`
- `vmx`: build a virtual machine image, see: :ref:`vmx`
- `oem`: results in an expandable image that can be deployed via a bootable
  installation medium, e.g. a USB drive or a CD. See :ref:`oem`
- `pxe`: creates an image that can be booted via PXE (network boot), see
  :ref:`build_pxe`

- `docker`, `oci`: container images, see :ref:`building-docker-build`

- `btrfs`, `ext2`, `ext3`, `ext4`, `xfs`: KIWI will convert the
  image into a mountable filesystem of the specified type.

- `squashfs`, `clicfs`: creates the image as a filesystem that can be used
  in live systems

- `tbz`, `cpio`: the unpacked source tree will be compressed into a `XZ
  <https://en.wikipedia.org/wiki/Xz>`_ or `CPIO
  <https://en.wikipedia.org/wiki/Cpio>`_ archive.


The `type` element furthermore supports the following subelements (as shown
above, `oemconfig` is a subelement of `<type image="oem" ...>`):

- `containerconfig`: contains settings specific for the creation of
  container images, see :ref:`building-docker-build`

- `oemconfig`: configurations relevant for building OEM images, see:
  :ref:`oem`

- `pxedeploy`: settings for PXE booting, see :ref:`build_pxe`

- `vagrantconfig`: instructs KIWI to build a Vagrant box instead of a
  standard virtual machine image, see :ref:`setup_vagrant`

- `systemdisk`: used to define LVM or Btrfs (sub)volumens, see
  :ref:`custom_volumes`

- `machine`: for configurations of the virtual machines, see
  :ref:`vmx-the-machine-element`

- `size`: for adjusting the size of the final image, see
  :ref:`vmx-the-size-element`.


Common attributes of the `type` element
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `type` element supports a plethora of optional attributes, some of
these are only relevant for certain build types and will be covered in the
appropriate place. Certain attributes are however useful for nearly all
build types and will be covered here:

- `bootloader`: Specifies the bootloader used for booting the image. At
  the moment `grub2`, `zipl` and `grub2_s390x_emu` (a combination of zipl
  and a userspace GRUB2) are supported.
  The special `custom` entry allows to skip the bootloader configuration
  and installation and leaves this up to the user which can be done by
  using the `editbootinstall` and `editbootconfig` custom scripts.

- `boottimeout`: Specifies the boot timeout in seconds prior to launching
  the default boot option. By default the timeout is set to 10 seconds. It
  makes sense to set this value to `0` for images intended to be started
  non-interactively (e.g. virtual machines).

- `bootpartition`: Boolean parameter notifying KIWI whether an extra boot
  partition should be used or not (the default depends on the current
  layout). This will override KIWI's default layout.

- `btrfs_quota_groups`: Boolean parameter to activate filesystem quotas if
  the filesystem is `btrfs`. By default quotas are inactive.

- `btrfs_root_is_snapshot`: Boolean parameter that tells KIWI to install
  the system into a btrfs snapshot. The snapshot layout is compatible with
  snapper. By default snapshots are turned off.

- `btrfs_root_is_readonly_snapshot`: Boolean parameter notifying KIWI that
  the btrfs root filesystem snapshot has to made read-only. if this option
  is set to true, the root filesystem snapshot it will be turned into
  read-only mode, once all data has been placed to it. The option is only
  effective if `btrfs_root_is_snapshot` is also set to true. By default the
  root filesystem snapshot is writable.

- `compressed`: Specifies whether the image output file should be
  compressed or not. This option is only used for filesystem only images or
  for the `pxe` or `cpio` types.

- `editbootconfig`: Specifies the path to a script which is called right
  before the bootloader is installed. The script runs relative to the
  directory which contains the image structure.

- `editbootinstall`: Specifies the path to a script which is called right
  after the bootloader is installed. The script runs relative to the
  directory which contains the image structure.

- `filesystem`: The root filesystem, the following file systems are
  supported: `btrfs`, `ext2`, `ext3`, `ext4`, `squashfs` and `xfs`.

- `firmware` Specifies the boot firmware of the appliance, supported
  options are: `bios`, `ec2`, `efi`, `uefi`, `ofw` and `opal`.
  This attribute is used to differentiate the image according to the
  firmware which boots up the system. It mostly impacts the disk
  layout and the partition table type. By default `bios` is used on x86,
  `ofw` on PowerPC and `efi` on ARM.

- `force_mbr`: Boolean parameter to force the usage of a MBR partition
  table even if the system would default to GPT. This is occasionally
  required on ARM systems that use a EFI partition layout but which must
  not be stored in a GPT. Note that forcing a MBR partition table incurs
  limitations with respect to the number of available partitions and their
  sizes.

- `fsmountoptions`: Specifies the filesystem mount options which are passed
  via the `-o` flag to :command:`mount` and are included in
  :file:`/etc/fstab`.

- `fscreateoptions`: Specifies the filesystem options used to create the
  filesystem. In KIWI the filesystem utility to create a filesystem is
  called without any custom options. The default options are filesystem
  specific and are provided along with the package that provides the
  filesystem utility. For the Linux `ext[234]` filesystem, the default
  options can be found in the :file:`/etc/mke2fs.conf` file. Other
  filesystems provides this differently and documents information
  about options and their defaults in the respective manual page, e.g
  :command:`man mke2fs`. With the `fscreateoptions` attribute it's possible
  to directly influence how the filesystem will be created. The options
  provided as a string are passed to the command that creates the
  filesystem without any further validation by KIWI. For example, to turn
  off the journal on creation of an ext4 filesystem the following option
  would be required:

  .. code:: xml

      <type fscreateoptions="-O ^has_journal"/>

- `kernelcmdline`: Additional kernel parameters passed to the kernel by the
  bootloader.

- `luks`: Supplying a value will trigger the encryption of the partitions
  using the LUKS extension and using the provided string as the
  password. Note that the password must be entered when booting the
  appliance!

- `primary`: Boolean option, KIWI will by default build the image which
  `primary` attribute is set to `true`.

- `target_blocksize`: Specifies the image blocksize in bytes which has to
  match the logical blocksize of the target storage device. By default 512
  Bytes is used, which works on many disks. You can obtain the blocksize
  from the `SSZ` column in the output of the following command:

  .. code:: shell-session

     blockdev --report $DEVICE


.. _xml-description-preferences-common-elements:

Common Elements
---------------

Now that we have covered the `type` element, we shall return to the
remaining child-elements of `preferences`:

- `version`: A version number of this image. We recommend to use the
  following format: **Major.Minor.Release**, however other versioning
  schemes are possible, e.g. one can use the version of the underlying
  operating system.

- `packagemanager`: Specify the package manager that will be used to download
  and install the packages for your appliance. Currently the following package
  managers are supported: ``apt-get``, ``zypper`` and ``dnf``. Note that the
  package manager must be installed on the system **calling** KIWI, it is
  **not** sufficient to install it inside the appliance.

- `locale`: Specify the locale that the resulting appliance will use.

- `timezone`: Override the default timezone of the image to a more suitable
  value, e.g. the timezone in which the image's users reside.

- `rpm-check-signatures`: Boolean value that defines whether the signatures
  of the downloaded RPM packages will be verified before installation.
  Note that when building appliances for a different distribution you will
  have to either import the other distribution's signing-key or set this to
  `false` (RPM will otherwise fail to verify the package signatures, as it
  does will not trust the signature key of other distributions or even
  other versions of the same distribution).

- `rpm-excludedocs`: Boolean value that instructs RPM whether to install
  documentation with packages or not. Please bear in mind that enabling
  this can have quite a negative impact on user-experience and should thus
  be used with care.

- `bootloader-theme` and `bootsplash-theme`: themes for the bootloader and
  the bootsplash-screen. These themes have to be either built-in to the
  bootloader or installed via the `packages` section.


An example excerpt from a image description using these child-elements of
`preferences`, results in the following image description:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <preferences>
           <version>15.0</version>
           <packagemanager>zypper</packagemanager>
           <locale>en_US</locale>
           <keytable>us</keytable>
           <timezone>Europe/Berlin</timezone>
           <rpm-excludedocs>true</rpm-excludedocs>
           <rpm-check-signatures>false</rpm-check-signatures>
           <bootsplash-theme>openSUSE</bootsplash-theme>
           <bootloader-theme>openSUSE</bootloader-theme>
           <type image="vmx" filesystem="ext4" format="qcow2" boottimeout="0" bootloader="grub2">
       </preferences>
       <!-- snip -->
   </image>

.. _xml-description-image-profiles:

Image Profiles
==============

In the previous section we have covered build types, that are represented
in the image description as the `type` element. We have also shown how it
is possible to include multiple build types in the same
appliance. Unfortunately that approach has one significant limitation: one
can only include multiple build types with **different** settings for the
attribute `image`.

In certain cases this is undesirable, for instance when building multiple
very similar virtual machine disks. Then one would have to duplicate the
whole :file:`config.xml` for each virtual machine. KIWI supports *profiles*
to work around this issue.

A *profile* is a namespace for additional settings that can be applied by
KIWI on top of the default settings (or other profiles), thereby allowing
to build multiple appliances with the same build type but with different
configurations.

In the following example, we create two virtual machine images: one for
QEMU (using the `qcow2` format) and one for VMWare (using the `vmdk`
format).

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <profiles>
           <profile name="QEMU" description="virtual machine for QEMU"/>
           <profile name="VMWare" description="virtual machine for VMWare"/>
       </profiles>
       <preferences>
           <version>15.0</version>
           <packagemanager>zypper</packagemanager>
       </preferences>
       <preferences profiles="QEMU">
           <type image="vmx" format="qcow2" filesystem="ext4" bootloader="grub2">
       </preferences>
       <preferences profiles="VMWare">
           <type image="vmx" format="vmdk" filesystem="ext4" bootloader="grub2">
       </preferences>
       <!-- snip -->
   </image>

Each profile is declared via the element `profile`, which itself must be a
child of `profiles` and must contain the `name` and `description`
attributes. The `description` is only present for documentation purposes,
`name` on the other hand is used to instruct KIWI which profile to build
via the command line. Additionally, one can provide the boolean attribute
`import`, which defines whether this profile should be used by default when
KIWI is invoked via the command line.

A profile inherits the default settings which do not belong to any
profile. It applies only to elements that contain the profile in their
`profiles` attribute. The attribute `profiles` expects a comma separated
list of profiles for which the settings of this element apply. The
attribute is present in the following elements only:

- `preferences`
- `drivers`
- `repository` and `packages` (see
  :ref:`xml-description-repositories-and-packages`)
- `users`

Profiles can furthermore inherit settings from another profile via the
`requires` sub-element:

.. code:: xml

   <profiles>
       <profile name="VM" description="virtual machine"/>
       <profile name="QEMU" description="virtual machine for QEMU">
           <requires profile="VM"/>
       </profile>
   </profiles>

The profile `QEMU` would inherit the settings from `VM` in the above
example.

We cover the usage of *profiles* when invoking KIWI and when building in
the Open Build Service in :ref:`building-build-with-profiles`.

.. _xml-description-adding-users:

Adding Users
============

User accounts can be added or modified via the `users` element, which
supports a list of multiple `user` child elements:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <users>
           <user
               password="this_is_soo_insecure"
               home="/home/me" name="me"
               groups="users" pwdformat="plain"
           />
           <user
               password="$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
               home="/root" name="root" groups="root"
           />
       </users>
   </image>

Each `user` element represents a specific user that is added or
modified. The following attributes are mandatory:

- `name`: the UNIX username

- `home`: the path to the user's home directory

Additionally, the following optional attributes can be specified:

- `groups`: A comma separated list of UNIX groups. The first element of the
  list is used as the user's primary group. The remaining elements are
  appended to the user's supplementary groups. When no groups are assigned
  then the system's default primary group will be used.

- `id`: The numeric user id of this account.

- `pwdformat`: The format in which `password` is provided, either `plain`
  or `encrypted` (the latter is the default).

- `password`: The password for this user account. It can be provided either
  in cleartext form (`pwdformat="plain"`) or in `crypt`'ed form
  (`pwdformat="encrypted"`). Plain passwords are discouraged, as everyone
  with access to the image description would know the password. It is
  recommended to generate a hash of your password, e.g. using the
  ``mkpasswd`` tool (available in most Linux distributions via the
  ``whois`` package):

  .. code:: bash

     $ mkpasswd -m sha-512 -S $(date +%N) -s <<< INSERT_YOUR_PASSWORD_HERE


The `users` element furthermore accepts a list of profiles (see
:ref:`xml-description-image-profiles`) to which it applies via the
`profiles` attribute, as shown in the following example:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <profiles>
           <profile name="VM" description="standard virtual machine"/>
           <profile name="shared_VM" description="virtual machine shared by everyone"/>
       </profiles>
       <!-- snip -->
       <users>
           <user
               password="$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
               home="/root" name="root" groups="root"
           />
       </users>
       <users profiles="VM">
           <user
               password="$1$blablabl$FRTFJZxMPfM6LA1g0EZ5h1"
               home="/home/devel" name="devel"
           />
       </users>
       <users profiles="shared_VM">
           <user
               password="super_secr4t" pwdformat="plain"
               home="/share/devel" name="devel" groups="users,devel"
           />
       </users>
   </image>

Here the settings for the root user are shared among all appliances. The
configuration of the `devel` user on the other hand depends on the profile.


.. _xml-description-repositories-and-packages:

Defining Repositories and Adding or Removing Packages
=====================================================

A crucial part of each appliance is the package and repository
selection. KIWI allows the end user to completely customize the selection
of repositories and packages via the `repository` and `packages` elements.


Adding repositories
-------------------

KIWI installs packages into your appliance from the repositories defined in
the image description. Therefore at least one repository **must** be
defined, as KIWI will otherwise not be able to fetch any packages.

A repository is added to the description via the `repository` element,
which is a child of the top-level `image` element:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <repository type="rpm-md" alias="kiwi" priority="1">
           <source path="{exc_kiwi_repo}"/>
       </repository>
       <repository type="rpm-md" alias="OS" imageinclude="true">
           <source path="{exc_repo}"/>
       </repository>
   </image>

In the above snippet we defined two repositories:

1. The repository belonging to the KIWI project:
   *{exc_kiwi_repo}* at the Open Build Service (OBS)

2. The RPM repository belonging to the OS project:
   *{exc_repo}*, at the Open Build Service (OBS). The translated
   http URL will also be included in the final appliance.

The `repository` element accepts one `source` child element, which
contains the URL to the repository in an appropriate format and the
following optional attributes:

- `type`: repository type, accepts one of the following values: `apt-deb`,
  `apt-rpm`, `deb-dir`, `mirrors`, `rpm-dir`, `rpm-md`.
  For ordinary RPM repositories use `rpm-md`, for ordinary APT repositories
  `apt-deb`.

- `imageinclude`: Specify whether this repository should be added to the
  resulting image, defaults to false.

- `imageonly`: A repository with `imageonly="true"` will not be available
  during image build, but only in the resulting appliance. Defaults to
  false.

- `priority`: An integer priority for all packages in this repository. If
  the same package is available in more than one repository, then the one
  with the highest priority is used.

- `alias`: Name to be used for this repository, it will appear as the
  repository's name in the image, which is visible via ``zypper repos`` or
  ``dnf repolist``. KIWI will construct an alias from the path in the
  `source` child element (replacing each `/` with a `_`), if no value is
  given.

- `repository_gpgcheck`: Specify whether or not this specific repository is
  configured to to run repository signature validation. If not set, the
  package manager's default is used.

- `package_gpgcheck`: Boolean value that specifies whether each package's
  GPG signature will be verified. If omitted, the package manager's default
  will be used

- `components`: Distribution components used for `deb` repositories,
  defaults to `main`.

- `distribution`: Distribution name information, used for deb repositories.

- `profiles`: List of profiles to which this repository applies.

.. _xml-description-supported-supported-repository-paths:

Supported repository paths
^^^^^^^^^^^^^^^^^^^^^^^^^^

The actual location of a repository is specified in the `source` child
element of `repository` via its only attribute `path`. KIWI supports the
following paths types:

- `http://URL` or `https://URL` or `ftp://URL`: a URL to the repository
  available via HTTP(s) or FTP.

- `obs://$PROJECT/$REPOSITORY`: evaluates to the repository `$REPOSITORY`
  of the project `$PROJECT` available on the Open Build Service (OBS). By
  default KIWI will look for projects on `build.opensuse.org
  <https://build.opensuse.org>`_, but this can be overridden using the
  runtime configuration file (see :ref:`The Runtime Configuration
  File<working-with-kiwi-runtime-configuration-file>`).
  Note that it is not possible to add repositories using the `obs://` path
  from **different** OBS instances (use direct URLs to the :file:`.repo`
  file instead in this case).

- `obsrepositories:/`: special path only available for builds using the
  Open Build Service. The repositories configured for the OBS project in
  which the KIWI image resides will be available inside the appliance. This
  allows you to configure the repositories of your image from OBS itself
  and not having to modify the image description.

- `dir:///path/to/directory` or `file:///path/to/file`: an absolute path to
  a local directory or file available on the host building the
  appliance.

- `iso:///path/to/image.iso`: the specified ISO image will be mounted
  during the build of the KIWI image and a repository will be created
  pointing to the mounted ISO.


.. _xml-description-adding-and-removing-packages:

Adding and removing packages
----------------------------

Now that we have defined the repositories, we can define which packages
should be installed on the image. This is achieved via the `packages`
element which includes the packages that should be installed, ignore or
removed via individual `package` child elements:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <packages type="bootstrap">
           <package name="udev"/>
           <package name="filesystem"/>
           <package name="openSUSE-release"/>
           <!-- additional packages installed before the chroot is created -->
       </packages>
       <packages type="image">
           <package name="patterns-openSUSE-base"/>
           <!-- additional packages to be installed into the chroot -->
       </packages>
   </image>

The `packages` element provides a collection of different child elements
that instruct KIWI when and how to perform package installation or
removal. Each `packages` element acts as a group, whose behavior can be
configured via the following attributes:

- `type`: either `bootstrap`, `image`, `delete`, `uninstall` or one of the
  following build types: `docker`, `iso`, `oem`, `pxe`, `vmx`, `oci`.

  Packages for `type="bootstrap"` are pre-installed to populate the images'
  root file system before chrooting into it.

  Packages in `type="image"` are installed immediately after the initial
  chroot into the new root file system.

  Packages in `type="delete"` and `type="uninstall"` are removed from the
  image, for details see :ref:`xml-description-uninstall-system-packages`.

  And packages which belong to a build type are only installed when that
  specific build type is currently processed by KIWI.

- `profiles`: a list of profiles to which this package selection applies
  (see :ref:`xml-description-image-profiles`).

- `patternType`: selection type for patterns, supported values are:
  `onlyRequired`, `plusRecommended`, see:
  :ref:`xml-description-product-and-namedCollection-element`.

We will describe the different child elements of `packages` in the following
sections.

.. _xml-description-package-element:

The `package` element
^^^^^^^^^^^^^^^^^^^^^

The `package` element represents a single package to be installed (or
removed), whose name is specified via the mandatory `name` attribute:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="bootstrap">
           <package name="udev"/>
       </packages>
   </image>

which adds the package `udev` to the list of packages to be added to the
initial filesystem. Note, that the value that you pass via the `name`
attribute is passed directly to the used package manager. Thus, if the
package manager supports other means how packages can be specified, you may
pass them in this context too. For example, RPM based package managers
(like :command:`dnf` or :command:`zypper`) can install packages via their
`Provides:`. This can be used to add a package that provides a certain
capability (e.g. `Provides: /usr/bin/my-binary`) via:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="bootstrap">
           <package name="/usr/bin/my-binary"/>
       </packages>
   </image>

Whether this works depends on the package manager and on the environment
that is being used. In the Open Build Service, certain `Provides` either
are not visible or cannot be properly extracted from the KIWI
description. Therefore, relying on `Provides` is not recommended.

Packages can also be included only on specific architectures via the `arch`
attribute. KIWI compares the `arch` attributes value with the output of
`uname -m`.

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="image">
           <package name="grub2"/>
           <package name="grub2-x86_64-efi" arch="x86_64"/>
           <package name="shim" arch="x86_64"/>
       </packages>
   </image>

which results in `grub2-x86_64-efi` and `shim` being only installed on 64
Bit images, but GRUB2 also on 32 Bit images.


.. _xml-description-archive-element:

The `archive` element
^^^^^^^^^^^^^^^^^^^^^

It is sometimes necessary to include additional packages into the image
which are not available in the package manager's native format. KIWI
supports the inclusion of ordinary archives via the `archive` element,
whose `name` attribute specifies the filename of the archive (KIWI looks
for the archive in the image description folder).

.. code:: xml

   <packages type="image">
       <archive name="custom-program1.tgz"/>
       <archive name="custom-program2.tar"/>
   </packages>

KIWI will extract the archive into the root directory of the image using
`GNU tar <https://www.gnu.org/software/tar/>`_, thus only archives
supported by it can be included. When multiple `archive` elements are
specified then they will be applied in a top to bottom order. If a file is
already present in the image, then the file from the archive will overwrite
it (same as with the image overlay).

.. _xml-description-uninstall-system-packages:

Uninstall System Packages
^^^^^^^^^^^^^^^^^^^^^^^^^

KIWI supports two different methods how packages can be removed from the
appliance:

1. Packages present as a child element of `<packages type="uninstall">`
   will be gracefully uninstalled by the package manager alongside with
   dependent packages and orphaned dependencies.

2. Packages present as a child element of `<packages type="delete">` will
   be removed by RPM/DPKG without any dependency check, thus potentially
   breaking dependencies and compromising the underlying package database.

Both types of removals take place after :file:`config.sh` is run in the
:ref:`prepare step <prepare-step>` (see also
:ref:`working-with-kiwi-user-defined-scripts`).

.. warning::

   An `uninstall` packages request deletes:

     * the listed packages,
     * the packages dependent on the listed ones, and
     * any orphaned dependency of the listed packages.

   Use this feature with caution as it can easily cause the removal of
   sensitive tools leading to failures in later build stages.


Removing packages via `type="uninstall"` can be used to completely remove a
build time tool (e.g. a compiler) without having to specify a all
dependencies of that tool (as one would have when using
`type="delete"`). Consider the following example where we wish to compile a
custom program in :file:`config.sh`. We ship its source code via an
`archive` element and add the build tools (`ninja`, `meson` and `clang`) to
`<packages type="image">` and `<packages type="uninstall">`:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="image">
           <package name="ca-certificates"/>
           <package name="coreutils"/>
           <package name="ninja"/>
           <package name="clang"/>
           <package name="meson"/>
           <archive name="foo_app_sources.tar.gz"/>
       </packages>
       <!-- These packages will be uninstalled after running config.sh -->
       <packages type="uninstall">
           <package name="ninja"/>
           <package name="meson"/>
           <package name="clang"/>
       </packages>
   </image>

The tools `meson`, `clang` and `ninja` are then available during the
:ref:`prepare step <prepare-step>` and can thus be used in
:file:`config.sh` (for further details, see
:ref:`working-with-kiwi-user-defined-scripts`), for example to build
``foo_app``:

.. code:: bash

   pushd /opt/src/foo_app
   mkdir build
   export CC=clang
   meson build
   cd build && ninja && ninja install
   popd

The `<packages type="uninstall">` element will make sure that the final
appliance will no longer contain our tools required to build ``foo_app``,
thus making our image smaller.

There are also other use cases for `type="uninstall"`, especially for
specialized appliances. For containers one can often remove the package
`shadow` (it is required to setup new user accounts) or any left over
partitioning tools (`parted` or `fdisk`). All networking tools can be
safely uninstalled in images for embedded devices without a network
connection.

.. _xml-description-product-and-namedCollection-element:

The `product` and `namedCollection` element
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

KIWI supports the inclusion of openSUSE products or of namedCollections
(*patterns* in SUSE based distributions or *groups* for RedHat based
distributions). These can be added via the `product` and `namedCollection`
child elements, which both take the mandatory `name` attribute and the
optional `arch` attribute.

`product` and `namedCollection` can be utilized to shorten the list of
packages that need to be added to the image description tremendously. A
named pattern, specified with the namedCollection element is a
representation of a predefined list of packages. Specifying a pattern will
install all packages listed in the named pattern. Support for patterns is
distribution specific and available in SLES, openSUSE, CentOS, RHEL and
Fedora. The optional `patternType` attribute on the packages element allows
you to control the installation of dependent packages. You may assign one
of the following values to the `patternType` attribute:

- `onlyRequired`: Incorporates only patterns and packages that the
  specified patterns and packages require. This is a "hard dependency" only
  resolution.

- `plusRecommended`: Incorporates patterns and packages that are required
  and recommended by the specified patterns and packages.


The `ignore` element
^^^^^^^^^^^^^^^^^^^^

Packages can be explicitly marked to be ignored for installation inside a
`packages` collection. This useful to exclude certain packages from being
installed when using patterns with `patternType="plusRecommended"` as shown
in the following example:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <packages type="image" patternType="plusRecommended">
           <namedCollection name="network-server"/>
           <package name="grub2"/>
           <package name="kernel"/>
           <ignore name="ejabberd"/>
           <ignore name="puppet-server"/>
       </packages>
   </image>


Packages can be marked as ignored during the installation by adding a
`ignore` child element with the mandatory `name` attribute set to the
package's name. Optionally one can also specify the architecture via the
`arch` similarly to :ref:`xml-description-package-element`.

.. warning::

   Adding `ignore` elements as children of a `<packages type="delete">` or
   a `<packages type="uninstall">` element has no effect! The packages will
   still get deleted.


.. [#f1] `RELAX NG <https://en.wikipedia.org/wiki/RELAX_NG>`_ is a
         so-called schema language: it describes the structure of a XML
         document.

.. [#f2] A hybrid persistent filesystem contains a copy-on-write file to
         keep data persistent over a reboot.
