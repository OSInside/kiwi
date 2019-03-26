Working with KIWI
=================

.. hint:: **Abstract**

   The following sections describe the general workflow of building
   appliances with KIWI |version|.

.. toctree::
   :maxdepth: 1

   working_with_kiwi/xml_description
..   working_with_kiwi/overlay
..   working_with_kiwi/
..   working_with_kiwi/terminology


Overview
--------

KIWI builds so-called system images (a fully installed and optionally
configured system in a single file) of a Linux distribution in two steps:

1. *Prepare operation*: generate an *unpacked image tree* of your
   image. The unpacked tree is a directory containing the future file
   system of your image, generated from your image description.

2. *Create operation*: the unpacked tree generated in step 1 is packaged
   into the format required for the final usage (e.g. a ``qcow2`` disk
   image to launch the image with QEMU).

KIWI executes these steps using the following components, which it expects
to find in the *description directory*:

#. ``config.xml``: :ref:`xml-description`

   This XML file contains the image description, which is a collection of
   general settings of the final image, like the partition table, installed
   packages, present users, etc.

   The filename :file:`config.xml` is not mandatory, the image description
   file can also have an arbitrary name plus the :file:`*.kiwi` extension.
   KIWI first looks for a :file:`config.xml` file. If it cannot be found,
   it picks the first :file:`*.kiwi` file.

#. ``config.sh`` shell script

   If present, this configuration shell script runs at the end of the
   *prepare operation*. It can be used to fine tune the unpacked image in
   ways that are not possible via the settings provided in
   :file:`config.xml`.

#. ``images.sh`` shell script

   The configuration shell script that runs at the beginning of the *create
   operation*. It is used to handle tasks specific to an image type.

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

