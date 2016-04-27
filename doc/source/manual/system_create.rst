kiwi system create
==================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng system create | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

DESCRIPTION
-----------

Create an image from a previously prepared image root directory.
The kiwi create call is usually issued after a kiwi prepare command
and builds the requested image type in the specified target directory

OPTIONS
-------

--root=<directory>

  Path to the image root directory. This directory is usually created
  by the kiwi prepare command. If a directory is used which was not
  created by kiwi's prepare command, it's important to know that kiwi
  stores image build metadata below the image/ directory which needs
  to be present in order to let the create command operate correctly.

--target-dir=<directory>

  Path to store the build results.
