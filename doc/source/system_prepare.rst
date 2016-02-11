kiwi system prepare
===================

SYNOPSIS
--------

*kiwi* system prepare --description=<directory> --root=<directory>

    | [--allow-existing-root]
    | [--set-repo=<source,type,alias,priority>]
    | [--add-repo=<source,type,alias,priority>...]
    | [--obs-repo-internal]

DESCRIPTION
-----------

Create a new image root directory. The prepare step builds a new image
root directory from the specified XML description. The specified
root directory is the root directory of the new image root system.
As the root user you can enter this system via chroot as follows:

.. code-block:: bash

   $ chroot <directory> bash

OPTIONS
-------

--description=<directory>

  Path to the kiwi XML description. Inside of that directory there
  must be at least a config.xml of \*.kiwi XML description.

--root=<directory>

  Path to create the new root system.

--allow-existing-root

  allow to re-use an existing image root directory

--set-repo=<source,type,alias,priority>

  See the kiwi::system::build manual page for further details

--add-repo=<source,type,alias,priority>

  See the kiwi::system::build manual page for further details

--obs-repo-internal

  See the kiwi::system::build manual page for further details
