.. _build_results:

Build Results
=============

.. sidebar:: Abstract

   This page describes the image types {kiwi} builds, the files a build
   creates, and how to bundle them for a release.

The image type is selected with the `image` attribute of the
`<preferences><type>` element, see :ref:`sec.preferences`. After a
successful `kiwi-ng system build` or `kiwi-ng system create`, the target
directory contains the image and further files. Their names follow the
pattern:

.. code:: bash

   <image-name>.<arch>-<version>.<extension>

`<image-name>` is the `name` attribute of the :ref:`sec.image` element,
`<arch>` the architecture of the build, `<version>` the `<version>`
element of the :ref:`preferences <sec.preferences>`, and `<extension>`
depends on the image type. `kiwi-ng result list` lists the results of
the last build in a target directory.

.. _image_types:

Image Types
-----------

The examples below use the image name `{exc_image_base_name}`, the
architecture `x86_64` and the version `{exc_image_version}`.

.. list-table::
   :header-rows: 1
   :widths: 20 45 35

   * - `image`
     - Image
     - Result files
   * - `oem`
     - A disk image for virtual machines, clouds or bare metal, which
       can resize itself to the disk it is deployed on. Optionally with
       an install ISO (`installiso="true"`) or an archive for network
       installation (`installpxe="true"`). The `format` attribute selects
       a virtual disk format instead of raw, for example `qcow2`. See
       :ref:`simple_disk` and :ref:`expandable_disk`.
     - :file:`.raw` or the selected format, for example :file:`.qcow2`;
       optionally :file:`.install.iso` and :file:`.install.tar`
   * - `iso`
     - A hybrid live ISO image, which boots from CD/DVD or a USB stick
       without touching the storage of the system. See :ref:`hybrid_iso`.
     - :file:`.iso`
   * - `docker`
     - A container image for Docker, loadable with `docker load -i`.
       See :ref:`building_container_build`.
     - :file:`.docker.tar.xz`
   * - `oci`
     - A container image in the format of the Open Container Initiative.
     - :file:`.oci.tar.xz`
   * - `wsl`
     - A container image for the Windows Subsystem for Linux 2.4.4 or
       later, a gzip-compressed tar archive. See :ref:`building_wsl_build`.
     - :file:`.wsl`
   * - `appx`
     - A container image for the Windows Subsystem for Linux, the former
       format replaced by `wsl`.
     - :file:`.appx`
   * - `kis`, `pxe`
     - A root filesystem image with a kernel and an initrd, packed into
       one archive, for custom deployments such as network boot. `pxe` is
       the legacy name. See :ref:`kis`.
     - :file:`.tar.xz`
   * - `enclave`
     - An initrd-based image in the `eif` format for AWS Nitro Enclaves,
       or for tests in QEMU. See :ref:`eif`.
     - :file:`.eif`
   * - `btrfs`, `ext2`, `ext3`, `ext4`, `erofs`, `squashfs`, `xfs`
     - The root tree in a filesystem image of the given type.
     - :file:`.<type>`, for example :file:`.ext4`
   * - `tbz`
     - The root tree in an xz-compressed tar archive.
     - :file:`.tar.xz`
   * - `cpio`
     - The root tree in a cpio archive.
     - :file:`.cpio`

Further Result Files
--------------------

Every build also creates the following files:

:file:`<image-name>.<arch>-<version>.packages`
   The packages of the image, sorted, one per line in the format
   `name|epoch|version|release|arch|disturl|license`. The fields are
   based on RPM metadata. Fields which other package managers do not
   provide are set to `None`. Compare the files of two builds to track
   package changes.

:file:`<image-name>.<arch>-<version>.verified`
   The result of the package verification of `rpm` or `dpkg` against the
   package database, in the RPM verification format. It shows the state
   of all packages before the first boot of the image.

.. _result_bundle_format:

Bundling Results
----------------

`kiwi-ng result bundle` copies the files needed for a release from the
target directory into a bundle directory, see :ref:`kiwi_result_bundle`.
It appends the given identifier to the version in the file names:

.. code:: bash

   $ kiwi-ng result bundle --target-dir /path/to/build_result \
       --bundle-dir /path/to/release_result --id release_identifier

For example, :file:`{exc_image_base_name}.x86_64-{exc_image_version}.iso`
is bundled as
:file:`{exc_image_base_name}.x86_64-{exc_image_version}-release_identifier.iso`.

For other file names, set the `bundle_format` attribute of the `type`
element, or use the option ``--bundle-format``, which takes precedence:

.. code:: xml

   <type image="..." bundle_format="%N-%v-%I"/>

The format is the base name of the bundled files and supports the
following placeholders:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Placeholder
     - Value
   * - `%N`
     - The `name` attribute of the `<image>` element.
   * - `%P`
     - The profiles used for the build, joined with `_` in the order they
       were given.
   * - `%A`
     - The architecture of the build, as reported by Python's
       `platform.machine`.
   * - `%I`
     - The identifier of the ``--id`` option.
   * - `%T`
     - The `image` attribute of the `<type>` element.
   * - `%M`, `%m`, `%p`
     - The major, minor and patch number of the `<version>` element.
   * - `%v`
     - The `<version>` element.
