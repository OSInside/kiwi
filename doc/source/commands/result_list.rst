kiwi-ng result list
===================

.. _db_kiwi_result_list_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng result list -h | --help
   kiwi-ng result list --target-dir=<directory>
   kiwi-ng result list help

.. _db_kiwi_result_list_desc:

DESCRIPTION
-----------

List build results from a previous build or create command.
Please note if you build an image several times with the same
target directory the build result information will be overwritten
each time you build the image. Therefore the build result list
is valid for the last build

.. _db_kiwi_result_list_opts:

OPTIONS
-------

--target-dir=<directory>

  directory containing the kiwi build results
