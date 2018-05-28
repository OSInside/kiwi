Basic Workflow
==============

.. hint:: **Abstract**

    Installation of a Linux system generally occurs by booting the target
    system from an installation source such as an installation CD/DVD, a live
    CD/DVD, or a network boot environment (PXE). The installation process is
    often driven by an installer that interacts with the user to collect
    information about the installation. This information generally includes the
    *software to be installed*, the *timezone*, system *user* data, and
    other information. Once all the information is collected, the installer
    installs the software onto the target system using packages from the
    software sources (repositories) available. After the installation is
    complete the system usually reboots and enters a configuration procedure
    upon start-up. The configuration may be fully automatic or it may include
    user interaction.
    This description applies for version |version|.

A system image (usually called "image"), is a *complete installation* of a Linux
system within a file. The image represents an operational system and,
optionally, contains the "final" configuration.

The behavior of the image upon deployment varies depending on the image type
and the image configuration since KIWI allows you to completely customize
the initial start-up behavior of the image. Among others, this includes
images that:

* can be deployed inside an existing virtual environment without requiring
  configuration at start-up.
* automatically configure themselves in a known target environment.
* prompt the user for an interactive system configuration.

The image creation process with KIWI is automated and does not require any
user interaction. The information required for the image creation process is
provided by the primary configuration file named :file:`config.xml`. 
This file is validated against the schema documented in
:ref:`Schema Documentation <schema-docs>` section.
In addition, the image can optionally be customized
using the :file:`config.sh` and :file:`images.sh` scripts
and by using an *overlay tree (directory)* called :file:`root`.
See `Components of an Image Description`_ section for further details.

.. note:: Previous Knowledge
    
    This documentation assumes that you are familiar with the general
    concepts of Linux, including the boot process, and distribution concepts
    such as package management.

Building Images
---------------

KIWI creates images in a two step process. The first step, the
``prepare`` operation, generates a so-called *unpacked image* tree
(directory) using the information provided in the :file:`config.xml`
configuration file. The :file:`config.xml` file is part of the *configuration
directory (tree)* that describes the image to be created by KIWI.

The second step, the ``create`` operation, creates the *packed image* or
*image* in the specified format based on the unpacked image and the information
provided in the :file:`config.xml` configuration file.

.. figure:: ../.images/intro.png
    :align: center
    :alt: Image Creation Architecture

    Image Creation Architecture

(1) Unpacked Image
    Encapsulated system reachable via chroot

(2) Packed Image
    Encapsulated system reachable via kernel file system/extension drivers such
    as loopback mounts, etc.

.. _name-convention:

.. note:: KIWI configuration file name convention

   KIWI at first place looks for a configuration file named
   :file:`config.xml`. If there is no such file, KIWI looks for files with a 
   :regexp:`*.kiwi` extension. In that case, the first match is the loaded file.

.. _prepare-step:

The Prepare Step
................

The creation of an image with KIWI is a two step process. The first step is
called the ``prepare`` step and it must complete successfully before the
second step, the ``create`` step can be executed.

During the prepare step, KIWI creates an *unpacked image*, also called "root
tree". The new root tree is created in a directory specified on the command
line with the option `--root` argument or the value of the ``defaultroot``
element in the :file:`config.xml` file. This directory will be the installation
target for software packages to be installed during the image creation process.

For package installation, KIWI relies on the package manager specified with the
``packagemanager`` element in the :file:`config.xml` file. KIWI supports the
following package managers: ``dnf``, ``zypper`` (default), ``yum`` and
``apt/dpkg``.

The prepare step consists of the following substeps:

#. **Create Target Root Directory.**

   KIWI will exit with an error if the target root tree already exists to
   avoid accidental deletion of an existing unpacked image. 

#. **Install Packages.**

   Initially, KIWI configures the package manager to use the repositories
   specified in the configuration file and/or the command line. Following the
   repository setup, the packages specified in the ``bootstrap`` section of the
   configuration file are installed in a temporary workspace external to
   the target root tree. This establishes the initial environment to support
   the completion of the process in chroot setting. The essential packages to
   specify as part of the bootstrap environment are the ``filesystem`` and
   ``glibc-locale`` packages. The dependency chain of these two packages is
   sufficient to populate the bootstrap environment with all required software
   to support the installation of packages into the new root tree.

   The installation of software packages through the selected package manager
   may install unwanted packages. Removing such packages can be accomplished by
   marking them for deletion in the configuration file. To do so specify a
   configuration entry like:

   .. code-block:: xml

      <package type="delete">package_to_be_deleted</package>

#. **Apply the Overlay Tree.**

   After the package installation is complete, KIWI will apply all files and
   directories present in the overlay directory named :file:`root` to the target
   root tree. Files already present in the target root directory will be
   overwritten, others will be added. This allows you to overwrite any file
   that was installed by one of the packages during the installation phase.

#. **Apply Archives.**

   Any archive specified with the ``archive`` element in the :file:`config.xml`
   file is applied in the specified order (top to bottom) after the overlay
   tree copy operation is complete. Files and directories will be extracted
   relative to the top level of the new root tree. As with the overlay tree,
   it is possible to overwrite files already existing in the target root tree.

#. **Execute the User-defined Scripts** :file:`config.sh`.

   At the end of the preparation stage the script named :file:`config.sh` is
   executed if present. It is executed on the top level of the target root tree.
   The script's primary function is to complete the system configuration, for
   example, by activating services. See `Image Customization with
   config.sh Shell Script`_ section for further details.

#. **Manage The New Root Tree.**

   The unpacked image directory is a directory, as far as the build system is
   concerned you can manipulate the content of this directory according to
   your needs. Since it represents a system installation you can "chroot" into
   this directory for testing purposes. The file system contains an additional
   directory named :file:`/image` that is not present in a regular system. It
   contains information KIWI requires during the create step, including a copy
   of the :file:`config.xml` file.

   Do not make any changes to the system, since they will get lost when
   re-running the ``prepare`` step again. Additionally, you may introduce errors
   that will occur during the ``create`` step which are difficult to track. The
   recommended way to apply changes to the unpacked image directory is to change
   the configuration and re-run the ``prepare`` step.


.. _create-step:

The Create Step
...............

The successful completion of the ``prepare`` step is a prerequisite for the
``create`` step. It ensures the unpacked root tree is complete and consistent.
Creating the packed, or final, image is done in the ``create`` step. Multiple
images can be created using the same unpacked root tree. It is, for example,
possible to create a self installing OEM image and a virtual machine image from
a single unpacked root tree. The only prerequisite is that both image types are
specified in the :file:`config.xml` before the prepare step is executed.

During the ``create`` step the following major operations are performed by
KIWI:

#. **Execute the User-defined Script** ``images.sh``.

   At the beginning of the image creation process the script named
   :file:`images.sh` is executed if present. It is executed on the top level of
   the target root tree. The script is usually used to remove files that are no
   needed in the final image. For example, if an appliance is being built for a
   specific hardware, unnecessary kernel drivers can be removed using this
   script. 
   
#. **Create Requested Image Type.** 

   The image types that can be created from a prepared image tree depend on the
   types specified in the image description :file:`config.xml` file. The
   configuration file must contain at least one ``type`` element. see: :ref:`building_types`
  
.. _description_components:

Components of an Image Description
----------------------------------

A KIWI image description can composed by several parts. The main part is
the KIWI description file itself (named :file:`config.xml` or an arbitrary
name plus the :file:`*.kiwi` extension). The configuration XML is the
only required component, others are optional.

These are the optional components of an image description:

#. ``config.sh`` shell script

   Is the configuration shell script that runs and the end of the
   :ref:`prepare step <prepare-step>` if present. It can be used to
   fine tune the unpacked image.

#. ``images.sh`` shell script

   Is the configuration shell script that runs at the begining of the
   create step. So it is expected to be used to handle image type specific
   tasks.

#. Overlay tree directory

   The *overlay tree* is a folder (called :file:`root`) 
   or a tarball file (called :file:`root.tar.gz`) that contains
   files and directories that will be copied to the target image build tree
   during the :ref:`prepare step <prepare-step>`. It is executed
   after all the packages included in the :file:`config.xml` file
   have been installed. Any already present file is overwritten.

#. CD root user data

   For live ISO images and install ISO images an optional cdroot archive
   is supported. This is a tar archive matching the name
   :file:`config-cdroot.tar[.compression_postfix]`. If present it will
   be unpacked as user data on the ISO image. This is mostly useful to
   add e.g license files or user documentation on the CD/DVD which
   can be read directly without booting from the media.

#. Archives included in the :file:`config.xml` file.

   The archives that are included in the `<packages>` using the `<archive>`
   subsection:

   .. code:: xml

      <packages type="image">
          <archive name="custom-archive.tgz"/>
      </packages>


Image Customization with ``config.sh`` Shell Script
...................................................

The KIWI image description allows to have an optional :file:`config.sh` bash
script in place. It can be used for changes appropriate for all images
to be created from a given unpacked image (since config.sh runs prior
to create step). Basically the script should be designed to take over
control of adding the image operating system configuration. Configuration
in that sense means all tasks which runs once in an os installation process
like activating services, creating configuration files, prepare an
environment for a firstboot workflow, etc. The :file:`config.sh` script is
called at the end of the :ref:`prepare step <prepare-step>` (after
users have been set and the *overlay tree directory* has been applied). If
:file:`config.sh` exits with an exit code != 0 the kiwi process will
exit with an error too.

See below a common template for `config.sh` script:

.. code:: bash

   #======================================
   # Functions...
   #--------------------------------------
   test -f /.kconfig && . /.kconfig
   test -f /.profile && . /.profile
   
   #======================================
   # Greeting...
   #--------------------------------------
   echo "Configure image: [$kiwi_iname]..."
   
   #======================================
   # Mount system filesystems
   #--------------------------------------
   baseMount
   
   #======================================
   # Call configuration code/functions
   #--------------------------------------
   ...
   
   #======================================
   # Umount kernel filesystems
   #--------------------------------------
   baseCleanMount

   #======================================
   # Exit safely
   #--------------------------------------
   exit 0

Common Functions
''''''''''''''''

The :file:`.kconfig` file allows to make use of a common set of functions. 
Functions specific to SUSE Linux specific begin with the name suse.
Functions applicable to all linux systems starts with the name base.
The following list describes the functions available inside the
:file:`config.sh` script.

``baseCleanMount``
  Umount the system filesystems :file:`/proc`, :file:`/dev/pts`, and
  :file:`/sys`.

``baseDisableCtrlAltDel``
  Disable the Ctrl–Alt–Del key sequence setting in :file:`/etc/inittab`.

``baseGetPackagesForDeletion``
  Return the name(s) of packages which will be deleted.

``baseGetProfilesUsed``
  Return the name(s) of profiles used to build this image.

``baseSetRunlevel {value}``
  Set the default run level.

``baseSetupBoot``
  Set up the linuxrc as init.

``baseSetupBusyBox {-f}``
  Activates busybox if installed for all links from the
  :file:`busybox/busybox.links` file—you can choose custom apps to be forced
  into busybox with the -f option as first parameter, for example:

  .. code:: bash

     baseSetupBusyBox -f /bin/zcat /bin/vi

``baseSetupInPlaceGITRepository``
  Create an in place git repository of the root directory. This process
  may take some time and you may expect problems with binary data handling.

``baseSetupInPlaceSVNRepository {path_list}``
  Create an in place subversion repository for the specified directories.
  A standard call could look like this baseSetupInPlaceSVNRepository
  :file:`/etc`, :file:`/srv`, and :file:`/var/log`.

``baseSetupPlainTextGITRepository``
  Create an in place git repository of the root directory containing all
  plain/text files.

``baseSetupUserPermissions``
  Search all home directories of all users listed in :file:`/etc/passwd` and
  change the ownership of all files to belong to the correct user and group.

``baseStripAndKeep {list of info-files to keep}``
  Helper function for strip* functions read stdin lines of files to check
  for removing params: files which should be keep.

``baseStripDocs {list of docu names to keep``
  Remove all documentation, except one given as parameter.

``baseStripInfos {list of info-files to keep}``
  Remove all info files, except one given as parameter.

``baseStripLocales {list of locales}``
  Remove all locales, except one given as parameter.

``baseStripMans {list of manpages to keep}``
  Remove all manual pages, except one given as parameter
  example:

  .. code:: bash
 
     baseStripMans more less

``baseStripRPM``
  Remove rpms defined in :file:`config.xml` in the image type=delete section.

``suseRemovePackagesMarkedForDeletion``
  Remove rpms defined in :file:`config.xml` in the image `type=delete`
  section. The difference compared to `baseStripRPM` is that the suse
  variant checks if the package is really installed prior to passing it
  to rpm to uninstall it. The suse rpm exits with an error exit code
  while there are other rpm version which just ignore if an uninstall
  request was set on a package which is not installed.

``baseStripTools {list of toolpath} {list of tools}``
  Helper function for suseStripInitrd function params: toolpath, tools.

``baseStripUnusedLibs``
  Remove libraries which are not directly linked against applications
  in the bin directories.

``baseUpdateSysConfig {filename} {variable} {value}``
  Update sysconfig variable contents.

``Debug {message}``
  Helper function to print a message if the variable DEBUG is set to 1.

``Echo {echo commandline}``
  Helper function to print a message to the controlling terminal.
 
``Rm {list of files}``
  Helper function to delete files and announce it to log.

``Rpm {rpm commandline}``
  Helper function to the RPM function and announce it to log.

``suseConfig``
  Setup keytable language, timezone and hwclock if specified in
  :file:`config.xml` and call SuSEconfig afterwards SuSEconfig is only
  called on systems which still support it.

``suseInsertService {servicename}``
  This function calls baseInsertService and exists only for
  compatibility reasons.

``suseRemoveService {servicename}``
  This function calls baseRemoveService and exists only for
  compatibility reasons.

``baseInsertService {servicename}``
  Activate the given service by using the :command:`chkconfig`
  or :command:`systemctl` program. Which init system is in use
  is auto detected.

``baseRemoveService {servicename}``
  Deactivate the given service by using the :command:`chkconfig`
  or :command:`systemctl` program. Which init system is in
  use is auto detected.

``baseService {servicename} {on|off}``
  Activate/Deactivate a service by using the :command:`chkconfig`
  or :command:`systemctl` program. The function requires the service
  name and the value on or off as parameters. Which init system is in
  use is auto detected.

``suseActivateDefaultServices``
  Activates the following sysVInit services to be on by default using
  the :command:`chkconfig` program: boot.rootfsck, boot.cleanup,
  boot.localfs, boot.localnet, boot.clock, policykitd, dbus, consolekit,
  haldaemon, network, atd, syslog, cron, kbd. And the following for
  systemd systems: network, cron.

``suseSetupProduct``
  This function creates the baseproduct link in :file:`/etc/products.d`
  pointing to the installed product.

``suseSetupProductInformation``
  This function will use zypper to search for the installed product
  and install all product specific packages. This function only
  makes sense if zypper is used as package manager.

``suseStripPackager {-a}``
  Remove smart or zypper packages and db files Also remove rpm
  package and db if -a given.

Profile Environment Variables
'''''''''''''''''''''''''''''

The :file:`.profile` environment file contains a specific set of
variables which are listed below. Some of the functions above
use the variables.

``$kiwi_compressed``
  The value of the compressed attribute set in the type element
  in :file:`config.xml`.

``$kiwi_delete``
  A list of all packages which are part of the packages section
  with `type="delete"` in :file:`config.xml`.

``$kiwi_drivers``
  A comma separated list of the driver entries as listed in the
  drivers section of the :file:`config.xml`.

``$kiwi_iname``
  The name of the image as listed in :file:`config.xml`.

``$kiwi_iversion``
  The image version string major.minor.release.

``$kiwi_keytable``
  The contents of the keytable setup as done in :file:`config.xml`.

``$kiwi_language``
  The contents of the locale setup as done in :file:`config.xml`.

``$kiwi_profiles``
  A list of profiles used to build this image.

``$kiwi_size``
  The predefined size value for this image. This is not the
  computed size but only the optional size value of the preferences
  section in :file:`config.xml`.

``$kiwi_timezone``
  The contents of the timezone setup as done in :file:`config.xml`.

``$kiwi_type``
  The basic image type.


Configuration Tips
''''''''''''''''''

In this section some ideas of how :file:`config.sh` file could be used to
fine tune the resulting unpacked image are quickly described:

#. **Stateless systemd UUIDs:**

  Usually during the image packages installation when *dbus* and/or
  *systemd* are installed machine ID files are created and set
  (:file:`/etc/machine-id`, :file:`/var/lib/dbus/machine-id`). Those
  UUIDs are meant to be unique and set only once in each deployment. In
  order to ensure that every single box running out from the same image
  has its own specific systemd UUID, the original image must not include
  any systemd or dbus ID, this way it is assigned during the first boot.
  The following bash snippet allows this behavior in :file:`config.sh`:

  .. code:: bash

     #======================================
     # Make machine-id stateless
     #--------------------------------------
     if [ -e /etc/machine-id ]; then
         > /etc/machine-id
         if [ -e /var/lib/dbus/machine-id ]; then
             rm /var/lib/dbus/machine-id
         fi
         ln -s /etc/machine-id /var/lib/dbus/machine-id
     fi

  .. note:: Avoid interactive boot

     It is important to remark that the file :file:`/etc/machine-id`    
     is set to an empty file instead of deleting it. Systemd may trigger 
     :command:`systemd-firstboot` service if this file is not present,
     which leads to an interactive firstboot where the user is
     asked to provide some data.

Image Customization with ``images.sh`` Shell Script
...................................................

The KIWI image description allows to have an optional :file:`images.sh`
bash script in place. It can be used for changes appropriate for
certain images/image types on case-by-case basis (since it runs at
beginning of :ref:`create step <create-step>`). Basically the script
should be designed to take over control of handling image type specific
tasks. For example if building the oem type requires some additional
package or config it can be handled in :file:`images.sh`. Please keep in
mind there is only one unpacked root tree the script operates in. This
means all changes are permanent and will not be automatically restored.
It is also the script authors tasks to check if changes done before do not
interfere in a negative way if another image type is created from the
same unpacked image root tree. If :file:`images.sh` exits with an exit
code != 0 the kiwi process will exit with an error too.

See below a common template for :file:`images.sh` script:

.. code:: bash

   #======================================
   # Functions...
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
   # Exit safely
   #--------------------------------------
   exit

Common Functions
''''''''''''''''

The :file:`.kconfig` file allows to make use of a common set of functions.
Functions specific to SUSE Linux specific begin with the name *suse*.
Functions applicable to all linux systems starts with the name *base*.
The following list describes the functions available inside the
:file:`images.sh` script.

``baseCleanMount``
  Umount the system file systems :file:`/proc`, :file:`/dev/pts`,
  and :file:`/sys`.

``baseGetProfilesUsed``
  Return the name(s) of profiles used to build this image.

``baseGetPackagesForDeletion``
  Return the list of packages setup in the packages *type="delete"*
  section of the :file:`config.xml` used to build this image.

``suseGFXBoot {theme} {loadertype}``
  This function requires the gfxboot and at least one *bootsplash-theme-**
  package to be installed to work correctly. The function creates from
  this package data a graphics boot screen for the isolinux and grub boot
  loaders. Additionally it creates the bootsplash files for the
  resolutions 800x600, 1024x768, and 1280x1024.

``suseStripKernel``
  This function removes all kernel drivers which are not listed in the
  drivers sections of the :file:`config.xml` file.

``suseStripInitrd``
  This function removes a whole bunch of tools binaries and libraries
  which are not required to boot a suse system with KIWI.

``Rm {list of files}``
  Helper function to delete files and announce it to log.

``Rpm {rpm commandline}``
  Helper function to the rpm function and announce it to log.

``Echo {echo commandline}``
  Helper function to print a message to the controlling terminal.

``Debug {message}``
  Helper function to print a message if the variable *DEBUG* is set to 1.

Profile environment variables
'''''''''''''''''''''''''''''

The :file:`.profile` environment file contains a specific set of
variables which are listed below. Some of the functions above use the
variables.

``$kiwi_iname``
  The name of the image as listed in :file:`config.xml`.

``$kiwi_iversion``
  The image version string major.minor.release.

``$kiwi_keytable``
  The contents of the keytable setup as done in :file:`config.xml`.

``$kiwi_language``
  The contents of the locale setup as done in :file:`config.xml`.

``$kiwi_timezone``
  The contents of the timezone setup as done in :file:`config.xml`.

``$kiwi_delete``
  A list of all packages which are part of the packages section with
  *type="delete"* in :file:`config.xml`.

``$kiwi_profiles``
  A list of profiles used to build this image.

``$kiwi_drivers``
  A comma separated list of the driver entries as listed in the drivers
  section of the :file:`config.xml`.

``$kiwi_size``
  The predefined size value for this image. This is not the computed size
  but only the optional size value of the preferences section in 
  :file:`config.xml`.

``$kiwi_compressed``
  The value of the compressed attribute set in the type element in
  :file:`config.xml`.

``$kiwi_type``
  The basic image type.


Customizing the Boot Process
----------------------------

Most Linux systems use a special boot image to control the system boot process
after the system firmware, BIOS or UEFI, hands control of the hardware to the
operating system. This boot image is called the :file:`initrd`. The Linux kernel
loads the :file:`initrd`, a compressed cpio initial RAM disk, into the RAM and
executes :command:`init` or, if present, :command:`linuxrc`.

Depending on the image type, KIWI creates the boot image automatically during
the ``create`` step. It uses a tool called `dracut` to create this initrd.
dracut generated initrd archives can be extended by custom modules to create
functionality which is not natively provided by dracut itself. In the scope
of KIWI the following dracut modules are used:

``kiwi-dump``
  The dracut module which serves as an image installer. It provides the
  required implementation to install a KIWI image on a selectable target.
  This module is required if one of the attributes `installiso`, `installstick`
  or `installpxe` is set to `true` in the image type definition

``kiwi-live``
  The dracut module which boots up a KIWI live image. This module is required
  if the `iso` image type is selected

``kiwi-overlay``
  The dracut module which allows to boot disk images configured with the
  attribute `overlayroot` set to `true`. Such a disk has its root partition
  compressed and readonly and boots up using overlayfs for the root filesystem
  using an extra partition on the same disk for persistent data.

``kiwi-repart``
  The dracut module which resizes an oem disk image after installation onto
  the target disk to meet the size constraints configured in the `oemconfig`
  section of the image description. The module takes over the tasks to
  repartition the disk, resizing of raid, lvm, luks and other layers and
  resizing of the system filesystems.

``kiwi-lib``
  The dracut module which provides functions of general use and serves
  as a library usable by other dracut modules. As the name says its
  main purpose is to function as library for the above mentioned kiwi
  dracut modules.

.. note:: Custom Boot Image Support

   Apart from the standard dracut based creation of the boot image, KIWI
   supports the use of custom boot images for the image types ``oem``
   and ``pxe``. The use of a custom boot image is activated by setting the
   following attribute in the image description:

   .. code-block:: none

      <type ... initrd_system="kiwi"/>

   Along with this setting it is now mandatory to provide a reference to
   a boot image description in the ``boot`` attribute like in the
   following example:

   .. code-block:: none

      <type ... boot="netboot/suse-leap42.3"/>

   Such boot descriptions for the oem and pxe types are currently still
   provided by the KIWI packages but will be moved into its own repository
   and package soon.

   The custom boot image descriptions allows a user to completely customize
   what and how the initrd behaves by its own implementation. This concept
   is mostly used in PXE environments which are usually highly customized
   and requires a specific boot and deployment workflow.
   

Boot Image Hook-Scripts
.......................

The dracut initrd system uses ``systemd`` to implement a predefined workflow
of services which are documented in the bootup document at:

http://man7.org/linux/man-pages/man7/dracut.bootup.7.html

To hook in a custom boot script into this workflow it's required to provide
a dracut module which is picked up by dracut at the time KIWI calls it.
The module files can be either provided as a package or as part of the
overlay directory in your image description

The following example demonstrates how to include a custom hook script
right before the system rootfs gets mounted.

1. Create a subdirectory for the dracut module

   .. code:: bash

       $ mkdir -p root/usr/lib/dracut/modules.d/90my-module

2. Register the dracut module in a configuration file

   .. code:: bash

       $ vi root/etc/dracut.conf.d/90-my-module.conf

       add_dracutmodules+=" my-module "

3. Create the hook script

   .. code:: bash

       $ touch root/usr/lib/dracut/modules.d/90my-module/my-script.sh

4. Create a module setup file

   .. code:: bash

       $ vi root/usr/lib/dracut/modules.d/90my-module/module-setup.sh

       #!/bin/bash

       # called by dracut
       check() {
           # check module integrity
       }

       # called by dracut
       depends() {
           # return list of modules depending on this one
       }

       # called by dracut
       installkernel() {
           # load required kernel modules when needed
           instmods _kernel_module_list_
       }

       # called by dracut
       install() {
           declare moddir=${moddir}
           inst_multiple _tools_my_module_script_needs_

           inst_hook pre-mount 30 "${moddir}/my-script.sh"
       }

That's it. At the time KIWI calls dracut the 90my-module will be taken
into account and is installed into the generated initrd. At boot time
systemd calls the scripts as part of the dracut-pre-mount.service

The dracut system offers a lot more possibilities to customize the
initrd than shown in the example above. For more information visit
the dracut project page at

http://people.redhat.com/harald/dracut.html

Boot Image Parameters
.....................

A dracut generated initrd in a KIWI image build process includes one ore
more of the KIWI provided dracut modules. The following list documents
the available kernel boot parameters for this modules:

``rd.kiwi.debug``
  This variable activates the debug log file for the kiwi part of
  the boot process at `/run/initramfs/log/boot.kiwi`

``rd.kiwi.install.pxe``
  This variable tells an oem installation image to lookup the system
  image on a remote location specified in rd.kiwi.install.image

``rd.kiwi.install.image=URI``
  This variable specifies the remote location of the system image in
  a pxe based oem installation

``rd.live.overlay.persistent``
  This variable tells a live iso image to prepare a persistent
  write partition.

``rd.live.overlay.cowfs``
  This variable tells a live iso image which filesystem should be
  used to store data on the persistent write partition.

``rd.live.dir``
  This variable tells a live iso image the directory which contains
  the live OS root directory. Defaults to `LiveOS`

``rd.live.squashimg``
  This variable tells a live iso image the name of the squashfs
  image file which holds the OS root. Defaults to `squashfs.img`

Boot Debugging
''''''''''''''

If the boot process encounters a fatal error, the default behavior is to
stop the boot process without any possibility to interact with the system.
Prevent this behavior by activating dracut's builtin debug mode in combination
with the kiwi debug mode as follows:

.. code-block:: bash

    rd.debug rd.kiwi.debug

This should be set at the Kernel command line. With those parameters activated,
the system will enter a limited shell environment in case of a fatal error
during boot. The shell contains a basic set of commands and allows for a closer
look to:

.. code-block:: bash

    less /run/initramfs/log/boot.kiwi
