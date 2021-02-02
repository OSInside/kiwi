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
       [--set-obs-repos=<user,password,project,name,profile,arch,repo>]
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


--set-obs-repos=<user,password,project,name,profile,arch,repo>

  overwrite the repo setup with the list of repositories provided
  from the given Open Build Service project.

  - **user**

    The OBS account user name

  - **password**

    The OBS account user password. The password is used in the
    GET request to the Open Build Service API server and not
    stored in any way

  - **project**

    The project source path as it is organized in the OBS project
    structure

  - **name**

    The name of the OBS package inside of the project. OBS
    organizes any type of build job as packages inside of a
    project. A KIWI image build is therefore also an OBS
    package. The `name` parameter wants this package name as
    it was used in OBS to build the image.

  - **profile**

    Optional name of the profile as defined in the KIWI image
    description. The selection of KIWI profiles is implemented
    with the multibuild feature in OBS. If your OBS project
    uses this feature it's needed to provide the profile
    name for the repo resolver, if not this field can be
    skipped or left empty

  - **arch**

    Optional architecture name. This defaults to `x86_64`

  - **repo**

    Optional repository name. In OBS a package build is connected
    to a repository name. This repository name groups a collection
    of software repositories to be used for the package build
    process. If the package build is a KIWI image build this
    repository name defaults to `images`. As the name can be
    set to any custom name, it's only required to specify the
    used repository name if another than the OBS default
    name is used.

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
