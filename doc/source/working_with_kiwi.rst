Working with KIWI
=================

.. hint:: **Abstract**

   The following sections describe the general workflow of building
   appliances with KIWI |version|.

.. toctree::
   :maxdepth: 1

   working_with_kiwi/xml_description
   working_with_kiwi/shell_scripts
   working_with_kiwi/customize_the_boot_process
   working_with_kiwi/legacy_kiwi


Overview
--------

KIWI builds so-called system images (a fully installed and optionally
configured system in a single file) of a Linux distribution in two steps
(for further details, see :ref:`working-with-kiwi-image-building-process`):

1. *Prepare operation*: generate an *unpacked image tree* of your
   image. The unpacked tree is a directory containing the future file
   system of your image, generated from your image description.

2. *Create operation*: the unpacked tree generated in step 1 is packaged
   into the format required for the final usage (e.g. a ``qcow2`` disk
   image to launch the image with QEMU).

KIWI executes these steps using the following components, which it expects
to find in the *description directory*:

#. :file:`config.xml`: :ref:`xml-description`

   This XML file contains the image description, which is a collection of
   general settings of the final image, like the partition table, installed
   packages, present users, etc.

   The filename :file:`config.xml` is not mandatory, the image description
   file can also have an arbitrary name plus the :file:`*.kiwi` extension.
   KIWI first looks for a :file:`config.xml` file. If it cannot be found,
   it picks the first :file:`*.kiwi` file.

#. :file:`config.sh` and :file:`images.sh`:
   :ref:`working-with-kiwi-user-defined-scripts`

   If present, these configuration shell scripts run at the end of the
   *prepare operation* (:file:`config.sh`) or at the beginning of the
   *create operation* (:file:`images.sh`). They can be used to fine tune
   the image in ways that are not possible via the settings provided in
   :file:`config.xml`.

#. Overlay tree directory

   The *overlay tree* is a folder (called :file:`root`) or a tarball
   (called :file:`root.tar.gz`) that contains files and directories that
   will be copied into the *unpacked image tree* during the *Prepare
   operation*.
   The copying is executed after all the packages included in
   :file:`config.xml` have been installed. Any already present files are
   overwritten.

#. CD root user data

   For live ISO images and install ISO images an optional archive
   is supported. This is a tar archive matching the name
   :file:`config-cdroot.tar[.compression_postfix]`.

   If present, the archive will be unpacked as user data on the ISO
   image. For example, this is used to add license files or user
   documentation. The documentation can then be read directly from the
   CD/DVD without booting from the media.

#. Archives included in the :file:`config.xml` file.

   The archives that are included in `<packages>` using the `<archive>`
   element (see :ref:`xml-description-archive-element`):

   .. code:: xml

      <packages type="image">
          <archive name="custom-archive.tgz"/>
      </packages>


.. _working-with-kiwi-image-building-process:

Image Building Process
----------------------

KIWI creates images in a two step process. The first step, the *prepare*
operation, generates a so-called *unpacked image* tree (directory) using
the information provided in the :file:`config.xml` configuration file
(see :ref:`xml-description`)

The second step, the *create* operation, creates the *packed image* or
*image* in the specified format based on the unpacked image and the
information provided in the :file:`config.xml` configuration file.

.. figure:: .images/intro.png
    :align: center
    :alt: Image Creation Architecture

    Image Creation Architecture


.. _prepare-step:

The Prepare Step
^^^^^^^^^^^^^^^^

The first step of the image creation is the *prepare* step, during which
KIWI creates an *unpacked image*, also called the "root tree". This
directory will be the installation target for software packages to be
installed during the image creation process.

For the package installation, KIWI relies on the package manager specified
in the ``packagemanager`` element in :file:`config.xml` (see
:ref:`xml-description-preferences-common-elements`). KIWI supports the
following package managers: ``dnf``, ``zypper`` (default) and ``apt-get``.

The prepare step consists of the following substeps:

#. **Create Target Root Directory.**

   KIWI will exit with an error if the target root tree already exists to
   avoid accidental deletion of an existing unpacked image.

#. **Install Packages.**

   KIWI first configures the package manager to use the repositories
   specified in the configuration file and/or via the command line. After
   the repository setup, the packages specified in the ``bootstrap``
   section of the image description are installed in a temporary workspace
   external to the target root tree. This establishes the initial
   environment to support the completion of the process in a chroot
   setting. The essential packages to specify as part of the bootstrap
   environment are the ``filesystem`` and ``glibc-locale`` packages. The
   dependency chain of these two packages is usually sufficient to populate
   the bootstrap environment with all required software to support the
   installation of packages into the new root tree. Note that the
   aforementioned two packages might not be enough for every distribution,
   consult the `kiwi-descriptions repository
   <https://github.com/SUSE/kiwi-descriptions/>`_ for examples for various
   Linux distributions.

   The installation of software packages through the selected package
   manager may install unwanted packages. Removing these packages can be
   accomplished by marking them for deletion in the image description, see
   :ref:`xml-description-adding-and-removing-packages`.

#. **Apply the Overlay Tree.**

   Next, KIWI will apply all files and directories present in the overlay
   directory named :file:`root` or in the compressed overlay
   :file:`root.tar.gz` to the target root tree. Files already present in
   the target root directory will be overwritten. This allows you to
   overwrite any file that was installed by one of the packages during the
   installation phase.

#. **Apply Archives.**

   All archives specified in the `archive` element in the
   :file:`config.xml` file are applied in the specified order (top to
   bottom) after the overlay tree copy operation is complete (see
   :ref:`xml-description-archive-element`). Files and directories will be
   extracted relative to the top level of the new root tree. As with the
   overlay tree, it is possible to overwrite files already existing in the
   target root tree.

#. **Execute the user-defined script** :file:`config.sh`.

   At the end of the preparation stage the script :file:`config.sh` is
   executed (if present). It is run in the top level directory of the
   target root tree. The script's primary function is to complete the
   system configuration, for example to activate services. See
   :ref:`image-customization-config-sh` section for further details.

#. **Manage The New Root Tree.**

   .. FIXME: I don't understand the purpose of this paragraph, is this even
      relevant?

   The unpacked image directory is a directory, as far as the build system
   is concerned you can manipulate the content of this directory according
   to your needs. Since it represents a system installation you can
   "chroot" into this directory for testing purposes. The file system
   contains an additional directory named :file:`/image` that is not
   present in a regular system. It contains information KIWI requires
   during the create step, including a copy of the :file:`config.xml` file.

   Do not make any changes to the system, since they will get lost when
   re-running the ``prepare`` step again. Additionally, you may introduce
   errors that will occur during the ``create`` step which are difficult to
   track. The recommended way to apply changes to the unpacked image
   directory is to change the configuration and re-run the ``prepare``
   step.


.. _create-step:

The Create Step
^^^^^^^^^^^^^^^

KIWI creates the final image during the *create step*: it converts the
unpacked root tree into one or multiple output files appropriate for the
respective build type.

Note, that it is possible to create multiple images from the same unpacked
root tree. For example, it is possible to create a self installing OEM
image and a virtual machine image from the same image description. The only
prerequisite is that both image types are specified in :file:`config.xml`.

During the *create step* the following operations are performed by KIWI:

#. **Execute the User-defined Script** :file:`images.sh`.

   At the beginning of the image creation process the script named
   :file:`images.sh` is executed (if present). It is run in the top level
   directory of the unpacked root tree. The script is usually used to
   remove files that are no needed in the final image. For example, if an
   appliance is being built for a specific hardware, unnecessary kernel
   drivers can be removed using this script.

   See :ref:`image-customization-images-sh` for further details.

#. **Create the Requested Image Type.**

   KIWI converts the unpacked root into an output format appropriate for
   the requested build type.
