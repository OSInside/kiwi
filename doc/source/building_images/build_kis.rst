.. _kis:

Build KIS Image (Kernel, Initrd, System)
========================================

.. sidebar:: Abstract

   This page explains how to build an image that consists
   out of three components. The kernel an initrd and an
   optional root filesystem image. In {kiwi} terminology
   this is called KIS.

A KIS image is a collection of image components that are not
associated with a dedicated use case. This means from a {kiwi}
perspective we don't know in which environment these components
are later used. The predecessor of this image type was called
`pxe` under the assumption that the components will be used
in a pxe boot environment. However this assumption is not
neccessarily true and the image components are used in a different
way. Because there are so many possible deployment strategies
for a `kernel` plus `initrd` and optional `system root filesystem`,
{kiwi} provides this as generic `KIS` type that is generically
usable.

The former `pxe` image type will continue to exist but is expected
to be used only in combination with the legacy `netboot` infrastructure
as described in :ref:`build_legacy_pxe`.

To add a KIS build to your appliance, create a `type` element with
`image` set to `kis` in your :file:`config.xml` as shown below:

.. code:: xml

   <preferences>
       <type image="kis"/>
   </preferences>

With this image type setup {kiwi} will just build a kernel and initrd
not associated to any system root file system. Usually such
an image is only useful with some custom dracut extensions
as part of the image description.

The following attributes of the `type` element are often used when
building KIS images:

- `filesystem`: Specifies the root filesystem and triggers the build
  of an additional filesystem image of that filesystem. The generated
  kernel command line options file (append file) will then also
  include a `root=` parameter that references this filesystem image UUID.
  If the information from the append file should be used or not is
  optional.

- `kernelcmdline`: Specifies kernel command line options that will be
  part of the generated kernel command line options file (append file).
  By default the append file contains no information or the reference
  to the root UUID if the `filesystem` attribute is used.

All other attributes of the `type` element that applies to an optional
root filesystem image will be effective in the system image of a KIS
image as well.

With the appropriate settings present in :file:`config.xml` {kiwi} can now
build the image:

.. code:: bash

   $ sudo kiwi-ng --type kis system build \
       --description kiwi/build-tests/{exc_description_pxe} \
       --set-repo {exc_repo_tumbleweed} \
       --target-dir /tmp/myimage

The resulting image components are saved in the folder :file:`/tmp/myimage`.
Outside of a deployment infrastructure the example KIS image can be
tested with QEMU as follows:

.. code:: bash

   $ sudo qemu
       -kernel /tmp/myimage/*.kernel \
       -initrd /tmp/myimage/*.initrd.xz \
       -append $(cat /tmp/myimage/*.append) \
       -hda /tmp/myimage/{exc_image_base_name_pxe}.*-{exc_image_version} \
       -serial stdio

.. note::

   For testing the components of a KIS image a deployment infrastructure
   and also a deployment process is usually needed. One example of a
   deployment infrastructure using PXE is provided by {kiwi} with the
   `netboot` infrastructure. However that netboot infrastructure is no
   longer developed and only kept for compatibiliy reasons. For details
   see :ref:`build_legacy_pxe`
