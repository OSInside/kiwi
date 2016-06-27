Manual Pages
============

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

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

--compat

  Support legacy kiwi commandline, see COMPATIBILITY section for details

--debug

  Print debug information on the commandline

--version

  Show program version

EXAMPLE
-------

.. code-block:: bash

   $ git clone https://github.com/SUSE/kiwi-descriptions

   $ kiwi --type vmx system build \
       --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --target-dir /tmp/myimage

SERVICES and COMMANDS
---------------------

.. toctree::

   result_list
   result_bundle
   system_prepare
   system_create
   system_update
   system_build

COMPATIBILITY
-------------

This version of KIWI uses a different caller syntax compared to
former versions. However there is a compatibility mode which allows
to use a legacy KIWI commandline as follows:

.. code-block:: bash

   $ kiwi --compat -- \
       --build kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --type vmx -d /tmp/myimage
