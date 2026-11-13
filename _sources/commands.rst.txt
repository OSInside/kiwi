Working from the Command Line
=============================

.. sidebar:: Abstract

   This chapter describes the `kiwi-ng` command line of {kiwi-product}
   |version|: its structure, the global options and each command with
   its options.

.. toctree::
   :hidden:

   commands/kiwi
   commands/system_build
   commands/system_prepare
   commands/system_create
   commands/system_update
   commands/system_boxbuild
   commands/system_stash
   commands/system_stackbuild
   commands/result_list
   commands/result_bundle
   commands/image_info
   commands/image_resize

A `kiwi-ng` call consists of the global options, a service, a command
of the service and the options of the command:

.. code:: bash

   kiwi-ng [global options] <service> <command> [command options]

The global options are described in :doc:`commands/kiwi`. They must be
given before the service. The following services and commands exist:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Purpose
   * - :doc:`kiwi-ng system build <commands/system_build>`
     - Build an image from an image description, the prepare and the
       create step in one call.
   * - :doc:`kiwi-ng system prepare <commands/system_prepare>`
     - Create the root tree of an image from an image description.
   * - :doc:`kiwi-ng system create <commands/system_create>`
     - Create the image from a prepared root tree.
   * - :doc:`kiwi-ng system update <commands/system_update>`
     - Update a prepared root tree from its repositories.
   * - :doc:`kiwi-ng system boxbuild <commands/system_boxbuild>`
     - Build an image in a self-contained virtual machine or container.
   * - :doc:`kiwi-ng system stash <commands/system_stash>`
     - Store a root tree as an OCI container, called a stash.
   * - :doc:`kiwi-ng system stackbuild <commands/system_stackbuild>`
     - Build an image based on one or more stashes.
   * - :doc:`kiwi-ng result list <commands/result_list>`
     - List the results of the last build in a target directory.
   * - :doc:`kiwi-ng result bundle <commands/result_bundle>`
     - Bundle the results of a build for distribution.
   * - :doc:`kiwi-ng image info <commands/image_info>`
     - Show information about an image description.
   * - :doc:`kiwi-ng image resize <commands/image_resize>`
     - Resize a disk image.

Plugins can add further commands to the `system` service.

Getting Help
------------

`--help` shows the usage of `kiwi-ng`, of a service or of a command.
The positional argument `help` after a command opens its manual page,
which contains the same information as the command's page in this
documentation:

.. code:: shell-session

   $ kiwi-ng system build --help
   $ kiwi-ng system build help

Writing Options
---------------

* An option and its value are separated by a space or by `=`, for example
  `--target-dir /tmp/myimage` or `--target-dir=/tmp/myimage`.
* Options marked with ``...`` can be given multiple times.
* Shell completion is set up with `kiwi-ng --install-completion`, or
  printed for a custom setup with `kiwi-ng --show-completion`.
