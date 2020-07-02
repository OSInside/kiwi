kiwi-ng
=======

.. _db_commands_kiwi_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng -h | --help
   kiwi-ng [--profile=<name>...]
           [--type=<build_type>]
           [--logfile=<filename>]
           [--debug]
           [--color-output]
       image <command> [<args>...]
   kiwi-ng [--debug]
           [--color-output]
       result <command> [<args>...]
   kiwi-ng [--profile=<name>...]
           [--shared-cache-dir=<directory>]
           [--type=<build_type>]
           [--logfile=<filename>]
           [--debug]
           [--color-output]
       system <command> [<args>...]
   kiwi-ng compat <legacy_args>...
   kiwi-ng -v | --version
   kiwi-ng help

.. _db_commands_kiwi_desc:

DESCRIPTION
-----------

{kiwi} is an imaging solution that is based on an image XML description.
Such a description is represented by a directory which includes at least
one :file:`config.xml` or :file:`.kiwi` file and may as well include other files like
scripts or configuration data.

A collection of example image descriptions can be found on the github
repository here: https://github.com/OSInside/kiwi-descriptions. Most of the
descriptions provide a so called JeOS image. JeOS means Just enough
Operating System. A JeOS is a small, text only based image including a
predefined remote source setup to allow installation of missing
software components at a later point in time.

{kiwi} operates in two steps. The system build command combines
both steps into one to make it easier to start with {kiwi}. The first
step is the preparation step and if that step was successful, a
creation step follows which is able to create different image output
types.

In the preparation step, you prepare a directory including the contents
of your new filesystem based on one or more software package source(s)
The creation step is based on the result of the preparation step and
uses the contents of the new image root tree to create the output
image.

{kiwi} supports the creation of the following image types:

- ISO Live Systems
- Virtual Disk for e.g cloud frameworks
- OEM Expandable Disk for system deployment from ISO or the network
- File system images for deployment in a pxe boot environment

Depending on the image type a variety of different disk formats and
architectures are supported.

.. _db_commands_kiwi_opts:

GLOBAL OPTIONS
--------------

--color-output

  Use Escape Sequences to print different types of information
  in colored output. The underlaying terminal has to understand
  those escape characters. Error messages appear red, warning
  messages yellow and debugging information will be printed light
  grey.

--debug

  Print debug information on the commandline.

--logfile=<filename>

  Specify log file. the logfile contains detailed information about
  the process.

--profile=<name>

  Select profile to use. The specified profile must be part of the
  XML description. The option can be specified multiple times to
  allow using a combination of profiles

--shared-cache-dir=<directory>

  Specify an alternative shared cache directory. The directory
  is shared via bind mount between the build host and image
  root system and contains information about package repositories
  and their cache and meta data. The default location is set
  to /var/cache/kiwi

--type=<build_type>

  Select image build type. The specified build type must be configured
  as part of the XML description.

--version

  Show program version

.. _db_commands_kiwi_example:

EXAMPLE
-------

.. code:: bash

   $ git clone https://github.com/OSInside/kiwi-descriptions

   $ kiwi --type vmx system build \
       --description kiwi-descriptions/suse/x86_64/{exc_description} \
       --target-dir /tmp/myimage


.. _db_commands_kiwi_compat:

COMPATIBILITY
-------------

This version of {kiwi} uses a different caller syntax compared to
former versions. However there is a compatibility mode which allows
to use a legacy {kiwi} commandline as follows:

.. code:: bash

   $ kiwi compat \
       --build kiwi-descriptions/suse/x86_64/{exc_description} \
       --type vmx -d /tmp/myimage
