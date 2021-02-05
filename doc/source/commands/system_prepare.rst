kiwi-ng system prepare
======================

.. _db_kiwi_system_prepare_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system prepare -h | --help
   kiwi-ng system prepare --description=<directory> --root=<directory>
       [--allow-existing-root]
       [--clear-cache]
       [--ignore-repos]
       [--ignore-repos-used-for-build]
       [--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>]
       [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>...]
       [--add-package=<name>...]
       [--add-bootstrap-package=<name>...]
       [--delete-package=<name>...]
       [--set-container-derived-from=<uri>]
       [--set-container-tag=<name>]
       [--add-container-label=<label>...]
       [--signing-key=<key-file>...]
   kiwi-ng system prepare help

.. _db_kiwi_system_prepare_desc:

DESCRIPTION
-----------

Create a new image root directory. The prepare step builds a new image
root directory from the specified XML description. The specified
root directory is the root directory of the new image root system.
As the root user you can enter this system via chroot as follows:

.. code:: bash

   $ chroot <directory> bash

.. _db_kiwi_system_prepare_opts:

OPTIONS
-------

--add-bootstrap-package=<name>

  specify package to install as part of the early kiwi bootstrap phase.
  The option can be specified multiple times

--add-container-label=<name=value>

  add a container label in the container configuration metadata. It
  overwrites the label with the provided key-value pair in case it was
  already defined in the XML description

--add-package=<name>

  specify package to add(install). The option can be specified
  multiple times

--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>

  Add a new repository to the existing repository setup in the XML
  description. This option can be specified multiple times.
  For details about the provided option values see the **--set-repo**
  information below

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

--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>

  Overwrite the first repository entry in the XML description with the
  provided information:

  - **source**

    source url, pointing to a package repository which must be in a format
    supported by the selected package manager. See the URI_TYPES section for
    details about the supported source locators.

  - **type**

    repository type, could be one of `rpm-md`, `rpm-dir` or `yast2`.

  - **alias**

    An alias name for the repository. If not specified kiwi calculates
    an alias name as result from a sha sum. The sha sum is used to uniquely
    identify the repository, but not very expressive. We recommend to
    set an expressive and uniq alias name.

  - **priority**

    A number indicating the repository priority. How the value is evaluated
    depends on the selected package manager. Please refer to the package
    manager documentation for details about the supported priority ranges
    and their meaning.

  - **imageinclude**

    Set to either **true** or **false** to specify if this repository
    should be part of the system image repository setup or not.

  - **package_gpgcheck**

    Set to either **true** or **false** to specify if this repository
    should validate the package signatures.

--set-container-derived-from=<uri>

  overwrite the source location of the base container for the selected
  image type. The setting is only effective if the configured image type
  is setup with an initial derived_from reference

--set-container-tag=<name>

  overwrite the container tag in the container configuration.
  The setting is only effective if the container configuraiton
  provides an initial tag value

--signing-key=<key-file>

  set the key file to be trusted and imported into the package
  manager database before performing any opertaion. This is useful
  if an image build should take and validate repository and package
  signatures during build time. This option can be specified multiple
  times.
