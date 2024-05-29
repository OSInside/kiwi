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
`boxbuild` and `build` options is done using the `--` separator. The following
example shows how to build one of {kiwi}'s integration test image:

.. code:: bash

   $ kiwi-ng --type oem system boxbuild --box leap -- \
         --description KIWI_GIT_CHECKOUT/build-tests/{exc_description_disk} \
         --set-repo {exc_repo_leap} \
         --target-dir /tmp/myimage

.. note::

   The provided `--description` and `--target-dir` options are
   setup as shared folders between the host and the box. No other
   data will be shared with the host.

Sharing Backends
----------------

As mentioned above, the `boxbuild` call shares the two host directories
provided in `--description` and `--target-dir` with the box. To do this
the following sharing backends are supported:

``--9p-sharing``
  With QEMU's `9pfs` you can create virtual filesystem devices
  (virtio-9p-device) and expose them to the box. For more information
  see `9pfs <https://wiki.qemu.org/Documentation/9psetup>`__. Using
  this sharing backend does not require any setup procedure from the
  user and is also the default for `boxbuild`
   
``--sshfs-sharing``
  SSHFS is a FUSE-based filesystem client for mounting remote
  directories over a Secure Shell connection (SSH). In `boxbuild`
  this is used to mount directories from the host into the box.
  Because this runs through an SSH connection the host must allow
  connections from the box. If you plan to use `sshfs` add the
  following SSH public key to the :file:`~/.ssh/authorized_keys`
  file of the user which is expected to call `boxbuild`

  .. code:: bash

     echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCtiqDaYgEMkr7za7qc4iPXftgu/j3sodPOtpoG8PinwRX6/3xZteOJzCH2qCZjEgA5zsP9lxy/119cWXvdxFUvyEINjH77unzRnaHj/yTXPhHuhHgAiEubuHer2gZoOs+UH4cGJLKCrabjTjZdeK9KvL+hoAgJaWxDUvGsXYDQTBHXlKjniOL1MGbltDBHnYhu4k+PjjJ+UEBN+8+F74Y5fYgIovXXY88WQrybuEr1eAYjhvk/ln6TKw1P6uvVMuIbAGUgnZFntDCI91Qw8ps1j+lX3vNc8ZBoOwM6nHZqq4FAqbXuH+NvQFS/xDM6wwZQhAe+14dTQBA5F1mgCVf+fSbteb0/CraSGmgKIM8aPnK8rfF+BY6Jar3AJFKVRPshRzrQj6CWYu3BfmOLupCpqOK2XFyoU2lEpaZDejgPSJq/IBGZdjKplWJFF8ZRQ01a8eX8K2fjrQt/4k9c7Pjlg1aDH8Sf+5+vcehlSNs1d50wnFoaIPrgDdy04omiaJ8= kiwi@boxbuild" >> ~/.ssh/authorized_keys

  The public key mentioned here is associated with an SSH key pair
  we provide in the pre-built box images.

  .. warning::

     If the `sshfs` backend is used without the host trusting the box,
     the `boxbuild` call will become interactive at the time of the sshfs
     mount. In this case the user might be asked for a passphrase or
     depending on the host `sshd` setup the request will be declined and
     the boxbuild fails.

``--virtiofs-sharing``
  QEMU virtio-fs shared file system daemon. Share a host directory tree
  with a box through a virtio-fs device. For more information
  see `virtiofs <https://qemu.readthedocs.io/en/latest/tools/virtiofsd.html>`__.
  Using this sharing backend does not require any setup procedure from the
  user  

  .. warning::

     virtiofs support was added but considered experimental and
     not yet stable across the distributions. Feedback welcome.
