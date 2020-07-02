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
       [--ignore-repos]
       [--add-repo=<source,type,alias,priority>...]
       [--print-xml|--print-yaml]
   kiwi-ng image info help

.. _db_image_info_desc:

DESCRIPTION
-----------

Provides information about the specified image description.
If no specific info option is provided the command just
lists basic information about the image which could also be
directly obtained by reading the image XML description file.
Specifying an extension option like `resolve-package-list`
will cause a dependency resolver to run over the list of
packages and thus provides more detailed information about
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
  Using that option is usally done with a sequence of --add-repo
  options otherwise there are no repositories available for the
  processing the requested image information which could lead
  to an error.

--resolve-package-list

  Solve package dependencies and return a list of all
  packages including their attributes e.g size,
  shasum, and more.

--print-xml

  Print image description in XML format. The given image
  description is read in, transformed internally to XML and
  send to the XSLT stylesheet processor. From there the result
  gets validated using the RelaxNG schema and the schematron
  rules. This result data will then be displayed. The typical
  use case for this command is to turn an old image description
  to the latest schema.

--print-yaml

  Behaves the same like `--print-xml` except that after
  validation the result data will be transformed into the
  YAML format and displayed. Due to this processing the
  command can be used for different operations:

  * Conversion of a given image description from or into
    different formats. It's required to install the `anymarkup`
    python module for this to work. The module is not a
    hard requirement and loaded on demand. If not available
    and a request to convert into a format different from XML
    is made an exception will be thrown.

  * Update of an old image description to the latest schema
