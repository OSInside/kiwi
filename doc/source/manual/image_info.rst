kiwi image info
===============

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi image info -h | --help
   kiwi image info --description=<directory>
       [--resolve-package-list]
       [--ignore-repos]
       [--add-repo=<source,type,alias,priority>...]
       [--obs-repo-internal]
   kiwi image info help

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


OPTIONS
-------

--add-repo=<source,type,alias,priority>

  Add repository with given source, type, alias and priority.

--description=<directory>

  The description must be a directory containing a kiwi XML
  description and optional metadata files.

--ignore-repos

  Ignore all repos from the XML configuration.

--obs-repo-internal

  When using obs repos resolve them using the SUSE internal
  buildservice. This only works if access to SUSE's internal
  buildservice is granted.

--resolve-package-list

  Solve package dependencies and return a list of all
  packages including their attributes e.g size,
  shasum, and more.
