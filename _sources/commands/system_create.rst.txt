.. _kiwi_system_create:

kiwi-ng system create
=====================

.. _db_kiwi_system_create_desc:

Runs the create step: builds the image from a root tree created by
`kiwi-ng system prepare` and stores the image files in the target
directory, see :ref:`create-step`.

.. _db_kiwi_system_create_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system create \
       --root <directory> \
       --target-dir <directory> \
       [options]

.. _db_kiwi_system_create_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--root <directory>``
     - Required. The root tree. It must contain the build metadata in
       :file:`image/`, which the prepare step stores.
   * - ``--target-dir <directory>``
     - Required. The directory for the build results.
   * - ``--signing-key <key-file>...``
     - Import the key as trusted key into the package manager database.
       In the create step, this only affects the boot image.

.. _db_kiwi_system_create_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system create --root /tmp/myimage/root --target-dir /tmp/myimage
