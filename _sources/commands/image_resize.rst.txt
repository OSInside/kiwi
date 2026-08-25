.. _db_kiwi_image_resize:

kiwi-ng image resize
====================

.. _db_kiwi_image_resize_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng image resize -h | --help
   kiwi-ng image resize --target-dir=<directory> --size=<size>
       [--root=<directory>]
   kiwi-ng image resize help

.. _db_kiwi_image_resize_desc:

DESCRIPTION
-----------

For disk-based images, this allows you to resize the image to a new disk geometry. The
additional space is free and not in use by the image. The OEM boot code in
{kiwi} offers a resizing procedure that can be used to make use of the
additional free space. For OEM image builds, it is advisable to run the resizing
operation.

.. _db_kiwi_image_resize_opts:

OPTIONS
-------

--root=<directory>

  The path to the root directory. If not specified, kiwi
  searches for the root directory in `build/image-root` under
  the specified target directory.

--size=<size>

  The new size of the image. The value is either a size in bytes,
  or it can be specified with m (MB) or g (GB). Example: 20g

--target-dir=<directory>

  The directory containing the kiwi build results.
