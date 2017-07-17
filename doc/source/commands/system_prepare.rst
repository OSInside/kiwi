kiwi system prepare
===================

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi system prepare -h | --help
   kiwi system prepare --description=<directory> --root=<directory>
       [--allow-existing-root]
       [--clear-cache]
       [--ignore-repos]
       [--ignore-repos-used-for-build]
       [--set-repo=<source,type,alias,priority,imageinclude>]
       [--add-repo=<source,type,alias,priority,imageinclude>...]
       [--add-package=<name>...]
       [--delete-package=<name>...]
       [--signing-key=<key-file>...]
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

--add-repo=<source,type,alias,priority,imageinclude>

  See the kiwi::system::build manual page for further details

--allow-existing-root

  allow to re-use an existing image root directory

--clear-cache

  delete repository cache for each of the used repositories
  before installing any package. This is useful if an image build
  should take and validate the signature of the package from the
  original repository source for any build. Some package managers
  unconditionally trust the contents of the cache, which is ok for
  cache data dedicated to one build but in case of kiwi the cache
  is shared between multiple image builds on that host for performance
  reasons.

--delete-package=<name>

  specify package to delete. The option can be specified
  multiple times

--description=<directory>

  Path to the kiwi XML description. Inside of that directory there
  must be at least a config.xml of \*.kiwi XML description.

--ignore-repos

  Ignore all repository configurations from the XML description.
  Using that option is usally done with a sequence of --add-repo
  options otherwise there are no repositories available for the
  image build which would lead to an error.

--ignore-repos-used-for-build

  Works the same way as --ignore-repos except that repository
  configurations which has the imageonly attribute set to true
  will not be ignored.

--root=<directory>

  Path to create the new root system.

--set-repo=<source,type,alias,priority,imageinclude>

  See the kiwi::system::build manual page for further details

--signing-key=<key-file>

  set the key file to be trusted and imported into the package
  manager database before performing any opertaion. This is useful
  if an image build should take and validate repository and package
  signatures during build time. This option can be specified multiple
  times.
