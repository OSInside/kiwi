.. _image_types:

Image Types
===========

.. note::

   Before building an image with {kiwi} it's important to understand
   the different image types and their meaning. This document provides
   an overview about the supported {kiwi} image types, their results
   and some words about the environment to run the build.

ISO Hybrid Live Image
  An iso image which can be dumped on a CD/DVD or USB stick
  and boots off from this media without interfering with other
  system storage components. A useful pocket system for testing
  and demo and debugging purposes. For further details refer
  to :ref:`hybrid_iso`

Virtual Disk Image
  An image representing the system disk, useful for cloud frameworks
  like Amazon EC2, Google Compute Engine or Microsoft Azure.
  For further details refer to :ref:`simple_disk`

OEM Expandable Disk Image
  An image representing an expandable system disk. This means after
  deployment the system can resize itself to the new disk geometry.
  The resize operation is configurable as part of the image description
  and an installation image for CD/DVD, USB stick and Network deployment
  can be created in addition. For further details refer to: :ref:`expandable_disk`

Docker Container Image
  An archive image suitable for the docker container engine.
  The image can be loaded via the `docker load` command and
  works within the scope of the container engine.
  For further details refer to: :ref:`building_docker_build`

WSL Container Image
  An archive image suitable for the Windows Subsystem For Linux
  container engine. The image can be loaded From a Windows System
  that has support for WSL activated. For further details refer
  to: :ref:`building_wsl_build`

KIS Root File System Image
  An optional root filesystem image associated with a kernel and initrd.
  The use case for this component image type is highly customizable.
  Many different deployment strategies are possible.
  For further details refer to: :ref:`kis`

Image Results
-------------

{kiwi} execution results in an appliance image after a successful run of
:ref:`kiwi_system_build` or :ref:`kiwi_system_create` command.
The result is the image binary in addition a couple of metadata files that can
be handy to describe or identify the resulting image. The output files follow
this naming convention:

`<image-name>.\<arch\>-\<version\>.\<extension\>`

where `<image-name>` is the name stated in the :ref:`image-description` as an
attribute of the :ref:`sec.image` element. The `<arch>` is the CPU
architecture used for the build, `<version>` is the image version defined in
:ref:`\<version\><sec.preferences>` element of the image description
and the `<extension>` is dependent on the image type and its definition.

Any {kiwi} appliance build results in, at least, the following output files:


1. The image binary, `<image-name>.\<arch\>-\<version\>.\<image-extension\>`:

   This is the file containig the actual image binary, depending
   on the image type and its definition it can be a virtual disk image
   file, and ISO image, a tarball, etc.

2. The `<image-name>.<arch>-<version>.packages` file:

   This file includes a sorted list of the packages
   that are included into the image. In fact this is normalized dump of the
   package manager database. It follows the following cvs format where each
   line is represented by:

   `<name>|\<epoch\>|\<version\>|\<release\>|\<arch\>|\<disturl\>|\<license\>`

   The values represented here are mainly based on RPM packages metadata.
   Other package managers may not provide all of these values, in such cases
   the format is the same and the fields that cannot be provided are set as
   `None` value. This list can be used to track changes across multiple
   builds of the same image description over time by diffing the
   packages installed.

3. The `<image-name>.<arch>-<version>.verified` file:

   This file is the output of a verification done by the package manager
   against the package data base. More specific it is the output of
   the :command:`rpm` verification process or :command:`dpkg` verification
   depending on the packaging technology selected for the image.
   In both cases the output follows the RPM verification syntax. This
   provides an overview of all packages status right before any boot of
   the image.

More specific  the result files for a given image name and version such
as `{exc_image_base_name}` and `{exc_image_version}` will be:

- **image packages**:
  :file:`{exc_image_base_name}.x86_64-{exc_image_version}.packages`
- **image verified**:
  :file:`{exc_image_base_name}.x86_64-{exc_image_version}.verified`

In addition to the image binaries itself that depend on the image type:

image="tbz"
  For this image type the result is mainly a root tree packed in a tarball:

  - **root archive**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.tar.xz`

image="btrfs|ext2|ext3|ext4|squashfs|xfs"
  The image root tree data is packed into a filesystem image of the given
  type, hence the resutl for an `ext4` image would be:

  - **filesystem image**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.ext4`

image="iso"
  The image result is an ISO file:

  - **live image**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.iso`

image="oem"
  An image representing an expandable disk image. {kiwi} can also produce an
  installation ISO for this disk image by setting `installiso="true"` in
  the :ref:`\<preferences\>\<type\><sec.preferences>`) section or a tarball
  including the artifacts for a network deployment by setting `installiso="true"`.
  For further details see :ref:`expandable_disk`. The results for `oem`
  can be:

  - **disk image**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.raw`
  - **installation image (optional)**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.install.iso`
  - **installation pxe archive (optional)**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.install.tar`

  The disk image can also be provided in one of the various virtual disk
  formats which can be specified in `format` attribute of the
  :ref:`\<preferences\>\<type\><sec.preferences>` section. For further
  details see :ref:`simple_disk`. The result for e.g  `format="qcow2"`
  would be:

  - **disk image**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.qcow2`

  instead of the `.raw` default disk format.

image="docker"
  An archive image suitable for the docker container engine. The result is
  a loadable (:command:`docker load -i <image>`) tarball:

  - **container**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.docker.tar.xz`

image="oci"
  An archive image that builds a container matching the OCI
  (Open Container Interface) standard. The result is a tarball matching OCI
  standards:

  - **container**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.oci.tar.xz`


image="appx"
  An archive image suitable for the Windows Subsystem For Linux
  container engine. The result is an `appx` binary file:

  - **container**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.appx`

image="kis"
  An optional root filesystem image associated with a kernel and initrd.
  All three binaries are packed in a tarball, see :ref:`kis` for further
  details about the kis archive:

  - **kis archive**:
    :file:`{exc_image_base_name}.x86_64-{exc_image_version}.tar.xz`
