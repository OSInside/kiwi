.. _building_types:

Building Images for Supported Types
===================================

.. note::

   This document provides an overview about the supported {kiwi} image
   types. Before building an image with {kiwi} it's important to understand
   the different image types and their meaning.

.. toctree::
   :maxdepth: 1

   building_images/build_live_iso
   building_images/build_vmx_disk
   building_images/build_oem_disk
   building_images/build_docker_container
   building_images/build_wsl_container
   building_images/build_kis

Image Types
-----------

ISO Hybrid Live Image
  An iso image which can be dumped on a CD/DVD or USB stick
  and boots off from this media without interfering with other
  system storage components. A useful pocket system for testing
  and demo and debugging purposes.

Virtual Disk Image
  An image representing the system disk, useful for cloud frameworks
  like Amazon EC2, Google Compute Engine or Microsoft Azure.

OEM Expandable Disk Image
  An image representing an expandable system disk. This means after
  deployment the system can resize itself to the new disk geometry.
  The resize operation is configurable as part of the image description
  and an installation image for CD/DVD, USB stick and Network deployment
  can be created in addition.

Docker Container Image
  An archive image suitable for the docker container engine.
  The image can be loaded via the `docker load` command and
  works within the scope of the container engine

WSL Container Image
  An archive image suitable for the Windows Subsystem For Linux
  container engine. The image can be loaded From a Windows System
  that has support for WSL activated.

KIS Root File System Image
  An optional root filesystem image associated with a kernel and initrd.
  The use case for this component image type is highly customizable.
  Many different deployment strategies are possible.


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

- **image packages**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.packages`
- **image verified**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.verified`

In addition to the image binaries itself that depend on the image type:

image="tbz"
  For this image type the result is mainly a root tree packed in a tarball:

  - **root archive**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.tar.xz`

image="btrfs|ext2|ext3|ext4|squashfs|xfs"
  The image root tree data is packed into a filesystem image of the given
  type, hence the resutl for an `ext4` image would be:

  - **filesystem image**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.ext4`

image="iso"
  The image result is an ISO file:

  - **live image**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.iso`

image="vmx"
  An image representing the system disk. The disk format can be
  defined in :ref:`\<preferences\>\<type\><sec.preferences>` element as
  documented in :ref:`vmx`. For a `format="qcow2"` the result is:

  - **disk image**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.qcow2`

image="oem"
  An image representing an expandable system disk. As for `vmx` type this
  results in a disk image. In addition to the `vmx` type `oem` has a couple
  of optional additional installation images. {kiwi} can produce an
  installation ISO (by setting `installiso="true"` in
  :ref:`\<preferences\>\<type\><sec.preferences>`) or a tarball including
  the artifacts for a network deployment (by setting `installiso="true"` in
  :ref:`\<preferences\>\<type\><sec.preferences>`), see
  :ref:`OEM example<oem>` for further details. The results for `oem` can be:

  - **disk image**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.raw`
  - **installation image (optional)**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.install.iso`
  - **installation pxe archive (optional)**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.install.tar`

image="docker"
  An archive image suitable for the docker container engine. The result is
  a loadable (:command:`docker load -i <image>`) tarball:

  - **container**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.docker.tar.xz`

image="oci"
  An archive image that builds a container matching the OCI
  (Open Container Interface) standard. The result is a tarball matching OCI
  standards:

  - **container**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.oci.tar.xz`


image="appx"
  An archive image suitable for the Windows Subsystem For Linux
  container engine. The result is an `appx` binary file:

  - **container**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.appx`

image="kis"
  An optional root filesystem image associated with a kernel and initrd.
  All three binaries are packed in a tarball, see :ref:`kis` for further
  details about the kis archive:

  - **kis archive**: :file:`{exc_image_base_name}.x86_64-{exc_image_version}.tar.xz`

.. _supported-distributions:

Supported Distributions
-----------------------

{kiwi} can build images for the distributions which are **equal** or **newer**
compared to the table below. For anything older use the
legacy {kiwi} version *v7.x* For more details on the legacy {kiwi},
see: :ref:`legacy_kiwi`

The most compatible environment is provided if the build host is of the same
distribution than the target image. This always applies for the Open Build
Service (OBS). In other cases please check the table if your target combination
is known to be supported.


.. table::
   :align: left

   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | Host / Image     | CentOS 7   | Fedora 30     | openSUSE Leap 15 | RHEL 7   | SLE 12      | SLE 15      | openSUSE TW | Ubuntu 19   |
   +==================+============+===============+==================+==========+=============+=============+=============+=============+
   | CentOS 7         | yes        | no            | no               | yes      | no          | no          |  no         | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | Fedora 30        | untested   | yes           | no               | untested | no          | no          |  no         | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | openSUSE Leap 15 | untested   | **note:dnf**  | yes              | untested | no          | yes         |  no         | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | RHEL 7           | untested   | no            | no               | yes      | no          | no          |  no         | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | SLE 12           | no         | untested      | untested         | no       | yes         | no          |  no         | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | SLE 15           | untested   | **note:dnf**  | yes              | no       | no          | yes         |  untested   | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | openSUSE TW      | untested   | **note:dnf**  | yes              | untested | no          | untested    |  yes        | no          |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+
   | Ubuntu 19        | no         | no            | no               | no       | no          | no          |  no         | yes         |
   +------------------+------------+---------------+------------------+----------+-------------+-------------+-------------+-------------+

.. admonition:: dnf

   dnf is the package manager used on Fedora and RHEL and is
   the successor of yum. When {kiwi} builds images for this distributions
   the latest version of dnf is required to be installed on the host to
   build the image.

In general, our goal is to support any major distribution with {kiwi}. However
for building images we rely on core tools which are not under our control.
Also several design aspects of distributions like **secure boot** and working
with **upstream projects** are different and not influenced by us. There
are many side effects that can be annoying especially if the build host
is not of the same distribution vendor than the image target.

Supported Platforms and Architectures
-------------------------------------

Images built with {kiwi} are designed for a specific use case. The author of
the image description sets this with the contents in the {kiwi} XML document
as well as custom scripts and services. The following list provides an
abstract of the platforms where {kiwi} built images are productively used:

* Amazon EC2
* Microsoft Azure
* Google Compute Engine
* Private Data Centers based on OpenStack
* Bare metal deployments e.g Microsoft Azure Large Instance
* SAP workloads

The majority of the workloads is based on the x86 architecture. {kiwi}
also supports other architectures, shown in the table below:

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
   | ppc64        | no (alpha-phase)    |
   +--------------+---------------------+

.. admonition:: distro

   The support status for an architecture depends on the distribution.
   If the distribution does not build its packages for the desired
   architecture, {kiwi} will not be able to build an image for it
