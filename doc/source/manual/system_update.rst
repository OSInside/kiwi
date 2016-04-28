kiwi system update
==================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng system update | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

DESCRIPTION
-----------

Update a previously prepare image root tree. The update command
refreshes the contents of the root directory with potentially new
versions of the packages according to the repository setup of the
image XML description. In addition the update command also allows
to add or remove packages from the image root tree

OPTIONS
-------

--add-package=<name>

  specify package to add(install). The option can be specified
  multiple times

--delete-package=<name>

  specify package to delete. The option can be specified
  multiple times

--root=<directory>

  Path to the root directory of the image.
