Overview
========

.. hint:: **Abstract**

   This document provides a conceptual overview about the steps
   of creating an image with KIWI. It also explains the terminology
   regarding the concept and process when building system images
   with KIWI |version|.

.. toctree::
   :maxdepth: 1

   overview/legacy_kiwi
   overview/workflow

Conceptual Overview
-------------------
A system image (usually called "image"), is a *complete installation* of a Linux
system within a file. The image represents an operation system and,
optionally, contains the "final" configuration.

KIWI creates images in a two step process:

1. The first step, the *prepare operation*, generates a so-called
   *unpacked image tree* (directory) using the information provided in
   the image description.

2. The second step, the *create operation*, creates the *packed image* or
   *image* in the specified format based on the unpacked image and the
   information provided in the configuration file.

The image creation process with KIWI is automated and does not require any
user interaction. The information required for the image creation process is
provided by the image description.


Terminology
-----------

Appliance
   An appliance is a ready to use image of an operating system
   including a preconfigured application for a specific use case.
   The appliance is provided as an image file and needs to be
   deployed to, or activated in the target system or service.

Image
   The result of a KIWI build process.

Image Description
   Specification to define an appliance. The image description is a
   collection of human readable files in a directory. At least one XML
   file :file:`config.xml` or :file:`.kiwi` is required. In addition
   there may be as well other files like scripts or configuration data.
   These can be used to customize certain parts either of the KIWI
   build process or of the initial start-up behavior of the image.

Overlay Files
   A directory structure with files and subdirectories stored as part
   of the Image Description. This directory structure is packaged as
   a file :file:`root.tar.gz` or stored below a directory named
   :file:`root`. The content of the directory structure is copied over
   the existing file system (overlayed) of the appliance root.
   This includes permissions and attributes as a supplement.

KIWI
   An OS appliance builder.

Virtualization Technology
   Software simulated computer hardware. A virtual machine acts like
   a real computer, but is separated from the physical hardware.
   Within this documentation the Qemu virtualization system is used.

System Requirements
-------------------

To use and run KIWI, you need:

* A recent Linux distribution, see :ref:`supported-distributions` for details.
  Alternatively a Linux distribution which supports the docker container
  system as it would be required when running KIWI in a container, see:
  :ref:`container-building`

* Enough free disk space to build and store the image. We recommend a
  minimum of 10GB.

* Python version 2.7, 3.4 or higher; as KIWI supports both Python
  versions, the information in this guide applies also to both
  packages, be it ``python3-kiwi`` or ``python2-kiwi``.

* Git (package ``git-core``) to clone a repository.

* Virtualization technology to start the image. We recommend QEMU
