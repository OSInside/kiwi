kiwi result list
================

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi result list -h | --help
   kiwi result list --target-dir=<directory>
   kiwi result list help

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
