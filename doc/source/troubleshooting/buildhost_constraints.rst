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
