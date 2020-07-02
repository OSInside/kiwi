.. _legacy_kiwi:

Legacy KIWI vs. {kiwi-product}
==============================================

.. note:: **Abstract**

   Users currently have the choice for the kiwi legacy version
   or this next generation kiwi. This document describes the
   maintenance state of the legacy kiwi version and under which
   circumstances the use of the legacy kiwi version is required.

There is still the former
`{kiwi-legacy} <https://github.com/OSInside/kiwi-legacy>`__
version and we decided to rewrite it.

The reasons to rewrite software from scratch could be very different
and should be explained in order to let users understand why it
makes sense. We are receiving feedback and defect reports from a
variety of groups with different use cases and requirements. It
became more and more difficult to handle those requests in good
quality and without regressions. At some point we asked ourselves:

  `Is {kiwi-legacy} really well prepared for future challenges?`

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
decision was made to start a rewrite of {kiwi-legacy} with a maintained and
stable version in the background.

Users will be able to use both versions in parallel. In addition,
{kiwi} will be fully compatible with the current format of
the appliance description. This means, users can build an appliance from
the same appliance description with {kiwi-legacy} and
{kiwi}, if the distribution and all configured features are
supported by the used version.

This provides an opportunity for users to test {kiwi}
with their appliance descriptions without risk. If it builds and works
as expected, I recommend to switch to the {kiwi}. If not,
please open an issue on https://github.com/OSInside/kiwi.

The {kiwi-legacy} version will be further developed in maintenance mode.
There won't be any new features added in that code base though.
Packages will be available at the known place:
`{kiwi-legacy} packages <http://download.opensuse.org/repositories/Virtualization:/Appliances>`__

When Do I need to use {kiwi-legacy}
-----------------------------------

* If you are building images using one of the features of the dropped
  features list below.

* If you are building images for an older distribution compared to
  the list on the main page, see :ref:`supported-distributions`.

Dropped Features
----------------

The following features have been dropped. If you make use of them
consider to use the {kiwi-legacy} version.

Split systems
  The {kiwi-legacy} version supports building of split systems
  which uses a static definition of files and directories marked
  as read-only or read-write. Evolving technologies like overlayfs
  makes this feature obsolete.

ZFS filesystem
  The successor for ZFS is Btrfs in the opensource world. All major
  distributions put on Btrfs. This and the proprietary attitude of
  ZFS obsoletes the feature.

Reiserfs filesystem
  The number of people using this filesystem is decreasing. For image
  building reiserfs was an interesting filesystem however with Btrfs and
  XFS there are good non inode based alternatives out there. Therefore we
  don't continue supporting Reiserfs.

Btrfs seed based live systems
  A Btrfs seed device is an alternative for other copy on write
  filesystems like overlayfs. Unfortunately the stability of the seed
  device when used as cow part in a live system was not as good as we
  provide with overlayfs and clicfs. Therefore this variant is no longer
  supported. We might think of adding this feature back if people demand
  it.

lxc container format
  lxc has a successor in docker based on the former lxc technology.
  Many distributions also dropped the lxc tools from the distribution
  in favour of docker.

OEM Recovery/Restore
  Recovery/Restore in the world of images has been moved from the
  operating system layer into higher layers. For example, in private and
  public Cloud environments disk and image recovery as well as backup
  strategies are part of Cloud services. Pure operating system recovery
  and snapshots for consumer machines are provided as features of the
  distribution. SUSE as an example provides this via Rear
  (Relax-and-Recover) and snapshot based filesystems (btrfs+snapper).
  Therefore the recovery feature offered in the {kiwi-legacy} version
  will not be continued.

Partition based install method in OEM install image
  The section :ref:`deployment_methods` describes the supported OEM
  installation procedures. The {kiwi-legacy} version also provided a method
  to install an image based on the partitions of the OEM disk image.
  Instead of selecting one target disk to dump the entire image file to,
  the user selects target partitions. Target partitions could be located
  on several disks. Each partition of the OEM disk image must be mapped
  on a selectable target partition. It turned out, users needed a lot of
  experience in a very sensitive area of the operating system. This is
  contrary to the idea of images to be dumped and be happy. Thus the
  partition based install method will not be continued.

Compatibility
-------------

The {kiwi-legacy} version can be installed and used together with
{kiwi}.

.. note:: Automatic Link Creation for :command:`kiwi` Command

   Note the python3-kiwi package uses the alternatives mechanism to
   setup a symbolic link named :command:`kiwi` to the real executable
   named :command:`kiwi-ng`. If the link target :file:`/usr/bin/kiwi`
   already exists on your system, the alternative setup will skip the
   creation of the link target because it already exists.

From an appliance description perspective, both versions are fully
compatible. Users can build their appliances with both versions and the
same appliance description. If the appliance description uses features
{kiwi} does not provide, the build will fail with an
exception early. If the appliance description uses next generation
features like the selection of the initrd system, it's not possible to
build that with the {kiwi-legacy}, unless the appliance description
properly encapsulates the differences into a profile.

{kiwi} also provides the `--compat` option and
the :command:`kiwicompat` tool to be able to use the same commandline
as provided with the {kiwi-legacy} version.
