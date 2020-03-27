.. _building_types:

Building Images
===============

.. note::

   This document provides an overview about the supported {kiwi} image
   types. Before building an image with {kiwi} it's important to understand
   the different image types and their meaning.

.. toctree::
   :maxdepth: 1

   building/build_live_iso
   building/build_vmx_disk
   building/build_oem_disk
   building/build_pxe_root_filesystem
   building/build_docker_container
   building/build_wsl_container
   building/build_containerized
   building/build_with_profiles
   building/build_in_buildservice

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

PXE root File System Image
  A root filesystem image which can be deployed via {kiwi}'s PXE netboot
  infrastructure. A client configuration file on the pxe server controls
  how the root filesystem image should be deployed. Many different
  deployment strategies are possible, e.g root over NBD, AoE or NFS for
  diskless and diskfull clients.

Docker Container Image
  An archive image suitable for the docker container engine.
  The image can be loaded via the `docker load` command and
  works within the scope of the container engine

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
