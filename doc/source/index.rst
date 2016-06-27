.. kiwi documentation master file

KIWI Appliance Builder |version|
================================

The Next Generation of the KIWI project.

.. sidebar:: Links

   * `GitHub Project <https://github.com/SUSE/kiwi>`__
   * `Sources <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__

.. toctree::
   :maxdepth: 1

   quickstart
   container_builder
   contributing
   manual/kiwi
   api/kiwi

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

* Distribution independent design
* GPL v2 license
* Complete rewrite from Perl to Python
* Supports Python 2.7 and 3
* openSUSE, SLES, RHEL [CentOS] supported
* Build images for private and public clouds, e.g Amazon EC2
* Build images for data center deployment
* Supports the following image types:

  * ISO Hybrid Live Systems
  * Virtual Disk for e.g cloud frameworks
  * OEM Expandable Disk for system deployment from ISO or the network
  * File system images for deployment in a pxe boot environment
  * Container images for e.g. docker
* Supported architectures: x86/x86_64, s390/s390x, ppc/ppc64, arm/aarch64
* Help on mailinglist and IRC
* and many more

Supported Distributions
-----------------------

"KIWI NG (Next Generation)" can build appliances for distributions
which are equal or newer compared to the following list:

*  SUSE Linux Enterprise 12
*  Red Hat Enterprise 7
*  openSUSE Leap, Tumbleweed
*  Ubuntu Xenial

For anything older please consider to use the legacy KIWI version v7.x.x.

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

Legacy KIWI vs. Next Generation
-------------------------------

There is still the former `KIWI <https://github.com/openSUSE/kiwi>`__
version and we decided to rewrite it.

The reasons to rewrite software from scratch could be very different
and should be explained in order to let users understand why it
makes sense. We are receiving feedback and defect reports from a
variety of groups with different use cases and requirements. It
became more and more difficult to handle those requests in good
quality and without regressions. At some point we asked ourselves:

  `Is KIWI really well prepared for future challenges?`

The conclusion was that the former version has some major weaknesses
which has to be addressed prior to continue with future development.
The following issues are most relevant:

*  Not based on a modern programming language
*  Major design flaws but hardly any unit tests. The risk for
   regressions on refactoring is high
*  No arch specific build integration tests
*  Lots of legacy code for old distributions

In order to address all of these the questions came up:

  `How to modernize the project without producing regressions?`

  `How to change/drop features without making anybody unhappy?`

As there is no good way to achieve this in the former code base the
decision was made to start a rewrite of KIWI with a maintained and
stable version in the background.

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

The legacy KIWI version will be further developed in maintenance mode.
There won't be any new features added in that code base though.
Packages will be available at the known place:
`Legacy KIWI packages <http://download.opensuse.org/repositories/Virtualization:/Appliances>`__

Dropped Features
----------------

The following features have been dropped. If you make use of them
consider to use the legacy KIWI version.

*  Split systems

   The legacy KIWI version supports building of split systems
   which uses a static definition of files and directories marked
   as read-only or read-write. Evolving technologies like overlayfs
   makes this feature obsolete.

*  ZFS filesystem

   The successor for ZFS is Btrfs in the opensource world. All major
   distributions put on Btrfs. This and the proprietary attitude of
   ZFS obsoletes the feature.

*  Reiserfs filesystem

   The number of people using this filesystem is decreasing. For image
   building reiserfs was an interesting filesystem however with Btrfs and
   XFS there are good non inode based alternatives out there. Therefore we
   don't continue supporting Reiserfs.

*  Btrfs seed based live systems

   A Btrfs seed device is an alternative for other copy on write
   filesystems like overlayfs. Unfortunately the stability of the seed
   device when used as cow part in a live system was not as good as we
   provide with overlayfs and clicfs. Therefore this variant is no longer
   supported. We might think of adding this feature back if people demand
   it.

*  VDI image subformat

   The vdi disk image format is supported by the legacy KIWI version but
   we are not aware of any user. The missing business perspective makes
   this feature obsolete.

*  lxc container format

   lxc has a successor in docker based on the former lxc technology.
   Many distributions also dropped the lxc tools from the distribution
   in favour of docker.

Help
----

* Mailing list: https://groups.google.com/forum/#!forum/kiwi-images

  The `kiwi-images` group is an open group and anyone can subscribe, even
  if you do not have a Google account.

  Send mail to `kiwi-images+subscribe@googlegroups.com
  <mailto:kiwi-images+subscribe@googlegroups.com>`__.
* IRC: `#opensuse-kiwi` on irc.freenode.net
