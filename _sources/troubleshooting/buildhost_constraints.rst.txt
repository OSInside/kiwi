.. _supported-distributions:

Build Host Constraints
======================

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

Package Manager Behavior
------------------------

One of the key requirements for {kiwi} is that the target distribution
consists out of a collection of software packages provided through
software repositories. As of today this applies to every Linux
distribution in some shape or form. For the installation of this
software packages there are tools available called `package manager`
and {kiwi} implements an API for a variety of package managers to
support the different Linux distributions.

In {kiwi} the package manager tools are called in a way that allows
for a non interactive installation of the packages specified in the
image description. However, {kiwi} does intentionally not configure
other features of the package manager to keep their distribution
default behavior as much as possible. There are many options that
can be set for a package manager to behave differently. This
part of the troubleshooting exists to inform about the most common
surprises or unexpected behavior of certain package managers and
solutions how to address them.

.. note::

   All of the following information applies to package manager
   calls performed inside of the image root tree. Meaning `after`
   the image bootstrap phase. During the image bootstrap phase
   all package manager calls happens on the build host and their
   behavior can only be influenced by changing the setup of the
   build host. An isolated build environment is required to
   address issues in this area. See :ref:`self_contained` for
   details.

zypper: modalias matching
~~~~~~~~~~~~~~~~~~~~~~~~~
A module alias is an identifier that exists if the respective
hardware was found by the kernel on this system. The package
manager can use this information to match package(s) that holds
a reference to the alias name and installs it automatically.
For example: Automatically install a driver package if the
respective hardware is present. In zypper this behavior is by
default enabled. When building an image this feature can be
unwanted and lead to interesting side effects. As it's required
to build the image on some host, there is also some hardware
available during build. This must not necessarily be the same
or compatible hardware the image is expected to run on later.
For example: The buildhost has a nvidia graphics card. An
image build process would install the nvidia driver package due
to the modalias match. The image is expected to run on a system
without a nvidia card. The build process would install unneeded
software. To switch off modalias matching in zypper follow
these steps:

1. Add a `post_bootstrap.sh` hook script to your image description
   with the following code:

   .. code:: bash
      
      echo 'ZYPP_MODALIAS_SYSFS=""' > .kiwi.package_manager.env

2. Optionally add a `config.sh` hook script to your image description
   with the following code:

   .. code:: bash

      rm .kiwi.package_manager.env

   This will delete the custom environment file such that it does
   not appear in the final image

3. Rebuild your image. The `.kiwi.package_manager.env` environment
   file is used by kiwi and added to the execution environment
   of the package manager. The `ZYPP_MODALIAS_SYSFS` variable
   can be used to switch off the modalias matching. For more
   details on zypper setting please refer to: https://doc.opensuse.org/projects/libzypp/HEAD/zypp-envars.html
