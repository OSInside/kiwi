.. _working-with-kiwi-user-defined-scripts:

User-Defined Scripts
====================

.. note:: **Abstract**

   This chapter describes the purpose of the user-defined scripts
   :file:`config.sh`, :file:`image.sh`, :file:`pre_disk_sync.sh` and
   :file:`disk.sh`. These scripts can be used to further customize an image in
   ways that are not possible via the image description alone.

{kiwi} supports the following optional scripts that it runs in a
root environment (chroot) containing an appliance:

post_bootstrap.sh
  Runs at the end of the `bootstrap` phase as part of the :ref:`prepare step
  <prepare-step>`. The script can be used to configure the package manager with
  additional settings that apply in the following chroot-based installation step
  which completes the installation. The script can also be used for other tasks.

config.sh
  Runs at the end of the :ref:`prepare step <prepare-step>`
  and after users have been set and the *overlay tree directory*
  has been applied. It is usually used to apply a permanent and final
  change of data in the root tree, such as modifying a package-specific
  config file.

config-overlay.sh
  Available only if `delta_root="true"` is set. In this case, the script runs at
  the end of the :ref:`prepare step <prepare-step>` prior the umount of the
  overlay root tree. It runs after `config.sh` (if specified), and it is the
  last entry point to change the delta root tree.

config-host-overlay.sh
  Available only if `delta_root="true"` is set. In this case, the script runs at
  the end of the :ref:`prepare step <prepare-step>` prior the umount of the
  overlay root tree. The script is called **NOT CHROOTED** from the host with
  the image root directory as its working directory. It runs after `config.sh`
  and `config-overlay.sh` (if any or both are specified), and it is the last
  entry point to change the delta root tree.

images.sh
  Executed at the beginning of the :ref:`image creation process <create-step>`.
  It runs in the same image root tree created by the prepare step,
  but it is invoked whenever an image needs to be created from that root tree.
  It is normally used to apply image type specific changes to the root tree, such
  as a modification to a config file that must be done when building a live
  iso, but not when building a virtual disk image.

pre_disk_sync.sh
  Executed for the disk image type `oem` only, and it runs
  right before the synchronization of the root tree into the disk image
  loop file. The :file:`pre_disk_sync.sh` can be used to change
  content of the root tree as a last action before the sync to
  the disk image is performed. This is useful, for example, for deleting
  components from the system which were needed earlier or cannot
  be modified afterwards when syncing into a read-only filesystem.

disk.sh
  Executed for the disk image type `oem` only, and it runs after the
  synchronization of the root tree to the disk image loop file. The chroot
  environment for this script call is the virtual disk itself and not the root
  tree. The script :file:`disk.sh` is normally used to apply changes at parts of
  the system that are not an element of the file-based root tree, such as the
  partition table, the contents of the final initrd, the bootloader, filesystem
  attributes, etc.

{kiwi} executes scripts via the operating system if their executable
bit is set (in that case, a shebang is mandatory); otherwise they are
invoked via the Bash shell. If a script exits with a non-zero exit code,
{kiwi} reports the failure and aborts the image creation.

Developing/Debugging Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating a custom script may require some experimenting and testing. To help
developers with this task, {kiwi} calls scripts associated with a `screen`
session. The connection to `screen` is only done if {kiwi} is called with the
`--debug` option.

In this mode, a script can be started using the following template:

.. code:: bash

   # The magic bits are still not set

   echo "break"
   /bin/bash

Calling the script executes a `screen` session executes, which gives you access
to the break in shell. You can then implement the desired script code in this
environment.. Once the shell is closed the {kiwi} process continues.

In addition to providing a fully featured terminal throughout the execution of
the script code, you also have have control of the session during the process of
the image creation. Listing the active sessions for script execution can be done
as follows:

.. code:: bash

   $ sudo screen -list

   There is a screen on:
        19699.pts-4.asterix     (Attached)
   1 Socket in /run/screens/S-root.

.. note::

   As shown above the screen session for executing the script code provides
   extended control, which can be considered a security risk. Because of that,
   {kiwi} only runs scripts through `screen` when explicitly enabled via the
   `--debug` switch. In production, all scripts must run natively and
   must not require a terminal to operate correctly.

Script Template for config.sh / images.sh
-----------------------------------------

{kiwi} provides a collection of methods and variables that offer custom
actions. For details, see :ref:`image-customization-methods`. The following
template shows how to import this information into a script:

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
   and are not automatically restored.


.. _image-customization-methods:

Functions and Variables Provided by {kiwi}
-------------------------------------------

{kiwi} creates the :file:`.kconfig` and :file:`.profile` files to be sourced
by the shell scripts :file:`config.sh` and :file:`images.sh`.
:file:`.kconfig` contains several helper functions that can be used to
simplify image configuration, while :file:`.profile` contains environment
variables populated from the settings provided in the image
description.

Functions
^^^^^^^^^

The :file:`.kconfig` file provides a common set of functions.  Functions
specific to SUSE Linux Enterprise and openSUSE start with ``suse``, functions
applicable to all Linux distributions start with ``base``.

The following list describes all functions provided by :file:`.kconfig`:

baseSetRunlevel {value}
  Set the default run level.

baseStripAndKeep {list of info-files to keep}
  Helper function for the ``baseStrip*`` functions that reads a list of files to
  check from stdin for removing params: files which should be kept.

baseStripLocales {list of locales}
  Removes all locales, except for the ones given as the parameter.

baseStripTranslations {list of translations}
  Removes all translations, except those given as the parameter.

baseStripUnusedLibs
  Removes libraries that are not directly linked against applications
  in the bin directories.

baseUpdateSysConfig {filename} {variable} {value}
  Updates the contents of a sysconfig variable.

baseSystemdServiceInstalled {service}
  Prints the path of the first found systemd unit or mount with name passed
  as the first parameter.

baseSysVServiceInstalled {service}
  Prints the name `${service}` if a SysV init service with the same name is
  found; otherwise it prints nothing.

baseSystemdCall {service_name} {args}
  Calls `systemctl ${args} ${service_name}` if a systemd unit, a systemd
  mount, or a SysV init service with the `${service_name}` exists.

baseInsertService {servicename}
  Activates the specified service via :command:`systemctl`.

baseRemoveService {servicename}
  Deactivates the specified service via :command:`systemctl`.

baseService {servicename} {on|off}
  Activates or deactivates a service via :command:`systemctl`.
  The function requires the service name and the value ``on`` or ``off`` as
  parameters.

  The following example enables the sshd service on boot:

  .. code:: bash

     baseService sshd on

suseInsertService {servicename}
  Calls baseInsertService. It exists only for
  compatibility reasons.

suseRemoveService {servicename}
  Calls baseRemoveService. It exists only for
  compatibility reasons.

suseService {servicename} {on|off}
  Calls baseService. It exists only for compatibility
  reasons.

suseSetupProduct
  Creates the :file:`/etc/products.d/baseproduct` link
  pointing to the product referenced either by :file:`/etc/SuSE-brand` or
  :file:`/etc/os-release` or the latest `.prod` file available in
  :file:`/etc/products.d`

baseVagrantSetup
  Configures the image to work as a vagrant box by performing the following
  changes:

  - add the ``vagrant`` user to :file:`/etc/sudoers`
    or :file:`/etc/sudoers.d/vagrant`
  - insert the insecure vagrant ssh key, apply recommended
    ssh settings and start the ssh daemon
  - create the default shared folder :file:`/vagrant`

Debug {message}
  Helper function to print the supplied message if the variable DEBUG is
  set to 1 (disabled by default).

Echo {echo commandline}
  Helper function to print a message to the controlling terminal.

Rm {list of files}
  Helper function to delete files and log the deletion.

Profile Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :file:`.profile` environment file is created by {kiwi} and contains a
specific set of variables listed below.

$kiwi_compressed
  A value of the `compressed` attribute set in the `type` element in
  :file:`config.xml`.

$kiwi_delete
  A list of all packages which are children of the `packages` element
  with `type="delete"` in :file:`config.xml`.

$kiwi_drivers
  A comma-separated list of driver entries as listed in the
  `drivers` section of :file:`config.xml`.

$kiwi_iname
  The name of the image as listed in :file:`config.xml`.

$kiwi_iversion
  The image version as a string.

$kiwi_keytable
  The contents of the keytable setup as specified in :file:`config.xml`.

$kiwi_language
  The contents of the locale setup as specified in :file:`config.xml`.

$kiwi_profiles
  A comma-separated list of profiles used to build this image.

$kiwi_timezone
  The contents of the timezone setup as specified in :file:`config.xml`.

$kiwi_type
  The image type as extracted from the `type` element in
  :file:`config.xml`.

.. note:: **.profile.extra**

   If there is the file :file:`/.profile.extra` available in the initrd, {kiwi}
   imports the file importing :file:`/.profile`.

Configuration Tips
------------------

#. **Locale configuration:**

   To set locale, {kiwi} relies on :command:`systemd-firstboot` that writes the
   locale configuration file :file:`/etc/locale.conf`. The values for the locale
   settings are taken from the description XML file in the `<locale>` element
   under `<preferences>`.

   Keep im mind that if the build distribution does not use `/etc/locale.conf`,
   the :command:`systemd-firstboot` does not have any effect on the locale
   settings. For example, in the SLE12 distribution,
   :command:`systemd-firstboot` is only effective when locales in
   :file:`/etc/sysconfig/language` are not set, or when the file does not exist
   at all. For compatibility reasons, the file :file:`/etc/sysconfig/language`
   in SLE12 has precedence over :file:`/etc/locale.conf`, and management tools
   can still use `sysconfig` files for locale settings.

   In any case, it is possible to configure the locale setting inside the
   :file:`config.sh` script in {kiwi} using in distribution-specific way, or by
   adding any additional configuration file as part of the overlay root-tree.

#. **Stateless systemd UUIDs:**

   Machine ID files (:file:`/etc/machine-id`, :file:`/var/lib/dbus/machine-id`)
   may be created and set during the image package installation depending on
   the distribution. Those UUIDs must be unique and must be set only once
   in each deployment.

   If :file:`/etc/machine-id` does not exist or contains the string
   `uninitialized` (systemd v249 and later), this triggers firstboot action
   in systemd, and the services are run with `ConditionFirstBoot=yes`. Unless the
   file already contains a valid machine ID, systemd generates a machine ID and
   write it into the file, creating it if necessary. See the `machine-id man
   page <https://www.freedesktop.org/software/systemd/man/machine-id.html>`_
   for more details.

   Depending on whether firstboot action should be triggered or not,
   :file:`/etc/machine-id` can be created, removed, or set to
   `uninitialized` by :file:`config.sh`.

   To prevent images from including a generated machine ID, {kiwi} clears
   :file:`/etc/machine-id` if it exists and does not contain the string
   `uninitialized`. This only applies to images based on a dracut initrd.

   .. note:: `rw` is necessary if :file:`/etc/machine-id` does not exist.

      For systemd to be able to write :file:`/etc/machine-id` on boot,
      either the file must exist (so that a bind mount can be created) or
      :file:`/etc` must be writable.

      By default, the root filesystem is mounted read-only by dracut/systemd,
      so a missing :file:`/etc/machine-id` will lead to an error on boot.
      To force the initial mount to be read-write, add the `rw` option to the kernel commandline.

   .. note:: Avoid inconsistent :file:`/var/lib/dbus/machine-id`

      :file:`/etc/machine-id` and :file:`/var/lib/dbus/machine-id`
      **must** contain the same unique ID. On modern systems
      :file:`/var/lib/dbus/machine-id`, there is already a symlink to
      :file:`/etc/machine-id`. However, on older systems there might be two
      different files. This is the case for SLE-12 based images. If you are
      targeting older operating systems, it is recommended to add the
      symlink creation into :file:`config.sh`:

      .. code:: bash

         #======================================
         # Make machine-id consistent with dbus
         #--------------------------------------
         if [ -e /var/lib/dbus/machine-id ]; then
             rm /var/lib/dbus/machine-id
         fi
         ln -s /etc/machine-id /var/lib/dbus/machine-id
