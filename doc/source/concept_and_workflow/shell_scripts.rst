.. _working-with-kiwi-user-defined-scripts:

User Defined Scripts
====================

.. note:: **Abstract**

   This chapter describes the purpose of the user defined scripts
   :file:`config.sh`, :file:`image.sh` and :file:`disk.sh`, which can
   be used to further customize an image in ways that are not possible
   via the image description alone.

{kiwi} supports the following optional scripts that it runs in a
root environment (chroot) containing your new appliance:

config.sh
  runs at the end of the :ref:`prepare step <prepare-step>`
  and after users have been set and the *overlay tree directory*
  has been applied. It is usually used to apply a permanent and final
  change of data in the root tree, such as modifying a package provided
  config file.

images.sh
  is executed at the beginning of the :ref:`image
  creation process <create-step>`. It runs in the same image root tree
  that has been created by the prepare step but is invoked any
  time an image should be created from that root tree. It is usually
  used to apply image type specific changes to the root tree such as
  a modification to a config file that should be done when building
  a live iso but not when building a virtual disk image.

disk.sh
  is executed for the disk image types `vmx` and `oem`
  only and runs after the synchronisation of the root tree into the
  disk image loop file. At call time of the script the device name
  of the currently mapped root device is passed as a parameter.
  The chroot environment for this script call is the virtual disk
  itself and not the root tree as with :file:`config.sh` and
  :file:`images.sh`. :file:`disk.sh` is usually used to apply
  changes at parts of the system that are not an element of the
  file based root tree such as the partition table, the bootloader
  or filesystem attributes.

{kiwi} executes scripts via the operating system if their executable
bit is set (in that case a shebang is mandatory) otherwise they will be
invoked via the BASH. If a script exits with a non-zero exit code
then {kiwi} will report the failure and abort the image creation.

Script Template for config.sh / images.sh
-----------------------------------------

{kiwi} provides a collection of methods and variables that supports users
with custom operations. For details see :ref:`image-customization-methods`.
The following template shows how to import this information in your
script:

.. code:: bash

   #======================================
   # Include functions & variables
   #--------------------------------------
   test -f /.kconfig && . /.kconfig
   test -f /.profile && . /.profile

   ...

.. warning:: Modifications of the unpacked root tree

   Keep in mind that there is only one unpacked root tree the
   script operates in. This means that all changes are permanent
   and will not be automatically restored!


.. _image-customization-methods:

Functions and Variables Provided by {kiwi}
-------------------------------------------

{kiwi} creates the :file:`.kconfig` and :file:`.profile` files to be sourced
by the shell scripts :file:`config.sh` and :file:`images.sh`.
:file:`.kconfig` contains various helper functions which can be used to
simplify the image configuration and :file:`.profile` contains environment
variables which get populated from the settings provided in the image
description.

Functions
^^^^^^^^^

The :file:`.kconfig` file provides a common set of functions.  Functions
specific to SUSE Linux begin with the name ``suse``, functions applicable
to all Linux distributions start with the name ``base``.

The following list describes all functions provided by :file:`.kconfig`:

baseCleanMount
  Unmount the filesystems :file:`/proc`, :file:`/dev/pts`, :file:`/sys` and
  :file:`/proc/sys/fs/binfmt_misc`.

baseGetPackagesForDeletion
  Return the name(s) of the packages marked for deletion in the image
  description.

baseGetProfilesUsed
  Return the name(s) of profiles used to build this image.

baseSetRunlevel {value}
  Set the default run level.

baseSetupUserPermissions
  Set the ownership of all home directories and their content to the correct
  users and groups listed in :file:`/etc/passwd`.

baseStripAndKeep {list of info-files to keep}
  Helper function for the ``baseStrip*`` functions, reads the list of files
  to check from stdin for removing
  params: files which should be kept

baseStripDocs {list of docu names to keep}
  Remove all documentation files, except for the ones given as the
  parameter.

baseStripInfos {list of info-files to keep}
  Remove all info files, except for the one given as the parameter.

baseStripLocales {list of locales}
  Remove all locales, except for the ones given as the parameter.

baseStripTranslations {list of translations}
  Remove all translations, except for the ones given as the parameter.

baseStripMans {list of manpages to keep}
  Remove all manual pages, except for the ones given as the parameter.

  Example:

  .. code:: bash

     baseStripMans more less

suseImportBuildKey
  Add the SUSE build keys to the RPM database.

baseStripUnusedLibs
  Remove libraries which are not directly linked against applications
  in the bin directories.

baseUpdateSysConfig {filename} {variable} {value}
  Update the contents of a sysconfig variable

suseConfig
  This function is deprecated and is a NOP.

baseSystemdServiceInstalled {service}
  Prints the path of the first found systemd unit or mount with name passed
  as the first parameter.

baseSysVServiceInstalled {service}
  Prints the name `${service}` if a SysV init service with that name is
  found, otherwise it prints nothing.

baseSystemdCall {service_name} {args}
  Calls `systemctl ${args} ${service_name}` if a systemd unit, a systemd
  mount or a SysV init service with the `${service_name}` exist.

baseInsertService {servicename}
  Activate the given service via :command:`systemctl`.

baseRemoveService {servicename}
  Deactivate the given service via :command:`systemctl`.

baseService {servicename} {on|off}
  Activate or deactivate a service via :command:`systemctl`.
  The function requires the service name and the value ``on`` or ``off`` as
  parameters.

  Example to enable the sshd service on boot:

  .. code:: bash

     baseService sshd on

suseInsertService {servicename}
  Calls baseInsertService and exists only for
  compatibility reasons.

suseRemoveService {servicename}
  Calls baseRemoveService and exists only for
  compatibility reasons.

suseService {servicename} {on|off}
  Calls baseService and exists only for compatibility
  reasons.

suseActivateDefaultServices
  Activates the `network` and `cron` services to run at boot.

suseSetupProduct
  Creates the :file:`/etc/products.d/baseproduct` link
  pointing to the product referenced by either :file:`/etc/SuSE-brand` or
  :file:`/etc/os-release` or the latest `.prod` file available in
  :file:`/etc/products.d`

suseSetupProductInformation
  Uses :command:`zypper` to search for the installed product
  and installs all product specific packages. This function fails
  when :command:`zypper` is not the appliances package manager.

Debug {message}
  Helper function to print the supplied message if the variable DEBUG is
  set to 1.

Echo {echo commandline}
  Helper function to print a message to the controlling terminal.

Rm {list of files}
  Helper function to delete files and log the deletion.

Rpm {rpm commandline}
  Helper function for calling ``rpm``: forwards all commandline arguments to
  ``rpm`` and logs the call.

Profile Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :file:`.profile` environment file is created by {kiwi} and contains a
specific set of variables which are listed below.

$kiwi_compressed
  The value of the `compressed` attribute set in the `type` element in
  :file:`config.xml`.

$kiwi_delete
  A list of all packages which are children of the `packages` element
  with `type="delete"` in :file:`config.xml`.

$kiwi_drivers
  A comma separated list of the driver entries as listed in the
  `drivers` section of the :file:`config.xml`.

$kiwi_iname
  The name of the image as listed in :file:`config.xml`.

$kiwi_iversion
  The image version as a string.

$kiwi_keytable
  The contents of the keytable setup as done in :file:`config.xml`.

$kiwi_language
  The contents of the locale setup as done in :file:`config.xml`.

$kiwi_profiles
  A comma separated list of profiles used to build this image.

$kiwi_timezone
  The contents of the timezone setup as done in :file:`config.xml`.

$kiwi_type
  The image type as extracted from the `type` element in
  :file:`config.xml`.


Configuration Tips
------------------

#. **Locale configuration:**

  KIWI in order to set the locale relies on :command:`systemd-firstboot`,
  which in turn writes the locale configuration file :file:`/etc/locale.conf`.
  The values for the locale settings are taken from the description XML
  file in the `<locale>` element under `<preferences>`.

  KIWI assumes systemd adoption to handle these locale settings, in case the
  build distribution does not honor `/etc/locale.conf` this is likely to not
  produce any effect on the locale settings. As an example, in SLE12
  distribution the locale configuration is already possible by using the
  systemd toolchain, however this approach overlaps with SUSE specific
  managers such as YaST. In that case using :command:`systemd-firstboot`
  is only effective if locales in :file:`/etc/sysconfig/language` are
  not set or if the file does not exist at all. In SLE12
  :file:`/etc/sysconfig/language` has precendence over
  :file:`/etc/locale.conf` for compatibility reasons and management tools
  could still relay on `sysconfig` files for locale settings.

  In any case the configuration is still possible in KIWI by using
  any distribution specific way to configure the locale setting inside the
  :file:`config.sh` script or by adding any additional configuration file
  as part of the overlay root-tree.

#. **Stateless systemd UUIDs:**

  Machine ID files are created and set (:file:`/etc/machine-id`,
  :file:`/var/lib/dbus/machine-id`) during the image package installation
  when *systemd* and/or *dbus* are installed. Those UUIDs are intended to
  be unique and set only once in each deployment. {kiwi} follows the `systemd
  recommendations
  <https://www.freedesktop.org/software/systemd/man/machine-id.html>`_ and
  wipes any :file:`/etc/machine-id` content, leaving it as an empty file.
  Note, this only applies to images based on a dracut initrd, it does not
  apply for container images.

  In case this setting is also required for a non dracut based image,
  the same result can achieved by removing :file:`/etc/machine-id` in
  :file:`config.sh`.

  .. note:: Avoid interactive boot

     It is important to remark that the file :file:`/etc/machine-id` is set
     to an empty file instead of deleting it. :command:`systemd` may
     trigger :command:`systemd-firstboot` service if this file is not
     present, which leads to an interactive firstboot where the user is
     asked to provide some data.

  .. note:: Avoid inconsistent :file:`/var/lib/dbus/machine-id`

     Note that :file:`/etc/machine-id` and :file:`/var/lib/dbus/machine-id`
     **must** contain the same unique ID. On modern systems
     :file:`/var/lib/dbus/machine-id` is already a symlink to
     :file:`/etc/machine-id`. However on older systems those might be two
     different files. This is the case for SLE-12 based images. If you are
     targeting these older operating systems, it is recommended to add the
     symlink creation into :file:`config.sh`:

     .. code:: bash

        #======================================
        # Make machine-id consistent with dbus
        #--------------------------------------
        if [ -e /var/lib/dbus/machine-id ]; then
            rm /var/lib/dbus/machine-id
        fi
        ln -s /etc/machine-id /var/lib/dbus/machine-id
