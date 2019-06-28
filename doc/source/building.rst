.. _building_types:

Building Images
===============

.. hint::

   This document provides an overview about the supported KIWI image
   types. Before building an image with KIWI it's important to understand
   the different image types and their meaning.

.. toctree::
   :maxdepth: 1

   building/build_live_iso
   building/build_vmx_disk
   building/build_oem_disk
   building/build_pxe_root_filesystem
   building/build_docker_container
   building/build_containerized
   building/build_with_profiles
   building/build_in_buildservice
   building/working_with_images

* ISO Hybrid Live Image

  An iso image which can be dumped on a CD/DVD or USB stick
  and boots off from this media without interfering with other
  system storage components. A useful pocket system for testing
  and demo and debugging purposes.

* Virtual Disk Image

  An image representing the system disk, useful for cloud frameworks
  like Amazon EC2, Google Compute Engine or Microsoft Azure.

* OEM Expandable Disk Image

  An image representing an expandable system disk. This means after
  deployment the system can resize itself to the new disk geometry.
  The resize operation is configurable as part of the image description
  and an installation image for CD/DVD, USB stick and Network deployment
  can be created in addition.

* PXE root File System Image

  A root filesystem image which can be deployed via KIWI's PXE netboot
  infrastructure. A client configuration file on the pxe server controls
  how the root filesystem image should be deployed. Many different
  deployment strategies are possible, e.g root over NBD, AoE or NFS for
  diskless and diskfull clients.

* Docker Container Image

  An archive image suitable for the docker container engine.
  The image can be loaded via the `docker load` command and
  works within the scope of the container engine

.. _supported-distributions:

Supported Distributions
-----------------------

KIWI can build images for the distributions which are **equal** or **newer**
compared to the table below. For anything older use the
legacy KIWI version *v7.x* For more details on the legacy KIWI,
see: :ref:`legacy_kiwi`

The most compatible environment is provided if the build host is of the same
distribution than the target image. This always applies for the Open Build
Service (OBS). In other cases please check the table if your target combination
is known to be supported.


.. table::
   :align: left

   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | Host / Image     | CentOS 7   | Fedora 25     | openSUSE Leap 15 | RHEL 7   | openSUSE TW | Ubuntu 16 |
   +==================+============+===============+==================+==========+=============+===========+
   | CentOS 7         | yes        | no            | no               | yes      | no          | no        |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | Fedora 25        | untested   | yes           | no               | untested | no          | no        |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | openSUSE Leap 15 | untested   | **note:dnf**  | yes              | untested | no          | no        |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | RHEL 7           | untested   | no            | no               | yes      | no          | no        |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | openSUSE TW      | untested   | **note:dnf**  | yes              | untested | yes         | no        |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+
   | Ubuntu 16        | no         | no            | no               | no       | no          | yes       |
   +------------------+------------+---------------+------------------+----------+-------------+-----------+

.. admonition:: dnf

   dnf is the package manager used on Fedora and RHEL and is
   the successor of yum. When KIWI builds images for this distributions
   the latest version of dnf is required to be installed on the host to
   build the image.

In general, our goal is to support any major distribution with KIWI. However
for building images we rely on core tools which are not under our control.
Also several design aspects of distributions like **secure boot** and working
with **upstream projects** are different and not influenced by us. There
are many side effects that can be annoying especially if the build host
is not of the same distribution vendor than the image target.

Supported Platforms and Architectures
-------------------------------------

Images built with KIWI are designed for a specific use case. The author of
the image description sets this with the contents in the KIWI XML document
as well as custom scripts and services. The following list provides a brief
overview of the platforms where KIWI built images are productively used:

* Amazon EC2
* Microsoft Azure
* Google Compute Engine
* Private Data Centers based on OpenStack
* Bare metal deployments e.g Microsoft Azure Large Instance
* SAP workloads

For further information or on interest in one of the above areas,
contact us directly: :ref:`contact_us`

The majority of the workloads is based on the x86 architecture. KIWI
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
   architecture, KIWI will not be able to build an image for it
