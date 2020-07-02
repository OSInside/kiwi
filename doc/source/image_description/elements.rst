.. _image-description-elements:

Image Description Elements
==========================

.. note::

   This document provides a reference for the elements
   and attributes of the {kiwi} XML document in version |version|

.. _sec.image:

<image>
-------

The toplevel of any {kiwi} image description

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- descendants -->
   </image>

The image definition starts with an image tag and requires the schema
format at version {schema_version}. The attribute name specifies the name
of the image which is also used for the filenames created by KIWI. Because
we don’t want spaces in filenames the name attribute must not have any
spaces in its name.

The following optional attributes can be inserted in the image tag:

displayname
   Allows setup of the boot menu title for the selected boot loader. So
   you can have *suse-SLED-foo* as the image name but a different name
   as the boot display name. Spaces are not allowed in the display name
   because it causes problems for some boot loaders and kiwi did not
   take the effort to separate the ones which can display them correctly
   from the ones which can't

id
   sets an identification number which appears as file ``/etc/ImageID``
   within the image.

.. _sec.description:

<description>
-------------

Provide an image identity.

.. code:: xml

   <description type="system">
     <author>name</author>
     <contact>contact</contact>
     <specification>text</specification>
   </description>

The mandatory description section contains information about the creator
of this image description. The attribute type could be either of the
value `system` which indicates this is a system image description or at
value `boot` for custom kiwi boot image descriptions.

The following optional sub sections can be inserted below the description tag:

license
  Specifies the license name which applies to this image description.

.. _sec.preferences:

<preferences>
-------------

Setup image type and layout.

.. code:: xml

   <preferences>
     <version>1.2.3</version>
     <packagemanager name="zypper"/>
     <type image="tbz"/>
   </preferences>

The mandatory preferences section contains information about the
supported image type(s), the used package manager, the version of this
image, and further optional elements.

<preferences><version>
~~~~~~~~~~~~~~~~~~~~~~
The mandatory image version must be a three-part version number of the
format: **Major**.\ **Minor**.\ **Release**. In case of changes to
the image description the following rules should apply:

* For smaller image modifications that do not add or remove any new
  packages, only the release number is incremented. The XML description
  file(``config.xml``) remains unchanged.

* For image changes that involve the addition or removal of packages
  the minor number is incremented and the release number is reset.

* For image changes that changes the behavior or geometry of the
  image file the major number is incremented.

<preferences><packagemanager>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The mandatory packagemanager element specifies which package manager
should be used to handle software packages. The packagemanager setup
is connected to the distribution used to build the image. The following
table shows which package manager is connected to which distributor:

+--------------+-----------------+
| Distributor  | Package Manager |
+==============+=================+
| SUSE         | zypper          |
+--------------+-----------------+
| RedHat       | dnf             |
+--------------+-----------------+
| Debian Based | apt-get         |
+--------------+-----------------+ 
| Arch Linux   | pacman          |
+--------------+-----------------+

In general the specification of one preferences section is sufficient.
However, it’s possible to specify multiple preferences sections and
distinguish between the sections via the profiles attribute.

In combination with the above the preferences element supports the
following optional elements:

<preferences><rpm-locale-filtering>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
locale-filtering can be set to "true" or "false". If set to "true" it
sets the install_lang macro for RPM based installations to the RPM
configured locale list. This results in language specific files to
become filtered out by `rpm` if they don't match the configured list.

.. code:: xml

   <preferences>
     <rpm-locale-filtering>true</rpm-locale-filtering>
   </preferences>

.. note::

   It depends on the individual package design if the install_lang
   macro contents apply to the package or not.

<preferences><rpm-check-signatures>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifies whether package signatures should be checked or not

.. code:: xml

   <preferences>
     <rpm-check-signatures>true</rpm-check-signatures>
   </preferences>

<preferences><rpm-excludedocs>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifies whether files marked as documentation should be skipped
during installation

.. code:: xml

   <preferences>
     <rpm-excludedocs>true</rpm-excludedocs>
   </preferences>

<preferences><keytable>
~~~~~~~~~~~~~~~~~~~~~~~
Specifies the name of the console keymap to use. The value
corresponds to a map file in ``/usr/share/kbd/keymaps/xkb``.

.. code:: xml

   <preferences>
     <keytable>us</keytable>
   </preferences>

<preferences><timezone>
~~~~~~~~~~~~~~~~~~~~~~~
Specifies the time zone. Available time zones are located in the
``/usr/share/zoneinfo`` directory. Specify the attribute value
relative to ``/usr/share/zoneinfo``. For example, specify
Europe/Berlin for ``/usr/share/zoneinfo/Europe/Berlin``.

.. code:: xml

   <preferences>
     <keytable>Europe/Berlin</keytable>
   </preferences>

<preferences><locale>
~~~~~~~~~~~~~~~~~~~~~
Specifies the name of the UTF-8 locale to use, which defines the
contents of the RC_LANG system environment variable used in the
image and to run the custom scripts specified as part of the
{kiwi} image description. Please note only UTF-8 locales are
supported here which also means that the encoding must *not* be part
of the locale information. This means you need to specify the
locale using the 4-digit name like the following example: en_US or
en_US,de_DE

.. code:: xml

   <preferences>
     <locale>en_US</locale>
   </preferences>

<preferences><bootsplash-theme>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifies the name of the plymouth bootsplash theme to use

.. code:: xml

   <preferences>
     <bootsplash-theme>bgrt</bootsplash-theme>
   </preferences>

<preferences><bootloader-theme>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifies the name of the bootloader theme to use if that used
bootloader has theme support.

.. code:: xml

   <preferences>
     <bootloader-theme>openSUSE</bootloader-theme>
   </preferences>


Along with the version and the packagemanager at least one image type
element must be specified to indicate which image type should be build.

<preferences><type>
~~~~~~~~~~~~~~~~~~~
At least one type element must be configured. It is possible to
specify multiple type elements in a preferences block. To set a given
type description as the default image use the boolean attribute primary
and set its value to true:

.. code:: xml

   <preferences>
     <type image="typename" primary="true"/>
   </preferences>

The image type to be created is determined by the value of the image
attribute. The following list describes the supported types and
possible values of the image attribute:

image="tbz"
  A simple tar archive image. The tbz type packs the contents of
  the image root tree into a xz compressed tarball.

image="btrfs|ext2|ext3|ext4|squashfs|xfs"
  A filesystem image. The image root tree data is packed into a
  filesystem image of the given type. An image of that type can
  be loop mounted and accessed according to the capabiities of
  the selected filesystem.

image="iso"
  An iso image which can be dumped on a CD/DVD or USB stick
  and boots off from this media without interfering with other
  system storage components. A useful pocket system for testing
  and demo and debugging purposes.

image="vmx"
  An image representing the system disk, useful for cloud frameworks
  like Amazon EC2, Google Compute Engine or Microsoft Azure.

image="oem"
  An image representing an expandable system disk. This means after
  deployment the system can resize itself to the new disk geometry.
  The resize operation is configurable as part of the image description
  and an installation image for CD/DVD, USB stick and Network deployment
  can be created in addition.

image="docker"
  An archive image suitable for the docker container engine.
  The image can be loaded via the `docker load` command and
  works within the scope of the container engine

image="oci"
  An archive image that builds a container matching the OCI
  (Open Container Interface) standard. The container should be
  able to run with any oci compliant container engine.

image="appx"
  An archive image suitable for the Windows Subsystem For Linux
  container engine. The image can be loaded From a Windows System
  that has support for WSL activated.

image="kis"
  An optional root filesystem image associated with a kernel and initrd.
  The use case for this component image type is highly customizable.
  Many different deployment strategies are possible.

For completion of a type description, there could be several other
optional attributes and child elements. The `type` element supports a
plethora of optional attributes, some of these are only relevant for
certain build types and will be covered in extra chapters that describes
the individual image types more detailed. Certain attributes are however
useful for nearly all build types and will be covered next:

bootpartition="true|false":
  Boolean parameter notifying {kiwi} whether an extra boot
  partition should be used or not (the default depends on the current
  layout). This will override {kiwi}'s default layout.

btrfs_quota_groups="true|false":
  Boolean parameter to activate filesystem quotas if
  the filesystem is `btrfs`. By default quotas are inactive.

btrfs_root_is_snapshot="true|false":
  Boolean parameter that tells {kiwi} to install
  the system into a btrfs snapshot. The snapshot layout is compatible with
  snapper. By default snapshots are turned off.

btrfs_root_is_readonly_snapshot="true|false":
  Boolean parameter notifying {kiwi} that
  the btrfs root filesystem snapshot has to made read-only. if this option
  is set to true, the root filesystem snapshot it will be turned into
  read-only mode, once all data has been placed to it. The option is only
  effective if `btrfs_root_is_snapshot` is also set to true. By default the
  root filesystem snapshot is writable.

compressed="true|false":
  Specifies whether the image output file should be
  compressed or not. This option is only used for filesystem only images or
  for the `pxe` or `cpio` types.

editbootconfig="file_path":
  Specifies the path to a script which is called right
  before the bootloader is installed. The script runs relative to the
  directory which contains the image structure.

editbootinstall="file_path":
  Specifies the path to a script which is called right
  after the bootloader is installed. The script runs relative to the
  directory which contains the image structure.

filesystem="btrfs|ext2|ext3|ext4|squashfs|xfs"
  The root filesystem

firmware="efi|uefi"
  Specifies the boot firmware of the appliance, supported
  options are: `bios`, `ec2`, `efi`, `uefi`, `ofw` and `opal`.
  This attribute is used to differentiate the image according to the
  firmware which boots up the system. It mostly impacts the disk
  layout and the partition table type. By default `bios` is used on x86,
  `ofw` on PowerPC and `efi` on ARM.

force_mbr="true|false":
  Boolean parameter to force the usage of a MBR partition
  table even if the system would default to GPT. This is occasionally
  required on ARM systems that use a EFI partition layout but which must
  not be stored in a GPT. Note that forcing a MBR partition table incurs
  limitations with respect to the number of available partitions and their
  sizes.

fsmountoptions="option_string":
  Specifies the filesystem mount options which are passed
  via the `-o` flag to :command:`mount` and are included in
  :file:`/etc/fstab`.

fscreateoptions="option_string":
  Specifies the filesystem options used to create the
  filesystem. In {kiwi} the filesystem utility to create a filesystem is
  called without any custom options. The default options are filesystem
  specific and are provided along with the package that provides the
  filesystem utility. For the Linux `ext[234]` filesystem, the default
  options can be found in the :file:`/etc/mke2fs.conf` file. Other
  filesystems provides this differently and documents information
  about options and their defaults in the respective manual page, e.g
  :command:`man mke2fs`. With the `fscreateoptions` attribute it's possible
  to directly influence how the filesystem will be created. The options
  provided as a string are passed to the command that creates the
  filesystem without any further validation by {kiwi}. For example, to turn
  off the journal on creation of an ext4 filesystem the following option
  would be required:

  .. code:: xml

     <preferences>
       <type fscreateoptions="-O ^has_journal"/>
     </preferences>

kernelcmdline="string":
  Additional kernel parameters passed to the kernel by the
  bootloader.

luks="passphrase":
  Supplying a value will trigger the encryption of the partitions
  using the LUKS extension and using the provided string as the
  password. Note that the password must be entered when booting the
  appliance!

target_blocksize="number"
  Specifies the image blocksize in bytes which has to
  match the logical blocksize of the target storage device. By default 512
  Bytes is used, which works on many disks. You can obtain the blocksize
  from the `SSZ` column in the output of the following command:

  .. code:: shell-session

     blockdev --report $DEVICE

The following sections shows the supported child elements of the `type`
element including references to their usage in a detailed type setup:

<preferences><type><bootloader>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to describe the bootloader setup in vmx or oem disk image types.
For details see: :ref:`vmx-bootloader`

<preferences><type><containerconfig>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to describe the container configuration metadata in docker or wsl
image types. For details see: :ref:`building-docker-build` and:
:ref:`building-wsl-build`

<preferences><type><vagrantconfig>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to describe vagrant configuration metadata in vmx disk image
that is being used as a vagrant box. For details see: :ref:`setup_vagrant`

<preferences><type><systemdisk>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to describe the geometry, partitions and volumes, in a vmx or oem
disk image. For details see: :ref:`custom_volumes`

<preferences><type><oemconfig>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to customize the deployment process in an oem disk image.
For details see: :ref:`oem_customize`

<preferences><type><size>
~~~~~~~~~~~~~~~~~~~~~~~~~
Used to customize the size of the resulting disk image in a vmx or
oem image. For details see: :ref:`vmx-the-size-element`

<preferences><type><machine>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Used to customize the virtual machine configuration which describes
the components of an emulated hardware.
For details see: :ref:`vmx-the-machine-element`

.. _sec.repository:

<repository>
-------------

Setup software sources for the image.

.. code:: xml

   <repository>
     <source path="uri"/>
   </repository>

The mandatory repository element specifies the location and type of a
repository to be used by the package manager as a package installation
source. {kiwi} supports apt, dnf, pacman and zypper as package managers,
specified with the packagemanager element. The repository element has
the following optional attributes:

alias="name"
  Specifies an alternative name for the configured repository. If the
  attribute is not specified {kiwi} will generate a random alias name
  for the repository.

components="name"
  Used for Debian (apt) based repositories only. Specifies the
  component name that should be used from the repository. By default
  the `main` component is used

distribution="name"
  Used for Debian (apt) based repositories only. Specifies the
  distribution name to be used on call of `debootstrap`

imageonly="true|false"
  Specifies whether or not this repository should be configured in
  the resulting image without using it at build time. By default
  the value is set to false

repository_gpgcheck="true|false"
  Specifies whether or not this specific repository is configured to
  to run repository signature validation. If not set, no value is
  appended into the repository configuration file. If set the
  relevant key information needs to be provided on the {kiwi}
  commandline using the `--signing-key` option

imageinclude="true|false"
  Specifies whether the given repository should be configured as a
  repository in the image or not. The default behavior is that
  repositories used to build an image are not configured as a
  repository inside the image. This feature allows you to change the
  behavior by setting the value to true.

  .. note:: Scope of repository uri's

     The repository is configured in the image according to the source
     path as specified with the path attribute of the source element.
     Therefore, if the path is not a fully qualified URL, you may need
     to adjust the repository file in the image to accommodate the
     expected location. It is recommended that you use the alias
     attribute in combination with the imageinclude attribute to
     avoid having unpredictable random names assigned to the
     repository you wish to include in the image.

password="string"
  Specifies a password for the given repository. The password attribute
  must be used in combination with the username attribute. Dependent on
  the repository location this information may not be used.

username="name"
  Specifies a user name for the given repository. The username
  attribute must be used in combination with the password attribute.
  Dependent on the repository location this information may not be
  used.

prefer-license="true|false"
  The repository providing this attribute will be used primarily to
  install the license tarball if found on that repository. If no
  repository with a preferred license attribute exists, the search
  happens over all repositories. It's not guaranteed in that case that
  the search order follows the repository order like they are written
  into the XML description.

priority="number"
  Specifies the repository priority for this given repository. Priority
  values are treated differently by different package managers.
  Repository priorities allow the package management system to
  disambiguate packages that may be contained in more than one of the
  configured repositories. The zypper package manager for example
  prefers packages from a repository with a *lower* priority over
  packages from a repository with higher priority values.
  The value 99 means “no priority is set”. For other package managers
  please refer to the individual documentation about repository priorities.

sourcetype="baseurl|metalink|mirrorlist"
  Specifies the source type of the repository path. Depending on if the
  source path is a simple url or a pointer to a metadata file or mirror
  list, the configured package manager needs to be setup appropriately.
  By default the source is expected to be a simple repository baseurl.

<repository><source>
~~~~~~~~~~~~~~~~~~~~
The location of a repository is specified by the path attribute of the
mandatory source child element:

.. code:: xml

   <repository alias="kiwi">
     <source path="{exc_kiwi_repo}"/>
   </repository>

The location specification may include
the `%arch` macro which will expand to the architecture of the image
building host. The value for the path attribute may begin with any of
the following location indicators:

* ``dir:///local/path``
  An absolute path to a directory accessible through the local file system.

* ``ftp://<ftp://>``
  A ftp protocol based network location.

* ``http://<http://>``
  A http protocol based network location.

* ``https://<https://>``
  A https protocol based network location.

  .. note:: https repositories

     When specifying a https location for a repository it is generally
     necessary to include the openssl certificates and a cracklib word
     dictionary as package entries in the bootstrap section of the
     image configuration. The names of the packages to include are
     individual to the used distribution. On SUSE systems as one example
     this would be `openssl-certs` and `cracklib-dict-full`

* ``iso://<iso://>``
  An absolute path to an .iso file accessible via the local file
  system. {kiwi} will loop mount the the .iso file to a temporary
  directory with a generated name. The generated path is provided to
  the specified package manager as a directory based repository location.

* ``obs://Open:Build:Service:Project:Name``
  A reference to a project in the Open Build Service (OBS). {kiwi}
  translates the given project path into a remote url at which
  the given project hosts the packages.
  
* ``obsrepositories:/``
  A placeholder for the Open Build Service (OBS) to indicate that all
  repositories are taken from the project configuration in OBS.

.. _sec.packages:

<packages>
-----------

Setup software components to be installed in the image.

.. code:: xml

   <packages type="type"/>

The mandatory packages element specifies the setup of a packages
group for the given type. The value of the type attribute specifies
at which state in the build process the packages group gets handled,
supported values are as follows:

type="bootstrap"
  Bootstrap packages, list of packages to be installed first into
  a new (empty) root tree. The packages list the required components
  to support a chroot environment from which further software
  components can be installed

type="image"
  Image packages, list of packages to be installed as part of a chroot
  operation inside of the new root tree.

type="uninstall|delete"
  Packages to be uninstalled or deleted. For further details
  see :ref:`uninstall-system-packages`

type="*image_type_name*"
  Packages to be installed for the given image type name. For example
  if set to type="iso", the packages in this group will only be
  installed if the iso image type is build.


The packages element must contain at least one child element of the
following list to provide specific configuration information for the
specified packages group:

<packages><package>
~~~~~~~~~~~~~~~~~~~
.. code:: xml

   <packages type="image"/>
     <package name="name" arch="arch"/>
   </packages>

The package element installs the given package name. The optional
`arch` attribute can be used to limit the installation of the package
to the host architecture from which {kiwi} is called. The `arch`
attribute is also available in all of the following elements.

<packages><namedCollection>
~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: xml

   <packages type="image" patternType="onlyRequired">
     <namedCollection name="base"/>
   </packages>

The namedCollection element is used to install a number of packages
grouped together under a name. This is a feature of the individual
distribution and used in the implementation of the {kiwi} package
manager backend. At the moment collections are only supported for
SUSE and RedHat based distributions. The optional `patternType` attribute
is used to control the behavior of the dependency resolution of
the package collection. `onlyRequired` installs only the collection
and its required packages. `plusRecommended` installs the collection,
any of its required packages and any recommended packages.

.. note:: Collections on SUSE

   On SUSE based distributions collections are names patterns and are
   just simple packages. To get the names of the patterns such that
   they can be used in a namedCollection type the following command:
   `$ zypper patterns`. If for some reason the collection name cannot
   be used it is also possible to add the name of the package that
   provides the collection as part of a `package` element. To get the
   names of the pattern packages type the following command:
   `$ zypper search patterns`. By convention all packages that starts
   with the name "patterns-" are representing a pattern package.

.. note:: Collections on RedHat

   On RedHat based distributions collections are named groups and are
   extra metadata. To get the names of these groups type the following
   command: `$ dnf group list`. Please note that group names are allowed
   to contain whitespace characters.

<packages><archive>
~~~~~~~~~~~~~~~~~~~
.. code:: xml

   <packages type="image"/>
     <archive name="name"/>
   </packages>

The archive element takes the `name` attribute and looks up the
given name as file on the system. If specified relative {kiwi}
looks up the name in the image description directory. The archive
is installed using the `tar` program. Thus the file name is
expected to be a tar archive. The compression of the archive is
detected automatically by the tar program.

<packages><ignore>
~~~~~~~~~~~~~~~~~~
.. code:: xml

   <packages type="image"/>
     <ignore name="name"/>
   </packages>

The ignore element instructs the used package manager to ignore the
given package name at installation time. Please note whether or not
the package can be ignored is up to the package manager. Packages
that are hard required by other packages in the install procedure
cannot be ignored and the package manager will simply ignore the
request.

<packages><product>
~~~~~~~~~~~~~~~~~~~
.. code:: xml

   <packages type="image">
     <product name="name"/>
   </packages>

The product element instructs the used package manager to install
the given product. What installation of a product means is up to
the package manager and also distribution specific. This feature
currently only works on SUSE based distributions

.. _sec.users:

<users>
--------

Setup image users.

.. code:: xml

   <users>
     <user
       name="user"
       groups="group_list"
       home="dir"
       id="number"
       password="text"
       pwdformat="encrypted|plain"
       realname="name"
       shell="path"
     />
   </users>

The optional users element contains the user setup {kiwi} should create
in the system. At least one user child element must be specified as
part of the users element. Multiple user elements may be specified.

Each `user` element represents a specific user that is added or
modified. The following attributes are mandatory:

name="name":
  the UNIX username

home="path":
  The path to the user's home directory

Additionally, the following optional attributes can be specified:

groups="group_a,group_b":
  A comma separated list of UNIX groups. The first element of the
  list is used as the user's primary group. The remaining elements are
  appended to the user's supplementary groups. When no groups are assigned
  then the system's default primary group will be used.

id="number":
  The numeric user id of this account.

pwdformat="plain|encrypted":
  The format in which `password` is provided. The default if not
  specified is `encrypted`.

password="string"
  The password for this user account. It can be provided either
  in cleartext form or encrypted. An encrypted password can be created
  using `openssl` as follows:

  .. code::

     $ openssl passwd -1 -salt xyz PASSWORD

  It is also possible to specify the password as a non encrypted string
  by using the pwdformat attribute and setting it’s value to `plain`.
  {kiwi} will then encrypt the password prior to the user being added
  to the system.

  .. warning:: plain text passwords

     We do not recommend plain passwords as they will be readable in
     the image configuration in plain text

  All specified users and groups will be created if they do not already
  exist. The defined users will be part of the group(s) specified
  with the groups attribute or belong to the default group as configured
  in the system. If specified the first entry in the groups list is used
  as the login group.

.. _sec.profiles:

<profiles>
-----------

Manage image namespace(s).

.. code:: xml

   <profiles>
     <profile name="name" description="text"/>
   </profiles>

The optional profiles section lets you maintain one image description
while allowing for variation of other sections that are included. A
separate profile element must be specified for each variation. The
profile child element, which has name and description attributes,
specifies an alias name used to mark sections as belonging to a profile,
and a short description explaining what this profile does.

For example to mark a set of packages as belonging to a profile, simply
annotate them with the profiles attribute as shown below:

.. code:: xml

   <packages type="image" profiles="profile_name">
     <package name="name"/>
   </packages>

It is also possible to mark sections as belonging to multiple profiles
by separating the names in the profiles attribute with a comma:

.. code:: xml

   <packages type="image" profiles="profile_A,profile_B">
     <package name="name"/>
   </packages>

If a section tag does not have a profiles attribute, it is globally
present in the configuration. If global sections and profiled sections
contains the same sub-sections, the profiled sections will overwrite
the global sections in the order of the provided profiles. For a better
overview of the result configuration when profiles are used we
recommend to put data that applies in any case to non profiled (global)
sections and only extend those global sections with profiled data.
For example:

.. code:: xml

   <preferences>
     <version>1.2.3</version>
     <packagemanager name="zypper"/>
   </preferences>

   <preferences profiles="vmx_qcow_format">
     <type image="vmx" filesystem="ext4" format="qcow2"/>
   </preferences>

   <preferences profiles="vmx_vmdk_format">
     <type image="vmx" filesystem="ext4" format="vmdk"/>
   </preferences>

The above example configures two version of the same vmx type.
One builds a disk in qcow2 format the other builds a disk in
vmdk format. The global preferences section without a profile
assigned will be used in any case and defines those preferences
settings that are common to any build process. A user can
select both profiles at a time but that will result in building
the disk format that is specified last because one is overwriting
the other.

Use of one or more profile(s) during image generation is triggered
by the use of the ``--profile`` command line argument. multiple profiles
can be selected by passing this option multiple times.
