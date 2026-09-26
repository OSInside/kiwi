.. _kiwi_system_stash:

kiwi-ng system stash
====================

.. _db_kiwi_system_stash_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system stash --help
   kiwi-ng system stash --root=<directory>
       [--tag=<name>]
       [--container-name=<name>]
   kiwi-ng system stash --list

.. _db_kiwi_system_stash_desc:

DESCRIPTION
-----------

Create a container from the given root directory. The command
takes the contents of the given root directory at call time
and creates an OCI container from it, called a stash. The stash
is stored below `/var/tmp/kiwi-stash` and imported into the
local container registry using `podman`. If a stash with the
same container name already exists, a new layer is added to it.

A stash can be used as the image root for the
:ref:`kiwi_system_stackbuild` command. For a detailed introduction,
see :ref:`stackbuild`.

.. _db_kiwi_system_stash_opts:

OPTIONS
-------

--root=<directory>

  The path to the root directory, usually the result of
  a former system prepare or build call.

--tag=<name>

  The tag name for the container. By default, `latest`
  is used.

--container-name=<name>

  The name of the container. By default, it is
  set to the image name of the stash.

--list

  List the available stashes.

.. _db_kiwi_system_stash_example:

EXAMPLE
-------

.. code:: bash

   $ kiwi-ng system stash --root /tmp/mytest/build/image-root
