.. _kiwi_system_create:

kiwi-ng system create
=====================

.. _db_kiwi_system_create_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system create -h | --help
   kiwi-ng system create --root=<directory> --target-dir=<directory>
       [--signing-key=<key-file>...]
   kiwi-ng system create help

.. _db_kiwi_system_create_desc:

DESCRIPTION
-----------

Create an image from a previously prepared image root directory.
The kiwi create call is usually issued after a kiwi prepare command
and builds the requested image type in the specified target directory

.. _db_kiwi_system_create_opts:

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

--signing-key=<key-file>

  set the key file to be trusted and imported into the package
  manager database before performing any opertaion. This is useful
  if an image build should take and validate repository and package
  signatures during build time. In create step this option only
  affects the boot image. This option can be specified multiple
  times
