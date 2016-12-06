.. _legacy_kiwi:

Legacy KIWI vs. Next Generation
===============================

.. hint:: **Abstract**

   Users currently have the choice for the kiwi legacy version
   or this next generation kiwi. This document describes the
   maintenance state of the legacy kiwi version and under which
   circumstances the use of the legacy kiwi version is required.

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

When Do I need to use the legacy kiwi
-------------------------------------

* If you are building images using one of the features of the dropped
  features list below.

* If you are building images for an older distribution compared to
  the list on the main page, see :ref:`supported-distributions`.

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

*  lxc container format

   lxc has a successor in docker based on the former lxc technology.
   Many distributions also dropped the lxc tools from the distribution
   in favour of docker.
