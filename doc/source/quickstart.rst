Quick Start: Building an Image with KIWI |version|
==================================================

.. hint:: **Abstract**

   This document describes how to start with KIWI, an OS appliance builder,
   to build system images.
   This Quick Start Guide covers:

   * what KIWI and an appliance is
   * how to use KIWI to build a syste, image from a predefinied image description
   * how you can start and use the created image


Usage Scenario
--------------
The procedures in this guide describe the process of creating a minimal
image with KIWI and how to start it with a virtualization technology.

For this, you will use an existing image description
The resulting image contains the following characteristics:

* openSUSE Leap
* FIXME B
* FIXME C


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
~~~~~~~~~~~

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

KIWI
   An OS appliance builder.

Virtualization Technology
   Software simulated computer hardware. A virtual machine acts like
   a real computer, but is separated from the physical hardware.


System Requirements
-------------------
To use and run KIWI, you need:

* A supported Linux distribution. Currently, KIWI can build appliances for
  distributions which are equal or newer compared to the following list:

  * CentOS 7
  * Fedora 25+
  * openSUSE Leap, Tumbleweed
  * Red Hat Enterprise 7
  * SUSE Linux Enterprise 12
  * Ubuntu Xenial

* Enough free disk space to build and store the image. We recommend a minimum of FIXME GB.
* Python version 2.7, 3.4 or higher; as KIWI supports both Python
  versions, the information in this guide applies also to both
  packages, be it ``python3-kiwi`` or ``python2-kiwi``.
* Git (package ``git-core``) to clone a repository.
* Virtualization technology to start the image.


Installing KIWI
---------------
KIWI can be installed with different methods. For this guide, only the
installation as a packages through a package manager is described.

Packages for the new KIWI version are provided at the `openSUSE
buildservice <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__.

.. todo:: Two questions:
    a) Is the following procedure a bit "too much"?
    b) Should we mention/describe/... other distributions too?

To install KIWI, do:

1. Open the URL http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder
   in your browser.

2. Click the link of your preferred operating system.

3. Right-click on the file :file:`Virtualization:Appliances:Builder.repo` and copy the URL.
   In Firefox it is the menu :menuselection:`Copy link address`.

4. Insert the copied URL from the last step in your shell. The ``DIST`` placeholder
   contains the respective distribution. Use :command:`zypper ar` to add it to your
   list of repositories:

   .. code-block:: shell-session

      $ sudo zypper ar -f http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>/Virtualization:Appliances:Builder.repo

5. Install KIWI:

   .. code-block:: shell-session

      $ sudo zypper in python3-kiwi


.. note:: **Compatibility with Legacy KIWI**

   A legacy KIWI version can be installed and used together with
   KIWI version 9 and higher ("next generation").

   The ``python3-kiwi`` package uses the alternatives mechanism to
   setup a symbolic link named :command:`kiwi` to the real executable
   named :command:`kiwi-ng`. If the link target :file:`/usr/bin/kiwi`
   already exists on your system, the alternative setup will skip the
   creation of the link target because it already exists.


Building an Image
-----------------
As you want to create a image for openSUSE Leap, the following procedure describes
how to do it:

1. Open a shell and clone some KIWI example descriptions:

   .. code-block:: shell-session

      $ git clone https://github.com/SUSE/kiwi-descriptions

2. Build the openSUSE Leap image with :command:`kiwi-ng`:

   .. code-block:: shell-session

      $ sudo kiwi-ng --type vmx system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

After the command is successfully executed, find the image with the
suffix :file:`.raw` below :file:`/tmp/myimage`.


Starting the Image
------------------
The disk image built in the last step can be used with any virtualization
technology you may use already.

.. todo:: this procedure doesn't work correct. Any tips/recommendations how to
   "start" the image? What should we recommend: VirtualBox, KVM, QEMU, VMware, ...
   There are so many...


1. Install the CPU emulator QEMU:

   .. code-block:: shell-session

      $ sudo zypper in qemu-x86

2. Start the image through QEMU:

   .. code-block:: shell-session

      $ su -
      # qemu-sysstem-x86_64 -drive format=raw,file=/tmp/myimage/*.raw

