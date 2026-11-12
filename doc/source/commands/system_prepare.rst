.. _kiwi_system_prepare:

kiwi-ng system prepare
======================

.. _db_kiwi_system_prepare_desc:

Runs the prepare step: creates the root tree of an image from the image
description, see :ref:`prepare-step`. The image is then built from it
with `kiwi-ng system create`. In between, the root tree can be
inspected and changed, for example with `chroot <directory> bash`.

.. _db_kiwi_system_prepare_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system prepare \
       --description <directory> \
       --root <directory> \
       [options]

.. _db_kiwi_system_prepare_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--description <directory>``
     - Required. The image description directory.
   * - ``--root <directory>``
     - Required. The directory to create the root tree in.

All other options are the same as for `kiwi-ng system build`, see
:ref:`kiwi_system_build`: ``--allow-existing-root``, ``--clear-cache``,
the repository options, the package options, the image settings and the
key and certificate options.

.. _db_kiwi_system_prepare_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system prepare \
       --description kiwi/build-tests/{exc_description_disk} \
       --set-repo {exc_repo_leap} \
       --root /tmp/myimage/root
