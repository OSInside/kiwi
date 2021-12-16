Architectures
-------------

With regards to the information in :ref:`supported-distributions`
one requirement between the build host and the image when it comes to
architecture support is, that the image architecture should match the
build host architecture. Cross arch building would require any core
tool that is used to build an image to be cross arch capable.

To patch e.g an x86_64 system such that it can build an
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
