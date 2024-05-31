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
       [--ignore-repos]
       [--add-repo=<source,type,alias,priority>...]
       [--print-xml|--print-yaml]
   kiwi-ng image info help

.. _db_image_info_desc:

DESCRIPTION
-----------

Provides information about the specified image description. If no specific info
option is provided, the command lists basic information about the image. This
information is also available in the image XML description file. Specifying an
extension option like `resolve-package-list` makes a dependency resolver to
run through the list of packages, providing more detailed information about
the image description.

.. _db_image_info_opts:

OPTIONS
-------

--add-repo=<source,type,alias,priority>

  Add repository with given source, type, alias and priority.

--description=<directory>

  The description must be a directory containing a kiwi XML
  description and optional metadata files.

--ignore-repos

  Ignore all repository configurations from the XML description.
  This option is usually used together with the --add-repo
  option. Otherwise there are no repositories available for the
  processing the requested image information, which could lead
  to an error.

--list-profiles

  list profiles available for the selected/default type.

  NOTE:
  If the image description is designed in a way that there
  is no default build type configured and/or the main build
  type is also profiled, it's required to provide this
  information to kiwi to list further profiles for this type.
  For example: kiwi-ng --profile top_level_entry_profile image info ...

--resolve-package-list

  Solve package dependencies and return a list of all
  packages including their attributes, for example size,
  shasum, and more.

--print-xml

  Print image description in the XML format. The specified image description is
  converted to XML and sent to the XSLT stylesheet processor. The result is then
  validated using the RelaxNG schema and the schematron rules. The command is
  normally used to convert an old image description to the latest schema.

--print-yaml

  Behaves similar to `--print-xml`, but after validation, the result is
  converted to the YAML format. The command can be used for different
  operations:

  * Conversion of the specified image description from or into different
    formats. This requires the `anymarkup` Python module to be installed. The
    module is not a hard requirement and loaded on demand. If the module is
    missing, requests to convert to other format than XML fail.

  * Update of an old image description to the latest schema
