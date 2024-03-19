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

List build results from a previous build or create command. During multiple
image builds with the same target directory, the build result information is
overwritten every time you build an image. This means that the build result list
is valid for the last build only.

.. _db_kiwi_result_list_opts:

OPTIONS
-------

--target-dir=<directory>

  Directory containing the {kiwi} build results.
