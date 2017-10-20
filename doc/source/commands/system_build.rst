kiwi system build
=================

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi system build -h | --help
   kiwi system build --description=<directory> --target-dir=<directory>
       [--allow-existing-root]
       [--clear-cache]
       [--ignore-repos]
       [--ignore-repos-used-for-build]
       [--set-repo=<source,type,alias,priority,imageinclude>]
       [--add-repo=<source,type,alias,priority,imageinclude>...]
       [--add-package=<name>...]
       [--delete-package=<name>...]
       [--signing-key=<key-file>...]
   kiwi system build help

DESCRIPTION
-----------

build an image in one step. The build command combines kiwi's prepare and
create steps in order to build an image with just one command call. The
build command creates the root directory of the image below
`<target-dir>/build/image-root` and if not specified differently writes
a log file `<target-dir>/build/image-root.log`. The result image files
are created in the specified target-dir.

OPTIONS
-------

--add-package=<name>

  specify package to add(install). The option can be specified
  multiple times

--add-repo=<source,type,alias,priority,imageinclude>

  Add a new repository to the existing repository setup in the XML
  description. This option can be specified multiple times.
  For details about the provided option values see the **--set-repo**
  information below

--allow-existing-root

  Allow to use an existing root directory from an earlier
  build attempt. Use with caution this could cause an inconsistent
  root tree if the existing contents does not fit to the
  former image type setup

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

  Path to the XML description. This is a directory containing at least
  one _config.xml_ or _*.kiwi_ XML file.

--ignore-repos

  Ignore all repository configurations from the XML description.
  Using that option is usally done with a sequence of --add-repo
  options otherwise there are no repositories available for the
  image build which would lead to an error.

--ignore-repos-used-for-build

  Works the same way as --ignore-repos except that repository
  configurations which has the imageonly attribute set to true
  will not be ignored.

--set-repo=<source,type,alias,priority,imageinclude>

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
    should be part of the system image repository setup or not

--signing-key=<key-file>

  set the key file to be trusted and imported into the package
  manager database before performing any opertaion. This is useful
  if an image build should take and validate repository and package
  signatures during build time. This option can be specified multiple
  times

--target-dir=<directory>

  Path to store the build results.

URI_TYPES
---------

- **http://** | **https://** | **ftp://**

  remote repository delivered via http or ftp protocol.

- **obs://**

  Open Buildservice repository. The source data is translated into
  an http url pointing to http://download.opensuse.org.

- **ibs://**

  Internal Open Buildservice repository. The source data is translated into
  an http url pointing to download.suse.de.

- **iso://**

  Local iso file. kiwi loop mounts the file and uses the mount point
  as temporary directory source type

- **dir://**

  Local directory
