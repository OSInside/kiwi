.. _kiwi_system_build:

kiwi-ng system build
====================

.. _db_kiwi_system_build_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system build -h | --help
   kiwi-ng system build --description=<directory> --target-dir=<directory>
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
   kiwi-ng system build help

.. _db_kiwi_system_build_desc:

DESCRIPTION
-----------

Build an image in one step. The build command combines preparation and building
steps, which makes it possible to create an image with a single command. The
build command creates the root directory of the image under
`<target-dir>/build/image-root` and writes a log file
`<target-dir>/build/image-root.log`. The result image files are created in the
specified target directory.

.. _db_kiwi_system_build_opts:

OPTIONS
-------

--add-bootstrap-package=<name>

  Specify package to install as part of the early {kiwi} bootstrap phase.
  The option can be specified multiple times.

--add-container-label=<name=value>

  Add a container label in the container configuration metadata. It
  overwrites the label with the provided key-value pair if it is
  already defined in the XML description.

--add-package=<name>

  Specify package to add (install). The option can be specified
  multiple times.

--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>

  Add a new repository to the existing repository setup in the XML
  description. This option can be specified multiple times.
  For details about the possible option values see the **--set-repo**
  information below.

--add-repo-credentials=<user:pass_or_filename>

  For **uri://user:pass@location** repositories, set the user and password
  associated with an add-repo specification. If the provided value describes a
  filename in the filesystem, the first line of that file is used as
  credentials.

--allow-existing-root

  Use an existing root directory from a previous
  build attempt. Use with caution, because this can cause an inconsistent
  root tree if the existing contents does not fit to the
  previous image type setup.

--clear-cache

  Delete repository cache for each of the used repositories
  before installing any package. This is useful when an image build
  validates the signature of the package from the
  original repository source for any build. Some package managers
  unconditionally trust the contents of the cache, which works for
  cache data dedicated to one build. In case of {kiwi}, the cache
  is shared between multiple image builds on that host for performance
  reasons.

--delete-package=<name>

  Specify package to delete. The option can be specified
  multiple times.

--description=<directory>

  Path to an XML description. This is a directory containing at least
  one _config.xml_ or _*.kiwi_ XML file.

--ignore-repos

  Ignore all repository configurations from the XML description.
  This option is used in combination with the `--add-repo``
  option. Otherwise, there are no repositories available for an
  image build, which leads to an error.

--ignore-repos-used-for-build

  Works the same way as `--ignore-repos`, except that repository configuration
  with the imageonly attribute set to **true** is not ignored.

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
    an alias name as result of hex representation from uuid4. While the hex 
    is used to uniquely identify the repository, it is not descriptive. 
    We recommend using descriptive aliases.

  - **priority**

    A number indicating the repository priority. How the value is evaluated
    depends on the selected package manager. Refer to the package
    manager documentation for details about the supported priority ranges
    and their meaning.

  - **imageinclude**

    Set to either **true** or **false** to indicate if the repository
    is be part of the system image repository setup or not.

  - **package_gpgcheck**

    Set to either **true** or **false** to indicate if the repository
    should validate the package signatures.

  - **{signing_keys}**

    List of signing_keys enclosed in curly brackets and delimited by 
    the semicolon. The reference to a signing key must be provided in the URI
    format.

  - **components**

    Component list for Debian-based repos as space-delimited string.

  - **distribution**

    Main distribution name for Debian-based repos.

  - **repo_gpgcheck**

    Set to either **true** or **false** to indicate if the repository
    should validate the repository signature.

--set-repo-credentials=<user:pass_or_filename>

  For **uri://user:pass@location** type repositories, set the user and
  password connected to the set-repo specification. If the provided
  value describes a filename in the filesystem, the first line of that file
  is used as credentials.

--set-container-derived-from=<uri>

  Overwrite the source location of the base container for the selected
  image type. The setting applies only if the configured image type
  is setup with an initial derived_from reference.

--set-container-tag=<name>

  Overwrite the container tag in the container configuration.
  The setting is only effective if the container configuration
  provides the initial tag value.

--set-type-attr=<attribute=value>

  Overwrite/set the attribute with the provided value in the selected
  build type section. Example: `--set-type-attr volid=some`

--set-release-version=<version>

  Overwrite/set the release-version element in the selected
  build type preferences section

--signing-key=<key-file>

  Set the key file to be trusted and imported into the package
  manager database before performing any operation. This is useful
  when an image build validates repository and package
  signatures during build time. This option can be specified multiple
  times.

--target-dir=<directory>

  Path to store the build results.

.. _db_kiwi_system_build_uri:

URI_TYPES
---------

- **http://** | **https://** | **ftp://**

  Remote repository delivered via the HTTP or FTP protocol.

- **obs://**

  Open Buildservice repository. The source data is translated into
  an HTTP URL pointing to http://download.opensuse.org.

- **ibs://**

  Internal Open Buildservice repository. The source data is translated into
  an HTTP URL pointing to download.suse.de.

- **iso://**

  Local ISO file. {kiwi} loop mounts the file and uses the mount point
  as temporary directory source type.

- **dir://**

  Local directory.
