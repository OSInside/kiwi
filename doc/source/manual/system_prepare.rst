kiwi system prepare
===================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng system prepare | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

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
