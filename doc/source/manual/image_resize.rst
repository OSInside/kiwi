kiwi image resize
=================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng image resize | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

DESCRIPTION
-----------

For disk based images, allow to resize the image to a new disk geometry.
The additional space is free and not in use by the image. In order to
make use of the additional free space a repartition process is required
like it is provided by kiwi's oem boot code. Therefore the resize operation
is useful for oem image builds most of the time.

OPTIONS
-------

--root=<directory>

  The path to the root directory, if not specified kiwi
  searches the root directory in build/image-root below
  the specified target directory

--size=<size>

  New size of the image. The value is either a size in bytes
  or can be specified with m=MB or g=GB. Example: 20g

--target-dir=<directory>

  Directory containing the kiwi build results
