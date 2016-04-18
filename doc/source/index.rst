.. kiwi documentation master file

KIWI Appliance Builder
======================

.. toctree::
   :maxdepth: 1

   manual/kiwi
   api/kiwi

KIWI is an imaging solution that is based on an image XML description.
Such a description is represented by a directory which includes at least
one :file:`config.xml` or :file:`.kiwi` file and may as well include
other files like scripts or configuration data.

A collection of example image descriptions can be found on the github
repository here: https://github.com/SUSE/kiwi-descriptions. Most of the
descriptions provide a so called JeOS image. JeOS means Just enough
Operating System. A JeOS is a small, text only based image including a
predefined remote source setup to allow installation of missing
software components at a later point in time.

KIWI operates in two steps. The system build command combines
both steps into one to make it easier to start with KIWI. The first
step is the preparation step and if that step was successful, a
creation step follows which is able to create different image output
types.

In the preparation step, you prepare a directory including the contents
of your new filesystem based on one or more software package source(s)
The creation step is based on the result of the preparation step and
uses the contents of the new image root tree to create the output
image.

KIWI supports the creation of the following image types:

- ISO Hybrid Live Systems
- Virtual Disk for e.g cloud frameworks
- OEM Expandable Disk for system deployment from ISO or the network
- File system images for deployment in a pxe boot environment

Depending on the image type a variety of different disk formats
architectures and distributions are supported.

Installation and Quick Start
----------------------------

Take a look on the github project page how to install and build your
first image with KIWI: https://github.com/SUSE/kiwi

Need Help with KIWI
-------------------

- Mailing list: https://groups.google.com/forum/#!forum/kiwi-images
- IRC: `#opensuse-kiwi` on irc.freenode.net

The `kiwi-images` group is an open group and anyone can subscribe, even
if you do not have a Google account. Simply send mail to
mailto:kiwi-images+subscribe@googlegroups.com
