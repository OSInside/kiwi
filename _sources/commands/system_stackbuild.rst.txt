.. _kiwi_system_stackbuild:

kiwi-ng system stackbuild
=========================

.. _db_kiwi_system_stackbuild_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system stackbuild --help
   kiwi-ng system stackbuild --stash=<name>... --description=<directory> --target-dir=<directory>
       [--from-registry=<URI>]
       [kiwi <kiwi_build_command_args>...]
   kiwi-ng system stackbuild --stash=<name>... --target-dir=<directory>
       [--from-registry=<URI>]
       [kiwi <kiwi_create_command_args>...]

.. _db_kiwi_system_stackbuild_desc:

DESCRIPTION
-----------

Build an image based on one or more stash containers. A stash
is a {kiwi} built root tree stored as an OCI container, see
:ref:`kiwi_system_stash`. Using OCI images as the portable format
to store and distribute a root tree allows them to be pushed to
and pulled from OCI registries.

The `stackbuild` command operates in two modes:

1. Rebuild an image from a stash

   In this mode, `stackbuild` takes a stash, makes it available to the
   local registry, and builds the image using the stash rootfs and
   the image description stored in the stash. The given
   `kiwi` subcommand arguments are passed along to the
   `kiwi-ng system create` command.

   .. code:: bash

      $ kiwi-ng system stackbuild --stash NAME \
          --target-dir /target/rebuild

2. Build an image based on a stash

   In this mode, `stackbuild` takes a stash, makes it available to the
   local registry, and uses the stash rootfs as the base for an image
   build of another image description. The given `kiwi` subcommand
   arguments are passed along to the `kiwi-ng system build` command.

   .. code:: bash

      $ kiwi-ng system stackbuild --stash NAME \
          --description /some/image-description \
          --target-dir /target/rebuild

   .. note::

      The `stackbuild` command does not perform any consistency check
      to determine if the used stash rootfs is compatible with the
      provided image description. With that in mind, nothing prevents
      you from using a Leap stash and trying to build a Fedora
      image on top of it. It is the user's responsibility to
      combine only compatible stashes and image descriptions.

For a detailed introduction, see :ref:`stackbuild`.

.. _db_kiwi_system_stackbuild_opts:

OPTIONS
-------

--stash=<name>

  Name of the stash. See `kiwi-ng system stash --list` for available
  stashes. Multiple stashes will be stacked together in the given
  order.

--from-registry=<URI>

  Pull the given stash container name from the provided
  registry URI.

--description=<directory>

  Path to the XML description. This is a directory containing at least
  one `config.xml` or `*.kiwi` XML file.

--target-dir=<directory>

  Path to store the build results.

kiwi <kiwi_build_command_args>...

  List of command parameters as supported by the `kiwi-ng
  system build` command. The information given here is passed
  along to the `kiwi-ng system build` command if the
  `--description` option is set.

kiwi <kiwi_create_command_args>...

  List of command parameters as supported by the `kiwi-ng
  system create` command. The information given here is passed
  along to the `kiwi-ng system create` command if the
  `--description` option is not set.

.. note::

   For compatibility with the former `kiwi-stackbuild-plugin`, the
   `--` separator is accepted as an alias for the `kiwi` subcommand.

.. _db_kiwi_system_stackbuild_example:

EXAMPLE
-------

.. code:: bash

   $ kiwi-ng system stackbuild --stash NAME --target-dir /target/rebuild \
       kiwi --signing-key /path/to/key
