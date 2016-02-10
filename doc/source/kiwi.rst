kiwi
====

SYNOPSIS
--------

*kiwi* [global-options] *system* <command> [<args>...]

*kiwi* *result* <command> [<args>...]

*kiwi* --compat <legacy_args>...

*kiwi* -v | --version

DESCRIPTION
-----------

KIWI is an imaging solution that is based on an image XML description.
Such a description is represented by a directory which includes at least
one config.xml or .kiwi file and may as well include other files like
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
- Filesystem images for deployment in a pxe boot environment

Depending on the image type a variety of different disk formats and
architectures are supported.

EXAMPLE
-------

.. code-block:: bash

   $ git clone https://github.com/SUSE/kiwi-descriptions

   $ kiwi --type vmx system build \
       --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --target-dir /tmp/myimage

COMMANDS
--------

- *result* list

    List build results. See *kiwi::result::list* manual page for further
    details

- *system* prepare

    Prepare image root system below a given directory.
    See *kiwi::system::prepare* manual page for further details

- *system* create

    Create image from a previous prepare or build command. See
    *kiwi::system::build* manual page for further details

- *system* build

    Build image in one step. This command combines the prepare and create
    steps to build one image target. See *kiwi::system::build* manual page
    for further details

- *system* update

    Update image root system with latest updates according to the
    configured repositories. The update command also allows to remove
    or install new packages. See *kiwi::system::update* manual page for
    further details

GLOBAL OPTIONS
--------------

--profile=<name>

  Select profile to use. The specified profile must be part of the
  XML description. The option can be specified multiple times to
  allow using a combination of profiles

--type=<build_type>

  Select image build type. The specified build type must be configured
  as part of the XML description.

--logfile=<filename>

  Specify log file. the logfile contains detailed information about
  the process.

--debug

  Print debug information on the commandline

COMPATIBILITY
-------------

This version of kiwi uses a different caller syntax compared to
former versions. However there is a compatibility mode which allows
to use a legacy kiwi commandline as follows:

.. code-block:: bash

   $ kiwi --compat -- \
       --build kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --type vmx -d /tmp/myimage
