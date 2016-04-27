kiwi result list
================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng result list | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

DESCRIPTION
-----------

List build results from a previous build or create command.
Please note if you build an image several times with the same
target directory the build result information will be overwritten
each time you build the image. Therefore the build result list
is valid for the last build

OPTIONS
-------

--target-dir=<directory>

  directory containing the kiwi build results
