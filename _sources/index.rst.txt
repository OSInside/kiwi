.. kiwi documentation master file

Welcome to KIWI NG
==================

**Your flexible operating system image and appliance builder**

KIWI NG is a powerful, command-line-driven tool that allows you to create customized Linux operating system images for a variety of platforms and use cases. Whether you're building for bare metal, virtual machines, containers, or cloud environments, KIWI provides the flexibility and control you need to craft the perfect OS image.

.. note::
   This documentation covers {kiwi-product} |version|.

Why KIWI?
---------

* **Versatile Image Types**: Build everything from traditional ISOs and virtual machine images (VMware, KVM, Hyper-V) to container images (Docker, OCI), live systems for USB sticks, and images for cloud platforms (AWS, Azure, GCP).
* **Declarative by Design**: Define your entire image using a simple set of human-readable XML files. This allows for easy versioning, sharing, and reproducibility.
* **Cross-Distribution Support**: While born in the SUSE world, {kiwi} supports a wide range of Linux distributions, including openSUSE, SUSE Linux Enterprise, Red Hat Enterprise Linux, Fedora, CentOS, and Ubuntu.
* **Extensible and Customizable**: A flexible plugin architecture and the ability to include custom scripts and configuration files give you full control over the image-building process.
* **Battle-Tested**: {kiwi} is used by enterprises and open-source projects alike, and builds official images in the build service of SUSE and Fedora.

.. toctree::
   :maxdepth: 1
   :hidden:

   overview
   installation
   quickstart
   commands
   troubleshooting
   plugins
   concept_and_workflow
   image_description
   image_types_and_results
   building_images
   working_with_images
   contributing
   integration_testing
   api

.. sidebar:: Links

   * `GitHub Sources <https://github.com/OSInside/kiwi>`__
   * `GitHub Releases <https://github.com/OSInside/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
   * `Build Tests TumbleWeed(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:tumbleweed>`__
   * `Build Tests TumbleWeed(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm:tumbleweed>`__
   * `Build Tests TumbleWeed(s390) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_s390:tumbleweed>`__
   * `Build Tests TumbleWeed(ppc64le) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_ppc:tumbleweed>`__

   * `Build Tests RawHide(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:rawhide>`__
   * `Build Tests RawHide(s390) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_s390:rawhide>`__

   * `Build Tests Leap(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:leap>`__

   * `Build Tests Fedora(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:fedora>`__
   * `Build Tests Fedora(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm:fedora>`__

   * `Build Tests CentOS(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:centos>`__

   * `Build Tests Ubuntu(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:ubuntu>`__
   * `Build Tests Ubuntu(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm:ubuntu>`__

   * `Build Tests Debian(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:debian>`__

   * `Build Tests ArchLinux(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:archlinux>`__


Get Started
-----------

Ready to build your first image? Jump into the :doc:`quickstart` or explore the :doc:`concept_and_workflow` to get a deeper understanding of how {kiwi} works.

.. _contact:

Contact
-------

* `Mailing list <https://groups.google.com/forum/#!forum/kiwi-images>`__

  The `kiwi-images` group is an open group, and anyone can
  `subscribe <mailto:kiwi-images+subscribe@googlegroups.com>`__,
  even if you do not have a Google account.

* `Matrix <https://matrix.org>`__

  An open network for secure, decentralized communication. Please find the
  ``#kiwi:matrix.org`` room via
  `Matrix <https://matrix.to/#kiwi:matrix.org>`__ on the web
  or by using the supported
  `clients <https://matrix.org/ecosystem/clients>`__.
