kiwi
====

SYNOPSIS
--------

.. code-block:: bash

   kiwi [global options] service <command> [<args>]

   kiwi -h | --help
   kiwi [--profile=<name>...]
        [--type=<build_type>]
        [--logfile=<filename>]
        [--debug]
        [--color-output]
       image <command> [<args>...]
   kiwi [--debug]
        [--color-output]
       result <command> [<args>...]
   kiwi [--profile=<name>...]
        [--shared-cache-dir=<directory>]
        [--type=<build_type>]
        [--logfile=<filename>]
        [--debug]
        [--color-output]
       system <command> [<args>...]
   kiwi compat <legacy_args>...
   kiwi -v | --version
   kiwi help

DESCRIPTION
-----------

KIWI is an imaging solution that is based on an image XML description.
Such a description is represented by a directory which includes at least
one :file:`config.xml` or :file:`.kiwi` file and may as well include other files like
scripts or configuration data.

A collection of example image descriptions can be found on the github
repository here: https://github.com/SUSE/kiwi-descriptions. Most of the
descriptions provide a so called JeOS image. JeOS means Just enough
Operating System. A JeOS is a small, text only based image including a
predefined remote source setup to allow installation of missing
software components at a later point in time.

KIWI operates in two steps. The system build command combines
both steps into one to make it easier to start with KIWI. The first
step is the preparation step and if that step was successful, a
creation step follows which is able to create different image output
types.

In the preparation step, you prepare a directory including the contents
of your new filesystem based on one or more software package source(s)
The creation step is based on the result of the preparation step and
uses the contents of the new image root tree to create the output
image.

KIWI supports the creation of the following image types:

- ISO Live Systems
- Virtual Disk for e.g cloud frameworks
- OEM Expandable Disk for system deployment from ISO or the network
- File system images for deployment in a pxe boot environment

Depending on the image type a variety of different disk formats and
architectures are supported.

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

EXAMPLE
-------

.. code-block:: bash

   $ git clone https://github.com/SUSE/kiwi-descriptions

   $ kiwi --type vmx system build \
       --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --target-dir /tmp/myimage

RUNTIME CONFIG FILE
-------------------

To control custom paramters of the tool chain used by KIWI a user
specific configuration file can be provided as:

:file:`~/.config/kiwi/config.yml`

The contents of the file is in YAML format and supports the following
setup parameters:

.. code-block:: yaml

   xz:
     - options: -a -b -c

       # Specifies XZ-compression-options
       # For details see man xz

   obs:
     - download_url: url

       # Specifies download server url of an open buildservice instance
       # defaults to: http://download.opensuse.org/repositories

     - public: true|false

       # Specifies if the buildservice instance is public or private
       # defaults to: true

COMPATIBILITY
-------------

This version of KIWI uses a different caller syntax compared to
former versions. However there is a compatibility mode which allows
to use a legacy KIWI commandline as follows:

.. code-block:: bash

   $ kiwi compat \
       --build kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --type vmx -d /tmp/myimage
