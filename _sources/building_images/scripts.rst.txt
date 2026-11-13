.. _working-with-kiwi-user-defined-scripts:

Scripts
=======

.. sidebar:: Abstract

   This page describes the optional scripts of an image description,
   which customize the image in ways the image description itself does
   not support, and the functions {kiwi} provides for them.

Scripts in the image description directory run at defined points of the
build, see the diagram in :ref:`working-with-kiwi-image-building-process`.
Most of them run inside of the root tree (chroot):

.. list-table::
   :header-rows: 1
   :widths: 26 32 42

   * - Script
     - Runs
     - Purpose
   * - :file:`post_bootstrap.sh`
     - Prepare step, after the bootstrap
     - Configure the package manager for the following installation,
       or other early tasks.
   * - :file:`config.sh`
     - Prepare step, after the overlay tree and the users are set up
     - Final changes to the root tree, for example to configuration
       files of packages.
   * - :file:`config-overlay.sh`
     - Prepare step, after :file:`config.sh`
     - Last change to the delta root tree of a `docker` or `oci` type
       with `derived_from` and `delta_root="true"`.
   * - :file:`config-host-overlay.sh`
     - Prepare step, after :file:`config-overlay.sh`, **not chrooted**
     - Like :file:`config-overlay.sh`, but called on the host in the
       image root directory.
   * - :file:`images.sh`
     - Create step, at the beginning
     - Changes for the image type being built, for example only for a
       live ISO.
   * - :file:`pre_disk_sync.sh`
     - Create step of `oem` disk images, before the root tree is synced
       into the disk image
     - Last changes to the root tree, for example to remove tools or to
       change files which become read-only.
   * - :file:`disk.sh`
     - Create step of `oem` disk images, after the sync, chrooted into
       the disk image
     - Changes outside of the root tree, such as the partition table,
       the initrd or the bootloader.

Two further scripts are set with the `editbootconfig` and
`editbootinstall` attributes of the `type` element. Both are called on
the host, **not chrooted**, in the image root directory:

`editbootconfig`
   Runs after the bootloader configuration was written, before the root
   tree is synced into the disk, for disk and live ISO images. Its
   arguments are the name of the boot filesystem and the number of the
   boot partition.

`editbootinstall`
   Runs as the last step of an `oem` disk build, after the bootloader
   was installed. Its arguments are the disk image file name and the
   device of the boot partition.

A script with the executable bit set is run directly and needs a shebang
line, otherwise it is run with Bash. Scripts which are not chrooted
always run with Bash. If a script exits with a non-zero code, {kiwi}
stops the build.

.. warning::

   All scripts change the one root tree of the build. Their changes are
   permanent and are not undone.

Script Template
---------------

{kiwi} provides functions and variables to scripts in the file
:file:`/.kconfig`. Source it at the start of :file:`config.sh` or
:file:`images.sh`:

.. code:: bash

   #!/bin/bash
   test -f /.kconfig && . /.kconfig

.. _image-customization-methods:

Functions and Variables Provided by {kiwi}
-------------------------------------------

Functions
~~~~~~~~~

Functions starting with `base` work on all distributions, functions
starting with `suse` are specific to SUSE distributions. Other functions
in :file:`/.kconfig` are internal to {kiwi} and may change without
notice.

baseInsertService {servicename}
  Enables the service with `systemctl`.

baseRemoveService {servicename}
  Disables the service with `systemctl`.

baseService {servicename} {on|off}
  Enables or disables the service, for example `baseService sshd on`.

baseSystemdCall {service_name} {args}
  Calls `systemctl ${args} ${service_name}` if a systemd unit, mount or
  SysV init service with this name exists.

baseSystemdServiceInstalled {service}
  Prints the path of the first systemd unit or mount with this name.

baseSysVServiceInstalled {service}
  Prints the service name if a SysV init service with this name exists.

baseSetRunlevel {value}
  Sets the default run level.

baseUpdateSysConfig {filename} {variable} {value}
  Sets a variable in a sysconfig file.

baseStripLocales {list of locales}
  Removes all locales except the given ones.

baseStripTranslations {list of translations}
  Removes all translations except the given ones.

baseStripUnusedLibs
  Removes libraries which no program in the bin directories links
  against.

baseStripAndKeep {list of info-files to keep}
  Helper of the `baseStrip*` functions: removes the files read from
  stdin, except the given ones.

baseVagrantSetup
  Sets up the image as a Vagrant box: adds the `vagrant` user to the
  sudoers, installs the insecure Vagrant ssh key with the recommended
  ssh settings, starts the ssh daemon and creates the shared folder
  :file:`/vagrant`.

suseSetupProduct
  Creates the link :file:`/etc/products.d/baseproduct` to the product
  referenced by :file:`/etc/SuSE-brand`, :file:`/etc/os-release` or the
  latest `.prod` file in :file:`/etc/products.d`.

suseInsertService, suseRemoveService, suseService
  Call the respective `base` function, for compatibility only.

Debug {message}
  Prints the message if the variable `DEBUG` is set to 1.

Echo {echo commandline}
  Prints a message to the controlling terminal.

Rm {list of files}
  Deletes the files and logs the deletion.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Each script runs with the environment of the build, which contains the
following variables, among others. To list all of them, run:

.. code:: shell-session

   $ kiwi-ng image info --description=<directory> --print-kiwi-env

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Value
   * - `$kiwi_iname`
     - The name of the image.
   * - `$kiwi_iversion`
     - The version of the image.
   * - `$kiwi_type`
     - The image type of the `type` element.
   * - `$kiwi_profiles`
     - The profiles used for the build, comma-separated.
   * - `$kiwi_compressed`
     - The `compressed` attribute of the `type` element.
   * - `$kiwi_delete`
     - The packages of the `<packages type="delete">` section.
   * - `$kiwi_drivers`
     - The entries of the `drivers` section, comma-separated.
   * - `$kiwi_keytable`
     - The keytable setting.
   * - `$kiwi_language`
     - The locale setting.
   * - `$kiwi_timezone`
     - The timezone setting.

Debugging Scripts
-----------------

With the option `--debug-run-scripts-in-screen`, {kiwi} runs the scripts
in a `screen` session. A script can then open a shell to try out
commands while the build waits:

.. code:: bash

   echo "break"
   /bin/bash

The build continues when the shell is closed. List the sessions with:

.. code:: shell-session

   $ sudo screen -list

.. note::

   The `screen` session gives extended control over the build and is
   therefore only used with the option. In production, scripts must run
   without a terminal.

Configuration Tips
------------------

Locale
   {kiwi} sets the locale from the `locale` element with
   `systemd-firstboot`, which writes :file:`/etc/locale.conf`. On
   distributions which do not use this file, set the locale in
   :file:`config.sh` or with a file in the overlay tree instead.

Machine ID
   :file:`/etc/machine-id` must be unique for each deployment of an
   image. For images with a dracut initrd, {kiwi} clears the file if it
   exists and does not contain `uninitialized`. On first boot, systemd
   then generates a new ID and runs the services with
   `ConditionFirstBoot=yes`, see `machine-id(5)
   <https://www.freedesktop.org/software/systemd/man/machine-id.html>`_.
   :file:`config.sh` can create, remove or set the file to
   `uninitialized` to control this.

   If :file:`/etc/machine-id` does not exist, systemd can only create it
   if :file:`/etc` is writable at boot. Add `rw` to the kernel command
   line in this case, as dracut mounts the root filesystem read-only by
   default.

   :file:`/var/lib/dbus/machine-id` must contain the same ID. On older
   distributions, such as SLE 12, where it is a separate file, replace
   it with a link in :file:`config.sh`:

   .. code:: bash

      rm -f /var/lib/dbus/machine-id
      ln -s /etc/machine-id /var/lib/dbus/machine-id
