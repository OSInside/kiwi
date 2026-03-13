kiwi-ng
=======

.. _db_commands_kiwi_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng -h | --help
   kiwi-ng [--profile=<name>...]
           [--setenv=<variable=value>...]
           [--temp-dir=<directory>]
           [--type=<build_type>]
           [--logfile=<filename>]
           [--logsocket=<socketfile>]
           [--loglevel=<number>]
           [--debug]
           [--debug-run-scripts-in-screen]
           [--color-output]
           [--config=<configfile>]
           [--kiwi-file=<kiwifile>]
       image <command> [<args>...]
   kiwi-ng [--logfile=<filename>]
           [--logsocket=<socketfile>]
           [--loglevel=<number>]
           [--debug]
           [--debug-run-scripts-in-screen]
           [--color-output]
           [--config=<configfile>]
       result <command> [<args>...]
   kiwi-ng [--profile=<name>...]
           [--setenv=<variable=value>...]
           [--shared-cache-dir=<directory>]
           [--temp-dir=<directory>]
           [--target-arch=<name>]
           [--type=<build_type>]
           [--logfile=<filename>]
           [--logsocket=<socketfile>]
           [--loglevel=<number>]
           [--debug]
           [--debug-run-scripts-in-screen]
           [--color-output]
           [--config=<configfile>]
           [--kiwi-file=<kiwifile>]
       system <command> [<args>...]
   kiwi-ng -v | --version
   kiwi-ng help

.. _db_commands_kiwi_desc:

DESCRIPTION
-----------

{kiwi} is an imaging solution that is based on an image XML description. A
description can consist of a single :file:`config.xml` or :file:`.kiwi` file. It
may also include additional files, such as scripts or configuration data.

A collection of example image descriptions can be found in the following GitHub
repository: https://github.com/OSInside/kiwi-descriptions. Most of the
descriptions provide a so-called appliance image. An appliance is a
small, text-based image, including a predefined remote source setup to allow the
installation of missing software components.

Although {kiwi} operates in two steps, the system build command combines both
steps into one to make it easier to start with {kiwi}.

The first step is to prepare a directory that includes the contents of a new
filesystem based on one or more software package sources. The second step uses
the prepared contents of the new image root tree to create an output image.

{kiwi} supports the creation of the following image types:

- ISO Live Systems
- virtual disk for, e.g., cloud frameworks
- OEM expandable disk for system deployment from ISO or the network
- filesystem images for deployment in a PXE boot environment

Depending on the image type, different disk formats and
architectures are supported.

.. _db_commands_kiwi_opts:

GLOBAL OPTIONS
--------------

--color-output

  Uses escape sequences to print different types of information in colored
  output. for this option to work, the underlying terminal must support those
  escape characters. Error messages appear in red, warning messages in yellow,
  and debugging information is printed in light grey.

--config=<configfile>

  Use the specified runtime configuration file. If not specified, the
  runtime configuration is expected to be in the :file:`~/.config/kiwi/config.yml`
  or :file:`/etc/kiwi.yml` files.

--debug

  Prints debug information on the command line. Same as: `--loglevel 10`.

--debug-run-scripts-in-screen

  Runs scripts called by {kiwi} in a screen session.

--logfile=<filename>

  Specifies the log file. The logfile contains detailed information about
  the process. The special call `--logfile stdout` sends all
  information to standard out instead of writing to a file.

--logsocket=<socketfile>

  Sends log data to the specified Unix Domain socket in the same
  format as with `--logfile`.

--loglevel=<number>

  Specifies the logging level as a number. Further info about the
  available log levels can be found at:
  https://docs.python.org/3/library/logging.html#logging-levels.
  Setting a log level displays all messages above the specified level.

  .. code:: bash

     ----------------------------
     | Level    | Numeric value |
     ----------------------------
     | CRITICAL | 50            |
     | ERROR    | 40            |
     | WARNING  | 30            |
     | INFO     | 20            |
     | DEBUG    | 10            |
     | NOTSET   | 0             |
     ----------------------------

--profile=<name>

  Selects a profile to use. The specified profile must be part of the
  XML description. The option can be specified multiple times to
  allow a combination of profiles.

--setenv=<variable=value>

  exports an environment variable and its value into the caller's
  environment. This option can be specified multiple times.

--shared-cache-dir=<directory>

  Specifies an alternative shared cache directory. The directory
  is shared via bind mount between the build host and image
  root system, and it contains information about package repositories
  and their cache and metadata. The default location is `/var/cache/kiwi`.

--temp-dir=<directory>

  Specifies an alternative base temporary directory. The
  provided path is used as a base directory to store temporary
  files and directories. The default is `/var/tmp`.

--target-arch=<name>

  Specifies an image architecture. By default, the host architecture is used as
  the image architecture. If the specified architecture name does not match the
  host architecture (thus requesting a cross-architecture image build), you must
  configure the support for the image architecture and binary format on the
  building host. This must be done during the preparation stage, and it is
  beyond the scope of {kiwi}.

--type=<build_type>

  Selects an image build type. The specified build type must be configured
  as part of the XML description.

--kiwi-file=<kiwifile>

  The basename of the kiwi file that contains the main image
  configuration elements. If not specified, kiwi uses
  a file named `config.xml` or a file matching `*.kiwi`.

--version

  Show the program version.

.. _db_commands_kiwi_example:

EXAMPLE
-------

.. code:: bash

   $ git clone https://github.com/OSInside/kiwi

   $ sudo kiwi-ng system build \
       --description kiwi/build-tests/{exc_description_disk} \
       --set-repo {exc_repo_leap} \
       --target-dir /tmp/myimage
