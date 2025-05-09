kiwi-ng system update
=====================

.. _db_kiwi_system_update_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system update -h | --help
   kiwi-ng system update --root=<directory>
       [--add-package=<name>...]
       [--delete-package=<name>...]
   kiwi-ng system update help

.. _db_kiwi_system_update_desc:

DESCRIPTION
-----------

Update a previously prepare image root tree. The update command refreshes the
contents of the root directory according to the repository setup of the image
XML description. The update command can also be used to add or remove
packages from the image root tree.

.. _db_kiwi_system_update_opts:

OPTIONS
-------

--add-package=<name>

  Specify a package to add (install). The option can be specified
  multiple times.

--delete-package=<name>

  Specify a package to delete. The option can be specified
  multiple times.

--root=<directory>

  Path to the root directory of the image.
