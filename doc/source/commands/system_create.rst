kiwi system create
==================

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi system create -h | --help
   kiwi system create --root=<directory> --target-dir=<directory>
   kiwi system create help

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
