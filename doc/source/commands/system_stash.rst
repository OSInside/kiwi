.. _kiwi_system_stash:

kiwi-ng system stash
====================

.. _db_kiwi_system_stash_desc:

Stores a root tree as an OCI container, called a stash, below
:file:`/var/tmp/kiwi-stash` and in the local container storage of
`podman`. Storing a root tree with an existing container name adds a
new layer. Stashes are the base of :ref:`kiwi_system_stackbuild`, see
:ref:`stackbuild`.

.. _db_kiwi_system_stash_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system stash --root <directory> [options]
   kiwi-ng system stash --list

.. _db_kiwi_system_stash_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--root <directory>``
     - The root tree, usually from `kiwi-ng system prepare` or
       `kiwi-ng system build`.
   * - ``--container-name <name>``
     - The container name. Default: the image name.
   * - ``--tag <name>``
     - The container tag. Default: `latest`.
   * - ``--list``
     - List the available stashes.

.. _db_kiwi_system_stash_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system stash --root /tmp/myimage/build/image-root
