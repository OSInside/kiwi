.. kiwi documentation master file

KIWI Appliance Builder |version|
================================

The Next Generation of the KIWI project.

.. sidebar:: Links

   * `GitHub Project <https://github.com/SUSE/kiwi>`__
   * `Sources <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
   * `Build Tests <https://ci.opensuse.org/view/kiwi/>`__

.. toctree::
   :maxdepth: 1

   quickstart
   container_builder
   legacy_kiwi
   contributing
   manual/kiwi
   api/kiwi
   schema
   workflow
   extensions

What is KIWI?
-------------

KIWI is an OS appliance builder.

An appliance is a ready to use image of an operating system including
a preconfigured application for a specific use case. The appliance is
provided as an image file and needs to be deployed to, or activated in
the target system or service.

The appliance is specified by a collection of human readable files in a
directory, also called as the `image description`. At least one XML
file :file:`config.xml` or :file:`.kiwi` is required. In addition
there may be as well other files like scripts or configuration data.

Motivation
----------

The idea of KIWI is simple: Provide a human readable image
description and build the system for any kind of target or service.

Since the early days the project was well received and within SUSE all
product appliances, product media, appliances for private and public
cloud as well as on top projects like SUSE Studio uses KIWI. New
opportunities with partners, other distribution vendors and technologies
are ahead.

We are looking forward to address the challenges in the private
and public cloud space as well as the deployment for SoC (System on Chip)
platforms like we see them today for the Arm and PowerPC landscape.

Feature Highlights
------------------

* GPL v2 license
* Distribution independent design
* Module extension for python projects
* Supports Python 2.7 and 3
* Build images for private and public clouds, e.g OpenStack,
  Amazon EC2, Google Compute Engine, Microsoft Azure
* Build images for data center deployment
* Supported architectures: x86/x86_64, s390/s390x, ppc/ppc64, arm/aarch64
* Help on mailinglist and IRC
* and many more

Supported Image Types
---------------------

* ISO Hybrid Live Systems
* Virtual Disk for e.g cloud frameworks
* OEM Expandable Disk for system deployment from ISO or the network
* File system images for deployment in a pxe boot environment
* Container images for e.g. docker

.. _supported-distributions:

Supported Distributions
-----------------------

"KIWI NG (Next Generation)" can build appliances for distributions
which are equal or newer compared to the following list:

*  SUSE Linux Enterprise 12
*  Red Hat Enterprise 7
*  Fedora 25+
*  CentOS 7
*  openSUSE Leap, Tumbleweed
*  Ubuntu Xenial

For anything older please consider to use the legacy KIWI version *v7.x*
For more details on the legacy kiwi, see: :ref:`legacy_kiwi`.

Example Descriptions
--------------------

A collection of example image descriptions can be found on the GitHub
repository here: https://github.com/SUSE/kiwi-descriptions.

Most of the descriptions provide a so called "JeOS image" ("Just enough
Operating System"). A JeOS is a small, text only based image including a
predefined remote source setup to allow installation of missing
software components at a later point in time.

Concept
-------

KIWI operates in two steps. The system build command combines
both steps into one to make it easier to start with KIWI.

The first step is the *preparation step* and if that step was successful, a
*creation step* follows which is able to create different image output
types:

1. In the *preparation step*, you prepare a directory including the
   contents of your new filesystem based on one or more software
   package source(s).

2. The *creation step* is based on the result of the preparation step and
   uses the contents of the new image root tree to create the output image.

Help
----

* Mailing list: https://groups.google.com/forum/#!forum/kiwi-images

  The `kiwi-images` group is an open group and anyone can subscribe, even
  if you do not have a Google account.

  Send mail to `kiwi-images+subscribe@googlegroups.com
  <mailto:kiwi-images+subscribe@googlegroups.com>`__.
* IRC: `#opensuse-kiwi` on irc.freenode.net
