.. _kiwi_system_stackbuild:

kiwi-ng system stackbuild
=========================

.. _db_kiwi_system_stackbuild_desc:

Builds an image based on one or more stashes created by
:ref:`kiwi_system_stash`. Without ``--description``, it rebuilds the
image from the root tree and image description stored in the stash with
`kiwi-ng system create`. With ``--description``, it builds the given
image description on top of the stash with `kiwi-ng system build`. The
arguments after the `kiwi` subcommand are passed to that command, ``--``
is accepted instead of `kiwi`. For an introduction, see
:ref:`stackbuild`.

.. note::

   {kiwi} does not check if a stash fits the image description, for
   example nothing prevents building a Fedora image on a Leap stash.

.. _db_kiwi_system_stackbuild_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system stackbuild \
       --stash <name>... \
       --target-dir <directory> \
       [options] [kiwi <create options>]

   kiwi-ng [global options] system stackbuild \
       --stash <name>... \
       --target-dir <directory> \
       --description <directory> \
       [options] [kiwi <build options>]

.. _db_kiwi_system_stackbuild_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--stash <name>...``
     - Required. The stash, see ``kiwi-ng system stash --list``. Several
       stashes are stacked in the given order.
   * - ``--target-dir <directory>``
     - Required. The directory for the build results.
   * - ``--description <directory>``
     - The image description to build on top of the stash.
   * - ``--from-registry <URI>``
     - Pull the stash from this registry.

.. _db_kiwi_system_stackbuild_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system stackbuild --stash NAME --target-dir /target/rebuild \
       kiwi --signing-key /path/to/key
