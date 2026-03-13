kiwi-ng image info
==================

.. _db_image_info_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng image info -h | --help
   kiwi-ng image info --description=<directory>
       [--resolve-package-list]
       [--list-profiles]
       [--print-kiwi-env]
       [--ignore-repos]
       [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>...]
       [--add-repo-credentials=<user:pass_or_filename>...]
       [--print-xml|--print-yaml]
   kiwi-ng image info help

.. _db_image_info_desc:

DESCRIPTION
-----------

Provides information about the specified image description. If no specific info
option is provided, the command lists basic information about the image. This
information is also available in the image XML description file. Specifying an
extension option like `resolve-package-list` makes a dependency resolver run
through the list of packages, providing more detailed information about
the image description.

.. _db_image_info_opts:

OPTIONS
-------

--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>

  Adds a new repository to the existing repository setup in the XML
  description. This option can be specified multiple times.

  - **source**

    Source URL pointing to a package repository that must be in a format
    supported by the selected package manager. See the URI_TYPES section for
    details about the supported source locators.

  - **type**

    Repository type: `rpm-md`, `apt-deb`.

  - **alias**

    An alias name for the repository. If not specified, {kiwi} generates
    an alias name as a result of a hex representation from uuid4. While the hex
    is used to uniquely identify the repository, it is not descriptive.
    We recommend using descriptive aliases.

  - **priority**

    A number indicating the repository priority. How the value is evaluated
    depends on the selected package manager. Refer to the package
    manager documentation for details about the supported priority ranges
    and their meaning.

  - **imageinclude**

    Set to either **true** or **false** to indicate if the repository
    is part of the system image repository setup or not.

  - **package_gpgcheck**

    Set to either **true** or **false** to indicate if the repository
    should validate the package signatures.

  - **{signing_keys}**

    A list of `signing_keys` enclosed in curly brackets and delimited by
    a semicolon. The reference to a signing key must be provided in the URI
    format.

  - **components**

    A component list for Debian-based repos as a space-delimited string.

  - **distribution**

    The main distribution name for Debian-based repos.

  - **repo_gpgcheck**

    Set to either **true** or **false** to indicate if the repository
    should validate the repository signature.

  - **repo_sourcetype**

    Specifies the source type of the repository path. Supported values
    are `baseurl`, `metalink`, or `mirrorlist`. With `baseurl`, the source
    path is interpreted as a simple URI. If `metalink` is set, the source
    path is resolved as a metalink URI, and if `mirrorlist` is set, the
    source path is resolved as a mirrorlist file. If not specified,
    `baseurl` is the default.

--add-repo-credentials=<user:pass_or_filename>

  For **uri://user:pass@location** repositories, set the user and password
  associated with an add-repo specification. If the provided value describes a
  filename in the filesystem, the first line of that file is used as
  credentials.

--description=<directory>

  The description must be a directory containing a kiwi XML
  description and optional metadata files.

--ignore-repos

  Ignores all repository configurations from the XML description.
  This option is usually used together with the `--add-repo`
  option. Otherwise, there are no repositories available for
  processing the requested image information, which could lead
  to an error.

--list-profiles

  Lists profiles available for the selected/default type.

  NOTE:
  If the image description is designed in a way that there
  is no default build type configured and/or the main build
  type is also profiled, it's required to provide this
  information to kiwi to list further profiles for this type.
  For example: kiwi-ng --profile top_level_entry_profile image info ...

--print-kiwi-env

  Prints kiwi profile environment variables. The listed variables
  are available in the shell environment of the kiwi hook scripts.

  NOTE:
  The kiwi profile environment grows during the build process.
  When used in early stages, e.g., in a `post_bootstrap.sh` script,
  it can happen that not all variables have a value. The setup
  of the kiwi profile environment in the image info output can
  therefore also only list the static configuration values
  that are known at the beginning of a build process.

--resolve-package-list

  Solves package dependencies and returns a list of all
  packages, including their attributes, for example, size,
  shasum, and more.

--print-xml

  Prints the image description in the XML format. The specified image description is
  converted to XML and sent to the XSLT stylesheet processor. The result is then
  validated using the RelaxNG schema and the schematron rules. The command is
  normally used to convert an old image description to the latest schema.

--print-yaml

  Behaves similarly to `--print-xml`, but after validation, the result is
  converted to the YAML format. The command can be used for different
  operations:

  * Conversion of the specified image description from or into different
    formats. This requires the `anymarkup` Python module to be installed. The
    module is not a hard requirement and is loaded on demand. If the module is
    missing, requests to convert to a format other than XML will fail.

  * Updates an old image description to the latest schema.
