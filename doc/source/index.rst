.. kiwi documentation master file

{kiwi} Documentation
=====================

.. note::
   This documentation covers {kiwi-product} |version|- the command line
   utility to build Linux system appliances. {kiwi} is stable and all
   new features, bugfixes, and improvements will be developed here.
   Versions older or equal to v7.x.x are out of maintenance and do
   not get any updates or bugfixes. If you still need this version,
   refer to the documentation for
   `{kiwi-legacy} <https://doc.opensuse.org/projects/kiwi/doc>`__

.. toctree::
   :maxdepth: 1

   overview
   installation
   quickstart
   commands
   troubleshooting
   plugins
   concept_and_workflow
   image_description
   image_types_and_results
   building_images
   working_with_images
   contributing
   api

.. sidebar:: Links

   * `GitHub Sources <https://github.com/OSInside/kiwi>`__
   * `GitHub Releases <https://github.com/OSInside/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
   * `Build Tests TumbleWeed(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed>`__
   * `Build Tests TumbleWeed(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm:tumbleweed>`__
   * `Build Tests TumbleWeed(s390) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_s390:tumbleweed>`__
   * `Build Tests TumbleWeed(ppc64le) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_ppc:tumbleweed>`__

   * `Build Tests RawHide(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:rawhide>`__

   * `Build Tests Leap(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:leap>`__

   * `Build Tests Fedora(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:fedora>`__
   * `Build Tests Fedora(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm:fedora>`__
   * `Build Tests Fedora(ppc64le) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_ppc:fedora>`__

   * `Build Tests CentOS(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:centos>`__

   * `Build Tests Ubuntu(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:ubuntu>`__

   * `Build Tests Debian(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:debian>`__

   * `Build Tests ArchLinux(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:archlinux>`__

The Appliance Concept
---------------------

An appliance is a ready to use image of an operating system including
a pre-configured application for a specific use case. The appliance is
provided as an image file and needs to be deployed to, or activated in
the target system or service.

{kiwi} can create appliances in various forms: beside classical installation
ISOs and images for virtual machines it can also build images that boot via
PXE or Vagrant boxes.

In {kiwi}, the appliance is specified via a collection of human readable files
in a directory, also called the `image description`. At least one XML file
:file:`config.xml` or :file:`.kiwi` is required. In addition there may as
well be other files like scripts or configuration data.

Use Cases
---------

The following list shows a selection of use cases for which an
appliance is needed:

Private and Public Clouds
  Cloud environments are managed through an API provided by the cloud
  service provider. The classic way to install a machine is not
  possible in such an environment because there is no physical access
  to the machine. An appliance is needed to be registered with the
  cloud

Custom Linux Distribution
  Linux distributors provides their distribution based on a collection
  of packages and release them on an install media like a DVD or an USB
  stick. Typically a lot more software components exists for the
  distribution which are not part of the default installation media
  or the installation media comes with software and installation
  routines that are not matching your target audience. With an
  appliance made by {kiwi} you can create provide an installation
  media that matches custom criteria as needed by the customer
  and does not require extra post processing steps after the
  default installation method provided by the distributor.

Live Systems
  The ability to have a Linux OS that runs from a small storage
  device like a USB stick or a SD card is the swiss army knife of many
  system administrators. The creation of such a live system includes
  use of technologies that are not part of a standard installation
  process. An appliance builder is needed to create this sort of
  system

Embedded Systems
  Embedded Systems like the Raspberry Pi comes with limited hardware
  components. Their boot sequences often does not allow for classic
  installation methods through USB or DVD devices. Instead they boot
  through SD card slots or via the network. SoC (System on Chip) devices
  also tend to implement non standard boot methods which can only
  be implemented through custom OS appliances.

And More
  ...

Contact
-------

* `Mailing list <https://groups.google.com/forum/#!forum/kiwi-images>`__

  The `kiwi-images` group is an open group and anyone can
  `subscribe <mailto:kiwi-images+subscribe@googlegroups.com>`__,
  even if you do not have a Google account.

* `Matrix <https://matrix.org>`__

  An open network for secure, decentralized communication. Please find the
  ``#kiwi:matrix.org`` room via
  `Matrix <https://matrix.to/#kiwi:matrix.org>`__ on the web
  or by using the supported
  `clients <https://matrix.org/docs/projects/clients-matrix>`__.
