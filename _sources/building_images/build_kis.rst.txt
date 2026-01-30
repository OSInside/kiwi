.. _kis:

Build KIS Image (Kernel, Initrd, System)
========================================

.. sidebar:: Abstract

   This page explains how to build an image that consists
   out of three components: the kernel an initrd, and an
   optional root filesystem image. In {kiwi} terminology,
   this type of image is called KIS.

A KIS image is a collection of image components that are not
associated with a dedicated use case. This means that as far as {kiwi}
is concerned, it is not known in which environment these components
are expected to be used. The predecessor of this image type was called
`pxe` under the assumption that the components will be used
in a PXE boot environment. However, this assumption is not
always true, and the image components may be used in different
ways. Because there are so many possible deployment strategies
for a `kernel` plus `initrd` and optional `system root filesystem`,
{kiwi} provides this as the universal `KIS` type.

The former `pxe` image type still exist, but it is expected
to be used only in combination with the legacy `netboot` infrastructure,
as described in :ref:`build_legacy_pxe`.

To add a KIS build to an appliance, create a `type` element with
`image` set to `kis` in the :file:`config.xml` as shown below:

.. code:: xml

   <preferences>
       <type image="kis"/>
   </preferences>

With this image type setup, {kiwi} builds a kernel and initrd
not associated with any system root file system. Normally, such
an image is only useful with certain custom dracut extensions
as part of the image description.

The following attributes of the `type` element are often used when
building KIS images:

- `filesystem`: Specifies the root filesystem and triggers the build
  of an additional filesystem image of that filesystem. The generated
  kernel command-line options file (append file) then also
  include a `root=` parameter that references this filesystem image UUID.
  Whther the information from the append file should be used or not is
  optional.

- `kernelcmdline`: Specifies kernel command-line options that are
  part of the generated kernel command-line options file (append file).
  By default, the append file contains neither information nor the reference
  to the root UUID, if the `filesystem` attribute is used.

All other attributes of the `type` element that applies to an optional
root filesystem image remain in effect in the system image of a KIS
image as well.

With the appropriate settings present in :file:`config.xml`, you can use {kiwi} to
build the image:

.. code:: bash

   $ sudo kiwi-ng --type kis system build \
       --description kiwi/build-tests/{exc_description_pxe} \
       --set-repo {exc_repo_tumbleweed} \
       --target-dir /tmp/myimage

The resulting image components are saved in :file:`/tmp/myimage`.
Outside of a deployment infrastructure, the example KIS image can be
tested with QEMU as follows:

.. code:: bash

   $ sudo qemu
       -kernel /tmp/myimage/*.kernel \
       -initrd /tmp/myimage/*.initrd \
       -append "$(cat /tmp/myimage/*.append) rw" \
       -drive file=/tmp/myimage/{exc_image_base_name_pxe}.*-{exc_image_version},if=virtio,driver=raw \
       -serial stdio

.. note::

   For testing the components of a KIS image normally requires a deployment
   infrastructure and a deployment process. An example of a deployment
   infrastructure using PXE is provided by {kiwi} with the `netboot`
   infrastructure. However, that netboot infrastructure is no longer developed
   and only kept for compatibility reasons. For details, see
   :ref:`build_legacy_pxe`
