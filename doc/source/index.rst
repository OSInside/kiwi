.. kiwi documentation master file

KIWI Documentation
==================

Welcome to the documentation for KIWI |version|- the command line utility to
build linux system appliances.

.. sidebar:: Links

   * `GitHub Sources <https://github.com/SUSE/kiwi>`__
   * `GitHub Releases <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
   * `Build Tests(x86) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86>`__
   * `Build Tests(arm) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_arm>`__
   * `Build Tests(s390) <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_s390>`__

.. toctree::
   :maxdepth: 1

   overview
   installation
   quickstart
   building
   commands
   development

Appliance ?
-----------

An appliance is a ready to use image of an operating system including
a preconfigured application for a specific use case. The appliance is
provided as an image file and needs to be deployed to, or activated in
the target system or service.

In KIWI the appliance is specified by a collection of human readable files
in a directory, also called as the `image description`. At least one XML
file :file:`config.xml` or :file:`.kiwi` is required. In addition
there may be as well other files like scripts or configuration data.

Contact
-------

* `Mailing list <https://groups.google.com/forum/#!forum/kiwi-images>`__

  The `kiwi-images` group is an open group and anyone can
  `subscribe <mailto:kiwi-images+subscribe@googlegroups.com>`__,
  even if you do not have a Google account.

* IRC:

  `#opensuse-kiwi` on irc.freenode.net
