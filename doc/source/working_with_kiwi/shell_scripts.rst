.. _working-with-kiwi-user-defined-scripts:

User Defined Scripts
====================

.. hint:: **Abstract**

   This chapter describes the usage of the user defined scripts
   :file:`config.sh` and :file:`image.sh`, which can be used to further
   customize an image in ways that are not possible via the image
   description alone.


KIWI supports up to two user defined scripts that it runs in the change
root environment (chroot) containing your new appliance:

1. :file:`config.sh` runs the end of the :ref:`prepare step <prepare-step>`
   if present. It can be used to fine tune the unpacked image.

2. :file:`images.sh` is executed at the beginning of the :ref:`image
   creation process <create-step>`. It is run on the top level of the
   target root tree. The script is usually used to remove files that are
   not needed in the final image. For example, if an appliance is being
   built for a specific hardware, unnecessary kernel drivers can be removed
   using this script.

KIWI will execute both scripts via the operating system if their executable
bit is set (in that case a shebang is mandatory) otherwise they will be
invoked via the BASH.

.. _image-customization-config-sh:

Image Customization via the ``config.sh`` Shell Script
------------------------------------------------------

The KIWI image description allows to have an :file:`config.sh` script in
place. It can be used for changes appropriate for all images to be created
from a given unpacked image (:file:`config.sh` runs prior to the *create
step*). The script should add operating system configuration files which
would be otherwise added by a user driven installer, like the activation of
services, creation of configuration files, preparation of an environment
for a firstboot workflow, etc.

The :file:`config.sh` script is called at the end of the :ref:`prepare step
<prepare-step>` (after users have been set and the *overlay tree directory*
has been applied). If :file:`config.sh` exits with a non-zero exit code
then KIWI will report the failure and abort the image creation.

Find a common template for `config.sh` script below:

.. code:: bash

   #======================================
   # Include functions & variables
   #--------------------------------------
   test -f /.kconfig && . /.kconfig
   test -f /.profile && . /.profile

   #======================================
   # Greeting...
   #--------------------------------------
   echo "Configure image: [$kiwi_iname]..."

   #======================================
   # Call configuration code/functions
   #--------------------------------------
   ...

Configuration Tips
^^^^^^^^^^^^^^^^^^

#. **Stateless systemd UUIDs:**

  Machine ID files are created and set (:file:`/etc/machine-id`,
  :file:`/var/lib/dbus/machine-id`) during the image package installation
  when *systemd* and/or *dbus* are installed. Those UUIDs are intended to
  be unique and set only once in each deployment. KIWI follows the `systemd
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


.. _image-customization-images-sh:

Image Customization via the ``images.sh`` Shell Script
------------------------------------------------------

The KIWI image description allows to have an optional :file:`images.sh`
bash script in place. It can be used for changes appropriate for certain
images/image types on a case-by-case basis (since it runs at beginning of
:ref:`create step <create-step>`).

.. warning:: Modifications of the unpacked root tree

   Keep in mind that there is only one unpacked root tree the script
   operates in. This means that all changes are permanent and will not be
   automatically restored!

The script should be designed to take over control of handling image type
specific tasks. For example, if building the OEM type requires some
additional packages or configurations then that can be handled in
:file:`images.sh`. Additionally, the script authors tasks is to check if
changes performed beforehand do not interfere in a negative way if another
image type is created from the same unpacked image root tree.

If :file:`images.sh` exits with a non-zero exit code, then KIWI will report
an error and abort the image creation.

See below a common template for :file:`images.sh` script:

.. code:: bash

   #======================================
   # Include functions & variables
   #--------------------------------------
   test -f /.kconfig && . /.kconfig
   test -f /.profile && . /.profile

   #======================================
   # Greeting...
   #--------------------------------------
   echo "Configure image: [$kiwi_iname]..."

   #======================================
   # Call configuration code/functions
   #--------------------------------------
   ...

   #======================================
   # Exit successfully
   #--------------------------------------
   exit 0


Functions and Variables Provided by KIWI
----------------------------------------

KIWI creates the :file:`.kconfig` and :file:`.profile` files to be sourced
by the shell scripts :file:`config.sh` and :file:`images.sh`.
:file:`.kconfig` contains various helper functions which can be used to
simplify the image configuration and :file:`.profile` contains environment
variables which get populated from the settings provided in the image
description.

Provided Functions
^^^^^^^^^^^^^^^^^^

The :file:`.kconfig` file provides a common set of functions.  Functions
specific to SUSE Linux begin with the name ``suse``, functions applicable
to all Linux distributions start with the name ``base``.

The following list describes all functions provided by :file:`.kconfig`:

``baseCleanMount``
  Unmount the filesystems :file:`/proc`, :file:`/dev/pts`, :file:`/sys` and
  :file:`/proc/sys/fs/binfmt_misc`.

``baseGetPackagesForDeletion``
  Return the name(s) of the packages marked for deletion in the image
  description.

``baseGetProfilesUsed``
  Return the name(s) of profiles used to build this image.

``baseSetRunlevel {value}``
  Set the default run level.

``baseSetupUserPermissions``
  Search all home directories of all users listed in :file:`/etc/passwd` and
  change the ownership of all files to belong to the correct user and group.

``baseStripAndKeep {list of info-files to keep}``
  Helper function for the ``baseStrip*`` functions, reads the list of files
  to check from stdin for removing
  params: files which should be kept

``baseStripDocs {list of docu names to keep}``
  Remove all documentation files, except for the ones given as the
  parameter.

``baseStripInfos {list of info-files to keep}``
  Remove all info files, except for the one given as the parameter.

``baseStripLocales {list of locales}``
  Remove all locales, except for the ones given as the parameter.

``baseStripTranslations {list of translations}``
  Remove all translations, except for the ones given as the parameter.

``baseStripMans {list of manpages to keep}``
  Remove all manual pages, except for the ones given as the parameter.

  Example:

  .. code:: bash

     baseStripMans more less

``suseImportBuildKey``
  Add the SUSE build keys to the RPM database.

``baseStripUnusedLibs``
  Remove libraries which are not directly linked against applications
  in the bin directories.

``baseUpdateSysConfig {filename} {variable} {value}``
  Update the contents of a sysconfig variable

``suseConfig``
  This function is deprecated and is a NOP.

``baseSystemdServiceInstalled {service}``
  Prints the path of the first found systemd unit or mount with name passed
  as the first parameter.

``baseSysVServiceInstalled {service}``
  Prints the name `${service}` if a SysV init service with that name is
  found, otherwise it prints nothing.

``baseSystemdCall {service_name} {args}``
  Calls `systemctl ${args} ${service_name}` if a systemd unit, a systemd
  mount or a SysV init service with the `${service_name}` exist.

``baseInsertService {servicename}``
  Activate the given service via :command:`systemctl`.

``baseRemoveService {servicename}``
  Deactivate the given service via :command:`systemctl`.

``baseService {servicename} {on|off}``
  Activate or deactivate a service via :command:`systemctl`.
  The function requires the service name and the value ``on`` or ``off`` as
  parameters.

  Example to enable the sshd service on boot:

  .. code:: bash

     baseService sshd on

``suseInsertService {servicename}``
  Calls baseInsertService and exists only for
  compatibility reasons.

``suseRemoveService {servicename}``
  Calls baseRemoveService and exists only for
  compatibility reasons.

``suseService {servicename} {on|off}``
  Calls baseService and exists only for compatibility
  reasons.

``suseActivateDefaultServices``
  Activates the `network` and `cron` services to run at boot.

``suseSetupProduct``
  Creates the :file:`/etc/products.d/baseproduct` link
  pointing to the product referenced by either :file:`/etc/SuSE-brand` or
  :file:`/etc/os-release` or the latest `.prod` file available in
  :file:`/etc/products.d`

``suseSetupProductInformation``
  Uses :command:`zypper` to search for the installed product
  and installs all product specific packages. This function fails
  when :command:`zypper` is not the appliances package manager.

``Debug {message}``
  Helper function to print the supplied message if the variable DEBUG is
  set to 1.

``Echo {echo commandline}``
  Helper function to print a message to the controlling terminal.

``Rm {list of files}``
  Helper function to delete files and log the deletion.

``Rpm {rpm commandline}``
  Helper function for calling ``rpm``: forwards all commandline arguments to
  ``rpm`` and logs the call.

Functions for Custom non-dracut Based Boot
''''''''''''''''''''''''''''''''''''''''''

KIWI also provides the following functions (mostly for compatibility
reasons) which can be used to customize the boot process when using the
custom boot option (see
:ref:`working-with-kiwi-customizing-the-boot-process`):

``baseStripInitrd``
  Removes various tools binaries and libraries which
  are not required to boot a SUSE system with KIWI. This function is not
  required when using the dracut initrd system and is kept for
  compatibility reasons.

``baseStripFirmware``
  Check all kernel modules if they require a firmware and strip out all
  firmware files which are not referenced by a kernel module

``baseStripModules``
  Search for updated modules and remove the old version which might be
  provided by the standard kernel

``baseStripKernel``
  Strips the kernel:

  1. create the :file:`vmlinux.gz` and :file:`vmlinuz` files which are used
     as a fallback for the kernel extraction

  2. handle `<strip type="delete">` requests. Because this information is
     generic not only files of the kernel are affected but also other data
     which are unwanted get deleted here

  3. only keep kernel modules matching the `<drivers>` patterns from the
     kiwi boot image description

  4. lookup kernel module dependencies and bring back modules which were
     removed but still required by other modules that were kept in the
     system

  5. search for duplicate kernel modules due to kernel module updates and
     keep only the latest version

  6. search for kernel firmware files and keep only those for which a
     kernel driver is still present in the system

``suseStripKernel``
  Removes all kernel drivers which are not listed in the
  drivers sections of :file:`config.xml`.

``baseStripTools {list of toolpath} {list of tools}``
  Helper function for suseStripInitrd
  function parameters: toolpath, tools.


Profile Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :file:`.profile` environment file is created by KIWI and contains a
specific set of variables which are listed below.

``$kiwi_compressed``
  The value of the `compressed` attribute set in the `type` element in
  :file:`config.xml`.

``$kiwi_delete``
  A list of all packages which are children of the `packages` element
  with `type="delete"` in :file:`config.xml`.

``$kiwi_drivers``
  A comma separated list of the driver entries as listed in the
  `drivers` section of the :file:`config.xml`.

``$kiwi_iname``
  The name of the image as listed in :file:`config.xml`.

``$kiwi_iversion``
  The image version as a string.

``$kiwi_keytable``
  The contents of the keytable setup as done in :file:`config.xml`.

``$kiwi_language``
  The contents of the locale setup as done in :file:`config.xml`.

``$kiwi_profiles``
  A comma separated list of profiles used to build this image.

``$kiwi_timezone``
  The contents of the timezone setup as done in :file:`config.xml`.

``$kiwi_type``
  The image type as extracted from the `type` element in
  :file:`config.xml`.
