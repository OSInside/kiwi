.. _db_kiwi_image_resize:

kiwi-ng image resize
====================

.. _db_kiwi_image_resize_desc:

Resizes a disk image. The added space is not used by the image until the
partitions are resized, for example by the resize on first boot of an
`oem` disk image. The command is therefore mostly useful for `oem`
images.

.. _db_kiwi_image_resize_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] image resize \
       --target-dir <directory> \
       --size <size> \
       [options]

.. _db_kiwi_image_resize_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--target-dir <directory>``
     - Required. The target directory of the build.
   * - ``--size <size>``
     - Required. The new size in bytes, or with the unit `m` (MiB) or `g`
       (GiB), for example `20g`.
   * - ``--root <directory>``
     - The root tree of the image. Default:
       :file:`<target-dir>/build/image-root`.

.. _db_kiwi_image_resize_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng image resize --target-dir /tmp/myimage --size 20g
