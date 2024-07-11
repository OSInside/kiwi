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
       [--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>]
       [--set-repo-credentials=<user:pass_or_filename>]
       [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>...]
       [--add-repo-credentials=<user:pass_or_filename>...]
       [--add-package=<name>...]
       [--add-bootstrap-package=<name>...]
       [--delete-package=<name>...]
       [--set-container-derived-from=<uri>]
       [--set-container-tag=<name>]
       [--add-container-label=<label>...]
       [--set-type-attr=<attribute=value>...]
       [--set-release-version=<version>]
       [--signing-key=<key-file>...]
   kiwi-ng system prepare help

.. _db_kiwi_system_prepare_desc:

DESCRIPTION
-----------

Create a new image root directory. The prepare step sets up a new image
root directory from the specified XML description. The specified
directory acts as a root directory of the new image root system.
You can enter the system as root via chroot using the following command:

.. code:: bash

   $ chroot <directory> bash

.. _db_kiwi_system_prepare_opts:

OPTIONS
-------

--add-bootstrap-package=<name>

  Specify a package to install as part of the early {kiwi} bootstrap phase.
  The option can be specified multiple times.

--add-container-label=<name=value>

  Add a container label to the container configuration metadata. It
  overwrites the label with the provided key-value pair if it was
  already defined in the XML description.

--add-package=<name>

  Specify a package to add (install). The option can be specified
  multiple times.

--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>

  Add a new repository to the existing repository setup in the XML
  description. This option can be specified multiple times.
  For details about the supported option values, see the **--set-repo**
  information below

--add-repo-credentials=<user:pass_or_filename>

  For **uri://user:pass@location** type repositories, set the user and password
  connected with an add-repo specification. If the provided value is a
  filename in the filesystem, the first line of the file is used as
  credentials.

--allow-existing-root

  Allow to re-use an existing image root directory.

--clear-cache

  Delete repository cache for each of the used repositories
  before installing any package. This is useful if an image build
  validates the signature of the package from the
  original repository source for any build. Some package managers
  unconditionally trust the contents of the cache, which works for
  cache data dedicated to one build. In case of {kiwi}, the cache
  is shared between multiple image builds on the host for performance
  reasons.

--delete-package=<name>

  Specify a package to delete. The option can be specified
  multiple times.

--description=<directory>

  Path to the {kiwi} XML description. The directory must contain at least a
  config.xml of \*.kiwi XML description.

--ignore-repos

  Ignore all repository configurations in the XML description.
  This option is normally used in combination with the `--add-repo``
  option. Otherwise, an image build operation results in an error.

--ignore-repos-used-for-build

  Works the same way as `--ignore-repos`,` but the repository
  configurations that have the imageonly attribute set to **true**
  are not ignored.

--root=<directory>

  Path to the new root system.

--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>

  Overwrite the first repository entry in the XML description with the
  provided information:

  - **source**

    Source URL pointing to a package repository that must be in a format
    supported by the selected package manager. See the URI_TYPES section for
    details about the supported source locators.

  - **type**

    Repository type: `rpm-md`, `apt-deb`.

  - **alias**

    An alias name for the repository. If not specified, {kiwi} generates
    an alias name based hex representation of uuid4. While the hex 
    is used to uniquely identify the repository, it is not descriptive. 
    We recommend to use a descriptive and unique alias name.

  - **priority**

    A number indicating the repository priority. How the value is evaluated
    depends on the selected package manager. Refer to the package
    manager documentation for details about the supported priority ranges
    and their meaning.

  - **imageinclude**

    Set to either **true** or **false** to specify if the repository
    is part of the system image repository setup or not.

  - **package_gpgcheck**

    Set to either **true** or **false** to specify if the repository
    must validate the package signatures.

    - **{signing_keys}**

    List of signing_keys enclosed in curly brackets and delimited by
    the semicolon. The reference to a signing key must be provided in the URI
    format.

  - **components**

    Component list for Debian-based repos as a space-delimited string.

  - **distribution**

    Main distribution name for Debian-based repos.

  - **repo_gpgcheck**

    Set to either **true** or **false** to specify if the repository
    must validate the repository signature.

--set-repo-credentials=<user:pass_or_filename>

  For **uri://user:pass@location** type repositories, set the user and
  password connected to the set-repo specification. If the provided value
  is a filename in the filesystem, the first line of that file is
  used as credentials.

--set-container-derived-from=<uri>

  Overwrite the source location of the base container for the selected
  image type. The setting is only effective if the configured image type
  is setup with an initial derived_from reference

--set-container-tag=<name>

  Overwrite the container tag in the container configuration.
  The setting applies only if the container configuration
  provides an initial tag value.

--set-type-attr=<attribute=value>

  Overwrite/set the attribute with the provided value in the selected
  build type section. Example: `--set-type-attr volid=some`

--set-release-version=<version>

  Overwrite/set the release-version element in the selected
  build type preferences section

--signing-key=<key-file>

  Set the key file to be trusted and imported into the package
  manager database before performing any operation. This is useful
  if an image build validates repository and package
  signatures during build time. This option can be specified multiple
  times.
