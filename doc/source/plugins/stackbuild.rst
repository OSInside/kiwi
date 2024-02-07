.. _stackbuild:

Building based on Containers
============================

.. note:: **Abstract**

   When building images exposes one of the following
   requirements the stackbuild plugin provides an opportunity
   to address it:

   * Preserve the image rootfs for a later rebuild without
     requiring the original software repositories.

   * Build an image based on an existing container.

   * Build an image based on a container stack.

   * Transform a container into a {kiwi} image type

Installation
------------

Add the {kiwi} repo from the Open Build Service. For details see
:ref:`installation-from-obs`. The following {kiwi} plugin needs to be
installed on the build system:

.. code:: bash

    $ sudo zypper in python3-kiwi_stackbuild_plugin

Concept
-------

The design of the stackbuild plugin is two fold:

First the plugin comes with a command called `stash` which allows
to store a kiwi built root tree as an OCI container. OCI stands for
*Open Container Interface* and is a defacto standard format in the
container world. Once the container got created it can be managed
using the preferred container toolchain. The plugin code itself
uses `podman` to work with containers.

As a next step and with the root tree as a container the plugin offers
the opportunity to build images based on one ore more containers.
That's also the reason why the plugin is called *stackbuild* as it
allows you to stack different root containers together.
Consequently the other command provided is named `stackbuild`.

The `stash` and `stackbuild` commands can be used independently
from each other. If there is already a registry with containers
that should be used to build images from, `stackbuild` can
directly consume them.

This concept leads to a number of use cases and a few of them were
picked and put into the abstract of this article. For the purpose
of documenting the functionality of the plugin only a part of the
possibilities are taken into account as follows:

.. _stash:

Create a stash
--------------

The `stash` command creates an OCI compliant container from a given
{kiwi-product} image root tree and registers it in the local
container registry. From there a user can push it to any registry
of choice.

The following example creates a stash of a Tumbleweed build
and illustrates how to register it in a foreign container
registry:

.. code:: bash

    # Build some image...
    $ git clone https://github.com/OSInside/kiwi.git
    $ sudo kiwi-ng system build \
        --description kiwi/build-tests/x86/tumbleweed/test-image-MicroOS/ \
        --set-repo http://download.opensuse.org/tumbleweed/repo/oss \
        --target-dir /tmp/myTWToday

    # Stash the image root into a container
    $ sudo kiwi-ng system stash \
        --root /tmp/myTWToday/build/image-root \
        --container-name twmos-snapshot

    # Register the stash in a registry
    $ podman login
    $ podman push twmos-20211008 \
        docker://docker.io/.../twmos-snapshot:2021-10-08

If the `stash` command is called multiple times with the same
container-name this leads to a new layer in the container for
each call. To inspect the number of layers added to the
container the following command can be used:

.. code:: bash

    $ podman inspect twmos-snapshot

To list all stashes created by the `stash` command the following
command can be used

.. code:: bash

    $ kiwi-ng system stash --list

Rebuild from a stash
--------------------

The `stackbuild` command takes the given container(s) from the local or
remote registry and uses it/them to either rebuild an image from that
data or build a new image on top of that data. If multiple containers
are given the `stackbuild` command stacks them together in the order
as they were provided.

.. note:: 

   When using multiple containers the result stack root tree is
   created from a sequence of rsync commands into the same target
   directory. The stackbuild plugin does this with any container
   content given and does not check, validate or guarantee that
   the selection of containers are actually stackable or leads to
   an usable root tree. This means it's in the responsibility of
   the caller to make sure the provided containers can actually
   be stacked together in the given order.
   
To simply rebuild the image from the stash created in :ref:`stash`
call `stackbuild` as follows:

.. code:: bash

    # Delete the image
    $ sudo rm -rf /tmp/myTWToday

    # Rebuild image from stash
    $ sudo kiwi-ng system stackbuild \
        --stash twmos-snapshot:2021-10-08 \
        --target-dir /tmp/myTWToday

This rebuilds the image from the stash and the {kiwi} configuration
inside of the stash. As all rootfs data is already in the stash, the
command will not need external resources to rebuild the image.

Turn a container into a VM image
--------------------------------

Another use case for the `stackbuild` plugin is the transformation
of container images into another image type that is supported by {kiwi}.
The following example demonstrates how an existing container image
from the openSUSE registry can be turned into a virtual machine image.

When moving a container into a virtual machine image the following
aspects has to be taken into account:

1. A container image usually has no kernel installed.
2. A container image usually has no bootloader installed.
3. A container image usually has no user configured.

For a VM image the mentioned aspects are mandatory. Therefore
the following {kiwi} image description contains this additional
information which the container cannot provide: Create the
{kiwi} description as follows:

.. code:: bash

    $ mkdir container_to_VM_layer
    $ vi container_to_VM_layer/config.kiwi

And place the following content:

.. code:: xml

    <?xml version="1.0" encoding="utf-8"?>

    <image schemaversion="8.0" name="Leap-VM">
        <description type="system">
            <author>The Author</author>
            <contact>user@example.org</contact>
            <specification>
                Leap Container as VM
            </specification>
        </description>
        <preferences>
            <type image="oem" filesystem="xfs" firmware="uefi">
                <oemconfig>
                    <oem-resize>false</oem-resize>
                </oemconfig>
            </type>
            <version>1.99.1</version>
            <packagemanager>zypper</packagemanager>
            <locale>en_US</locale>
            <keytable>us</keytable>
            <timezone>UTC</timezone>
        </preferences>
        <repository type="rpm-md" alias="Leap">
            <source path="{exc_repo_leap}"/>
        </repository>
        <packages type="image">
            <package name="grub2"/>
            <package name="grub2-x86_64-efi" arch="x86_64"/>
            <package name="grub2-i386-pc"/>
            <package name="shim"/>
            <package name="kernel-default"/>
        </packages>
        <users>
            <user password="$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0" home="/root" name="root" groups="root"/>
        </users>
    </image>

To build the virtual machine image from the current hosted Leap 15.3
container at SUSE, call the following `stackbuild` command:

.. code:: bash

    $ sudo kiwi-ng system stackbuild \
        --stash leap:{exc_os_version} \
        --from-registry registry.opensuse.org/opensuse \
        --target-dir /tmp/myLeap \
        --description container_to_VM_layer

The resulting virtual machine image can be booted as follows:

.. code:: bash

    $ qemu-kvm Leap-VM.x86_64-1.99.1.raw
