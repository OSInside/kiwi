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
   building/build_in_buildservice
   building/working_with_images


* ISO Hybrid Live Image

  An iso image which can be dumped on a CD/DVD or USB stick
  and boots off from this media without interferring with other
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
  infrastructure. A client configuration file on the pxe server controlls
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

KIWI can build the above image types for distributions
which are **equal** or **newer** compared to the following list:

*  CentOS 7
*  Fedora 25
*  openSUSE Leap 42
*  Red Hat Enterprise 7
*  SUSE Linux Enterprise 12
*  Tumbleweed
*  Ubuntu Xenial

For anything older please consider to use the legacy KIWI version *v7.x*
For more details on the legacy kiwi, see: :ref:`legacy_kiwi`.
