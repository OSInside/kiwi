.. _self_contained:

Building in a Self-Contained Environment
========================================

.. note:: **Abstract**

   Users building images with {kiwi} face problems if they want
   to build an image matching one of the following criteria:

   * build should happen as non root user.

   * build should happen on a host system distribution for which
     no {kiwi} packages exists.

   * build happens on an incompatible host system distribution
     compared to the target image distribution. For example
     building an apt/dpkg  based system on an rpm based system.

   * run more than one build process at the same time on the
     same host.

   * run a build process for a different target architecture
     compared to the host architecture (Cross Arch Image Build)

   This document describes how to perform the build process in
   a self contained environment using fast booting virtual
   machines to address the issues listed above.

   The changes on the machine to become a build host will
   be reduced to the requirements of the {kiwi} `boxed plugin`

Requirements
------------

Add the {kiwi} repo from the Open Build Service. For details see
:ref:`installation-from-obs`. The following {kiwi} plugin needs to be
installed on the build system:

.. code:: bash

    $ sudo zypper in python3-kiwi_boxed_plugin

Building with the boxbuild command
----------------------------------

The installation of the {kiwi} boxed plugin has registered a new kiwi
command named `boxbuild`. The command implementation uses KVM as
virtualization technology and runs the {kiwi} `build` command inside of
a KVM controlled virtual machine. For running the build process in a
virtual machine it's required to provide VM images that are suitable
to perform this job. We call the VM images `boxes` and they contain
kiwi itself as well as all other components needed to build appliances.
Those boxes are hosted in the Open Build Service and are publicly
available at the `Subprojects` tab in the: `Virtualization:Appliances:SelfContained <https://build.opensuse.org/project/show/Virtualization:Appliances:SelfContained>`__
project.

As a user you don't need to work with the boxes because this is all done
by the plugin and provided as a service by the {kiwi} team. The `boxbuild`
command knows where to fetch the box and also cares for an update of the
box when it has changed.

Building an image with the `boxbuild` command is similar to building with
the `build` command. The plugin validates the given command call with the
capabilities of the `build` command. Thus one part of the `boxbuild` command
is exactly the same as with the `build` command. The separation between
`boxbuild` and `build` options is done using the `--` separator like
shown in the following example:

.. code:: bash

   $ kiwi-ng --type iso system boxbuild --box leap -- \
         --description kiwi/build-tests/{exc_description_disk} \
         --set-repo {exc_repo_leap} \
         --target-dir /tmp/myimage

.. note::

   The provided `--description` and `--target-dir` options are
   setup as shared folders between the host and the guest. No other
   data will be shared with the host.
