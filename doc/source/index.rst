.. kiwi documentation master file

KIWI Documentation
==================

Welcome to the documentation for KIWI |version|- the command line utility to
build Linux system appliances.

.. sidebar:: Links

   * `GitHub Sources <https://github.com/SUSE/kiwi>`__
   * `GitHub Releases <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
   * `Build Tests(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86>`__
   * `Build Tests(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm>`__
   * `Build Tests(s390) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_s390>`__

.. toctree::
   :maxdepth: 1

   quickstart
   installation
   working_with_kiwi
   overview
   building
   commands
   development

Appliance ?
-----------

An appliance is a ready to use image of an operating system including
a pre-configured application for a specific use case. The appliance is
provided as an image file and needs to be deployed to, or activated in
the target system or service.

KIWI can create appliances in various forms: beside classical installation
ISOs and images for virtual machines it can also build images that boot via
PXE or Vagrant boxes.

In KIWI, the appliance is specified via a collection of human readable files
in a directory, also called the `image description`. At least one XML file
:file:`config.xml` or :file:`.kiwi` is required. In addition there may as
well be other files like scripts or configuration data.


Use Cases
---------

Not convinced yet? You can find a selection of the possible uses cases
below:

* You are a system administrator and wish to create a customized installer
  for your network that includes additional software and your organizations
  certificates? KIWI allows you to select which packages will be included
  in the final image. On top of that you can add files to arbitrary
  locations in the filesystem, for example to include SSL or SSH keys. You
  can also tell KIWI to create an image that can be booted via PXE, so that
  you don't even have to leave your desk to reinstall a system.

* You want to create a custom spin of your favorite Linux distribution with
  additional repositories and packages that are not present by default?
  With KIWI you can configure the repositories of your final image via the
  image description and tweak the list of packages that are going to be
  installed to match your target audience.

* The Raspberry Pi that is coordinating your home's Internet of Thing (IoT)
  devices got very popular among your friends and every single one of them
  wants a copy of that? KIWI will build you ready to deploy images for your
  Raspberry Pi, tweaked to your needs.


Contact
-------

* `Mailing list <https://groups.google.com/forum/#!forum/kiwi-images>`__

  The `kiwi-images` group is an open group and anyone can
  `subscribe <mailto:kiwi-images+subscribe@googlegroups.com>`__,
  even if you do not have a Google account.

* `Matrix <https://matrix.org/blog/home/>`__

  An open network for secure, decentralized communication. Please find the
  `kiwi` room via `Riot <https://riot.im/app/>`__ on the web or by using
  the supported `clients
  <https://matrix.org/docs/projects/clients-matrix>`__.
