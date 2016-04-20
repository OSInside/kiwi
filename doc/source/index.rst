.. kiwi documentation master file

KIWI Appliance Builder
======================

.. sidebar:: Links

   * `GitHub Project <https://github.com/SUSE/kiwi>`__
   * `Sources <https://github.com/SUSE/kiwi/releases>`__
   * `RPM Packages <https://build.opensuse.org/package/show/Virtualization:Appliances:Builder/python3-kiwi>`__

.. toctree::
   :maxdepth: 1

   quickstart
   manual/kiwi
   api/kiwi


What is KIWI?
-------------

KIWI is an OS image and an appliance builder.

It is based on an image XML description. Such a description is represented by
a directory which includes at least one :file:`config.xml` or :file:`.kiwi`
file and may as well include other files like scripts or configuration data.

Feature Highlights
------------------

* Distribution independent design
* GPL v2 license
* Complete rewrite from Perl to Python
* openSUSE, SLES, RHEL [CentOS] supported
* Build images for virtualization systems, cloud, ISOs and more
* Supports the following image types:

  * ISO Hybrid Live Systems
  * Virtual Disk for e.g cloud frameworks
  * OEM Expandable Disk for system deployment from ISO or the network
  * File system images for deployment in a pxe boot environment
* Supported architectures: x86, x86_64, s390, ppc
* Help on mailinglist and IRC
* and many more

Image Example Descriptions
--------------------------

A collection of example image descriptions can be found on the GitHub
repository here: https://github.com/SUSE/kiwi-descriptions.

Most of the descriptions provide a so called "JeOS image" ("Just enough
Operating System"). A JeOS is a small, text only based image including a
predefined remote source setup to allow installation of missing
software components at a later point in time.

Concept
-------

KIWI operates in two steps. The system build command combines
both steps into one to make it easier to start with KIWI.

The first step is the *preparation step* and if that step was successful, a
*creation step* follows which is able to create different image output
types:

1. In the *preparation step*, you prepare a directory including the
   contents of your new filesystem based on one or more software package source(s).

2. The *creation step* is based on the result of the preparation step and
   uses the contents of the new image root tree to create the output image.



Help
----

* Mailing list: https://groups.google.com/forum/#!forum/kiwi-images

  The `kiwi-images` group is an open group and anyone can subscribe, even
  if you do not have a Google account.

  Send mail to `kiwi-images+subscribe@googlegroups.com
  <mailto:kiwi-images+subscribe@googlegroups.com>`__.
* IRC: `#opensuse-kiwi` on irc.freenode.net
