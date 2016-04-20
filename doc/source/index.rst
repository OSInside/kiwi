.. kiwi documentation master file


KIWI Appliance Builder
======================

.. sidebar:: Links

   * `GitHub Project <https://github.com/SUSE/kiwi>`__
   * `Sources <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <https://build.opensuse.org/package/show/Virtualization:Appliances:Builder/python3-kiwi>`__

.. toctree::
   :maxdepth: 1

   quickstart
   manual/kiwi
   api/kiwi


What is KIWI?
-------------

KIWI is an OS image and an appliance builder.

It is based on an image XML description. Such a description is represented by
a directory which includes at least one :file:`config.xml` or :file:`.kiwi`
file and may as well include other files like scripts or configuration data.


Motivation
----------

The idea of KIWI is simple: Provide a human readable appliance
description and build the system for any kind of target or service.

Since the early days the project was well received and within SUSE all
product appliances, product media, appliances for private and public
cloud as well as on top projects like SUSE Studio uses KIWI. New
opportunities with partners, other distribution vendors and technologies
are ahead. However, is KIWI really well prepared for future challenges?

The former `KIWI <https://github.com/openSUSE/kiwi>`__
version has some major weaknesses which has to be fixed prior to
continue with future development. The following issues are most
relevant:

*  Not based on a modern programming language
*  Major design flaws but hardly any unit tests. The risk for
   regressions on refactoring is high
*  No arch specific build integration tests
*  Lots of legacy code for old distributions

In order to address all of these the question came up:

  "How to modernize the project without producing regressions or making our users unhappy ?"

As there is no good way to achieve this in the former code base the
decision was made to start a rewrite of KIWI with a maintained and stable version
in the background.

After some coffee, lots of hacking hours and peanuts later, I'm happy to
introduce this next generation KIWI project to you.

Users will be able to use both versions in parallel. In addition, the
next generation KIWI will be fully compatible with the current format of
the appliance description. This means, users can build an appliance from
the same appliance description with the legacy and the next generation
KIWI, if the distribution and all configured features are supported by
the used KIWI version.

This provides an opportunity for users to test the next generation KIWI
with their appliance descriptions without risk. If it builds and works
as expected, I recommend to switch to the next generation KIWI. If not,
please open an issue on https://github.com/SUSE/kiwi.

Feature Highlights
------------------

* Distribution independent design
* GPL v2 license
* Complete rewrite from Perl to Python
* openSUSE, SLES, RHEL [CentOS] supported
* Build images for virtualization systems, cloud, ISOs and more
* Supports the following image types:

  * ISO Hybrid Live Systems
  * Virtual Disk for e.g cloud frameworks
  * OEM Expandable Disk for system deployment from ISO or the network
  * File system images for deployment in a pxe boot environment
* Supported architectures: x86, x86_64, s390, ppc
* Help on mailinglist and IRC
* and many more

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
   contents of your new filesystem based on one or more software package source(s).

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
