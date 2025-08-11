Concept and Workflow
====================

.. note:: **Abstract**

   The following sections describe the concept and general workflow
   of building appliances with {kiwi} |version|.

.. toctree::
   :maxdepth: 1

   concept_and_workflow/systemdeps.rst
   concept_and_workflow/repository_setup
   concept_and_workflow/packages
   concept_and_workflow/profiles
   concept_and_workflow/users
   concept_and_workflow/shell_scripts
   concept_and_workflow/runtime_configuration
   concept_and_workflow/customize_the_boot_process


Overview
--------

{kiwi} builds so-called *system images* (a fully installed and optionally
configured system in a single file) of a Linux distribution in two steps (for
further details, see :ref:`working-with-kiwi-image-building-process`):

1. *Prepare operation*: generate an *unpacked image tree* of your
   image. The unpacked tree is a directory containing the future file
   system of your image, generated from your image description.

2. *Create operation*: the unpacked tree generated in step 1 is packaged
   into the format required for the final usage (e.g. a ``qcow2`` disk
   image to launch the image with QEMU).

{kiwi} executes these steps using the following components, which it expects
to find in the *description directory*:

:ref:`image-description`:
  The :file:`config.xml` file contains the image description, which is a
  collection of general settings of the final image, like the image layout
  installed packages, present users, etc.

  .. note::

     The filename :file:`config.xml` is not mandatory, the image description
     file can also have an arbitrary name plus the :file:`*.kiwi` extension.
     {kiwi} first looks for a :file:`config.xml` file. If it cannot be found,
     it picks the first :file:`*.kiwi` file.

:ref:`working-with-kiwi-user-defined-scripts`:
   If present, custom configuration shell scripts run at different
   stages of the build process. They can be used to fine tune
   the image in ways that are not possible via the settings provided in
   :file:`config.xml`.

Overlay tree directory:
   The *overlay tree* is a folder (called :file:`root`) or a tarball
   (called :file:`root.tar.gz`) that contains files and directories that
   will be copied into the *unpacked image tree* during the *Prepare
   operation*.
   The copying is executed after all the packages included in
   :file:`config.xml` have been installed. Any already present files are
   overwritten.

CD root user data:
   For live ISO images and install ISO images an optional archive
   is supported. This is a tar archive matching the name
   :file:`config-cdroot.tar[.compression_postfix]`.

   If present, the archive will be unpacked as user data on the ISO
   image. For example, this is used to add license files or user
   documentation. The documentation can then be read directly from the
   CD/DVD without booting from the media.

.. _working-with-kiwi-image-building-process:

Image Building Process
----------------------

{kiwi} creates images in a two step process: The first step, the *prepare*
operation, generates a so-called *unpacked image tree* (directory) using
the information provided in the :file:`config.xml` configuration file
(see :ref:`image-description`)

The second step, the *create* operation, creates the *packed image* or
*image* in the specified format based on the unpacked image tree and the
information provided in the :file:`config.xml` configuration file.

.. figure:: .images/intro.png
    :align: center
    :alt: Image Creation Architecture

    Image Creation Architecture


.. _prepare-step:

The Prepare Step
^^^^^^^^^^^^^^^^

As the first step, {kiwi} creates an *unpackaged image tree*, also called "root tree". This
directory will be the installation target for software packages to be
installed during the image creation process.

For the package installation, {kiwi} relies on the package manager specified
in the ``packagemanager`` element in :file:`config.xml`. {kiwi} supports the
following package managers: ``dnf``, ``zypper`` (default) and ``apt``.

The prepare step consists of the following substeps:

#. **Create Target Root Directory**

   By default {kiwi} aborts with an error if the target root tree
   already exists to avoid accidental deletion of an existing
   unpacked image. The option `--allow-existing-root` can be used
   to work based on an existing root tree

#. **Bootstrap Target Root Directory**

   First, {kiwi} configures the package manager to use the repositories
   specified in the configuration file, via the command line, or
   both. After the repository setup, the packages specified in the
   ``bootstrap`` section of the image description are installed in a
   temporary directory external to the target root tree. This establishes
   the initial environment to support the completion of the process in a
   chroot setting. At the end of the ``bootstrap`` phase the script
   :file:`post_bootstrap.sh` is executed, if present.

   .. note::

      The essential bootstrap packages are usually ``filesystem`` and
      ``glibc-locale`` to specify as part of the bootstrap. The dependency
      chain of these two packages is usually sufficient to populate the
      bootstrap environment with all required software to support the
      installation of packages into the new root tree.

#. **Install Packages**

   After the ``bootstrap`` phase all other `<packages>` sections are
   used to complete the installation as chroot operation. {kiwi} uses
   the package manager as installed in the ``bootstrap`` phase and
   installs all other packages as configured.

   .. note::

      The installation of software packages through the selected package
      manager may install unwanted packages. Removing these packages can be
      accomplished by marking them for deletion in the image description, see
      :ref:`uninstall-system-packages`.

#. **Apply the Overlay Tree**

   Next, {kiwi} applies all files and directories present in the overlay
   directory named :file:`root` or in the compressed overlay
   :file:`root.tar.gz` to the target root tree. Files already present in
   the target root directory are overwritten. This allows you to
   overwrite any file that was installed by one of the packages during the
   installation phase.

#. **Apply Archives**

   All archives specified in the `archive` element of the
   :file:`config.xml` file are applied in the specified order (top to
   bottom) after the overlay tree copy operation is complete (see
   :ref:`archive-element`). Files and directories are
   extracted relative to the top level of the new root tree. As with the
   overlay tree, it is possible to overwrite files already existing in the
   target root tree.

#. **Execute the user-defined script** :file:`config.sh`

   At the end of the preparation stage the script :file:`config.sh` is
   executed (if present). It is run in the top level directory of the
   target root tree. The script's primary function is to complete the
   system configuration. For more details about custom scripts
   see :ref:`working-with-kiwi-user-defined-scripts`

#. **Modify the Root Tree**

   The unpacked image tree is now finished to be converted into the final
   image in the *create step*. It is possible to make manual modifications
   to the unpacked tree before it is converted into the final image.

   Since the unpacked image tree is just a directory, it can be modified
   using the standard tools. Optionally, it is also possible to "change
   root (:command:`chroot`)" into it, for instance to invoke the package
   manager. Beside the standard file system layout, the unpacked image tree
   contains an additional directory named :file:`/image` that is not
   present in a regular system. It contains information {kiwi} requires
   during the create step, including a copy of the :file:`config.xml` file.

   By default, {kiwi} will not stop after the *prepare step* and will
   directly proceed with the *create step*. Therfore to perform manual
   modifications, proceed as follows:

   .. code:: shell-session

      $ kiwi-ng system prepare $ARGS
      $ # make your changes
      $ kiwi-ng system create $ARGS

   .. warning:: Modifications of the unpacked root tree

      Do not make any changes to the system, since they are lost when
      re-running the ``prepare`` step again. Additionally, you may
      introduce errors that occur during the ``create`` step which are
      difficult to track. The recommended way to apply changes to the
      unpacked image directory is to change the configuration and re-run
      the ``prepare`` step.


.. _create-step:

The Create Step
^^^^^^^^^^^^^^^

{kiwi} creates the final image during the *create step*: it converts the
unpacked root tree into one or multiple output files appropriate for the
respective build type.

It is possible to create multiple images from the same unpacked
root tree, for example, a self installing OEM
image and a virtual machine image from the same image description. The only
prerequisite is that both image types are specified in :file:`config.xml`.

During the *create step* the following operations are performed by {kiwi}:

#. **Execute the User-defined Script** :file:`images.sh`

   At the beginning of the image creation process the script named
   :file:`images.sh` is executed (if present). For more details about
   custom scripts see :ref:`working-with-kiwi-user-defined-scripts`

#. **Create the Requested Image Type**

   {kiwi} converts the unpacked root into an output format appropriate for
   the requested build type.
