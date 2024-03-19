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

Create an image from the previously prepared image root directory. The `kiwi
create` command is normally issued after the `kiwi prepare` command, and it and
builds the requested image type in the specified target directory.

.. _db_kiwi_system_create_opts:

OPTIONS
-------

--root=<directory>

  Path to the image root directory. This directory is normally created by the
  `kiwi prepare` command. Keep in mind that if the specified directory is not
  created using the `kiwi prepare` command, {kiwi} stores image build metadata
  in the image/ directory. This directory must exist for the `kiwi create`
  command to work correctly.

--target-dir=<directory>

  Path to store the build results.

--signing-key=<key-file>

  Trusted key file to be imported into the package manager database before
  performing any operation. This is useful if an image build validates
  repository and package signatures during build time. In the create step, this
  option only affects the boot image. This option can be specified multiple
  times.
