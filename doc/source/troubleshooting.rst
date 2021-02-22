Troubleshooting
===============

.. note:: **Abstract**

   This document describes situations which leads to issues
   during build or boot time of the image build with {kiwi}.
   The suggested solutions are considered best practice but
   are just one out of other possible solution candidates.

.. toctree::
   :maxdepth: 1

   troubleshooting/filesystems

.. _supported-distributions:

Build Host Constraints
----------------------

For building images a host system is required that runs the build process.
Tools to create the image are used from that host and this creates an
indirect dependency to the target image. For example; Building an
Ubuntu image requires the apt and dpkg tools and metadata to be available
and functional on the host to build an Ubuntu image. There are many more
of those host vs. image dependencies and not all of them can be resolved
in a clear and clean way.

The most compatible environment is provided if the build host is of the same
distribution than the target image. In other cases our recommendation is that
the build host is of the same distribution than the target and near to the
major version (+-1) compared to the target. Such an environment can be
found in:
 
* The Open Build Service `OBS <https://build.opensuse.org>`__.
* The {kiwi} boxed plugin: :ref:`self_contained`
  
In general, our goal is to support any major distribution with {kiwi}. However
for building images we rely on core tools which are not under our control.
Also several design aspects of distributions like **secure boot** and working
with **upstream projects** are different and not influenced by us. There
are many side effects that can be annoying especially if the build host
is not of the same distribution vendor than the image target.

Architectures
-------------

As described in the section above one requirement between the build host
and the image when it comes to architecture support is, that the image
architecture should match the build host architecture. Cross arch building
would require any core tool that is used to build an image to be cross
arch capable. To patch e.g an x86_64 system such that it can build an
aarch64 image would require some work on binutils and hacks as well as
performance tweaks which is all not worth the effort and still can lead
to broken results. Thus we recommend to provide native systems for the
target architecture and build there. One possible alternative is to
use the kiwi boxed plugin as mentioned above together with a box
created for the desired architecture. However keep in mind the
performance problematic when running a VM of a different
architecture.

The majority of the image builds are based on the x86 architecture.
As mentioned {kiwi} also supports other architectures, shown in the
table below:

.. table::
   :align: left

   +--------------+---------------------+
   | Architecture | Supported           |
   +==============+=====================+
   | x86_64       | yes                 |
   +--------------+---------------------+
   | ix86         | yes **note:distro** |
   +--------------+---------------------+
   | s390/s390x   | yes **note:distro** |
   +--------------+---------------------+
   | arm/aarch64  | yes **note:distro** |
   +--------------+---------------------+
   | ppc64        | yes **note:distro** |
   +--------------+---------------------+

.. admonition:: distro

   The support status for an architecture depends on the distribution.
   If the distribution does not build its packages for the desired
   architecture, {kiwi} will not be able to build an image for it
