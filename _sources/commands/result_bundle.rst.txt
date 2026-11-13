.. _kiwi_result_bundle:

kiwi-ng result bundle
=====================

.. _db_kiwi_result_bundle_desc:

Bundles the results of the last build in a target directory for
distribution: adds the bundle identifier to the file names, compresses
uncompressed image files with xz, and creates a SHA checksum file for
each result.

.. _db_kiwi_result_bundle_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] result bundle \
       --target-dir <directory> \
       --id <bundle_id> \
       --bundle-dir <directory> \
       [options]

.. _db_kiwi_result_bundle_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--target-dir <directory>``
     - Required. The target directory of the build.
   * - ``--id <bundle_id>``
     - Required. Free-form text appended to the version in the file names.
   * - ``--bundle-dir <directory>``
     - Required. The directory to store the bundle in.
   * - ``--bundle-format <format>``
     - The file name format, overriding the `bundle_format` attribute of
       the image description. Placeholders: `%N` image name, `%P` profile
       names joined with `_`, `%A` architecture, `%I` bundle identifier,
       `%T` image type, `%M`, `%m`, `%p` major, minor and patch version,
       `%v` version.
   * - ``--zsync-source <location>``
     - The download location of the bundle for `zsync`. A zsync control
       file is created for each compressed result. All files of a bundle
       must be at the same location.
   * - ``--no-compress``
     - Do not compress the results. Files the build created compressed
       stay compressed.
   * - ``--package-as-rpm``
     - Package the results as RPM. Requires root permissions.

.. _db_kiwi_result_bundle_example:

Example
-------

.. code:: bash

   $ kiwi-ng result bundle --target-dir /tmp/myimage --id 1 \
       --bundle-dir /tmp/mybundle
