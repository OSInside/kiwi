kiwi system prepare
===================

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi system prepare -h | --help
   kiwi system prepare --description=<directory> --root=<directory>
       [--allow-existing-root]
       [--ignore-repos]
       [--set-repo=<source,type,alias,priority>]
       [--add-repo=<source,type,alias,priority>...]
       [--obs-repo-internal]
       [--add-package=<name>...]
       [--delete-package=<name>...]
   kiwi system prepare help

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

--add-package=<name>

  specify package to add(install). The option can be specified
  multiple times

--add-repo=<source,type,alias,priority>

  See the kiwi::system::build manual page for further details

--allow-existing-root

  allow to re-use an existing image root directory

--delete-package=<name>

  specify package to delete. The option can be specified
  multiple times

--description=<directory>

  Path to the kiwi XML description. Inside of that directory there
  must be at least a config.xml of \*.kiwi XML description.

--obs-repo-internal

  See the kiwi::system::build manual page for further details

--root=<directory>

  Path to create the new root system.

--set-repo=<source,type,alias,priority>

  See the kiwi::system::build manual page for further details
